"""Sonido: la capa de efectos que subraya los momentos del montaje.

Va después de cerrar la imagen, como en la postproducción de verdad (montaje
cerrado → diseño sonoro → masterización): toma un render ya hecho, le suma los
efectos y copia el video sin tocarlo. Cambiar un volumen cuesta segundos, no
otro render.

Los efectos se **sintetizan en código** (numpy), sin muestras grabadas: no hay
derechos que pedir, y los que tienen altura se afinan a la tonalidad del tramo.
Cada momento del timeline tiene su sonido:

| Momento | Sonido |
|---|---|
| `destacado` | **impacto** grave al entrar (y la canción se agacha un instante); un **soplo** suave cuando vuela a su lugar |
| `destacado` con `firma` | impacto + **campana** afinada a la tónica |
| `rafaga` | una **subida** de un golpe que desemboca en ella y un **obturador** en cada corte |
| `barrido` | un **soplo** que cruza de un lado al otro, en sentido contrario a la cámara (como se mueve la imagen) |
| `salvapantallas` | **estática** de radio AM con su silbido de sintonía, y un **rebote** en cada borde que toca el logo (bordes laterales: la quinta; arriba y abajo: la tónica; esquina: el acorde) |

Configuración en proyecto.json (todo opcional):

    "base": {"proyecto": "05-collage-curiana", "render": "curiana-3x2.mp4"},
    "nombre_salida": "curiana-3x2-sonido",
    "sonido": {
      "efectos": {"obturador": -3, "estatica": false},   # dB sobre lo de fábrica, o false
      "agachar": 3                                        # dB que baja la canción en cada impacto
    }

Sin `base`, usa el timeline y el render (`sonido.render`) del propio proyecto.
Deja el render con sonido en `render/`, la pista de efectos sola en
`sonido/efectos.wav` y un dibujo de la mezcla en `analisis/sonido.png`.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, fftconvolve, istft, sosfilt, stft

from .rutas import Proyecto, leer_json, salir

SR = 48000

# Nivel de pico de cada efecto (dBFS) antes de lo que pida el proyecto. La canción
# está masterizada fuerte (picos cerca de 0 dBFS): un impacto a −8 se siente sin tapar.
NIVEL = {
    "impacto": -9.0,
    "campana": -12.0,
    "soplo": -9.0,
    "vuelo": -11.0,
    "subida": -8.0,
    "obturador": -11.0,
    "rebote": -16.0,
    "estatica": -38.0,  # este es RMS: es una cama, no un golpe
}

# Perfiles de Krumhansl-Kessler para estimar la tonalidad.
_MAYOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
_MENOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
NOTAS = ["do", "do#", "re", "re#", "mi", "fa", "fa#", "sol", "sol#", "la", "la#", "si"]


# ── Utilidades de señal ────────────────────────────────────────────────────

def _t(dur: float) -> np.ndarray:
    return np.arange(int(dur * SR)) / SR


def _hz(clase: int, octava: int) -> float:
    return 440.0 * 2 ** ((12 * (octava + 1) + clase - 69) / 12)


def _banda(x: np.ndarray, bajo: float, alto: float, orden: int = 4) -> np.ndarray:
    return sosfilt(butter(orden, [bajo, alto], btype="bandpass", fs=SR, output="sos"), x)


def _pasabajos(x: np.ndarray, corte: float, orden: int = 2) -> np.ndarray:
    return sosfilt(butter(orden, corte, btype="lowpass", fs=SR, output="sos"), x)


def _paneo(mono: np.ndarray, p) -> np.ndarray:
    """Paneo de igual potencia; `p` en [-1, 1], fijo o uno por muestra."""
    ang = (np.asarray(p, dtype=float) + 1) * np.pi / 4
    return np.stack([mono * np.cos(ang), mono * np.sin(ang)], axis=1)


def _sala(x: np.ndarray, rt60: float, mezcla: float, rng) -> np.ndarray:
    """Reverberación por convolución con ruido que decae: una sala sin muestras."""
    if x.ndim == 1:
        x = _paneo(x, 0.0) * np.sqrt(2)
    n = int(rt60 * SR)
    caida = np.exp(-6.9 * np.arange(n) / n)
    salida = np.zeros((len(x) + n - 1, 2))
    for c in range(2):
        ir = _pasabajos(rng.standard_normal(n), 6000) * caida
        ir /= np.sqrt(np.sum(ir**2))
        salida[:, c] = fftconvolve(x[:, c], ir)
    salida[: len(x)] += x * (1 - mezcla) / max(mezcla, 1e-6)
    return salida * mezcla


def _normalizar(x: np.ndarray) -> np.ndarray:
    pico = np.max(np.abs(x))
    return x / pico if pico > 0 else x


def _fundidos(x: np.ndarray, entrada: float = 0.003, salida: float = 0.02) -> np.ndarray:
    ne, ns = int(entrada * SR), int(salida * SR)
    env = np.ones(len(x))
    if ne:
        env[:ne] = np.linspace(0, 1, ne)
    if ns:
        env[-ns:] = np.minimum(env[-ns:], np.linspace(1, 0, ns))
    return x * (env[:, None] if x.ndim == 2 else env)


# ── Los efectos ────────────────────────────────────────────────────────────

def soplo(dur: float, pico: float, pan: tuple[float, float], rng) -> np.ndarray:
    """*Whoosh*: ruido cuyo filtro sube hasta el pico y vuelve a bajar, cruzando de un lado al otro."""
    n = int(dur * SR)
    f, tt, Z = stft(rng.standard_normal(n), SR, nperseg=1024)
    u = tt / dur
    fc = np.where(u < pico, 280 * (2800 / 280) ** (u / pico), 2800 * (500 / 2800) ** ((u - pico) / (1 - pico)))
    f = np.maximum(f, 1.0)
    Z *= np.exp(-0.5 * (np.log2(f[:, None] / fc[None, :]) / 0.85) ** 2)
    y = istft(Z, SR, nperseg=1024)[1][:n]
    us = np.arange(len(y)) / SR / dur
    env = np.where(us < pico, (us / pico) ** 2.5, np.exp(-(us - pico) * dur / 0.16))
    y = y * env
    return _normalizar(_sala(_paneo(y, np.linspace(*pan, len(y))), 0.9, 0.18, rng))


def impacto(f0: float, rng) -> np.ndarray:
    """Golpe grave: un seno que cae de altura hasta la tónica, un chasquido y aire."""
    t = _t(1.8)
    frec = f0 * (1 + 1.6 * np.exp(-t / 0.05))
    cuerpo = np.sin(2 * np.pi * np.cumsum(frec) / SR) * np.exp(-t / 0.5)
    golpe = _pasabajos(rng.standard_normal(len(t)), 2500) * np.exp(-t / 0.012)
    aire = _banda(rng.standard_normal(len(t)), 3000, 9000) * np.exp(-t / 0.3) * 0.12
    y = np.tanh(1.6 * (cuerpo + 0.6 * golpe + aire))
    return _normalizar(_sala(_fundidos(y), 1.8, 0.22, rng))


def campana(clase: int, menor: bool, rng) -> np.ndarray:
    """Campana afinada a la tónica: parciales de campana (hum, prima, tercera, quinta, nominal…)."""
    f0 = _hz(clase, 4)
    t = _t(3.0)
    tercera = 1.2 if menor else 1.25
    parciales = [(0.5, 0.55, 2.6), (1.0, 1.0, 2.2), (tercera, 0.45, 1.6), (1.5, 0.35, 1.3), (2.0, 0.6, 1.5),
                 (2.52, 0.22, 0.8), (3.0, 0.2, 0.6), (4.07, 0.12, 0.4), (5.43, 0.08, 0.3)]
    y = sum(a * np.sin(2 * np.pi * f0 * r * t + rng.uniform(0, 6.28)) * np.exp(-t / d) for r, a, d in parciales)
    y = y * (1 - np.exp(-t / 0.002))
    return _normalizar(_sala(_fundidos(y, salida=0.3), 2.5, 0.3, rng))


def subida(dur: float, clase: int, rng) -> np.ndarray:
    """*Riser*: ruido que se abre hacia los agudos y un tono que sube dos octavas; desemboca seco."""
    n = int(dur * SR)
    u = np.arange(n) / n
    ruido = np.stack([rng.standard_normal(n), rng.standard_normal(n)], axis=1)
    f, tt, Z = stft(ruido.T, SR, nperseg=1024)
    fc = 500 * (6000 / 500) ** (tt / dur)
    Z *= np.exp(-0.5 * (np.log2(np.maximum(f, 1)[:, None] / fc[None, :]) / 1.0) ** 2)[None]
    y = istft(Z, SR, nperseg=1024)[1].T[:n]
    f_tono = _hz(clase, 3) * 4 ** u
    tono = np.sin(2 * np.pi * np.cumsum(f_tono) / SR) * 0.35
    y = (y + tono[:, None]) * (u**3)[:, None]
    return _normalizar(_fundidos(y, entrada=0.01, salida=0.006))


def obturador(rng) -> np.ndarray:
    """Un corte de la ráfaga: el doble chasquido de un obturador y un golpecito grave."""
    t = _t(0.09)
    clic = _banda(rng.standard_normal(len(t)), 1500, 7000) * np.exp(-t / 0.004)
    segundo = np.roll(clic * 0.55, int(0.011 * SR))
    segundo[: int(0.011 * SR)] = 0
    grave = np.sin(2 * np.pi * 170 * t) * np.exp(-t / 0.012) * 0.4
    return _normalizar(_fundidos(clic + segundo + grave, entrada=0.0005))


def rebote(frecs: list[float], rng) -> np.ndarray:
    """El logo toca un borde: una nota corta y redonda (un acorde si es una esquina)."""
    t = _t(0.7)
    y = sum(np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t) for f in frecs)
    return _fundidos(y * (1 - np.exp(-t / 0.002)) * np.exp(-t / 0.14))


def estatica(dur: float, rng) -> np.ndarray:
    """Cama de radio AM entre emisoras: ruido de banda angosta, crepitar y un silbido de sintonía que deriva."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    base = _banda(rng.standard_normal(n), 250, 3500)
    ondula = 0.75 + 0.15 * np.sin(2 * np.pi * 0.31 * t) + 0.1 * np.sin(2 * np.pi * 1.7 * t + 1)
    crepita = np.zeros(n)
    golpes = rng.random(n) < 28 / SR
    crepita[golpes] = rng.standard_normal(golpes.sum()) * 2.5
    crepita = _banda(crepita, 800, 6000, 2)
    silbido_f = 900 + 350 * np.sin(2 * np.pi * t / max(dur, 1) * 1.3) + 40 * np.sin(2 * np.pi * 5.5 * t)
    silbido = np.sin(2 * np.pi * np.cumsum(silbido_f) / SR) * 0.18 * np.clip(np.sin(np.pi * t / dur) * 1.5, 0, 1)
    y = base * ondula + crepita + silbido
    y = _fundidos(y, entrada=0.27, salida=0.27)
    izq, der = y, np.roll(y, int(0.0007 * SR))
    estereo = np.stack([izq, der], axis=1)
    return estereo / np.sqrt(np.mean(estereo**2))  # RMS 1: su nivel se da en RMS


