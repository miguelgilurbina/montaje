"""Collage infinito: imágenes opacas, nítidas, que se acumulan al pulso fino.

Lo que pidió Miguel para el experimento 03, regla por regla:

- **Cada imagen al 100 %**: opaca, sin mezcla, sin calado, y nunca más grande
  que su tamaño nativo (no se reescala hacia arriba). Son el producto de
  Curiana Radio: tienen que verse con su detalle.
- **Superpuesto es literal**: collage. Cada imagen nueva cae encima, como un
  papel con su sombra, y se queda. El cuadro se va llenando.
- **Infinito**: la cámara se aleja despacio todo el tiempo; lo viejo se achica
  debajo y lo nuevo llega grande arriba. Cada imagen busca el lugar del collage
  que lleva más tiempo sin cubrirse, para que se llene parejo hacia afuera.
- **Más rápido, al tempo fino**: el ritmo de entradas va por compases —una por
  compás en la intro, una por golpe al entrar la batería, luego corcheas y
  semicorcheas— según el avance y la energía del tramo.
"""

from __future__ import annotations

import datetime as dt
import math
import re

import numpy as np

from . import catalogo, musica
from .planificar import audio_de, escribir
from .rutas import Proyecto, salir

POR_DEFECTO = {
    "semilla": 11,
    "umbrales": [0.12, 0.32, 0.6],  # caos a partir del cual se entra por golpe, por corchea, por semicorchea
    "respiro": 0.1,  # un compás que cae esto o más en energía respecto del anterior baja dos niveles
    "alto": [0.8, 0.36],  # alto en pantalla de una imagen nueva (fracción del cuadro): al inicio → al final
    "acento": 1.25,  # las que caen en el primer tiempo del compás, más grandes
    "zoom_final": 0.42,  # escala de la cámara al final (1 = sin alejarse)
    "giro": 2.0,  # rotación máxima, en grados (collage de papel)
    "sombra": 0.55,
    "entrada_cuadros": [6, 2],  # duración del «golpe» de entrada: en calma → en el pico
    "candidatos": 28,
    "una_por_generacion": True,
}

NIVELES = [1, 4, 8, 16]  # entradas por compás de 4 golpes


def _generacion(slug: str) -> str:
    """Las variantes de una misma generación de Midjourney comparten todo menos el último número."""
    return re.sub(r"-\d+$", "", slug)


