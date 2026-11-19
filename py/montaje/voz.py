"""La voz en off, limpia: sin chasquidos de boca entre palabras, con nivel parejo.

Una voz grabada en casa trae, pegados al final de cada frase y entre palabras, los ruidos de la
boca (chasquidos, labios, saliva). La música los tapa a medias y el oído los encuentra igual. Esto
no inventa nada: baja lo que no es palabra.

1. **Graves y chasquidos**: filtro de graves bajo 75 Hz y `adeclick` (los impulsos de unos pocos
   milisegundos, también dentro de las palabras).
2. **Lo que no es palabra, más bajo**: con los tiempos de cada palabra (`transcribir`), corregidos con
   la energía de la voz en la banda del habla (100–4.000 Hz: un chasquido es agudo y no estira una
   palabra), todo lo que queda fuera de las palabras baja `atenuar` dB, con fundidos cortos. Los
   huecos breves dentro de una frase (menos de `hueco` s) no se tocan: la voz no suena picada.
3. **Nivel**: des-eseador suave, compresión leve y normalización a `lufs` (dos pasadas, picos bajo
   −1,5 dBTP).

    python montaje.py limpiar-voz <archivo> [--salida voz/vo1-limpia.wav] [--atenuar 30]

El original no se toca. Deja `<nombre>-limpia.wav` y dice cuánto ruido había entre palabras y
cuánto queda. Claude no oye: el veredicto es del oído de quien la escuche.
"""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from .rutas import MEDIOS, salir

SR = 48000
VENTANA = 0.010
PASO = 0.005


def _ffmpeg(origen: Path, destino: Path, filtros: str) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(origen), "-af", filtros, "-ac", "1", "-ar", str(SR), "-c:a", "pcm_f32le", str(destino)],
                   check=True)


def _leer(ruta: Path) -> np.ndarray:
    import soundfile as sf

    y, _ = sf.read(str(ruta), dtype="float64")
    return y if y.ndim == 1 else y.mean(axis=1)