# ── Lectura del timeline ───────────────────────────────────────────────────

def _tonalidad(ruta: Path, desde: float, hasta: float | None) -> tuple[int, bool]:
    import librosa

    y, sr = librosa.load(str(ruta), sr=22050, mono=True, offset=desde, duration=(hasta - desde) if hasta else None)
    croma = librosa.feature.chroma_cqt(y=y, sr=sr).mean(axis=1)
    mejor = max(
        ((np.corrcoef(croma, np.roll(perfil, k))[0, 1], k, menor) for k in range(12) for menor, perfil in ((False, _MAYOR), (True, _MENOR))),
    )
    return mejor[1], mejor[2]


def _toques(s: dict, W: int, H: int) -> list[tuple[float, str, float]]:
    """Cuándo toca el logo cada borde en un tramo de salvapantallas (cuadro, borde, x en pantalla)."""
    dur = s["fin"] - s["ini"]
    mx, my = W - s["ancho"], H - s["alto"]

    def pos(p0, v, t, mx_):
        periodo = 2 * mx_
        m = (p0 + v * t) % periodo
        return m if m <= mx_ else periodo - m

    toques = []
    for eje, p0, v, m in (("x", s["x0"], s["vx"], mx), ("y", s["y0"], s["vy"], my)):
        if not v:
            continue
        k = int(np.floor(p0 / m)) + (1 if v > 0 else 0)
        while True:
            t = (k * m - p0) / v
            if t >= dur:
                break
            if t > 0:
                toques.append((s["ini"] + t, eje, pos(s["x0"], s["vx"], t, mx) / mx))
            k += 1 if v > 0 else -1
    return sorted(toques)