def planificar(p: Proyecto) -> None:
    prm = {**POR_DEFECTO, **p.cfg.get("montaje", {})}
    out = {"ancho": 1920, "alto": 1080, "fps": 30, "fondo": "#08080a", **p.cfg.get("salida", {})}
    W, H, fps = out["ancho"], out["alto"], out["fps"]
    items = catalogo.cargar(p)
    m = musica.cargar(p)
    rng = np.random.default_rng(prm["semilla"])
    D = m["duracion"]
    beats = np.array(m["beats"])
    energia = np.array(m["energia"])
    fase = m["fase_compas"]

    # ── 1. Compases y su nivel de densidad ──────────────────────────────────
    entra_bateria = beats[m.get("golpes_intro", 0)]
    compases = []
    for i in range(fase, len(beats), 4):
        ini = beats[i]
        fin = beats[i + 4] if i + 4 < len(beats) else D
        e = float(energia[i : i + 4].mean())
        compases.append({"ini": float(ini), "fin": float(fin), "e": e, "intro": ini < entra_bateria - 0.05})
    if fase > 0:  # golpes sueltos antes del primer compás completo: van con la intro
        compases.insert(0, {"ini": float(beats[0]), "fin": float(beats[fase]), "e": 0.0, "intro": True})
    previo_e = None
    for c in compases:
        avance = c["ini"] / D
        caos = avance**0.9 * (0.5 + 0.5 * c["e"])
        nivel = sum(caos >= u for u in prm["umbrales"])
        if c["intro"]:
            nivel = 0
        else:
            nivel = max(1, nivel)
            if previo_e is not None and previo_e - c["e"] >= prm["respiro"]:
                nivel = max(1, nivel - 2)
        c["caos"], c["nivel"] = caos, nivel
        previo_e = c["e"]

    # ── 2. Entradas: el compás se parte en tantas como dice su nivel ─────────
    entradas = []
    for c in compases:
        k = NIVELES[c["nivel"]]
        if c["fin"] - c["ini"] < 0.5 * (60 / m["bpm"]) * 4 and c["intro"]:
            k = 1
        for j in range(k):
            t = c["ini"] + (c["fin"] - c["ini"]) * j / k
            if t >= D - 0.05:
                continue
            entradas.append({"t": t, "caos": c["caos"], "nivel": c["nivel"], "primero": j == 0, "e": c["e"]})
    n = len(entradas)

    # ── 3. Qué imagen: de oscuras a claras con la subida, encadenadas por tono ─
    elegidas = _elegir(items, entradas, prm, rng)

    # ── 4. Cámara: se aleja de forma continua (zoom exponencial, cada vez más rápido) ─
    def escala(t: float) -> float:
        u = min(1.0, max(0.0, t / D))
        return prm["zoom_final"] ** (u**1.6)

    deriva = rng.uniform(-1, 1, size=2) * np.array([W, H]) * 0.04
    camara = []
    for f in range(0, math.ceil(D * fps) + 3, 3):
        u = min(1.0, f / fps / D)
        camara.append([f, round(float(deriva[0] * u), 2), round(float(deriva[1] * u), 2), round(escala(f / fps), 5)])

    def cam(t):
        u = min(1.0, t / D)
        return deriva[0] * u, deriva[1] * u, escala(t)

    # ── 5. Dónde cae cada una: el hueco más viejo del collage ───────────────
    s_fin = escala(D)
    ancho_mundo, alto_mundo = W / s_fin * 1.1, H / s_fin * 1.1
    gx, gy = 96, 54
    edad = np.full((gy, gx), -1e9)  # último momento en que se cubrió cada celda del mundo

    def celdas(x, y, w, h):
        x0 = int(np.clip((x - w / 2 + ancho_mundo / 2) / ancho_mundo * gx, 0, gx))
        x1 = int(np.clip((x + w / 2 + ancho_mundo / 2) / ancho_mundo * gx, 0, gx))
        y0 = int(np.clip((y - h / 2 + alto_mundo / 2) / alto_mundo * gy, 0, gy))
        y1 = int(np.clip((y + h / 2 + alto_mundo / 2) / alto_mundo * gy, 0, gy))
        return slice(y0, max(y0 + 1, y1)), slice(x0, max(x0 + 1, x1))

    piezas = []
    for k, (en, it) in enumerate(zip(entradas, elegidas)):
        t = en["t"]
        cx, cy, s = cam(t)
        alto_px = (prm["alto"][0] + (prm["alto"][1] - prm["alto"][0]) * en["caos"]) * H * rng.uniform(0.85, 1.15)
        if en["primero"] and en["nivel"] >= 1:
            alto_px *= prm["acento"]
        alto_px = min(alto_px, it["h"], 0.95 * H)  # nunca más grande que su tamaño nativo
        ancho_px = alto_px * it["ratio"]
        if ancho_px > min(it["w"], 0.95 * W):
            ancho_px = min(it["w"], 0.95 * W)
            alto_px = ancho_px / it["ratio"]
        w, h = ancho_px / s, alto_px / s  # en unidades del mundo

        # Candidatos dentro de lo que la cámara ve ahora; gana el que cubre lo más viejo.
        vista_w, vista_h = W / s, H / s
        mejor, mejor_puntaje = None, -np.inf
        for _ in range(prm["candidatos"] if k else 1):
            if k == 0:
                x, y = cx, cy
            else:
                x = cx + rng.uniform(-0.5, 0.5) * max(vista_w - w * 0.6, 1)
                y = cy + rng.uniform(-0.5, 0.5) * max(vista_h - h * 0.6, 1)
            sy, sx = celdas(x, y, w, h)
            puntaje = float(np.mean(np.minimum(t - edad[sy, sx], 1e3)))
            if puntaje > mejor_puntaje:
                mejor, mejor_puntaje = (x, y), puntaje
        x, y = mejor
        sy, sx = celdas(x, y, w, h)
        edad[sy, sx] = t

        entrada = round(prm["entrada_cuadros"][0] + (prm["entrada_cuadros"][1] - prm["entrada_cuadros"][0]) * en["caos"])
        piezas.append(
            {
                "id": it["id"],
                "img": it["img"],
                "ini": round(t * fps),
                "entrada": max(1, entrada),
                "x": round(x, 1),
                "y": round(y, 1),
                "ancho": round(w, 1),
                "alto": round(h, 1),
                "rot": round(float(rng.uniform(-1, 1) * prm["giro"]), 2),
            }
        )

    _marcar_tapadas(piezas, ancho_mundo, alto_mundo)

    duracion = math.ceil(D * fps)
    timeline = {
        "version": 3,
        "modo": "collage",
        "proyecto": p.nombre,
        **{k: out[k] for k in ("ancho", "alto", "fps", "fondo")},
        "duracion": duracion,
        "audio": audio_de(p, m),
        "meta": {
            "generado": dt.datetime.now().isoformat(timespec="seconds"),
            "bpm": m["bpm"],
            "imagenes": n,
            "parametros": prm,
        },
        "camara": camara,
        "collage": {"sombra": prm["sombra"], "piezas": piezas},
        "capas": [],
    }
    escribir(p.timeline, timeline)

    print(f"{n} imágenes en collage sobre {D:.1f} s a {m['bpm']} BPM → {p.timeline}")
    nombres = ["por compás", "por golpe", "por corchea", "por semicorchea"]
    for c in compases:
        print(f"  {c['ini']:6.2f} s  energía {c['e']:.2f}  caos {c['caos']:.2f}  {NIVELES[c['nivel']]:2d} {nombres[c['nivel']]}{'  (intro)' if c['intro'] else ''}")


