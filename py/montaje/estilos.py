"""El catálogo de estilos: recetas con nombre para elegir según el guion.

Una **técnica** es lo que el motor sabe hacer (un modo, un momento o un comando).
Un **estilo** es una técnica con sus valores, un nombre, para qué sirve, con qué
material funciona y lo que Miguel dijo de ella. Cada estilo es un archivo en
`estilos/<id>.json` (el repo guarda sólo texto) y su **muestra**, unos segundos
livianos para verlo, vive en `<medios>/estilos/<id>.mp4`: los renders de los
ejercicios se pueden borrar después del veredicto, la receta y la muestra quedan.

    python montaje.py estilos                  # valida y lista el catálogo
    python montaje.py estilos --para abrir     # sólo los que sirven para abrir
    python montaje.py muestra <id> --de 13-variaciones/render/x.mp4 --desde 23.6 --hasta 31.6
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from .rutas import MEDIOS, PROYECTOS, RAIZ, escribir_json, salir

ESTILOS = RAIZ / "estilos"
MUESTRAS = MEDIOS / "estilos"

# Vocabulario cerrado: el guion habla con estas palabras y el catálogo también.
# Una palabra nueva se agrega aquí (y en estilos/README.md) a propósito.
PARA = {
    "abrir": "el comienzo del video: presentar el canal o el tema",
    "cerrar": "el final: la firma, lo que se queda",
    "transición": "pasar de una parte a otra",
    "presentar la marca": "que se vea Curiana Radio",
    "mostrar el archivo": "que se vea mucho material, el archivo como algo vivo",
    "destacar": "una sola imagen o un solo clip al frente",
    "subir la energía": "acelerar, el pico",
    "respirar": "bajar, dejar mirar",
    "loop": "que el final empalme con el comienzo",
}
MATERIAL = {
    "fotos": "imágenes fijas",
    "clips": "videos que se mueven",
    "mixto": "fotos y clips juntos",
    "serie": "variaciones de una misma imagen",
}
ENERGIA = {
    "calma": "lento, se deja mirar",
    "media": "pulso parejo",
    "alta": "rápido, el pico",
    "sube": "va de lento a rápido",
    "sigue": "acelera y frena con la canción",
}
ESTADOS = {
    "aprobado": "Miguel lo dijo",
    "a medias": "Miguel aprobó una parte y otra no (ver `miguel` y `evitar`)",
    "pedido": "Miguel lo pidió y está hecho, falta su veredicto",
    "propuesta": "de Claude, sin probar con Miguel",
    "rechazado": "Miguel dijo que no; queda para no repetirlo",
}
MODOS = {"collage", "secuencia", "cinta", "actos", "superposicion"}
MOMENTOS = {"destacado", "rafaga", "barrido", "video"}
COMANDOS = {"sincronizar", "senal", "sonorizar", "ensamblar", "musicalizar"}
CAMPOS = ["nombre", "frase", "para", "material", "energia", "dura", "tecnica", "estado", "miguel", "visto_en", "evitar"]


def leer() -> list[dict]:
    if not ESTILOS.exists():
        return []
    estilos = []
    for ruta in sorted(ESTILOS.glob("*.json")):
        try:
            e = json.loads(ruta.read_text(encoding="utf-8"))
        except json.JSONDecodeError as err:
            salir(f"{ruta.name}: no es JSON válido ({err})")
        e["id"] = ruta.stem
        estilos.append(e)
    return estilos


def errores(e: dict) -> list[str]:
    """Lo que le falta o le sobra a un estilo. Vacío = está bien."""
    mal = [f"falta `{c}`" for c in CAMPOS if c not in e]
    if mal:
        return mal
    for c in ("nombre", "frase", "dura"):
        if not isinstance(e[c], str) or not e[c].strip():
            mal.append(f"`{c}` tiene que ser un texto")
    for c in ("para", "miguel", "visto_en", "evitar"):
        if not isinstance(e[c], list) or not all(isinstance(x, str) for x in e[c]):
            mal.append(f"`{c}` tiene que ser una lista de textos")
    if mal:
        return mal
    mal += [f"`para`: «{x}» no está en el vocabulario ({', '.join(PARA)})" for x in e["para"] if x not in PARA]
    if not e["para"]:
        mal.append("`para` vacío: ¿para qué sirve?")
    if e["material"] not in MATERIAL:
        mal.append(f"`material`: «{e['material']}» no es {' / '.join(MATERIAL)}")
    if e["energia"] not in ENERGIA:
        mal.append(f"`energia`: «{e['energia']}» no es {' / '.join(ENERGIA)}")
    if e["estado"] not in ESTADOS:
        mal.append(f"`estado`: «{e['estado']}» no es {' / '.join(ESTADOS)}")
    if e["estado"] in ("aprobado", "a medias", "rechazado") and not e["miguel"]:
        mal.append(f"`estado` {e['estado']} sin las palabras de Miguel en `miguel`")
    t = e["tecnica"]
    claves = [k for k in ("modo", "momento", "comando") if isinstance(t, dict) and k in t]
    if len(claves) != 1:
        mal.append("`tecnica` lleva exactamente uno de `modo`, `momento` o `comando`")
    else:
        k = claves[0]
        validos = {"modo": MODOS, "momento": MOMENTOS, "comando": COMANDOS}[k]
        if t[k] not in validos:
            mal.append(f"`tecnica.{k}`: «{t[k]}» no es {' / '.join(sorted(validos))}")
    mal += [f"`visto_en`: no existe el experimento «{p}»" for p in e["visto_en"] if not (PROYECTOS / p / "proyecto.json").exists()]
    return mal


def muestra_de(e: dict) -> Path:
    return MUESTRAS / f"{e['id']}.mp4"


def listar(para: str | None = None, material: str | None = None, estado: str | None = None) -> None:
    estilos = leer()
    if not estilos:
        salir(f"no hay estilos en {ESTILOS}")
    con_error = {e["id"]: errores(e) for e in estilos}
    con_error = {k: v for k, v in con_error.items() if v}
    for k, v in con_error.items():
        print(f"✗ {k}")
        for m in v:
            print(f"    {m}")
    if con_error:
        salir(f"{len(con_error)} de {len(estilos)} estilos con errores")

    elegidos = [
        e
        for e in estilos
        if (para is None or para in e["para"]) and (material is None or e["material"] == material) and (estado is None or e["estado"] == estado)
    ]
    for e in elegidos:
        m = muestra_de(e)
        peso = f"muestra {m.stat().st_size / 1e6:.1f} MB" if m.exists() else "sin muestra"
        print(f"{e['estado']:<10} {e['id']:<26} {e['material']:<6} {e['energia']:<6} {', '.join(e['para'])}  · {peso}")
    total = sum(muestra_de(e).stat().st_size for e in estilos if muestra_de(e).exists())
    print(f"\n{len(elegidos)} de {len(estilos)} estilos · muestras: {total / 1e6:.1f} MB en {MUESTRAS}")


def muestra(id_: str, de: str, desde: float, hasta: float, alto: int) -> None:
    """Corta unos segundos de un render y los deja livianos como muestra del estilo.

    Una sola recodificación, alto `alto` (sin agrandar), H.264 CRF 30 y audio a
    96 kb/s: pocos cientos de KB por segundo, lo justo para reconocer el estilo.
    """
    ruta = ESTILOS / f"{id_}.json"
    if not ruta.exists():
        salir(f"no existe el estilo «{id_}» (hay: {', '.join(e['id'] for e in leer())})")
    fuente = (MEDIOS / de).resolve()
    if not fuente.is_file():
        salir(f"no existe {fuente}")
    if hasta <= desde:
        salir("`--hasta` tiene que ser mayor que `--desde`")
    if not shutil.which("ffmpeg"):
        salir("falta ffmpeg en el PATH")
    destino = MUESTRAS / f"{id_}.mp4"
    destino.parent.mkdir(parents=True, exist_ok=True)
    orden = [
        "ffmpeg", "-v", "error", "-y", "-ss", str(desde), "-i", str(fuente), "-t", str(hasta - desde),
        "-vf", f"scale=-2:'min({alto},ih)':flags=lanczos", "-c:v", "libx264", "-preset", "slow", "-crf", "30",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(destino),
    ]
    subprocess.run(orden, check=True)
    e = json.loads(ruta.read_text(encoding="utf-8"))
    # De dónde salió, por si el render ya no está cuando alguien la mire.
    e["muestra"] = {"de": de.replace("\\", "/"), "desde": desde, "hasta": hasta}
    escribir_json(ruta, e)
    print(f"→ {destino} ({destino.stat().st_size / 1e6:.2f} MB)")