def partitura(tl: dict) -> list[dict]:
    """Los eventos de sonido que piden los momentos y el logo del timeline (tiempos en segundos)."""
    fps = tl["fps"]
    golpe = 60 / tl.get("meta", {}).get("bpm", 90)
    ev: list[dict] = []
    for mo in tl.get("momentos", []):
        ini, fin = mo["ini"] / fps, mo["fin"] / fps
        if mo["tipo"] == "destacado":
            ev.append({"efecto": "impacto", "t": ini, "agacha": True, "que": f"destacado {mo.get('id', '')}"})
            if mo.get("pieza", -1) < 0 and not mo.get("desde"):
                ev.append({"efecto": "campana", "t": ini, "que": "firma"})
            else:
                despega = (mo["fin"] - mo["salida"]) / fps
                ev.append({"efecto": "vuelo", "t": despega, "dur": fin - despega + 0.25, "pico": 0.6, "que": "vuelve a su lugar"})
        elif mo["tipo"] == "rafaga":
            ev.append({"efecto": "subida", "t": ini - golpe, "dur": golpe, "que": "antes de la ráfaga"})
            for k, im in enumerate(mo["imagenes"]):
                ev.append({"efecto": "obturador", "t": im["ini"] / fps, "extra": 5.0 if k == 0 else 0.0, "pan": 0.35 * (-1) ** k, "primero": k == 0, "que": f"corte {k + 1}/{len(mo['imagenes'])}"})
        elif mo["tipo"] == "barrido":
            cam = tl.get("camara") or []
            a = next((c for c in cam if c[0] >= mo["ini"]), None)
            b = next((c for c in cam if c[0] >= mo["fin"]), None)
            dx = (b[1] - a[1]) if a and b else 1.0
            # La cámara va hacia +x: la imagen se desliza hacia la izquierda, y el sonido con ella.
            pan = (0.75, -0.75) if dx > 0 else (-0.75, 0.75)
            pre, post = (fin - ini) / 2 + 0.3, 0.5
            ev.append({"efecto": "soplo", "t": (ini + fin) / 2 - pre, "dur": pre + post, "pico": pre / (pre + post), "pan": pan, "que": "barrido"})
    logo = tl.get("logo") or {}
    for s in logo.get("salvapantallas", []):
        ev.append({"efecto": "estatica", "t": s["ini"] / fps, "dur": (s["fin"] - s["ini"]) / fps, "que": "salvapantallas"})
        toques = _toques(s, tl["ancho"], tl["alto"])
        usados = set()
        for i, (f, eje, xr) in enumerate(toques):
            if i in usados:
                continue
            esquina = i + 1 < len(toques) and toques[i + 1][0] - f < 2 and toques[i + 1][1] != eje
            if esquina:
                usados.add(i + 1)
            pan = (-0.8 if xr < 0.5 else 0.8) if eje == "x" else (xr * 1.6 - 0.8)
            ev.append({"efecto": "rebote", "t": f / fps, "borde": "esquina" if esquina else eje, "pan": pan, "extra": 4.0 if esquina else 0.0, "que": f"el logo toca {'una esquina' if esquina else 'un costado' if eje == 'x' else 'arriba o abajo'}"})
    return sorted(ev, key=lambda e: e["t"])


