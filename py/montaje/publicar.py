"""El paquete de publicación: lo que cada red necesita, listo para subir.

Para un experimento y una o más redes deja en `~/Videos/montaje/<p>/publicar/<red>/`:

- `video.mp4` — el render reencodado como lo piden las redes (H.264 high,
  yuv420p, 30 cps, AAC 48 kHz, faststart), a buena tasa para que la red
  recomprima desde algo limpio;
- `portada.jpg` — un cuadro elegido (`portada`: segundo del video), al tamaño de
  la red (miniatura 1280×720 en YouTube);
- `texto.txt` — el texto del posteo (Instagram) o título + descripción (YouTube),
  armado desde `publicacion.json` del experimento, que es lo que Miguel corrige.

El audio sale **masterizado** para las redes: −14 LUFS integrados y pico real
de −1 dBTP (`lufs` y `pico` en `publicacion.json` lo cambian). Se mide primero y
se aplica como ganancia pareja (`loudnorm` en dos pasadas, lineal): YouTube baja a
−14 lo que llega más fuerte, así que entregar ahí no pierde nada, y el pico de −1
evita que la compresión de la red recorte.

No publica nada: publicar es un paso aparte que siempre necesita el sí de Miguel.
Cada paquete queda anotado en PUBLICACIONES.md.
"""

from __future__ import annotations

import datetime as dt
import json
import subprocess
from pathlib import Path

from .rutas import RAIZ, Proyecto, leer_json, salir

REDES = {
    "instagram-reel": {"proporcion": (9, 16), "max_s": 180, "nombre": "Instagram · Reel"},
    "instagram-feed": {"proporcion_rango": (4 / 5, 1.91), "max_s": 3600, "nombre": "Instagram · publicación"},
    "youtube-short": {"proporcion": (9, 16), "max_s": 180, "nombre": "YouTube · Short"},
    "youtube": {"proporcion": (16, 9), "max_s": 43200, "nombre": "YouTube · video", "miniatura": (1280, 720)},
}


def _probar(ruta: Path) -> tuple[int, int, float]:
    salida = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration", "-of", "csv=p=0:s=,", str(ruta)],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    w, h = (int(x) for x in salida[0].split(",")[:2])
    return w, h, float(salida[1])


