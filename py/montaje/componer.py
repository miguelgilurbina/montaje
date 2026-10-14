"""Componer: una canción escrita en código, sin derechos de nadie.

Para cuando hace falta música «neutra»: una cama limpia que acompañe sin pedir
atención (un aviso, una cortina, una prueba), hecha aquí mismo con numpy, así
que es tuya y trabaja en local. No reemplaza a una canción de verdad: no tiene
melodía que se recuerde, a propósito.

Lo que arma, por capas, todas afinadas a la tonalidad:

- **pad**: el acorde de cada compás, suave, con entrada lenta (dientes de sierra
  desafinados entre sí y filtrados);
- **arpegio**: las notas del acorde en corcheas, con un timbre de cuerda pulsada
  y un eco a corchea con puntillo;
- **bajo**: la fundamental de cada acorde;
- **percusión** suave: bombo en 1 y 3, un toque en 2 y 4, charles en corcheas y
  una maraca a contratiempo.

La forma sigue la duración pedida: el primer compás entra solo con el pad y el
arpegio, el segundo suma el bajo, del tercero en adelante entra la percusión,
y el último compás se queda en la tónica y se apaga con el video.

Configuración en proyecto.json:

    "componer": {
      "duracion": 24.65,            # segundos (lo que dura el video)
      "bpm": 100,
      "tonalidad": "re mayor",      # «la menor», «fa# mayor»…
      "progresion": "I V vi IV",    # grados; en menor: "i VI III VII"
      "archivo": "audio/compuesta.wav",
      "semilla": 3
    }
"""

from __future__ import annotations

import math

import numpy as np
import soundfile as sf

from .rutas import Proyecto, salir
from .sonido import NOTAS, SR, _banda, _fundidos, _hz, _normalizar, _paneo, _pasabajos, _sala

POR_DEFECTO = {"bpm": 100, "tonalidad": "re mayor", "progresion": None, "archivo": "audio/compuesta.wav", "semilla": 3}

# Semitonos desde la tónica de cada grado (triadas), en mayor y en menor natural.
GRADOS = {
    "mayor": {"I": [0, 4, 7], "ii": [2, 5, 9], "iii": [4, 7, 11], "IV": [5, 9, 12], "V": [7, 11, 14], "vi": [9, 12, 16]},
    "menor": {"i": [0, 3, 7], "III": [3, 7, 10], "iv": [5, 8, 12], "v": [7, 10, 14], "VI": [8, 12, 15], "VII": [10, 14, 17]},
}
PROGRESION = {"mayor": "I V vi IV", "menor": "i VI III VII"}


def _tonalidad(texto: str) -> tuple[int, str]:
    partes = texto.lower().replace("sostenido", "#").split()
    if len(partes) != 2 or partes[0] not in NOTAS or partes[1] not in ("mayor", "menor"):
        salir(f"tonalidad «{texto}»: se espera algo como «re mayor» o «la menor» ({', '.join(NOTAS)})")
    return NOTAS.index(partes[0]), partes[1]


def _t(dur: float) -> np.ndarray:
    return np.arange(int(dur * SR)) / SR


# ── Timbres ────────────────────────────────────────────────────────────────

def _pad(frecs: list[float], dur: float, rng) -> np.ndarray:
    """Tres sierras suaves por nota, desafinadas entre sí, con entrada y salida lentas."""
    t = _t(dur + 0.8)
    y = np.zeros(len(t))
    for f in frecs:
        for det in (-0.004, 0.0, 0.004):
            fase = rng.uniform(0, 2 * np.pi)
            y += sum(np.sin(2 * np.pi * f * (1 + det) * k * t + fase * k) / k for k in range(1, 7))
    y = _pasabajos(y, 1400, 2)
    env = np.minimum(1, t / 0.5) * np.where(t < dur, 1, np.exp(-(t - dur) / 0.25))
    return y * env / (3 * len(frecs))


def _pulsada(f: float, rng) -> np.ndarray:
    """Una cuerda pulsada corta: parciales que mueren rápido."""
    t = _t(0.9)
    y = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.3) + 0.35 * np.sin(4 * np.pi * f * t) * np.exp(-t / 0.12) + 0.12 * np.sin(6 * np.pi * f * t) * np.exp(-t / 0.07)
    y *= 1 - np.exp(-t / 0.002)
    return y * rng.uniform(0.85, 1.0)


def _bajo(f: float, dur: float) -> np.ndarray:
    t = _t(dur + 0.15)
    y = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)
    env = np.minimum(1, t / 0.012) * np.where(t < dur, 0.55 + 0.45 * np.exp(-t / 0.4), np.exp(-(t - dur) / 0.05))
    return y * env


def _bombo() -> np.ndarray:
    t = _t(0.35)
    frec = 45 + 90 * np.exp(-t / 0.045)
    y = np.sin(2 * np.pi * np.cumsum(frec) / SR) * np.exp(-t / 0.13)
    return np.tanh(1.4 * y)


def _toque(rng) -> np.ndarray:
    """Un golpe seco y bajo en 2 y 4, como un aro: ruido corto en medios."""
    t = _t(0.12)
    return _banda(rng.standard_normal(len(t)), 900, 3200) * np.exp(-t / 0.022) * (1 - np.exp(-t / 0.001))


def _charles(rng, abierto: bool = False) -> np.ndarray:
    t = _t(0.25 if abierto else 0.06)
    return _banda(rng.standard_normal(len(t)), 6000, 13000) * np.exp(-t / (0.09 if abierto else 0.018))


def _maraca(rng) -> np.ndarray:
    t = _t(0.1)
    env = np.sin(np.pi * np.minimum(1, t / 0.08)) ** 2
    return _banda(rng.standard_normal(len(t)), 3000, 9000) * env