# ── Mezcla ─────────────────────────────────────────────────────────────────

def _poner(pista: np.ndarray, sonido: np.ndarray, t: float) -> None:
    i = int(round(t * SR))
    if sonido.ndim == 1:
        sonido = _paneo(sonido, 0.0) * np.sqrt(2)
    a, b = max(0, i), min(len(pista), i + len(sonido))
    if b > a:
        pista[a:b] += sonido[a - i : b - i]


def _sintetizar(e: dict, clase: int, menor: bool, rng) -> np.ndarray:
    tipo = e["efecto"]
    if tipo == "impacto":
        return impacto(_hz(clase, 1), rng)
    if tipo == "campana":
        return campana(clase, menor, rng)
    if tipo in ("soplo", "vuelo"):
        return soplo(e["dur"], e["pico"], e.get("pan", (-0.2, 0.2)), rng)
    if tipo == "subida":
        return subida(e["dur"], clase, rng)
    if tipo == "obturador":
        return _paneo(obturador(rng), e["pan"])
    if tipo == "rebote":
        tonica, quinta = _hz(clase, 5), _hz((clase + 7) % 12, 5)
        frecs = {"x": [quinta], "y": [tonica], "esquina": [tonica, quinta, tonica * 2]}[e["borde"]]
        return _normalizar(_sala(_paneo(rebote(frecs, rng), e["pan"]), 0.8, 0.2, rng))
    if tipo == "estatica":
        return estatica(e["dur"], rng)
    salir(f"efecto desconocido: {tipo}")


