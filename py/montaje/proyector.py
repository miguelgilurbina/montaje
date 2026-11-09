"""El sonido del proyector: lo que suena cuando el video se hace pasar por película.

Como `sonorizar`, va sobre un render ya hecho y copia la imagen sin tocarla. Lee
del timeline dónde hay película y suma, sintetizado en código (sin muestras):

- **traqueteo** — la película pasando por la ventanilla: un golpecito por cuadro
  (24 por segundo), con el temblor de un mecanismo viejo, y el **zumbido** del motor;
  mientras dure una capa `pelicula` o `cuenta`;
- **el pop del 2** — el pitido de sincronía que suena en el 2 de la cuenta regresiva
  de las colas de película;
- **clac de diapositiva** — cada vez que una «foto que despierta» entra (una capa
  con `congelar`): el carro del proyector que cambia la diapositiva.

    python montaje.py proyector <p> [--version v] [--render archivo.mp4]

El nivel de los efectos se fija contra el de la canción (medido): por defecto
`nivel` = 16 dB por debajo. Deja `<render>-proyector.mp4` y, para mirarla, la pista
de efectos sola en `analisis/`.
"""

from __future__ import annotations

import subprocess

import numpy as np

from .rutas import Proyecto, leer_json, salir
from .sonido import SR, _banda, _normalizar, _pasabajos