def _envolvente(y: np.ndarray, sr: int) -> np.ndarray:
    """Nivel (dB) en ventanas de 10 ms cada 5 ms."""
    w, h = int(VENTANA * sr), int(PASO * sr)
    n = max(1, (len(y) - w) // h + 1)
    idx = np.arange(w)[None, :] + h * np.arange(n)[:, None]
    return 10 * np.log10(np.mean(y[idx] ** 2, axis=1) + 1e-12)


def _banda(y: np.ndarray, sr: int, baja: float, alta: float) -> np.ndarray:
    """La señal filtrada entre `baja` y `alta` Hz (por FFT, sin fase: sólo para medir)."""
    Y = np.fft.rfft(y)
    f = np.fft.rfftfreq(len(y), 1 / sr)
    Y[(f < baja) | (f > alta)] = 0
    return np.fft.irfft(Y, len(y))


def habla_por_energia(y: np.ndarray, sr: int, palabras: list[tuple[float, float]], bajo: float = 26.0,
                      minimo: float = 0.1, union: float = 0.08) -> list[tuple[float, float]]:
    """Donde suena voz aunque la transcripción no lo tenga como palabra: la banda del habla a menos de `bajo` dB de su
    nivel típico durante `minimo` s o más. La transcripción a veces empieza una palabra tarde («Registrar» desde 55,82 s
    cuando el «Re-» suena desde 55,40) o se salta una entera; sin esto, la limpieza la bajaba como si fuera ruido y el
    acortado la cortaba (Miguel, 2026-11-17: «a registrar le falta como una sílaba»). Un chasquido dura menos de 50 ms."""
    habla = _envolvente(_banda(y, sr, 100, 4000), sr)
    t = np.arange(len(habla)) * PASO + VENTANA / 2
    dentro = np.zeros(len(habla), dtype=bool)
    for a, b in palabras:
        dentro |= (t >= a) & (t <= b)
    nivel = np.percentile(habla[dentro], 90) if dentro.any() else np.percentile(habla, 90)
    activa = habla > nivel - bajo
    tramos: list[list[float]] = []
    i = 0
    while i < len(activa):
        if activa[i]:
            j = i
            while j < len(activa) and activa[j]:
                j += 1
            a, b = i * PASO, j * PASO + VENTANA
            if tramos and a - tramos[-1][1] < union:
                tramos[-1][1] = b
            else:
                tramos.append([a, b])
            i = j
        else:
            i += 1
    return [(a, b) for a, b in tramos if b - a >= minimo]


def palabras_de(transcripcion: Path) -> list[tuple[float, float]]:
    d = json.loads(transcripcion.read_text(encoding="utf-8"))
    return [(float(w["ini"]), float(w["fin"])) for s in d["segmentos"] for w in s["palabras"]]


def mascara_de_voz(y: np.ndarray, sr: int, palabras: list[tuple[float, float]], hueco: float = 0.09,
                   antes: float = 0.025, despues: float = 0.045) -> np.ndarray:
    """Los tramos de habla, [inicio, fin] en segundos.

    Los bordes de cada palabra salen de la transcripción y se corrigen con la energía en la banda del
    habla: se estiran mientras la voz siga sonando (hasta 30 dB bajo su nivel típico) y se encogen si la
    transcripción la daba por más larga. Después, un margen (`antes`, `despues`) y los huecos de menos
    de `hueco` s se llenan.
    """
    habla = _envolvente(_banda(y, sr, 100, 4000), sr)
    t = np.arange(len(habla)) * PASO + VENTANA / 2
    dentro = np.zeros(len(habla), dtype=bool)
    for a, b in palabras:
        dentro |= (t >= a) & (t <= b)
    nivel = np.percentile(habla[dentro], 90) if dentro.any() else np.percentile(habla, 90)
    umbral = nivel - 30
    activa = habla > umbral
    tramos = []
    for a, b in palabras:
        i, j = int(a / PASO), min(len(habla) - 1, int(b / PASO))
        # Encoger: la palabra empieza y termina donde de verdad suena.
        sonando = np.where(activa[i: j + 1])[0]
        if len(sonando):
            i, j = i + sonando[0], i + sonando[-1]
        # Estirar: si sigue sonando pegado (sin un silencio de 30 ms), es la misma palabra.
        limite_fin = min(len(habla) - 1, j + int(0.25 / PASO))
        while j < limite_fin and activa[j + 1: j + 7].any():
            j += 1
        limite_ini = max(0, i - int(0.15 / PASO))
        while i > limite_ini and activa[max(0, i - 6): i].any():
            i -= 1
        tramos.append((max(0.0, i * PASO - antes), j * PASO + VENTANA + despues))
    # Más lo que suena como voz aunque la transcripción no lo tenga.
    tramos += [(max(0.0, a - antes), b + despues) for a, b in habla_por_energia(y, sr, palabras)]
    tramos.sort()
    unidos: list[list[float]] = []
    for a, b in tramos:
        if unidos and a - unidos[-1][1] < hueco:
            unidos[-1][1] = max(unidos[-1][1], b)
        else:
            unidos.append([a, b])
    # El comienzo de una frase, con generosidad: una «s», una «f» o el aliento antes de la primera palabra son
    # suaves y agudos, y quedaban bajo el umbral del habla: la frase empezaba recortada y entraba de golpe
    # (Miguel, 2026-11-17: «comienzan con un volumen muy bajo y de la nada suben»). Se busca hacia atrás en una
    # banda ancha (100–9.000 Hz) hasta 45 dB bajo la voz, y se abre 60 ms antes.
    ancho = _envolvente(_banda(y, sr, 100, 9000), sr)
    nivel_ancho = np.percentile(ancho[dentro], 90) if dentro.any() else np.percentile(ancho, 90)
    for tramo in unidos:
        i = min(len(ancho) - 1, int(tramo[0] / PASO))
        tope = max(0, i - int(0.25 / PASO))
        while i > tope and ancho[i - 1] > nivel_ancho - 45:
            i -= 1
        tramo[0] = max(0.0, min(tramo[0], i * PASO - 0.06))
    return np.array(unidos)


def ganancia(tramos: np.ndarray, n: int, sr: int, piso: float, sube: float = 0.05, baja: float = 0.015) -> np.ndarray:
    """La ganancia muestra a muestra: 1 en las palabras, `piso` fuera. Sube en `sube` s y llega entera justo al
    comienzo (el arranque no se toca); baja en `baja` s después del final (rápido: ahí están los chasquidos)."""
    g = np.full(n, piso)
    for a, b in tramos:
        i, j = int(a * sr), min(n, int(b * sr))
        k = int(sube * sr)
        r = max(0, i - k)
        g[r:i] = np.maximum(g[r:i], piso + (1 - piso) * np.linspace(0, 1, i - r, endpoint=False))
        g[i:j] = 1.0
        k = int(baja * sr)
        fin = min(n, j + k)
        g[j:fin] = np.maximum(g[j:fin], piso + (1 - piso) * np.linspace(1, 0, fin - j, endpoint=False))
    return g


def ruido_entre_palabras(y: np.ndarray, sr: int, tramos: np.ndarray) -> dict:
    """Lo que suena fuera de las palabras: cuántos golpes (ventanas de 10 ms agudas sobre el piso) y su nivel."""
    mascara = np.zeros(len(y))
    for a, b in tramos:
        mascara[int(a * sr): int(b * sr)] = 1
    agudos = _envolvente(_banda(y, sr, 2000, 12000), sr)
    fuera = mascara[(np.arange(len(agudos)) * PASO * sr).astype(int).clip(0, len(mascara) - 1)] < 0.5
    voz = _envolvente(y, sr)
    referencia = np.percentile(voz[~fuera], 90) if (~fuera).any() else np.percentile(voz, 90)
    golpes = fuera & (agudos > referencia - 45)
    # Golpes separados: ventanas seguidas cuentan como uno.
    n = int(np.sum(golpes[1:] & ~golpes[:-1]) + (golpes[0] if len(golpes) else 0))
    return {"golpes": n, "pico_db": round(float(agudos[fuera].max() - referencia), 1) if fuera.any() else None,
            "segundos_fuera": round(float(fuera.sum() * PASO), 1)}


def limpiar(archivo: str, salida: str | None = None, transcripcion: str | None = None, atenuar: float = 30.0,
            hueco: float = 0.09, lufs: float = -16.0) -> Path:
    origen = Path(archivo) if Path(archivo).is_absolute() else MEDIOS / archivo
    if not origen.exists():
        salir(f"no existe {origen}")
    destino = Path(salida) if salida and Path(salida).is_absolute() else (MEDIOS / salida if salida else origen.with_name(origen.stem + "-limpia.wav"))
    tr = Path(transcripcion) if transcripcion else MEDIOS / "transcripciones" / f"{origen.stem}.json"
    if not tr.exists():
        salir(f"falta la transcripción con tiempos por palabra ({tr}): corre primero `python montaje.py transcribir {archivo}`")
    import soundfile as sf

    with tempfile.TemporaryDirectory() as tmp:
        paso1 = Path(tmp) / "1.wav"
        _ffmpeg(origen, paso1, "highpass=f=75,adeclick=window=55:overlap=75:threshold=2")
        y = _leer(paso1)
        tramos = mascara_de_voz(y, SR, palabras_de(tr), hueco=hueco)
        antes_n = ruido_entre_palabras(y, SR, tramos)
        y = y * ganancia(tramos, len(y), SR, 10 ** (-atenuar / 20))
        paso2 = Path(tmp) / "2.wav"
        sf.write(str(paso2), y.astype(np.float32), SR, subtype="FLOAT")
        despues_n = ruido_entre_palabras(y, SR, tramos)
        cadena = "deesser=i=0.35:m=0.5:f=0.5,acompressor=threshold=-26dB:ratio=2.5:attack=12:release=180:makeup=2"
        r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(paso2), "-af", f"{cadena},loudnorm=I={lufs}:TP=-1.5:LRA=7:print_format=json", "-f", "null", "-"],
                           capture_output=True, text=True)
        m = json.loads(re.search(r'\{[^{}]*"input_i"[^{}]*\}', r.stderr, re.S).group(0))
        final = (f"{cadena},loudnorm=I={lufs}:TP=-1.5:LRA=7:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
                 f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
        destino.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(paso2), "-af", final, "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s24le", str(destino)], check=True)
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(destino), "-af", "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True)
    x = json.loads(re.search(r'\{[^{}]*"input_i"[^{}]*\}', r.stderr, re.S).group(0))
    print(f"fuera de las palabras: {antes_n['segundos_fuera']} s · golpes agudos {antes_n['golpes']} → {despues_n['golpes']} "
          f"(el más fuerte, {antes_n['pico_db']} → {despues_n['pico_db']} dB respecto de la voz)")
    print(f"→ {destino}  ({x['input_i']} LUFS, pico {x['input_tp']} dBTP)")
    return destino