def _agachar(n: int, tiempos: list[float], db: float) -> np.ndarray:
    """Ganancia de la canción: baja `db` en cada impacto (ataque 15 ms, vuelve en ~0,6 s)."""
    if not tiempos or db <= 0:
        return np.ones(n)
    profundidad = np.zeros(n)
    t = np.arange(n) / SR
    for t0 in tiempos:
        d = t - t0
        forma = np.where(d < 0, np.clip(1 + d / 0.015, 0, 1), np.exp(-d / 0.25))
        profundidad = np.maximum(profundidad, forma)
    return 10 ** (-db * profundidad / 20)


def _leer_audio(video: Path, destino: Path) -> np.ndarray:
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vn", "-ac", "2", "-ar", str(SR), "-c:a", "pcm_f32le", str(destino)], capture_output=True, text=True)
    if r.returncode:
        salir(f"no pude leer el audio de {video}: {r.stderr.strip()[-400:]}")
    return sf.read(str(destino), dtype="float64")[0]


def _rms_db(x: np.ndarray) -> float:
    return 20 * np.log10(np.sqrt(np.mean(x**2)) + 1e-12)


def _relacion(efectos: np.ndarray, cancion: np.ndarray, t: float, largo: float, ventana: float = 0.1) -> float:
    """Efecto contra canción en la ventana donde el efecto suena más fuerte."""
    a, b = max(0, int(t * SR)), min(len(efectos), int((t + largo) * SR))
    k = int(ventana * SR)
    if b - a < k:
        return _rms_db(efectos[a:b]) - _rms_db(cancion[a:b])
    energia = np.convolve(np.sum(efectos[a:b] ** 2, axis=1), np.ones(k), mode="valid")
    i = a + int(np.argmax(energia))
    return _rms_db(efectos[i : i + k]) - _rms_db(cancion[i : i + k])


