"""Transcribir un audio: lo que se dice, palabra por palabra y con su segundo.

Corre entera en este computador (faster-whisper; nada sale de aquí). Sirve para una nota
de voz, una grabación para voz en off o cualquier audio o video con habla:

    python montaje.py transcribir <archivo> [--idioma es] [--pistas "Paraguaná, Curiana"] [--cancion]

Deja en `<medios>/transcripciones/`: `<nombre>.txt` (para leer), `.srt` (subtítulos) y `.json`
(cada palabra con su segundo y, en `rotulos`, las líneas listas para la capa `rotulos` de un
montaje). Las `pistas` son nombres propios que el modelo no tiene por qué conocer.

**El texto de una voz en off sale del guion, no de lo que Whisper oye:** Whisper da los
tiempos; las palabras las escribió Miguel. Para una nota de voz, lo que oye es lo que hay, y
puede equivocarse: se lee antes de usarlo.

El modelo vive en `<medios>/modelos/faster-whisper-medium` (1,5 GB, fuera del repo).
"""

from __future__ import annotations

import re
import subprocess
import time
import unicodedata
from pathlib import Path

import numpy as np

from .rutas import MEDIOS, escribir_json, salir

MODELO = MEDIOS / "modelos" / "faster-whisper-medium"


def _cargar():
    """El modelo en la tarjeta de video si se puede; si no (faltan sus bibliotecas), en el procesador."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        salir("falta faster-whisper: python -m pip install faster-whisper")
    if not (MODELO / "model.bin").exists():
        salir(f"falta el modelo en {MODELO}")
    try:
        m = WhisperModel(str(MODELO), device="cuda", compute_type="float16")
        # La falta de las bibliotecas de CUDA no sale al cargar: sale al usarla. Un segundo de silencio lo descubre.
        list(m.transcribe(np.zeros(16000, dtype=np.float32), language="es")[0])
        return m, "tarjeta de video"
    except (RuntimeError, OSError, ValueError):
        return WhisperModel(str(MODELO), device="cpu", compute_type="int8"), "procesador"


def _hora(t: float) -> str:
    ms = round(t * 1000)
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def srt(segmentos: list[dict]) -> str:
    return "\n".join(f"{i}\n{_hora(s['ini'])} --> {_hora(s['fin'])}\n{s['texto']}\n" for i, s in enumerate(segmentos, 1))


def lineas_de_rotulos(segmentos: list[dict], max_palabras: int = 7) -> list[dict]:
    """Los segmentos en líneas cortas para la capa `rotulos`: cada una con su segundo y el de cada palabra.

    Corta en la puntuación si puede, y siempre antes de pasar de `max_palabras`.
    """
    lineas: list[dict] = []
    for s in segmentos:
        actual: list[dict] = []
        palabras = s["palabras"]
        for i, p in enumerate(palabras):
            actual.append(p)
            cierra = p["p"].rstrip().endswith((".", ",", ";", ":", "?", "!", "…"))
            resto = len(palabras) - i - 1
            # Sin dejar una palabra suelta en la línea siguiente.
            if resto and (len(actual) >= max_palabras or (cierra and len(actual) >= 3 and resto >= 2)):
                lineas.append(_linea(actual))
                actual = []
        if actual:
            lineas.append(_linea(actual))
    return lineas


def _linea(palabras: list[dict]) -> dict:
    return {"t": palabras[0]["ini"], "fin": palabras[-1]["fin"], "texto": " ".join(p["p"].strip() for p in palabras),
            "tiempos": [p["ini"] for p in palabras]}


def _nombre(ruta: Path) -> str:
    a = unicodedata.normalize("NFKD", ruta.stem).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", a).strip("-") or "audio"


def transcribir(archivo: str, idioma: str = "es", pistas: str | None = None, cancion: bool = False) -> Path:
    ruta = Path(archivo)
    if not ruta.is_absolute():
        ruta = (MEDIOS / archivo) if (MEDIOS / archivo).is_file() else ruta.resolve()
    if not ruta.is_file():
        salir(f"no existe {ruta}")
    modelo, donde = _cargar()
    t0 = time.time()
    # El audio lo lee ffmpeg, que el motor ya usa para todo: así vale para cualquier audio o video, y no
    # depende de la biblioteca `av` (su versión 19 rompe a faster-whisper 1.2.1 al abrir un archivo).
    crudo = subprocess.run(["ffmpeg", "-v", "error", "-i", str(ruta), "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True, check=True).stdout
    audio = np.frombuffer(crudo, dtype=np.float32)
    # El filtro de voz sirve para una nota de voz; en una canción toma el canto con instrumentos por ruido y lo bota
    # (en la Añoranza dejaba 4 palabras de 136). En una canción va sin él, y sin arrastrar el texto anterior: así no repite.
    partes, info = modelo.transcribe(audio, language=idioma, word_timestamps=True, vad_filter=not cancion,
                                     condition_on_previous_text=not cancion, initial_prompt=pistas or None)
    segmentos = []
    for s in partes:
        segmentos.append({
            "ini": round(s.start, 3), "fin": round(s.end, 3), "texto": s.text.strip(),
            "palabras": [{"p": w.word.strip(), "ini": round(w.start, 3), "fin": round(w.end, 3), "prob": round(w.probability, 3)} for w in (s.words or [])],
        })
    if not segmentos:
        salir(f"{ruta.name}: no se oyó habla")
    base = MEDIOS / "transcripciones" / _nombre(ruta)
    base.parent.mkdir(parents=True, exist_ok=True)
    texto = " ".join(s["texto"] for s in segmentos)
    base.with_suffix(".txt").write_text(texto + "\n", encoding="utf-8")
    rotulos = lineas_de_rotulos(segmentos)
    # El .srt va en líneas cortas, las mismas de los rótulos: es el que se corrige a mano y el que lee la capa.
    base.with_suffix(".srt").write_text(srt([{"ini": l["t"], "fin": l["fin"], "texto": l["texto"]} for l in rotulos]), encoding="utf-8")
    dudosas = sum(p["prob"] < 0.5 for s in segmentos for p in s["palabras"])
    escribir_json(base.with_suffix(".json"), {"archivo": ruta.name, "idioma": idioma, "duracion": round(info.duration, 2), "segmentos": segmentos, "rotulos": rotulos})
    print(f"{ruta.name}: {info.duration:.0f} s en {time.time() - t0:.0f} s ({donde}); {sum(len(s['palabras']) for s in segmentos)} palabras, {dudosas} dudosas")
    print(f"→ {base.with_suffix('.txt')}\n→ {base.with_suffix('.srt')}\n→ {base.with_suffix('.json')}")
    return base