def _sonoridad(ruta: Path, filtro: str) -> dict:
    """Corre `loudnorm` (que mide) y devuelve su informe JSON."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(ruta), "-vn", "-af", filtro, "-f", "null", "-"], capture_output=True, text=True)
    texto = r.stderr
    try:
        return json.loads(texto[texto.rindex("{") : texto.rindex("}") + 1])
    except ValueError:
        salir(f"no pude medir la sonoridad de {ruta}: {texto.strip()[-400:]}")


def _master(ruta: Path, lufs: float, pico: float) -> tuple[str, dict]:
    """Filtro de masterización (ganancia pareja hasta `lufs`, pico real ≤ `pico`) y la medición de entrada."""
    objetivo = f"loudnorm=I={lufs}:TP={pico}:LRA=20"
    m = _sonoridad(ruta, f"{objetivo}:print_format=json")
    filtro = (
        f"{objetivo}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
        f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true"
    )
    return filtro, m


def _texto(pub: dict, red: str) -> str:
    etiquetas = " ".join(pub.get("etiquetas", []))
    creditos = pub.get("creditos", "")
    if red.startswith("youtube"):
        yt = pub.get("youtube", {})
        titulo = yt.get("titulo", pub.get("titulo", ""))
        if red == "youtube-short" and "#Shorts" not in titulo:
            titulo = f"{titulo} #Shorts"
        return (
            f"TÍTULO\n{titulo}\n\n"
            f"DESCRIPCIÓN\n{pub.get('texto', '')}\n\n{creditos}\n\n{etiquetas}\n\n"
            f"PRIVACIDAD SUGERIDA: {yt.get('privacidad', 'private')}\n"
            f"CONTENIDO SINTÉTICO (declararlo en YouTube): {'sí' if pub.get('ia', True) else 'no'}\n"
        )
    return f"{pub.get('texto', '')}\n\n{creditos}\n\n{etiquetas}\n"


def paquete(p: Proyecto, redes: list[str]) -> None:
    ruta_pub = p.dir / "publicacion.json"
    if not ruta_pub.exists():
        salir(f"falta {ruta_pub}: el texto y el render a publicar")
    pub = leer_json(ruta_pub)
    render = p.salidas / "render" / pub["render"]
    if not render.exists():
        salir(f"no existe el render {render}")
    w, h, dur = _probar(render)
    lufs, pico = pub.get("lufs", -14.0), pub.get("pico", -1.0)
    master, entrada = _master(render, lufs, pico)

    filas = []
    for red in redes:
        spec = REDES.get(red)
        if not spec:
            salir(f"red desconocida: {red} (hay: {', '.join(REDES)})")
        prop = w / h
        if "proporcion" in spec:
            esperada = spec["proporcion"][0] / spec["proporcion"][1]
            if abs(prop - esperada) > 0.01:
                salir(f"{spec['nombre']} pide {spec['proporcion'][0]}:{spec['proporcion'][1]} y el render es {w}×{h}; hay que planificar una versión en ese formato")
        else:
            lo, hi = spec["proporcion_rango"]
            if not lo - 0.01 <= prop <= hi + 0.01:
                salir(f"{spec['nombre']} acepta proporciones entre 4:5 y 1,91:1 y el render es {w}×{h}")
        if dur > spec["max_s"]:
            salir(f"{spec['nombre']}: el video dura {dur:.0f} s y el máximo es {spec['max_s']} s")

        carpeta = p.salida("publicar", red, "x").parent
        video = carpeta / "video.mp4"
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", str(render),
             "-c:v", "libx264", "-profile:v", "high", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-r", "30",
             "-af", master, "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-movflags", "+faststart", str(video)],
            check=True,
        )
        salida = _sonoridad(video, f"loudnorm=I={lufs}:TP={pico}:print_format=json")
        portada = carpeta / "portada.jpg"
        filtro = []
        if spec.get("miniatura"):
            mw, mh = spec["miniatura"]
            filtro = ["-vf", f"scale={mw}:{mh}:force_original_aspect_ratio=decrease,pad={mw}:{mh}:(ow-iw)/2:(oh-ih)/2"]
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(pub.get("portada", 1.0)), "-i", str(render), "-frames:v", "1", *filtro, "-q:v", "2", str(portada)], check=True)
        (carpeta / "texto.txt").write_text(_texto(pub, red), encoding="utf-8")
        mb = video.stat().st_size / 1e6
        filas.append((red, spec["nombre"], carpeta, mb))
        print(
            f"{spec['nombre']}: {w}×{h}, {dur:.1f} s, {mb:.0f} MB, audio {entrada['input_i']} → {salida['input_i']} LUFS"
            f" (pico {salida['input_tp']} dBTP) → {carpeta}"
        )

    registro = RAIZ / "PUBLICACIONES.md"
    if not registro.exists():
        registro.write_text(
            "# Publicaciones\n\nCada paquete preparado y cada publicación. «Preparado» = el paquete existe en\n"
            "`~/Videos/montaje/<experimento>/publicar/<red>/`; nada se publica sin el sí de Miguel.\n\n"
            "| Fecha | Experimento | Red | Estado | Enlace |\n|---|---|---|---|---|\n",
            encoding="utf-8",
        )
    hoy = dt.date.today().isoformat()
    lineas = registro.read_text(encoding="utf-8").splitlines()
    for red, nombre, _, _ in filas:
        fila = f"| {hoy} | {p.nombre} | {nombre} | preparado | — |"
        # Rehacer un paquete que aún no se publicó actualiza su fila; no la repite.
        previa = next((i for i, l in enumerate(lineas) if f"| {p.nombre} | {nombre} | preparado |" in l), None)
        if previa is None:
            lineas.append(fila)
        else:
            lineas[previa] = fila
    registro.write_text("\n".join(lineas) + "\n", encoding="utf-8")