def sonorizar(p: Proyecto) -> Path:
    cfg = p.cfg.get("sonido", {})
    if p.cfg.get("base"):
        base = Proyecto(p.cfg["base"]["proyecto"])
        nombre_render = p.cfg["base"]["render"]
    else:
        base = p
        nombre_render = cfg.get("render") or salir("falta `sonido.render`: el render al que se le suma el sonido")
    video = base.salidas / "render" / nombre_render
    if not video.exists():
        salir(f"no existe el render {video}")
    if not base.timeline.exists():
        salir(f"falta el timeline de {base.nombre}")
    tl = leer_json(base.timeline)
    ajustes = cfg.get("efectos", {})
    rng = np.random.default_rng(cfg.get("semilla", 7))

    audio = tl.get("audio") or {}
    if audio.get("src"):
        clase, menor = _tonalidad(base.medios / audio["src"], audio.get("desde", 0), audio.get("hasta"))
    else:
        clase, menor = 9, True
    clase = cfg.get("tonica", clase)

    with tempfile.TemporaryDirectory() as tmp:
        cancion = _leer_audio(video, Path(tmp) / "cancion.wav")
        n = len(cancion)
        efectos = np.zeros((n, 2))
        eventos = partitura(tl)
        hechos = []
        for e in eventos:
            ajuste = ajustes.get(e["efecto"], 0.0)
            if ajuste is False:
                continue
            nivel = NIVEL[e["efecto"]] + float(ajuste) + e.get("extra", 0.0)
            s = _sintetizar(e, clase, menor, rng) * 10 ** (nivel / 20)
            _poner(efectos, s, e["t"])
            e["largo"] = len(s) / SR
            hechos.append(e)

        # Los efectos se apagan con la canción: una cola de campana no se corta en seco.
        efectos = _fundidos(efectos, entrada=0, salida=max(0.4, (audio.get("fundido") or [0, 0])[1]))
        agacha = _agachar(n, [e["t"] for e in hechos if e.get("agacha")], cfg.get("agachar", 3.0))
        mezcla = cancion * agacha[:, None] + efectos
        sf.write(str(p.salida("sonido", "efectos.wav")), efectos.astype(np.float32), SR, subtype="FLOAT")
        ruta_mezcla = Path(tmp) / "mezcla.wav"
        sf.write(str(ruta_mezcla), mezcla.astype(np.float32), SR, subtype="FLOAT")

        nombre = p.cfg.get("nombre_salida", f"{Path(nombre_render).stem}-sonido")
        final = p.salida("render", f"{nombre}.mp4")
        r = subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(ruta_mezcla), "-map", "0:v", "-map", "1:a",
             "-c:v", "copy", "-af", "alimiter=limit=0.891:attack=5:release=60:level=false:latency=1",
             "-c:a", "aac", "-b:a", "320k", "-ar", str(SR), "-movflags", "+faststart", "-shortest", str(final)],
            capture_output=True, text=True,
        )
        if r.returncode:
            salir(f"ffmpeg falló al mezclar: {r.stderr.strip()[-600:]}")

    _dibujar(p, cancion * agacha[:, None], efectos, hechos)
    tono = f"{NOTAS[clase]} {'menor' if menor else 'mayor'}"
    print(f"render: {video.name} · tonalidad estimada del tramo: {tono} (los efectos con altura se afinan ahí)")
    print(f"{len(hechos)} efectos. Cuánto suena cada uno frente a la canción (dB, RMS en sus 100 ms más fuertes):")
    vistos = {}
    for e in hechos:
        rel = _relacion(efectos, cancion * agacha[:, None], e["t"], e["largo"])
        vistos.setdefault(e["efecto"], []).append(rel)
        if e["efecto"] != "obturador" or e["primero"]:
            print(f"  {e['t']:6.2f} s  {e['efecto']:<10} {rel:+5.1f}  {e['que']}")
    print("Promedio por efecto: " + ", ".join(f"{k} {np.mean(v):+.1f}" for k, v in vistos.items()))
    print(f"→ {final}")
    return final


def _dibujar(p: Proyecto, cancion: np.ndarray, efectos: np.ndarray, eventos: list[dict]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    def envolvente(x, ventana=0.05):
        k = int(ventana * SR)
        m = len(x) // k
        bloques = np.abs(x[: m * k]).max(axis=1).reshape(m, k)
        return np.arange(m) * ventana, 20 * np.log10(bloques.max(axis=1) + 1e-6)

    tc, ec = envolvente(cancion)
    te, ee = envolvente(efectos)
    fig, ax = plt.subplots(figsize=(18, 4.5), dpi=110)
    ax.fill_between(tc, -60, ec, color="#5a6d85", alpha=0.6, label="canción")
    ax.fill_between(te, -60, ee, color="#e6b43c", alpha=0.85, label="efectos")
    colores = {"impacto": "#b64924", "campana": "#eee6d4", "soplo": "#2154c5", "vuelo": "#6685ac", "subida": "#c7c91c",
               "obturador": "#c36712", "rebote": "#e0bb66", "estatica": "#7e93aa"}
    for e in eventos:
        if e["efecto"] == "obturador" and not e["primero"]:
            continue
        ax.axvline(e["t"], color=colores[e["efecto"]], lw=0.8, alpha=0.8)
        ax.text(e["t"], 1.5, e["efecto"], rotation=90, fontsize=7, va="bottom", color=colores[e["efecto"]])
    ax.set_ylim(-60, 12)
    ax.set_xlim(0, len(cancion) / SR)
    ax.set_facecolor("#0f1621")
    ax.set_xlabel("segundos")
    ax.set_ylabel("pico (dBFS)")
    ax.legend(loc="lower right")
    ax.set_title(f"{p.nombre}: canción (agachada en los impactos) y efectos")
    fig.tight_layout()
    fig.savefig(p.salida("analisis", "sonido.png"))
    plt.close(fig)
