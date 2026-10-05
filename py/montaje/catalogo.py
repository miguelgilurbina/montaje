"""El catálogo: todas las imágenes de un proyecto en una lista homogénea.

Cada fuente (por ahora, la galería de Curiana Radio) se traduce a la misma forma:
proporción, familia, color dominante, luz y tono, y lo que dice la imagen
(título, alt, concepto). El montaje decide sobre esto sin abrir las imágenes;
mirarlas es para verificar, no para clasificar.
"""

from __future__ import annotations

import colorsys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .rutas import Proyecto, escribir_json, leer_json, salir

# Familias de proporción (ancho/alto). Los cortes salen del censo de la galería:
# agrupan los tamaños de Midjourney sin partir ninguna familia real.
FAMILIAS = [
    ("panoramica", 1.70, 99.0),
    ("horizontal-3-2", 1.45, 1.70),
    ("horizontal-4-3", 1.25, 1.45),
    ("cuadrada", 0.85, 1.25),
    ("vertical-4-5", 0.63, 0.85),
    ("vertical-9-16", 0.0, 0.63),
]

MARCA_PRUEBA = ".prueba"


def familia(ratio: float) -> str:
    for nombre, desde, hasta in FAMILIAS:
        if desde <= ratio < hasta:
            return nombre
    return "otra"


def color_a_rasgos(hexa: str) -> dict:
    h = hexa.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))
    tono, sat, _ = colorsys.rgb_to_hsv(r, g, b)
    return {
        "color": "#" + h.lower(),
        # Luma Rec. 709 sobre los valores tal cual: basta para ordenar de oscuro a claro.
        "luz": round(0.2126 * r + 0.7152 * g + 0.0722 * b, 4),
        "tono": round(tono * 360, 1),
        "sat": round(sat, 4),
    }


def desde_galeria_curiana(manifest: Path) -> list[dict]:
    if not manifest.exists():
        salir(f"no encuentro el manifest de la galería en {manifest}")
    datos = leer_json(manifest)
    base = datos["blobBase"]
    items = []
    for o in datos["obras"]:
        ancho = max(o["anchos"])  # la variante más grande que hay en el Blob
        alto = round(o["h"] * ancho / o["w"])
        items.append(
            {
                "id": o["slug"],
                "fuente": "galeria-curiana",
                "titulo": o.get("titulo", ""),
                "alt": o.get("alt", ""),
                "concepto": o.get("concepto", ""),
                "w": ancho,
                "h": alto,
                "ratio": round(o["w"] / o["h"], 4),
                "familia": familia(o["w"] / o["h"]),
                **color_a_rasgos(o["color"]),
                "url": f"{base}/{o['slug']}-{ancho}.webp",
                "img": f"imagenes/{o['slug']}.webp",
                "mini": f"miniaturas/{o['slug']}.webp",
            }
        )
    return items


# Tipo de imagen leído de su descripción (alt y título). Grueso a propósito: sirve
# para pedir «una ráfaga de retratos» o «paisajes en la intro», no para catalogar.
TIPOS = {
    "retrato": r"\b(retrato|rostro|cara|hombre|mujer|niñ[oa]|persona|joven|anciano|figura humana|perfil)\b",
    "paisaje": r"\b(paisaje|montaña|río|mar|océano|playa|desierto|selva|bosque|lago|costa|cielo|dunas?|valle|isla)\b",
    "ciudad": r"\b(ciudad|calle|edificio|casa|arquitectura|urbano|plaza|tren|metro|vagón|tienda)\b",
    "cartel": r"(texto|letras|título|portada|cartel|revista|logotipo|logo|tipografía|palabra)",
    "abstracto": r"\b(patrón|espiral|ondas|círculos|concéntric|textura|geométric|abstract|líneas)\w*",
    "ciencia-ficcion": r"\b(nave|planeta|astronauta|robot|futurista|espacial|ciborg|cyborg|androide|alien)\w*",
}

CURADURIA = Path(__file__).resolve().parents[2] / "curaduria"


def _curaduria(nombre: str) -> dict:
    ruta = CURADURIA / f"{nombre}.json"
    return leer_json(ruta) if ruta.exists() else {}


def construir(p: Proyecto) -> Path:
    import re

    items: list[dict] = []
    for fuente in p.cfg["fuentes"]:
        if fuente["tipo"] == "galeria-curiana":
            items += desde_galeria_curiana(Path(fuente["manifest"]).expanduser())
        else:
            salir(f"tipo de fuente desconocido: {fuente['tipo']}")
    cur = _curaduria(p.cfg.get("biblioteca", p.nombre))
    marca = set(cur.get("marca", []))
    for it in items:
        texto = f"{it['alt']} {it['titulo']}".lower()
        it["tipos"] = [t for t, r in TIPOS.items() if re.search(r, texto)]
        it["marca"] = it["id"] in marca
    destino = p.medio("analisis", "catalogo.json")
    escribir_json(destino, items)

    conteo: dict[str, int] = {}
    for it in items:
        conteo[it["familia"]] = conteo.get(it["familia"], 0) + 1
    print(f"{len(items)} imágenes → {destino}  ({sum(it['marca'] for it in items)} con la marca a la vista)")
    for nombre, *_ in FAMILIAS:
        print(f"  {nombre:<16}{conteo.get(nombre, 0):>5}")
    _copiar_logo(p, cur.get("logo"))
    return destino