def _eco(x: np.ndarray, retardo: float, veces: int, caida: float) -> np.ndarray:
    y = x.copy()
    d = int(retardo * SR)
    for k in range(1, veces + 1):
        y[k * d :] += x[: len(x) - k * d] * caida**k
    return y


# ── La pieza ───────────────────────────────────────────────────────────────

def componer(p: Proyecto, duracion: float | None = None) -> tuple[np.ndarray, dict]:
    cfg = {**POR_DEFECTO, **p.cfg.get("componer", {})}
    dur = float(duracion or cfg.get("duracion") or 0)
    if dur <= 0:
        salir("falta `componer.duracion` (segundos)")
    rng = np.random.default_rng(cfg["semilla"])
    tonica, modo = _tonalidad(cfg["tonalidad"])
    grados = GRADOS[modo]
    progresion = (cfg["progresion"] or PROGRESION[modo]).split()
    for g in progresion:
        if g not in grados:
            salir(f"grado «{g}» no existe en {modo}: {', '.join(grados)}")
    golpe = 60 / cfg["bpm"]
    compas = 4 * golpe
    n_compases = math.ceil(dur / compas)
    cola = 2.0
    n = int((dur + cola) * SR)
    capas = {k: np.zeros(n) for k in ("pad", "arpegio", "bajo", "bombo", "toque", "charles", "maraca")}

    def poner(capa: str, y: np.ndarray, t0: float, nivel: float) -> None:
        i = int(round(t0 * SR))
        if i < 0 or i >= n:
            return
        fin = min(n, i + len(y))
        capas[capa][i:fin] += y[: fin - i] * nivel

    ultimo = n_compases - 1
    for c in range(n_compases):
        t0 = c * compas
        # El último compás se queda en la tónica para cerrar.
        grado = progresion[c % len(progresion)] if c < ultimo else progresion[0]
        semis = grados[grado]
        notas = [_hz(tonica, 3) * 2 ** (s / 12) for s in semis]
        largo = compas if c < ultimo else max(compas, dur - t0 + 0.2)
        poner("pad", _pad(notas, largo, rng), t0, 1.0)
        if c >= 1:
            poner("bajo", _bajo(notas[0] / 2, compas * 0.95), t0, 1.0)
            poner("bajo", _bajo(notas[0] / 2, golpe * 0.6), t0 + 2 * golpe + golpe / 2, 0.55)
        # Arpegio en corcheas, sube y baja por dos octavas; en la intro arranca en el tercer golpe.
        patron = [0, 1, 2, 3, 4, 5, 4, 2]
        arpegio = notas + [f * 2 for f in notas]
        for k, idx in enumerate(patron):
            tk = t0 + k * golpe / 2 + rng.normal(0, 0.004)
            if c == 0 and k < 4:
                continue
            if c == ultimo and k > 0:
                continue
            poner("arpegio", _pulsada(arpegio[idx], rng), tk, 0.9 if k % 2 == 0 else 0.65)
        if 2 <= c < ultimo:
            for g in range(4):
                tg = t0 + g * golpe
                if g in (0, 2):
                    poner("bombo", _bombo(), tg, 1.0)
                else:
                    poner("toque", _toque(rng), tg, 1.0)
                poner("charles", _charles(rng), tg, 0.8)
                poner("charles", _charles(rng, abierto=g == 3), tg + golpe / 2, 0.5)
                poner("maraca", _maraca(rng), tg + golpe / 2 + rng.normal(0, 0.003), 1.0)
        elif c == ultimo:
            poner("bombo", _bombo(), t0, 1.0)

    # Niveles de cada capa (pico, dB), espacio y color.
    nivel = {"pad": -15, "arpegio": -13, "bajo": -11, "bombo": -11, "toque": -21, "charles": -24, "maraca": -26}
    mezcla = np.zeros((n, 2))
    for k, y in capas.items():
        y = _normalizar(y) * 10 ** (nivel[k] / 20)
        if k == "arpegio":
            y = _eco(y, golpe * 0.75, 3, 0.35)
            est = _sala(_paneo(y, 0.15), 1.4, 0.22, rng)[:n]
        elif k == "pad":
            est = _sala(_paneo(y, 0.0) * np.sqrt(2), 2.2, 0.3, rng)[:n]
        elif k == "toque":
            est = _sala(_paneo(y, -0.1), 0.9, 0.25, rng)[:n]
        elif k == "maraca":
            est = _paneo(y, 0.35)
        elif k == "charles":
            est = _paneo(y, -0.3)
        else:
            est = _paneo(y, 0.0) * np.sqrt(2)
        mezcla[: len(est)] += est
    # Se apaga con el video: cola corta después del último cuadro.
    mezcla = mezcla[: int(dur * SR)]
    mezcla = _fundidos(mezcla, entrada=0.01, salida=min(1.2, dur * 0.1))
    mezcla = _normalizar(mezcla) * 10 ** (-1.0 / 20)
    info = {"bpm": cfg["bpm"], "tonalidad": cfg["tonalidad"], "progresion": " ".join(progresion), "compases": n_compases, "duracion": dur}
    return mezcla, info


def escribir(p: Proyecto, duracion: float | None = None) -> None:
    cfg = {**POR_DEFECTO, **p.cfg.get("componer", {})}
    mezcla, info = componer(p, duracion)
    destino = p.medio(*cfg["archivo"].split("/"))
    sf.write(str(destino), mezcla.astype(np.float32), SR, subtype="PCM_24")
    print(f"{info['tonalidad']}, {info['bpm']} BPM, {info['compases']} compases ({info['progresion']}), {info['duracion']:.2f} s → {destino}")
