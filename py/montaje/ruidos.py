"""Los ruidos de los aparatos: lo que suena cuando la casetera pausa o rebobina, cuando la antena no alcanza, cuando la
canción sale por el parlante del televisor, cuando graba la cámara de los 90 o se corta la videollamada.

Miguel, el 2026-11-22: «hay efectos que deberían ir acompañados de audios característicos». De 53 estilos de la mesa,
8 cambiaban cómo suena la canción y ninguno sonaba en su momento. Eligió los cuatro grupos propuestos: la casetera, la
antena y el televisor, la película (el traqueteo ya estaba en `pelicula.py`: faltaba ponérselo) y las cámaras y la
videollamada.

Todo se sintetiza aquí, como los efectos de `sonido.py`: sin grabaciones, sin derechos que pedir. Cada ruido es la
perilla `sonido` de su aparato, así que viaja con la cadena y suena también en el probador:

| aparato | `sonido` | qué suena |
|---|---|---|
| `casetera` | `mecanica` | la pausa: el clac del solenoide, la cinta que calla y el tambor que sigue girando; rebobinar: la cinta que corre con un chirrido que sube y el golpe al parar; el arranque: el cassette que entra, el motor que carga, el PLAY y la canción que entra con el ruido del tracking |
| `antena` | `aire` | el siseo de la señal débil (sube con `nieve`), el crepitar, el zumbido del sincronismo (con `zumbido`, `rodar` o `desenganche`) y, sin sincronismo, la señal que va y viene |
| `pantalla` | `parlante` | la canción por el parlante chico del televisor: mono, sin graves ni brillo, la caja que resuena, y el silbido agudo del tubo |
| `camara` | `microfono` | el micrófono de la cámara de los 90: mono, el control automático que sube el ruido en lo quieto, el motor de la cinta y los golpes de la mano |
| `compresion` | `llamada` | el audio de una llamada por internet: banda de voz, y donde se pierde un paquete (los mismos cuadros donde se rompe la imagen) la voz robótica que repite y se apaga |
| `copia` | `camara` | (2026-11-22) la instantánea: el obturador y el motor que la expulsa, al principio; el fotomatón: el flash en cada disparo, con la carga que silba |
| `imprenta` | `maquina` | (2026-11-22) la máquina andando debajo de la canción: la fotocopiadora (la luz que barre y el clic de cada copia), el tambor de la riso y de la rotativa (el golpe y la hoja que sale), la rasqueta de la serigrafía |
| `radiofoto` | `tonos` | (2026-11-22) los tonos que dibujan la foto que llega por radio: cada línea, la altura sigue el brillo (1 500 Hz el negro, 2 300 el blanco, 1 200 el sincronismo); el encabezado de la sstv, la franja de fase del fax; la canción baja mientras llega |
| `dial` | `sintonia` | (2026-11-22) la canción que se va en la estática mientras la aguja busca, el silbido entre emisoras, y vuelve en sintonía |
| `juguete` | `mecanismo` | (2026-11-23) el juguete óptico: el tambor del zoótropo con el aleteo de las ranuras, el disco que gira, las hojas del libro que pasan, el obturador de la cronofotografía en cada pose |
| `rollo` | `proyector` | (2026-11-22) el proyector cuando falla la película: la quema traba el mecanismo y crepita; el cuadro que se corre es la uña que salta las perforaciones; el empalme pasa con un chasquido; la cola es la punta suelta que golpea en el carrete |

Los momentos caen donde caen en la imagen: la misma semilla y el mismo lugar en la cadena (`_paso`, que pasa
`analogo._audio_de_aparatos`) dan los mismos eventos. Los niveles van contra el de la canción y son [sin verificar]:
puntos de partida para el oído de Miguel.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.signal import butter, sosfilt

from . import analogo as A

#: Por aparato, los valores de su perilla `sonido` (el primero, «ninguno», no suena).
SONIDOS = {"casetera": ("ninguno", "mecanica"), "antena": ("ninguno", "aire"), "pantalla": ("ninguno", "parlante"),
           "camara": ("ninguno", "microfono"), "compresion": ("ninguno", "llamada"), "rollo": ("ninguno", "proyector"),
           "copia": ("ninguno", "camara"), "imprenta": ("ninguno", "maquina"),
           "radiofoto": ("ninguno", "tonos"), "dial": ("ninguno", "sintonia"),
           "juguete": ("ninguno", "mecanismo")}

#: De las capturas donde la llamada rompe la imagen, en cuántas se pierde también el audio.
PAQUETES_DE_AUDIO = 0.4

#: El silbido del transformador de salto (el «flyback») de un televisor NTSC: la frecuencia de línea, 15 734 Hz.
LINEA_HZ = 15734.26


# ── Piezas ─────────────────────────────────────────────────────────────────

def _filtrar(x: np.ndarray, tipo: str, f, sr: int, orden: int = 2) -> np.ndarray:
    return sosfilt(butter(orden, f, btype=tipo, fs=sr, output="sos"), x, axis=0)


def _rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(x)))) if len(x) else 0.0


def _db(v: float) -> float:
    return 10 ** (v / 20)


def _referencia(x: np.ndarray) -> float:
    """El nivel de la canción, contra el que va cada ruido (con un piso: en un silencio el ruido no se va a cero)."""
    return max(_rms(x), _db(-30))


def eventos_en(semilla: int, nombre: str, desde: float, hasta: float, por_minuto: float, dura: float) -> list[tuple[float, float]]:
    """Los eventos de `analogo.evento` (y `pelicula.evento_con_id`) que tocan el intervalo [desde, hasta): (inicio, fin)
    en segundos de la imagen. Las mismas ranuras y el mismo azar: suenan donde se ven."""
    if por_minuto <= 0 or hasta <= desde:
        return []
    ranura = 2 * dura
    prob = min(1.0, por_minuto / 60 * ranura)
    hay = []
    for s in range(math.floor(desde / ranura) - 1, math.floor(hasta / ranura) + 1):
        r = np.random.default_rng([semilla, A._num(nombre), s + 1_000_000])
        if r.random() < prob:
            inicio = (s + r.random()) * ranura
            if inicio < hasta and inicio + dura > desde:
                hay.append((inicio, inicio + dura))
    return hay


def golpecito(sr: int, rng: np.random.Generator, banda=(800, 5000), caida: float = 0.003, cuerpo: float = 0.0) -> np.ndarray:
    """Un golpe seco: ruido en banda que se apaga en `caida` segundos y, con `cuerpo`, un grave corto debajo."""
    n = int(max(caida * 8, 0.16 if cuerpo else 0.0) * sr)
    t = np.arange(n) / sr
    y = _filtrar(rng.standard_normal(n), "bandpass", banda, sr) * np.exp(-t / caida)
    if cuerpo:
        y = y / (np.abs(y).max() + 1e-9) + cuerpo * np.sin(2 * np.pi * 95 * t) * np.exp(-t / 0.035)
    return y / (np.abs(y).max() + 1e-9)


def clac(sr: int, rng: np.random.Generator) -> np.ndarray:
    """El solenoide de la casetera: un golpe con cuerpo y, un instante después, el seguro que cae."""
    a = golpecito(sr, rng, (700, 5000), 0.003, cuerpo=0.8)
    b = golpecito(sr, rng, (1500, 7000), 0.002) * 0.45
    d = int(rng.uniform(0.018, 0.032) * sr)
    y = np.zeros(max(len(a), d + len(b)))
    y[: len(a)] += a
    y[d:d + len(b)] += b
    return y / np.abs(y).max()


def motor(n: int, sr: int, rng: np.random.Generator, giro: float = 30.0) -> np.ndarray:
    """El tambor de la casetera girando (1 800 vueltas por minuto: 30 Hz y sus armónicos), un silbido fino que tiembla
    y el roce de la cinta. RMS 1."""
    t = np.arange(n) / sr
    y = sum(a * np.sin(2 * np.pi * giro * k * t + rng.uniform(0, 2 * np.pi)) for k, a in ((2, 1.0), (4, 0.5), (6, 0.25), (8, 0.12)))
    f = 1840 + 6 * np.sin(2 * np.pi * 0.9 * t)
    y = y + 0.08 * np.sin(2 * np.pi * np.cumsum(f) / sr)
    y = y + 0.15 * _filtrar(rng.standard_normal(n), "bandpass", (300, 3000), sr) / 0.3
    return y / (_rms(y) + 1e-9)


def chirrido(n: int, sr: int, rng: np.random.Generator) -> np.ndarray:
    """La cinta corriendo hacia atrás: el carrete que acelera canta cada vez más agudo, y el roce sisea. RMS 1."""
    t = np.arange(n) / sr
    u = t / max(t[-1] if n else 1.0, 1e-9)
    f = 520 + 900 * u ** 0.7 + 25 * np.sin(2 * np.pi * 7 * t)
    fase = 2 * np.pi * np.cumsum(f) / sr
    tono = np.sin(fase) + 0.4 * np.sin(2 * fase) + 0.2 * np.sin(3 * fase)
    siseo = _filtrar(rng.standard_normal(n), "bandpass", (2000, 9000), sr)
    y = (0.6 * tono / (_rms(tono) + 1e-9) + siseo / (_rms(siseo) + 1e-9)) * np.clip(t / 0.08, 0, 1)
    return y / (_rms(y) + 1e-9)


def siseo(n: int, sr: int, rng: np.random.Generator) -> np.ndarray:
    """El ruido de una señal débil: ancho, sin graves. RMS 1."""
    y = _filtrar(rng.standard_normal(n), "bandpass", (400, 11000), sr)
    return y / (_rms(y) + 1e-9)


class _Mezcla:
    """Lo que un aparato le hace al audio en el tiempo: cuánto deja pasar de lo que entra (`ganancia`) y lo que suma
    encima (en veces el nivel de la canción)."""

    def __init__(self, x: np.ndarray, t0: float, sr: int):
        self.x, self.t0, self.sr, self.n = x, t0, sr, len(x)
        self.ganancia = np.ones(self.n)
        self.encima = np.zeros(self.n)
        self.ref = _referencia(x)

    def i(self, t: float) -> int:
        return int(round((t - self.t0) * self.sr))

    def poner(self, sonido: np.ndarray, t: float, db: float) -> None:
        a = self.i(t)
        desde, hasta = max(a, 0), min(a + len(sonido), self.n)
        if hasta > desde:
            self.encima[desde:hasta] += sonido[desde - a:hasta - a] * _db(db)

    def bajar(self, a: float, b: float, db: float, rampa: float = 0.02) -> None:
        """La entrada baja a `db` entre a y b, con rampas de `rampa` segundos (sin clics)."""
        t = self.t0 + np.arange(self.n) / self.sr
        sube = np.clip((t - a) / rampa + 1, 0, 1) * np.clip((b - t) / rampa + 1, 0, 1)
        self.ganancia = np.minimum(self.ganancia, 1 - (1 - _db(db)) * sube)

    def salida(self) -> np.ndarray:
        y = self.x * self.ganancia[:, None] + (self.encima * self.ref)[:, None]
        return y.astype(np.float32)


# ── La casetera ────────────────────────────────────────────────────────────

def casetera(x: np.ndarray, p: dict, semilla: int, t0: float, sr: int, indice: int) -> np.ndarray:
    """Los botones de la casetera, donde la imagen los muestra (`casetera.casetera`)."""
    if p.get("sonido", "ninguno") == "ninguno" or not len(x):
        return x
    m = _Mezcla(x, t0, sr)
    rng = np.random.default_rng([semilla, A._num("casetera-sonido"), indice])
    s = semilla * 100 + p.get("_paso", 0)   # la semilla de la imagen
    fin = t0 + m.n / sr
    pausas = eventos_en(s, "pausa", t0, fin, p["pausa"], p["pausa_dura"]) if p["pausa"] else []
    for a, b in pausas:
        m.bajar(a, b, -26)                    # la casetera en pausa calla la cinta…
        m.poner(motor(int((b - a) * sr), sr, rng), a, -24)   # …y el tambor sigue girando
        m.poner(clac(sr, rng), a, -12)
        m.poner(clac(sr, rng), b, -15)
    if p["rebobinar"]:
        # La imagen no rebobina durante una pausa: el sonido tampoco.
        for a, b in eventos_en(s, "rebobinar", t0, fin, p["rebobinar"], p["rebobinar_dura"]):
            if any(pa < b and a < pb for pa, pb in pausas):
                continue
            m.bajar(a, b, -32, rampa=0.03)
            m.poner(chirrido(int((b - a) * sr), sr, rng), a, -8)
            m.poner(golpecito(sr, rng, (300, 3000), 0.006, cuerpo=1.2), b, -10)
    if p["inicio"]:
        ini = t0 + p["inicio"]   # la pantalla azul va desde el principio de la salida hasta `inicio`
        m.bajar(t0 - 1, ini, -60, rampa=0.01)
        m.poner(clac(sr, rng), t0 + 0.25, -11)             # el cassette entra
        carga = int(max(0.0, p["inicio"] + 0.6 - 0.55) * sr)
        if carga:
            arranca = np.clip(np.arange(carga) / (0.8 * sr), 0, 1)
            m.poner(motor(carga, sr, rng) * arranca, t0 + 0.55, -28)   # el motor carga y el tambor acelera
        m.poner(clac(sr, rng), max(t0 + 0.45, ini - 1.05), -13)        # ▶ PLAY (el letrero aparece 1,2 s antes)
        n = int(0.6 * sr)                                              # el tracking: la imagen entra con ruido
        m.poner(siseo(n, sr, rng) * np.exp(-np.arange(n) / (0.18 * sr)), ini, -14)
    return m.salida()


# ── La antena y el televisor ───────────────────────────────────────────────

def _suave_en(semilla: int, nombre: str, t: np.ndarray, base: float) -> np.ndarray:
    """`analogo.suave` a 100 valores por segundo, estirado a cada muestra."""
    rejilla = np.arange(t[0], t[-1] + 0.02, 0.01)
    return np.interp(t, rejilla, [A.suave(semilla, nombre, float(u), base) for u in rejilla])


def antena(x: np.ndarray, p: dict, semilla: int, t0: float, sr: int, indice: int) -> np.ndarray:
    """La señal que llega por el aire: el audio del televisor es FM, y con la señal débil sisea y crepita; sin
    sincronismo, el zumbido de los pulsos se cuela y la señal va y viene."""
    if p.get("sonido", "ninguno") == "ninguno" or not len(x):
        return x
    m = _Mezcla(x, t0, sr)
    rng = np.random.default_rng([semilla, A._num("antena-sonido"), indice])
    t = t0 + np.arange(m.n) / sr
    s = semilla * 100 + p.get("_paso", 0)
    sin_sincro = p["desenganche"] + 0.5 * min(abs(p["rodar"]), 1.0)
    # Va y viene: sin sincronismo la señal se pierde a ratos (0 = se oye entera).
    perdida = np.clip(_suave_en(s, "senal-audio", t, 0.35), 0, 1) * min(1.0, 1.6 * sin_sincro) if sin_sincro else np.zeros(m.n)
    m.ganancia = m.ganancia * (1 - 0.75 * perdida)
    ruido = siseo(m.n, sr, rng) * _db(-34 + 70 * p["nieve"]) * (1 + 1.5 * perdida)
    golpes = rng.random(m.n) < (8 + 160 * p["nieve"]) / sr     # el crepitar
    cre = np.zeros(m.n)
    cre[golpes] = rng.standard_normal(int(golpes.sum())) * 3
    ruido = ruido + _filtrar(cre, "bandpass", (1000, 6000), sr) * _db(-30 + 40 * p["nieve"])
    zumba = p["zumbido"] + 0.3 * sin_sincro
    if zumba:   # el zumbido del sincronismo vertical: 59,94 Hz con sus armónicos, casi un serrucho
        fase = 2 * np.pi * 59.94 * t
        diente = sum(np.sin(k * fase) / k for k in range(1, 16))
        ruido = ruido + diente / (_rms(diente) + 1e-9) * _db(-42 + 60 * min(zumba, 0.5))
    m.encima = ruido
    return m.salida()


def pantalla(x: np.ndarray, p: dict, semilla: int, t0: float, sr: int, indice: int) -> np.ndarray:
    """La canción por el parlante del televisor: mono, sin graves ni brillo, la caja que resuena cerca de 400 Hz, un
    poco de saturación, y el silbido del tubo a la frecuencia de línea (no todos lo oyen: es el de verdad)."""
    if p.get("sonido", "ninguno") == "ninguno" or not len(x):
        return x
    mono = x.mean(axis=1).astype(np.float64)
    y = _filtrar(mono, "highpass", 170, sr)
    y = _filtrar(y, "lowpass", 6000, sr, orden=4)
    y = y + 0.6 * _filtrar(y, "bandpass", (330, 520), sr)
    y = np.tanh(1.8 * y) / 1.8   # una ganancia fija: lo que el parlante no da, no se devuelve
    t = t0 + np.arange(len(y)) / sr
    y = y + _referencia(x) * _db(-50) * np.sin(2 * np.pi * LINEA_HZ * t)
    return np.repeat(y[:, None], x.shape[1], axis=1).astype(np.float32)


# ── Las cámaras y la llamada ───────────────────────────────────────────────

def camara(x: np.ndarray, p: dict, semilla: int, t0: float, sr: int, indice: int) -> np.ndarray:
    """El micrófono de la cámara de los 90: oye también el motor de la cinta y los golpes de la mano que la sostiene,
    y su control automático de ganancia los sube en lo quieto (el micrófono es el de `digital.py`, `videocamara`)."""
    from . import digital

    if p.get("sonido", "ninguno") == "ninguno" or not len(x):
        return x
    rng = np.random.default_rng([semilla, A._num("camara-sonido"), indice])
    n = len(x)
    t = np.arange(n) / sr
    ref = _referencia(x)
    zumbe = sum(a * np.sin(2 * np.pi * f * t) for f, a in ((52, 1.0), (104, 0.5), (650, 0.3), (1300, 0.15)))
    zumbe = zumbe * (1 + 0.2 * np.sin(2 * np.pi * 0.4 * t)) / 0.8
    manos = np.zeros(n)
    for a, _ in eventos_en(semilla * 100 + p.get("_paso", 0), "manos", t0, t0 + n / sr, 4.0, 0.3):
        g = golpecito(sr, rng, (60, 400), 0.02, cuerpo=0.6)
        i = int((a - t0) * sr)
        desde, hasta = max(i, 0), min(i + len(g), n)
        if hasta > desde:
            manos[desde:hasta] += g[desde - i:hasta - i]
    oye = x + ((zumbe * _db(-44) + manos * _db(-22)) * ref)[:, None]
    return digital.sonido("sensor", oye.astype(np.float32), {"sonido": "videocamara"}, semilla, t0, sr, indice)


def llamada(x: np.ndarray, p: dict, semilla: int, t0: float, sr: int, indice: int) -> np.ndarray:
    """El audio de una llamada por internet: banda de voz (16 kHz, como los códecs de entonces) y, donde se pierde un
    paquete, lo que hace el que recibe para tapar el hueco: repite los últimos 20 ms, que suenan a robot, y se apaga.
    Los paquetes perdidos son las capturas donde `digital.compresion` rompe la imagen."""
    from . import digital

    if p.get("sonido", "ninguno") == "ninguno" or not len(x):
        return x
    y = digital.sonido("sensor", x, {"sonido": "llamada"}, semilla, t0, sr, indice).astype(np.float64)
    n = len(y)
    cps = float(p.get("_cps") or p.get("_fps") or 30.0)
    s = semilla * 100 + p.get("_paso", 0)
    rng = np.random.default_rng([semilla, A._num("llamada"), indice])
    cuadro = int(0.02 * sr)
    for j in range(max(0, math.floor(t0 * cps)), math.ceil((t0 + n / sr) * cps) + 1):
        if not p["errores"] or np.random.default_rng([s, A._num("codec"), j]).random() >= 0.35 * p["errores"]:
            continue
        # El audio va en paquetes propios, más chicos: se pierde en algunas de las capturas que se rompen, no en todas.
        if np.random.default_rng([s, A._num("llamada-audio"), j]).random() >= PAQUETES_DE_AUDIO:
            continue
        a = int((j / cps - t0) * sr)
        largo = int(rng.uniform(1.0, 2.5) / cps * sr)
        if a < cuadro or a >= n:
            continue
        b = min(n, a + largo)
        ultimo = y[a - cuadro:a, 0].copy()
        relleno = np.tile(ultimo, (b - a) // cuadro + 1)[: b - a] * np.exp(-np.arange(b - a) / (0.05 * sr))
        y[a:b] = relleno[:, None]
    return y.astype(np.float32)


# ── El rollo de película ───────────────────────────────────────────────────

def tictac(n: int, sr: int, rng: np.random.Generator, desde: float, hasta: float, banda=(1200, 6000)) -> np.ndarray:
    """Golpecitos seguidos que pasan de `desde` a `hasta` por segundo: la uña que salta las perforaciones, la punta
    suelta que golpea en el carrete. RMS 1."""
    y = np.zeros(n)
    dur, t = n / sr, 0.0
    while t < dur:
        i = int(t * sr)
        g = golpecito(sr, rng, banda, 0.002)
        f = min(n, i + len(g))
        y[i:f] += g[: f - i] * (0.6 + 0.4 * rng.random())
        ritmo = desde + (hasta - desde) * t / max(dur, 1e-9)
        t += (1 / ritmo) * (1 + 0.08 * rng.standard_normal())
    return y / (_rms(y) + 1e-9)


def _se_cruza(a: float, b: float, otros: list[tuple[float, float]]) -> bool:
    return any(oa < b and a < ob for oa, ob in otros)


def rollo(x: np.ndarray, p: dict, semilla: int, t0: float, sr: int, indice: int) -> np.ndarray:
    """El proyector cuando falla la película, donde la imagen lo muestra (`rollo.rollo`). La imagen no corre el cuadro
    durante una quema ni empalma durante las otras dos: el sonido tampoco. Las marcas de cambio de rollo no suenan."""
    if p.get("sonido", "ninguno") == "ninguno" or not len(x):
        return x
    from .rollo import EMPALME_DURA

    m = _Mezcla(x, t0, sr)
    rng = np.random.default_rng([semilla, A._num("rollo-sonido"), indice])
    s = semilla * 100 + p.get("_paso", 0)
    fin = t0 + m.n / sr
    quemas = eventos_en(s, "quema", t0, fin, p["quema"], p["quema_dura"]) if p["quema"] else []
    for a, b in quemas:
        m.poner(golpecito(sr, rng, (200, 2500), 0.01, cuerpo=1.0), a, -8)       # el mecanismo se traba
        n = int(0.5 * sr)
        tt = np.arange(n) / sr
        ahogo = np.sin(2 * np.pi * np.cumsum(50 * (1 - 0.6 * tt / 0.5)) / sr) * np.exp(-tt / 0.35)
        m.poner(ahogo / (_rms(ahogo) + 1e-9), a, -22)                         # y el motor se ahoga
        n = int((b - a) * sr)
        crepita = np.zeros(n)
        for _ in range(int(rng.poisson(14 * (b - a)))):                       # la película que se ampolla
            i = int(rng.uniform(0.1, 1.0) * n)
            g = golpecito(sr, rng, (2000, 9000), 0.0015)
            f = min(n, i + len(g))
            crepita[i:f] += g[: f - i] * rng.uniform(0.3, 1.0)
        m.poner(crepita, a, -17)
    corridos = [(a, b) for a, b in (eventos_en(s, "corrido", t0, fin, p["corrido"], p["corrido_dura"]) if p["corrido"] else [])
                if not _se_cruza(a, b, quemas)]
    for a, b in corridos:
        m.poner(tictac(int((b - a) * sr), sr, rng, 38, 20, (900, 5000)), a, -16)
    if p["empalme"]:
        for a, b in eventos_en(s, "empalme", t0, fin, p["empalme"], EMPALME_DURA):
            if not _se_cruza(a, b, quemas + corridos):
                m.poner(golpecito(sr, rng, (400, 4000), 0.004, cuerpo=0.6), a, -6)
    final = p.get("_fin")
    if p["cola"] and final is not None:
        a = final - 0.2 * p["cola"]          # la punta suelta: el último quinto de la cola
        if a < fin:
            n = int((final - a) * sr)
            m.poner(tictac(n, sr, rng, 12, 5, (300, 3500)), a, -9)
    return m.salida()


# ── La copia de la foto ────────────────────────────────────────────────────

def obturador(sr: int, rng: np.random.Generator) -> np.ndarray:
    """El obturador de una cámara de fotos: dos golpes secos muy juntos (abre y cierra)."""
    a = golpecito(sr, rng, (1200, 7000), 0.0025, cuerpo=0.4)
    b = golpecito(sr, rng, (1500, 8000), 0.002) * 0.7
    d = int(rng.uniform(0.02, 0.05) * sr)
    y = np.zeros(max(len(a), d + len(b)))
    y[: len(a)] += a
    y[d:d + len(b)] += b
    return y / np.abs(y).max()


def copia(x: np.ndarray, p: dict, semilla: int, t0: float, sr: int, indice: int) -> np.ndarray:
    """La foto que se saca, donde la imagen lo muestra (`fotografia.copia`): la instantánea suena al principio (el
    obturador y el motor que la expulsa), el fotomatón en cada flash (el disparo y el silbido de la carga)."""
    if p.get("sonido", "ninguno") == "ninguno" or not len(x):
        return x
    from .fotografia import disparos

    m = _Mezcla(x, t0, sr)
    rng = np.random.default_rng([semilla, A._num("copia-sonido"), indice])
    fin = t0 + m.n / sr
    if p["forma"] == "instantanea" and p["revelado"]:
        m.poner(obturador(sr, rng), t0 + 0.05, -10)
        n = int(0.7 * sr)
        tt = np.arange(n) / sr
        sube = np.clip(tt / 0.05, 0, 1) * np.clip((0.7 - tt) / 0.08, 0, 1)
        engranaje = np.sin(2 * np.pi * np.cumsum(np.full(n, 310.0)) / sr) + 0.5 * np.sin(2 * np.pi * 930 * tt)
        zumbido = (engranaje / (_rms(engranaje) + 1e-9) * 0.6 + motor(n, sr, rng, 55.0) * 0.4) * sube
        m.poner(zumbido, t0 + 0.12, -20)                            # el motor que expulsa la foto
    if p["forma"] == "fotomaton":
        for t in disparos(p["intervalo"], t0, fin):
            m.poner(golpecito(sr, rng, (600, 6000), 0.004, cuerpo=0.5), t, -12)    # el flash
            n = int(0.9 * sr)
            tt = np.arange(n) / sr
            carga = np.sin(2 * np.pi * np.cumsum(3000 + 6000 * tt / 0.9) / sr) * np.exp(-tt / 0.5)
            m.poner(carga / (_rms(carga) + 1e-9), t + 0.08, -34)              # el capacitor que se carga
    return m.salida()


# ── La imprenta ───────────────────────────────────────────────────────────

#: Cada cuánto pasa una hoja, en segundos [sin verificar: del orden de las máquinas de verdad]: la riso imprime unas
#: 130 por minuto, una fotocopiadora de oficina unas 45, la serigrafía es a mano.
PERIODOS = {"riso": 0.46, "trama": 0.46, "fotocopia": 1.3, "serigrafia": 2.0}


def imprenta(x: np.ndarray, p: dict, semilla: int, t0: float, sr: int, indice: int) -> np.ndarray:
    """La máquina andando, debajo de la canción y a su propio ritmo (el de la máquina, no el de los cuadros)."""
    if p.get("sonido", "ninguno") == "ninguno" or not len(x):
        return x
    m = _Mezcla(x, t0, sr)
    rng = np.random.default_rng([semilla, A._num("imprenta-sonido"), indice])
    fin = t0 + m.n / sr
    tecnica = p["tecnica"]
    periodo = PERIODOS[tecnica]
    for j in range(math.floor(t0 / periodo), math.ceil(fin / periodo) + 1):
        t = j * periodo
        if tecnica == "fotocopia":   # el clic y la luz que barre el vidrio, ida y vuelta
            m.poner(golpecito(sr, rng, (500, 4000), 0.004, cuerpo=0.5), t, -22)
            n = int(0.9 * sr)
            tt = np.arange(n) / sr
            barrido = _filtrar(rng.standard_normal(n), "bandpass", (250, 2500), sr)
            barrido = barrido / (_rms(barrido) + 1e-9) * np.sin(np.pi * tt / 0.9) ** 0.7
            m.poner(barrido, t + 0.05, -27)
        elif tecnica == "serigrafia":  # la rasqueta que arrastra la tinta por la malla
            n = int(0.55 * sr)
            tt = np.arange(n) / sr
            arrastre = _filtrar(rng.standard_normal(n), "bandpass", (900, 6000), sr) * np.sin(np.pi * tt / 0.55) ** 0.5
            m.poner(arrastre / (_rms(arrastre) + 1e-9), t, -25)
        else:                          # el tambor que gira y la hoja que sale
            m.poner(golpecito(sr, rng, (80, 700), 0.012, cuerpo=1.0), t, -21)
            n = int(0.14 * sr)
            hoja = _filtrar(rng.standard_normal(n), "bandpass", (2500, 9000), sr) * np.exp(-np.arange(n) / (0.05 * sr))
            m.poner(hoja / (_rms(hoja) + 1e-9), t + 0.18, -30)
    if tecnica != "serigrafia":        # y el motor, todo el tiempo
        m.poner(motor(m.n, sr, rng, 25.0 if tecnica == "fotocopia" else 37.0), t0, -36)
    return m.salida()


# ── La radio ──────────────────────────────────────────────────────────────

def _tonos_radiofoto(lineas: np.ndarray, modo: str, dura: float, sr: int) -> np.ndarray:
    """La señal de una llegada (encabezado y dibujo) hecha de las líneas de la imagen: frecuencia de 1 500 (negro) a
    2 300 Hz (blanco), en fase continua. La sstv manda cada línea en verde, azul y rojo después del sincronismo; el
    fax, con un margen blanco al principio de cada línea; la telefoto, en amplitud sobre 1 800 Hz. RMS 1."""
    from .radio import DIBUJO, ENCABEZADO

    L, W, _ = lineas.shape
    enc, dib = dura * ENCABEZADO, dura * DIBUJO
    if modo == "sstv":   # el encabezado de la sstv: la guía a 1 900, el corte a 1 200 y el código del modo
        seq = [(1900, 0.3), (1200, 0.01), (1900, 0.3), (1200, 0.03)] + [(1100 if b else 1300, 0.03) for b in (0, 0, 1, 0, 1, 1, 0, 0)] + [(1200, 0.03)]
        escala = enc / sum(d for _, d in seq)
        f_enc = np.concatenate([np.full(max(1, int(d * escala * sr)), float(f)) for f, d in seq])
    else:                # la franja de fase: negro con un pulso blanco al principio de cada línea
        n = int(enc * sr)
        f_enc = np.where((np.arange(n) / sr * (L / dib)) % 1 < 0.05, 2300.0, 1500.0)
    n_lin = max(8, int(dib / L * sr))
    pos = np.arange(n_lin) / n_lin
    lum = lineas @ np.array([0.299, 0.587, 0.114], np.float32)
    filas = []
    for y in range(L):
        if modo == "sstv":
            v = np.empty(n_lin)
            partes = ((0.0, 0.08, None), (0.08, 0.10, -1.0), (0.10, 0.40, 1), (0.40, 0.70, 2), (0.70, 1.0, 0))
            for a, b, canal in partes:
                sel = (pos >= a) & (pos < b)
                if canal is None:
                    v[sel] = -2.0          # el sincronismo: 1 200 Hz
                elif canal == -1.0:
                    v[sel] = 0.0           # el umbral: 1 500 Hz
                else:
                    v[sel] = np.interp((pos[sel] - a) / (b - a), np.linspace(0, 1, W), lineas[y, :, canal])
            filas.append(np.where(v < -1, 1200.0, 1500 + 800 * np.clip(v, 0, 1)))
        else:
            v = np.interp(pos, np.linspace(0, 1, W), lum[y])
            filas.append(np.where(pos < 0.05, 2300.0, 1500 + 800 * v))
    f = np.concatenate([f_enc] + filas)
    if modo == "telefoto":
        t = np.arange(len(f)) / sr
        y = np.sin(2 * np.pi * 1800 * t) * (0.2 + 0.8 * (f - 1500) / 800)
    else:
        y = np.sin(2 * np.pi * np.cumsum(f) / sr)
    return y / (_rms(y) + 1e-9)


def radiofoto(x: np.ndarray, p: dict, semilla: int, t0: float, sr: int, indice: int) -> np.ndarray:
    """Los tonos de cada llegada, con el cuadro que la imagen manda (el de la entrada al empezar la llegada)."""
    if p.get("sonido", "ninguno") == "ninguno" or not len(x):
        return x
    from pathlib import Path

    from .radio import DIBUJO, ENCABEZADO, lineas_de

    m = _Mezcla(x, t0, sr)
    rng = np.random.default_rng([semilla, A._num("radiofoto-sonido"), indice])
    fin = t0 + m.n / sr
    dura = p["dura"]
    for c in range(math.floor(t0 / dura), math.floor(fin / dura) + 1):
        inicio = c * dura
        img = None
        if p.get("_entrada"):
            try:
                img = A.leer_cuadros(Path(p["_entrada"]), [max(0.0, inicio)], 270)[0].astype(np.float32) / 255
            except (StopIteration, SystemExit, OSError):
                img = None
        if img is None:
            img = rng.random((60, 80, 3)).astype(np.float32)
        tonos = _tonos_radiofoto(lineas_de(img, p["modo"]), p["modo"], dura, sr)
        m.poner(tonos, inicio, -17)
        n = len(tonos)
        m.poner(siseo(n, sr, rng) * (0.3 + p["ruido"]), inicio, -34)          # el ruido de la banda
        m.bajar(inicio + dura * ENCABEZADO, inicio + dura * (ENCABEZADO + DIBUJO), -7, rampa=0.15)
    return m.salida()


def dial(x: np.ndarray, p: dict, semilla: int, t0: float, sr: int, indice: int) -> np.ndarray:
    """Mover el dial, donde la imagen lo muestra (`radio.dial`): la misma cuenta de cuánto se pierde la emisora."""
    if p.get("sonido", "ninguno") == "ninguno" or not len(x) or not (p["sintonizar"] or p.get("inicio")):
        return x
    from .radio import INICIO, desintonia

    m = _Mezcla(x, t0, sr)
    rng = np.random.default_rng([semilla, A._num("dial-sonido"), indice])
    s = semilla * 100 + p.get("_paso", 0)
    fin = t0 + m.n / sr
    t = t0 + np.arange(m.n) / sr
    movimientos = [(a, b, math.floor(a / (2 * p["dura"])) + 1_000_000)   # el mismo número que `evento_con_id`
                   for a, b in (eventos_en(s, "dial", t0, fin, p["sintonizar"], p["dura"]) if p["sintonizar"] else [])]
    if p.get("inicio"):   # el del principio de la salida (t0), como en la imagen
        movimientos = [(t0, t0 + p["dura"], INICIO)] + [m for m in movimientos if m[0] >= t0 + p["dura"]]
    for a, b, ident in movimientos:
        rejilla = np.linspace(0, 1, 101)
        cuenta = [desintonia(float(u), ident, s) for u in rejilla]
        u = np.clip((t - a) / p["dura"], 0, 1)
        dentro = (t >= a) & (t < b)
        d = np.where(dentro, np.interp(u, rejilla, [c[0] for c in cuenta]), 0.0)
        corre = np.interp(u, rejilla, [c[1] for c in cuenta])
        m.ganancia = np.minimum(m.ganancia, 1 - 0.97 * d)
        n = int((b - a) * sr)
        i = m.i(a)
        tramo = slice(max(0, i), min(m.n, i + n))
        if tramo.stop > tramo.start:
            ruido = siseo(m.n, sr, rng)
            silbido = np.sin(2 * np.pi * np.cumsum(150 + 650 * np.abs(corre)) / sr) * (np.abs(corre) > 0.15)
            m.encima[tramo] += (ruido * d * _db(-8) + silbido * d * _db(-22))[tramo]
    return m.salida()


# ── Los juguetes ópticos ───────────────────────────────────────────────────

def juguete(x: np.ndarray, p: dict, semilla: int, t0: float, sr: int, indice: int) -> np.ndarray:
    """El juguete andando, debajo de la canción: lo que gira, las hojas, el obturador (`juguetes.juguete`)."""
    if p.get("sonido", "ninguno") == "ninguno" or not len(x) or p["modo"] == "lenticular":
        return x
    m = _Mezcla(x, t0, sr)
    rng = np.random.default_rng([semilla, A._num("juguete-sonido"), indice])
    n = m.n
    t = t0 + np.arange(n) / sr
    if p["modo"] in ("zootropo", "fenaquistiscopio"):
        # El roce del eje y el aleteo de las ranuras que pasan (13 por segundo en el zoótropo, como en la imagen).
        roce = _filtrar(rng.standard_normal(n), "bandpass", (80, 900), sr)
        aleteo = 0.55 + 0.45 * np.sin(2 * np.pi * (13.0 if p["modo"] == "zootropo" else 12.0) * t)
        m.poner(roce / (_rms(roce) + 1e-9) * aleteo, t0, -27)
    elif p["modo"] == "libro":
        from .juguetes import FIGURAS_POR_SEGUNDO

        m.poner(tictac(n, sr, rng, FIGURAS_POR_SEGUNDO, FIGURAS_POR_SEGUNDO, (2000, 8000)), t0, -23)
    else:   # la cronofotografía: el obturador en cada pose, a los mismos segundos que la imagen
        for j in range(math.floor(t0 / p["intervalo"]), math.ceil(t[-1] / p["intervalo"]) + 1):
            m.poner(golpecito(sr, rng, (900, 6000), 0.0025, cuerpo=0.3), j * p["intervalo"], -20)
    return m.salida()


#: Para `analogo._audio_de_aparatos`: el ruido de cada aparato que lo tiene aquí.
RUIDOS = {"casetera": casetera, "antena": antena, "pantalla": pantalla, "camara": camara, "compresion": llamada, "rollo": rollo,
          "copia": copia, "imprenta": imprenta, "radiofoto": radiofoto, "dial": dial,
          "juguete": juguete}


def sonido(nombre: str, x: np.ndarray, p: dict, semilla: int, t0: float, sr: int, indice: int) -> np.ndarray:
    return RUIDOS[nombre](x, p, semilla, t0, sr, indice)