def _copiar_logo(p: Proyecto, logo: dict | None) -> None:
    """Trae los archivos del logo a la biblioteca (marca/), para que Remotion los sirva."""
    import shutil

    if not logo:
        return
    origen = Path(logo["origen"]).expanduser()
    for clave, archivo in logo.items():
        if clave == "origen":
            continue
        fuente = origen / archivo
        if fuente.exists():
            shutil.copy2(fuente, p.medio("marca", archivo))
        else:
            print(f"  ojo: falta el logo {fuente}")


def cargar(p: Proyecto) -> list[dict]:
    ruta = p.medios / "analisis" / "catalogo.json"
    if not ruta.exists():
        salir("falta el catálogo; corre primero: python montaje.py catalogo " + p.nombre)
    return leer_json(ruta)


# ── Imágenes en disco ────────────────────────────────────────────────────────


def medir(p: Proyecto) -> None:
    """Suma el peso de lo que habría que bajar, sin bajar nada (peticiones HEAD)."""
    items = cargar(p)

    def peso(it):
        req = urllib.request.Request(it["url"], method="HEAD")
        with urllib.request.urlopen(req, timeout=30) as r:
            return int(r.headers.get("Content-Length", 0))

    with ThreadPoolExecutor(16) as ex:
        pesos = list(ex.map(peso, items))
    total = sum(pesos)
    print(f"{len(items)} archivos, {total / 1e6:.1f} MB en total (origen: {items[0]['url'].split('/galeria/')[0]})")


def bajar(p: Proyecto) -> None:
    items = cargar(p)
    carpeta = p.medio("imagenes", "x").parent
    marca = carpeta / MARCA_PRUEBA
    if marca.exists():
        # Las de prueba ocupan los mismos nombres: se reemplazan todas.
        for f in carpeta.glob("*.webp"):
            f.unlink()
        marca.unlink()

    def una(it):
        destino = p.medios / it["img"]
        if destino.exists() and destino.stat().st_size > 0:
            return 0
        tmp = destino.with_suffix(".parcial")
        urllib.request.urlretrieve(it["url"], tmp)
        tmp.replace(destino)
        return 1

    with ThreadPoolExecutor(8) as ex:
        nuevas = sum(ex.map(una, items))
    print(f"{nuevas} bajadas, {len(items) - nuevas} ya estaban → {carpeta}")


LADO_MINIATURA = 480


def generar_miniaturas(p: Proyecto) -> None:
    """Versiones chicas (lado mayor 480 px) para cuando la imagen es una pieza de la pared.

    Con cientos de piezas en pantalla, cargar el original de cada una hace lento
    el render y no se ve: a ese tamaño la imagen ocupa pocas decenas de píxeles.
    Se generan de las imágenes ya bajadas; no se baja nada.
    """
    from PIL import Image

    items = cargar(p)
    hechas = 0
    for it in items:
        origen = p.medios / it["img"]
        destino = p.medio(*it["mini"].split("/"))
        if not origen.exists():
            salir(f"falta {origen}; corre antes `imagenes {p.nombre} --bajar` (o --prueba)")
        if destino.exists() and destino.stat().st_mtime >= origen.stat().st_mtime:
            continue
        img = Image.open(origen)
        img.thumbnail((LADO_MINIATURA, LADO_MINIATURA))
        img.save(destino, "WEBP", quality=82)
        hechas += 1
    print(f"{hechas} miniaturas nuevas, {len(items) - hechas} al día → {p.medios / 'miniaturas'}")


def generar_prueba(p: Proyecto) -> None:
    """Imágenes de relleno con la proporción y el color reales de cada obra.

    Sirven para probar el montaje sin bajar nada: cada una es su color dominante
    con un halo más claro, un marco y su título, para reconocerla en el render.
    """
    from PIL import Image, ImageDraw, ImageFilter

    items = cargar(p)
    carpeta = p.medio("imagenes", "x").parent
    reales = [f for f in carpeta.glob("*.webp")] if not (carpeta / MARCA_PRUEBA).exists() else []
    if reales:
        salir(f"ya hay {len(reales)} imágenes reales en {carpeta}; no las piso con las de prueba")

    for it in items:
        w, h = it["w"], it["h"]
        base = tuple(int(it["color"][i : i + 2], 16) for i in (1, 3, 5))
        img = Image.new("RGB", (w, h), base)
        halo = Image.new("L", (w, h), 0)
        d = ImageDraw.Draw(halo)
        d.ellipse([w * 0.2, h * 0.2, w * 0.8, h * 0.8], fill=255)
        halo = halo.filter(ImageFilter.GaussianBlur(min(w, h) * 0.15))
        claro = tuple(min(255, int(c * 1.9 + 40)) for c in base)
        img = Image.composite(Image.new("RGB", (w, h), claro), img, halo)
        d = ImageDraw.Draw(img)
        d.rectangle([4, 4, w - 5, h - 5], outline=claro, width=6)
        d.text((24, 24), f"{it['familia']}  {it['titulo'][:40]}", fill=(255, 255, 255))
        img.save(p.medios / it["img"], "WEBP", quality=70)
    (carpeta / MARCA_PRUEBA).write_text("imágenes de relleno; `imagenes --bajar` las reemplaza\n", encoding="utf-8")
    print(f"{len(items)} imágenes de prueba → {carpeta}")