def traqueteo(dur: float, fps: float, rng) -> np.ndarray:
    """Un golpecito por cuadro, el zumbido del motor y un siseo que tiembla; estéreo, RMS 1."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = np.zeros(n)
    golpe = _banda(rng.standard_normal(int(0.012 * SR)), 900, 4500) * np.exp(-np.arange(int(0.012 * SR)) / (0.0025 * SR))
    k = 0.0
    while k < dur:
        i = int(k * SR)
        fin = min(n, i + len(golpe))
        y[i:fin] += golpe[: fin - i] * (0.6 + 0.4 * rng.random())
        k += 1 / fps * (1 + 0.04 * rng.standard_normal())  # el mecanismo no es exacto
    motor = 0.25 * np.sin(2 * np.pi * 50 * t) + 0.12 * np.sin(2 * np.pi * 100 * t + 0.3) + 0.05 * np.sin(2 * np.pi * 150 * t)
    motor *= 1 + 0.15 * np.sin(2 * np.pi * 0.7 * t)
    siseo = _banda(rng.standard_normal(n), 2500, 8000) * 0.15 * (1 + 0.5 * np.sin(2 * np.pi * 6 * t))
    mono = _normalizar(y) * 0.8 + motor * 0.35 + siseo
    estereo = np.stack([mono, np.roll(mono, int(0.0007 * SR))], axis=1)
    return estereo / np.sqrt(np.mean(estereo**2))


def pop() -> np.ndarray:
    """El pitido de un cuadro (1 kHz) del 2 de la cuenta regresiva."""
    t = np.arange(int(0.042 * SR)) / SR
    y = np.sin(2 * np.pi * 1000 * t) * np.minimum(1, np.minimum(t, t[::-1]) / 0.002)
    return np.stack([y, y], axis=1) / np.sqrt(np.mean(y**2))


def clac(rng) -> np.ndarray:
    """El carro del proyector de diapositivas: un golpe seco, el arrastre y el encaje."""
    def chasquido(largo: float, corte: float, caida: float) -> np.ndarray:
        r = rng.standard_normal(int(largo * SR))
        return _pasabajos(r, corte) * np.exp(-np.arange(len(r)) / (caida * SR))
    y = np.zeros(int(0.28 * SR))
    a = chasquido(0.04, 3500, 0.006)
    y[: len(a)] += a
    arrastre = _banda(rng.standard_normal(int(0.12 * SR)), 400, 2000) * np.hanning(int(0.12 * SR)) * 0.25
    y[int(0.03 * SR) : int(0.03 * SR) + len(arrastre)] += arrastre
    b = chasquido(0.05, 2500, 0.01) * 0.9
    y[int(0.17 * SR) : int(0.17 * SR) + len(b)] += b
    grave = np.sin(2 * np.pi * 70 * np.arange(int(0.08 * SR)) / SR) * np.exp(-np.arange(int(0.08 * SR)) / (0.02 * SR)) * 0.6
    y[int(0.17 * SR) : int(0.17 * SR) + len(grave)] += grave
    y = _normalizar(y)
    return np.stack([y, y * 0.92], axis=1) / np.sqrt(np.mean(y**2))


def _nivel_rms(ruta) -> float:
    """RMS (dBFS) del audio del render."""
    crudo = subprocess.run(["ffmpeg", "-v", "error", "-i", str(ruta), "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                           capture_output=True, check=True).stdout
    x = np.frombuffer(crudo, dtype=np.float32)
    return float(20 * np.log10(np.sqrt(np.mean(x.astype(float) ** 2)) + 1e-9))


def proyector(p: Proyecto, render: str | None, nivel: float = 16.0) -> None:
    import soundfile as sf

    tl = leer_json(p.timeline)
    fps = tl["fps"]
    origen = p.salidas / "render" / (render or (f"{p.version}-final.mp4" if p.version else "final.mp4"))
    if not origen.exists():
        salir(f"no existe el render {origen}")
    dur = tl["duracion"] / fps
    # Un render de un tramo («…-final-44-60.mp4») empieza en el segundo 44 del timeline.
    import re

    tramo = re.search(r"-(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?|fin)$", origen.stem)
    corrimiento = 0.0
    if tramo:
        # «…-9-16» también puede ser un formato: vale como tramo sólo si el render dura lo que dice el nombre.
        largo = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(origen)],
                                     capture_output=True, text=True, check=True).stdout)
        dice = (dur if tramo.group(2) == "fin" else float(tramo.group(2))) - float(tramo.group(1))
        if abs(largo - dice) < 0.5:
            corrimiento = float(tramo.group(1))
    rng = np.random.default_rng(5)
    pista = np.zeros((int(dur * SR) + SR, 2))

    def poner(s: np.ndarray, t: float, ganancia: float) -> None:
        t -= corrimiento
        if t + len(s) / SR < 0:
            return
        if t < 0:
            s, t = s[int(-t * SR) :], 0.0
        i = int(t * SR)
        fin = min(len(pista), i + len(s))
        if fin > i:
            pista[i:fin] += s[: fin - i] * ganancia

    tramos = [(s["ini"] / fps, s["fin"] / fps) for s in tl.get("sintesis", []) if s["tipo"] in ("pelicula", "cuenta")]
    for a, b in _unir(tramos):
        tr = traqueteo(b - a, fps, rng)
        env = np.minimum(1, np.minimum(np.arange(len(tr)), np.arange(len(tr))[::-1]) / (0.4 * SR))[:, None]
        poner(tr * env, a, 1.0)
    pops = 0
    for s in tl.get("sintesis", []):
        if s["tipo"] == "cuenta":
            for ini, numero in s["numeros"]:
                if numero == 2:
                    poner(pop(), ini / fps, 0.7)
                    pops += 1
    clacs = sorted({c["ini"] / fps for c in tl["capas"] if c.get("video", {}).get("congelar")})
    for t in clacs:
        poner(clac(rng), t, 0.9)
    if not np.any(pista):
        salir("el timeline no tiene película, cuenta ni fotos que despiertan: no hay proyector que sonar")

    # Nivel: la pista entera (RMS 1 en sus partes) se lleva a `nivel` dB bajo la canción.
    cancion = _nivel_rms(origen)
    activo = np.sqrt(np.mean(pista[np.any(pista != 0, axis=1)] ** 2))
    pista *= 10 ** ((cancion - nivel) / 20) / (activo + 1e-9)
    pico = np.abs(pista).max()
    if pico > 0.5:
        pista *= 0.5 / pico
    efectos = p.salida("analisis", f"proyector-{origen.stem}.wav")
    sf.write(efectos, pista.astype(np.float32), SR)
    destino = origen.with_name(origen.stem + "-proyector.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(origen), "-i", str(efectos),
                    "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first:normalize=0[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(destino)], check=True)
    print(f"proyector: {len(_unir(tramos))} tramos de película, {pops} pop del 2, {len(clacs)} clacs de diapositiva; "
          f"canción {cancion:.1f} dBFS, efectos {nivel:g} dB abajo")
    print(f"→ {destino}\n→ {efectos}")


def _unir(tramos: list[tuple[float, float]]) -> list[tuple[float, float]]:
    unidos: list[list[float]] = []
    for a, b in sorted(tramos):
        if unidos and a <= unidos[-1][1]:
            unidos[-1][1] = max(unidos[-1][1], b)
        else:
            unidos.append([a, b])
    return [(a, b) for a, b in unidos]
