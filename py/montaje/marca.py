"""El logo de Curiana Radio y las imágenes de marca, para cualquier modo de montaje.

- **Sello:** el isotipo fijo en una esquina, chico, que late en cada primer tiempo
  y se esconde cuando otro momento ocupa el cuadro.
- **Salvapantallas:** el logo suelto rebotando por el cuadro como el del DVD
  («como navegando el video»), en los compases que diga el proyecto.
- **Imágenes de marca:** las de la galería donde se lee «Curiana Radio»
  (curaduria/<biblioteca>.json); los destacados las prefieren.

Configuración en proyecto.json:

    "logo": {
      "sello": {"esquina": "abajo-derecha", "alto": 0.08, "opacidad": 0.85},
      "salvapantallas": [{"compas": 9, "compases": 4, "alto": 0.24, "velocidad": 5}]
    }
"""

from __future__ import annotations

import math

from PIL import Image

from .catalogo import _curaduria
from .rutas import Proyecto, salir


def archivos(p: Proyecto) -> dict:
    """Rutas (relativas a la biblioteca) de las versiones del logo."""
    cur = _curaduria(p.cfg.get("biblioteca", p.nombre)).get("logo")
    if not cur:
        salir("la curaduría de la biblioteca no declara el logo")
    return {k: f"marca/{v}" for k, v in cur.items() if k != "origen"}


def item_logo(p: Proyecto, clave: str) -> dict:
    """El logo como si fuera una imagen del catálogo (para destacarlo o meterlo en una cinta)."""
    ruta = archivos(p)[clave]
    w, h = Image.open(p.medios / ruta).size
    return {"id": f"logo-{clave}", "img": ruta, "w": w, "h": h, "ratio": w / h, "luz": 0.5, "tono": 0.0, "sat": 0.0, "marca": True, "tipos": ["cartel"]}


def destacadas_marca(p: Proyecto, items: list[dict]) -> list[dict]:
    """Las imágenes de marca en el orden de la curaduría (las mejores para destacar primero)."""
    cur = _curaduria(p.cfg.get("biblioteca", p.nombre))
    por_id = {it["id"]: it for it in items}
    primero = [por_id[i] for i in cur.get("destacadas_marca", []) if i in por_id]
    resto = [it for it in items if it.get("marca") and it not in primero]
    return primero + resto


def timeline_logo(p: Proyecto, compases: list[dict], fps: int, W: int, H: int, ocupado: list[tuple[int, int]], rng) -> dict | None:
    """El bloque `logo` del timeline. `ocupado`: tramos (cuadros) donde otro momento manda y el sello se esconde."""
    cfg = p.cfg.get("logo")
    if not cfg:
        return None
    arch = archivos(p)
    salida: dict = {}
    salvas = []
    for s in cfg.get("salvapantallas", []):
        c0 = compases[s["compas"]]
        c1 = compases[min(len(compases) - 1, s["compas"] + s.get("compases", 1) - 1)]
        ini, fin = round(c0["ini"] * fps), round(c1["fin"] * fps)
        imgs = [arch[k] for k in s.get("versiones", ["lockup_oscuro", "lockup_claro"])]
        w0, h0 = Image.open(p.medios / imgs[0]).size
        alto = s.get("alto", 0.24) * H
        ancho = alto * w0 / h0
        v = s.get("velocidad", 5.0)  # px por cuadro, a 1080 de alto
        ang = rng.uniform(0.35, 0.65) * 3.14159 / 2
        salvas.append(
            {
                "ini": ini,
                "fin": fin,
                "imgs": imgs,
                "ancho": round(ancho, 1),
                "alto": round(alto, 1),
                "x0": round(float(rng.uniform(0.1, 0.6) * (W - ancho)), 1),
                "y0": round(float(rng.uniform(0.1, 0.6) * (H - alto)), 1),
                "vx": round(v * H / 1080 * math.cos(ang), 3),
                "vy": round(v * H / 1080 * math.sin(ang), 3),
                "oscuro": s.get("oscuro", 0.45),
            }
        )
    if salvas:
        salida["salvapantallas"] = salvas

    sello = cfg.get("sello")
    if sello:
        img = arch[sello.get("version", "isotipo_claro")]
        w0, h0 = Image.open(p.medios / img).size
        alto = sello.get("alto", 0.08) * H
        ancho = alto * w0 / h0
        margen = sello.get("margen", 0.035) * H
        esquina = sello.get("esquina", "abajo-derecha")
        x = margen if "izquierda" in esquina else W - margen - ancho
        y = margen if "arriba" in esquina else H - margen - alto
        salida["sello"] = {
            "img": img,
            "x": round(x, 1),
            "y": round(y, 1),
            "ancho": round(ancho, 1),
            "alto": round(alto, 1),
            "opacidad": sello.get("opacidad", 0.85),
            "pulsos": [round(c["ini"] * fps) for c in compases],
            "ocultar": [list(o) for o in ocupado] + [[s["ini"], s["fin"]] for s in salvas],
        }
    return salida