# ── Acortar una voz: frases fuera, pausas más cortas, un poco más rápida ────

class Mapa:
    """De qué segundo de la voz original a qué segundo de la editada (lo que se cortó cae en el punto del corte)."""

    def __init__(self, pedazos: list[tuple[float, float, float]], velocidad: float):
        self.pedazos = pedazos  # (inicio viejo, fin viejo, inicio nuevo antes de la velocidad)
        self.velocidad = velocidad

    def __call__(self, t: float) -> float:
        p = self.pedazos
        if t <= p[0][0]:
            return 0.0
        for k, (a, b, n) in enumerate(p):
            if t < a:  # en lo que se sacó: cae donde empieza el pedazo siguiente
                return n / self.velocidad
            if t <= b:
                return (n + t - a) / self.velocidad
        a, b, n = p[-1]
        return (n + b - a + (t - b)) / self.velocidad


def editar(archivo: str, destino: str, transcripcion: Path, cortes: list[tuple[float, float]] = (), pausa: float = 0.45,
           velocidad: float = 1.0, entrada: float = 0.3, salida: float = 0.4, cruce: float = 0.012) -> Mapa:
    """La voz más corta: sin las palabras que caen en `cortes` ([inicio, fin] en segundos de la original), con los silencios
    entre palabras de a lo sumo `pausa` s y `velocidad` veces más rápida (sin cambiar el tono: `atempo`). Escribe también
    su transcripción con los tiempos nuevos (`transcripciones/<destino>.json`), para los subtítulos. Devuelve el mapa
    de tiempos, para que los planos se reacomoden solos."""
    import soundfile as sf

    origen = MEDIOS / archivo
    salida_ruta = MEDIOS / destino
    y, sr = sf.read(str(origen), dtype="float64")
    if y.ndim > 1:
        y = y.mean(axis=1)
    datos = json.loads(transcripcion.read_text(encoding="utf-8"))
    palabras = [w for s in datos["segmentos"] for w in s["palabras"]
                if not any(a <= w["ini"] < b for a, b in cortes)]
    if not palabras:
        salir(f"{archivo}: no queda ninguna palabra")
    # Lo que suena como voz cuenta como palabra para medir los silencios (aunque la transcripción no lo tenga):
    # así ningún silencio «largo» que se acorte se lleva una sílaba.
    sonidos = []
    for a, b in habla_por_energia(y, sr, [(w["ini"], w["fin"]) for w in palabras]):
        # Lo que toca un corte se va con el corte (el arranque de una frase cortada no queda colgando); si empezó
        # antes, queda la parte de antes.
        for c, d in cortes:
            if a < d and b > c:
                b = min(b, c - 0.05)
        if b - a >= 0.1 and not any(c <= a < d for c, d in cortes):
            sonidos.append({"ini": a, "fin": b})
    todo = sorted([{"ini": w["ini"], "fin": w["fin"]} for w in palabras] + sonidos, key=lambda w: w["ini"])
    unidos = [dict(todo[0])]
    for w in todo[1:]:
        if w["ini"] <= unidos[-1]["fin"]:
            unidos[-1]["fin"] = max(unidos[-1]["fin"], w["fin"])
        else:
            unidos.append(dict(w))
    # Los pedazos que quedan: de cada sonido al siguiente, salvo el medio de los silencios largos.
    pedazos_viejos = []
    ini = max(0.0, unidos[0]["ini"] - entrada)
    for w, sig in zip(unidos, unidos[1:]):
        if sig["ini"] - w["fin"] > pausa:
            pedazos_viejos.append((ini, w["fin"] + pausa / 2))
            ini = sig["ini"] - pausa / 2
    pedazos_viejos.append((ini, min(len(y) / sr, max(palabras[-1]["fin"], unidos[-1]["fin"]) + salida)))
    k = int(cruce * sr)
    rampa = np.sin(np.linspace(0, np.pi / 2, k)) ** 2
    out = np.zeros(0)
    pedazos = []
    for a, b in pedazos_viejos:
        trozo = y[int(a * sr): int(b * sr)].copy()
        if len(out) >= k and len(trozo) >= k:
            # Unión en cruce de igual potencia: sin chasquido en el corte.
            inicio_nuevo = (len(out) - k) / sr
            out[-k:] = out[-k:] * rampa[::-1] + trozo[:k] * rampa
            out = np.concatenate([out, trozo[k:]])
        else:
            inicio_nuevo = len(out) / sr
            out = np.concatenate([out, trozo])
        pedazos.append((a, b, inicio_nuevo))
    with tempfile.TemporaryDirectory() as tmp:
        crudo = Path(tmp) / "crudo.wav"
        sf.write(str(crudo), out.astype(np.float32), sr, subtype="FLOAT")
        salida_ruta.parent.mkdir(parents=True, exist_ok=True)
        filtro = f"atempo={velocidad}" if abs(velocidad - 1) > 1e-6 else "anull"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(crudo), "-af", filtro, "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s24le", str(salida_ruta)],
                       check=True)
    mapa = Mapa(pedazos, velocidad)
    nuevas = [{**w, "ini": round(mapa(w["ini"]), 3), "fin": round(mapa(w["fin"]), 3)} for w in palabras]
    (MEDIOS / "transcripciones" / f"{Path(destino).stem}.json").write_text(
        json.dumps({"archivo": destino, "segmentos": [{"palabras": nuevas}]}, ensure_ascii=False), encoding="utf-8")
    viejo, nuevo = palabras[-1]["fin"] - palabras[0]["ini"], nuevas[-1]["fin"] - nuevas[0]["ini"]
    print(f"{archivo}: {viejo:.1f} s de habla → {nuevo:.1f} s ({len(pedazos)} pedazos, ×{velocidad}) → {salida_ruta}")
    return mapa