def _marcar_tapadas(piezas: list[dict], ancho_mundo: float, alto_mundo: float) -> None:
    """Pone `tapada` (cuadro) en cada pieza que otras posteriores terminan cubriendo entera.

    Al final del collage hay cientos de papeles apilados y casi todos quedaron
    debajo: dibujarlos igual hace que cada cuadro tarde segundos. Se calcula en una
    rejilla del mundo, conservadora: la pieza tapada cuenta con su caja más un
    margen (por el giro y la sombra) y la que tapa sólo con su interior.
    """
    gx, gy = 640, 360

    def rect(p, factor):
        w, h = p["ancho"] * factor, p["alto"] * factor
        x0 = int(np.floor((p["x"] - w / 2 + ancho_mundo / 2) / ancho_mundo * gx))
        x1 = int(np.ceil((p["x"] + w / 2 + ancho_mundo / 2) / ancho_mundo * gx))
        y0 = int(np.floor((p["y"] - h / 2 + alto_mundo / 2) / alto_mundo * gy))
        y1 = int(np.ceil((p["y"] + h / 2 + alto_mundo / 2) / alto_mundo * gy))
        return max(0, y0), min(gy, y1), max(0, x0), min(gx, x1)

    # Por pieza: su caja con margen (110 %) y qué celdas de esa caja siguen a la vista.
    a_la_vista: list[tuple[int, int, np.ndarray] | None] = []
    for j, p in enumerate(piezas):
        # La nueva tapa sólo con su interior (93 %): las esquinas giradas no cuentan.
        ty0, ty1, tx0, tx1 = rect(p, 0.93)
        for i in range(j):
            if a_la_vista[i] is None:
                continue
            y0, x0, vista = a_la_vista[i]
            iy0, iy1 = max(y0, ty0), min(y0 + vista.shape[0], ty1)
            ix0, ix1 = max(x0, tx0), min(x0 + vista.shape[1], tx1)
            if iy0 >= iy1 or ix0 >= ix1:
                continue
            vista[iy0 - y0 : iy1 - y0, ix0 - x0 : ix1 - x0] = False
            if not vista.any():
                piezas[i]["tapada"] = p["ini"] + p["entrada"]
                a_la_vista[i] = None
        y0, y1, x0, x1 = rect(p, 1.10)
        a_la_vista.append((y0, x0, np.ones((y1 - y0, x1 - x0), dtype=bool)) if y1 > y0 and x1 > x0 else None)


def _elegir(items: list[dict], entradas: list[dict], prm: dict, rng) -> list[dict]:
    """Una imagen por entrada: la luz sube con la energía y el tono encadena con la anterior.
    Se evita repetir variantes de una misma generación mientras queden otras."""
    usadas_gen: set[str] = set()
    usadas: set[int] = set()
    luces = np.array([it["luz"] for it in items])
    lo, hi = np.percentile(luces, [5, 95])
    tono_previo = None
    elegidas = []
    for en in entradas:
        objetivo = lo + (hi - lo) * min(1.0, 0.15 + 0.85 * en["caos"])
        disponibles = [
            j
            for j in range(len(items))
            if j not in usadas and (not prm["una_por_generacion"] or _generacion(items[j]["id"]) not in usadas_gen)
        ]
        if not disponibles:
            disponibles = [j for j in range(len(items)) if j not in usadas] or list(range(len(items)))

        def puntaje(j):
            it = items[j]
            d = abs(it["luz"] - objetivo) * 2
            if tono_previo is not None and it["sat"] >= 0.12:
                dt_ = abs(it["tono"] - tono_previo) % 360
                d += min(dt_, 360 - dt_) / 180 * 0.6
            return d + rng.uniform(0, 0.08)  # un poco de azar para que no sea un degradé perfecto

        k = min(disponibles, key=puntaje)
        usadas.add(k)
        usadas_gen.add(_generacion(items[k]["id"]))
        elegidas.append(items[k])
        if items[k]["sat"] >= 0.12:
            tono_previo = items[k]["tono"]
    return elegidas
