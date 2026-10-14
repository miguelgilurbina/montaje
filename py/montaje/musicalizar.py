"""Musicalizar: ponerle una canción a un video que ya existe.

Para un video hecho afuera (un aviso, una cortina, algo grabado con el teléfono)
al que hay que cambiarle o ponerle música. No se toca la imagen: el video se
copia tal cual y sólo cambia la pista de audio.

Configuración en proyecto.json:

    "musicalizar": {
      "video": "video/aviso.mp4",          # relativo a los medios
      "musica": "audio/compuesta.wav",     # o cualquier archivo de audio
      "original": 0.0,                     # cuánto queda del audio original (0 = nada, 1 = igual)
      "lufs": -14, "pico": -1,             # masterización de la mezcla
      "nombre_salida": "aviso-con-cancion"
    }

Si `musica` es la que arma `componer`, se compone primero con la duración
exacta del video.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from . import componer
from .publicar import _master, _probar
from .rutas import Proyecto, salir


def musicalizar(p: Proyecto) -> Path:
    cfg = p.cfg.get("musicalizar") or salir("falta `musicalizar` en proyecto.json")
    video = p.medios / cfg["video"]
    if not video.exists():
        salir(f"no existe el video {video}")
    _, _, dur = _probar(video)
    compuesta = {**componer.POR_DEFECTO, **p.cfg.get("componer", {})}["archivo"]
    if cfg.get("musica", compuesta) == compuesta and "componer" in p.cfg:
        componer.escribir(p, duracion=dur)
    musica = p.medios / cfg.get("musica", compuesta)
    if not musica.exists():
        salir(f"no existe la música {musica}")
    original = float(cfg.get("original", 0.0))

    with tempfile.TemporaryDirectory() as tmp:
        mezcla = Path(tmp) / "mezcla.wav"
        if original > 0:
            filtro = f"[0:a]volume={original}[o];[1:a][o]amix=inputs=2:duration=first:normalize=0[a]"
            orden = ["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(musica), "-filter_complex", filtro, "-map", "[a]", "-t", f"{dur:.3f}", "-ar", "48000", "-ac", "2", str(mezcla)]
        else:
            orden = ["ffmpeg", "-v", "error", "-y", "-i", str(musica), "-t", f"{dur:.3f}", "-ar", "48000", "-ac", "2", str(mezcla)]
        r = subprocess.run(orden, capture_output=True, text=True)
        if r.returncode:
            salir(f"ffmpeg falló al mezclar: {r.stderr.strip()[-500:]}")
        master, medido = _master(mezcla, float(cfg.get("lufs", -14.0)), float(cfg.get("pico", -1.0)))
        final = p.salida("render", f"{cfg.get('nombre_salida', video.stem + '-con-cancion')}.mp4")
        r = subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(mezcla), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
             "-af", master, "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", str(final)],
            capture_output=True, text=True,
        )
        if r.returncode:
            salir(f"ffmpeg falló al unir: {r.stderr.strip()[-500:]}")
    print(f"video: {video.name} ({dur:.2f} s) · música: {musica.name} ({medido['input_i']} → {cfg.get('lufs', -14)} LUFS) · audio original al {original:.0%}")
    print(f"→ {final}")
    return final
