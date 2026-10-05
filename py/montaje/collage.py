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
    "silencio": 0.0,  # un compás con menos energía que esto no recibe imágenes (0 = nunca)
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
        # Intro = antes de que el detector encuentre pulso Y con poca energía (un tramo
        # puede empezar en plena canción y el primer golpe detectado llegar tarde).
        compases.append({"ini": float(ini), "fin": float(fin), "e": e, "intro": ini < entra_bateria - 0.05 and e < 0.35})
    if fase > 0:  # golpes sueltos antes del primer compás completo: van con la intro
        compases.insert(0, {"ini": float(beats[0]), "fin": float(beats[fase]), "e": 0.0, "intro": True})
    previo_e = None
    for c in compases:
        avance = c["ini"] / D
        caos = avance**0.9 * (0.5 + 0.5 * c["e"])
        nivel = sum(caos >= u for u in prm["umbrales"])
        if c["intro"]:
            nivel = 0
        elif c["e"] < prm["silencio"]:
            nivel = -1  # la canción casi calla: el collage se queda quieto
        else:
            nivel = max(1, nivel)
            if previo_e is not None and previo_e - c["e"] >= prm["respiro"]:
                nivel = max(1, nivel - 2)
        c["caos"], c["nivel"] = caos, nivel
        previo_e = c["e"]

    # ── 2. Momentos: compases donde cambia el tempo o el estilo ─────────────
    momentos_cfg = {int(mo["compas"]): mo for mo in p.cfg.get("momentos", [])}
    for i in momentos_cfg:
        if not 0 <= i < len(compases):
            salir(f"el momento del compás {i} cae fuera del tramo (hay {len(compases)} compases)")
    reservadas: set[str] = set()
    heroe_de: dict[int, dict] = {}
    rafaga_de: dict[int, list[dict]] = {}
    for i, mo in sorted(momentos_cfg.items()):
        if mo["tipo"] == "destacado":
            heroe_de[i] = _heroe(p, items, mo, reservadas)
        elif mo["tipo"] == "rafaga":
            rafaga_de[i] = _rafaga(items, mo.get("por_compas", 8), reservadas, rng, mo.get("de"))
        elif mo["tipo"] not in ("barrido", "video"):
            salir(f"tipo de momento desconocido: {mo['tipo']} (hay: destacado, rafaga, barrido, video)")
    # Compases que ocupa un video (puede durar varios).
    en_video = {i + k: i for i, mo in momentos_cfg.items() if mo["tipo"] == "video" for k in range(mo.get("compases", 1))}

    # ── 3. Entradas: el compás se parte en tantas como dice su nivel ─────────
    # Durante un destacado o una ráfaga el collage se detiene (cambio de tempo); al
    # terminar un destacado, su imagen cae al collage en el primer tiempo siguiente.
    entradas = []
    for ci, c in enumerate(compases):
        mo = momentos_cfg.get(ci)
        if (mo and mo["tipo"] in ("destacado", "rafaga")) or c["nivel"] < 0 or ci in en_video:
            continue
        k = NIVELES[c["nivel"]]
        if c["fin"] - c["ini"] < 0.5 * (60 / m["bpm"]) * 4 and c["intro"]:
            k = 1
        for j in range(k):
            t = c["ini"] + (c["fin"] - c["ini"]) * j / k
            if t >= D - 0.05:
                continue
            en = {"t": t, "caos": c["caos"], "nivel": c["nivel"], "primero": j == 0, "e": c["e"]}
            if j == 0 and (ci - 1) in heroe_de and not momentos_cfg[ci - 1].get("firma"):
                en["fija"] = heroe_de[ci - 1]
                en["heroe"] = ci - 1
            entradas.append(en)
    n = len(entradas)

    # ── 4. Qué imagen: de oscuras a claras con la subida, encadenadas por tono ─
    elegidas = _elegir(items, entradas, prm, rng, reservadas)

    # ── 5. Cámara: se aleja de forma continua (zoom exponencial, cada vez más rápido) ─
    def escala(t: float) -> float:
        u = min(1.0, max(0.0, t / D))
        return prm["zoom_final"] ** (u**1.6)

    deriva = rng.uniform(-1, 1, size=2) * np.array([W, H]) * 0.04

    # Barridos: la cámara salta de golpe a una zona vacía del mundo (una vista y algo más).
    direcciones = [(1.0, 0.0), (-0.55, 0.85), (-1.0, 0.0), (0.55, -0.85)]
    barridos = []
    for n_b, (ci, mo) in enumerate(sorted((i, mo) for i, mo in momentos_cfg.items() if mo["tipo"] == "barrido")):
        t0 = compases[ci]["ini"]
        dx, dy = mo.get("direccion", direcciones[n_b % len(direcciones)])
        distancia = 1.15 * W / escala(t0)
        barridos.append((t0, mo.get("cuadros", 10) / fps, dx * distancia, dy * distancia * H / W * 1.6))

    def desplazamiento(t):
        x = y = 0.0
        for t0, dur, bx, by in barridos:
            u = min(1.0, max(0.0, (t - t0) / dur))
            u = u * u * (3 - 2 * u)
            x, y = x + bx * u, y + by * u
        return x, y

    def cam(t):
        u = min(1.0, t / D)
        px, py = desplazamiento(t)
        return deriva[0] * u + px, deriva[1] * u + py, escala(t)

    camara = []
    for f in range(0, math.ceil(D * fps) + 3, 1 if barridos else 3):
        cx, cy, s = cam(f / fps)
        camara.append([f, round(float(cx), 2), round(float(cy), 2), round(s, 5)])

    # ── 6. Dónde cae cada una: el hueco más viejo del collage ───────────────
    s_fin = escala(D)
    ancho_mundo, alto_mundo = W / s_fin * 1.1, H / s_fin * 1.1
    # El mundo se agranda hacia donde barre la cámara.
    px_tot = [desplazamiento(t)[0] for t in (0, D)] + [0.0]
    py_tot = [desplazamiento(t)[1] for t in (0, D)] + [0.0]
    for t0, dur, bx, by in barridos:
        px_tot.append(desplazamiento(t0 + dur)[0])
        py_tot.append(desplazamiento(t0 + dur)[1])
    mundo = (
        -ancho_mundo / 2 + min(px_tot),
        ancho_mundo / 2 + max(px_tot),
        -alto_mundo / 2 + min(py_tot),
        alto_mundo / 2 + max(py_tot),
    )
    gx = round(96 * (mundo[1] - mundo[0]) / ancho_mundo)
    gy = round(54 * (mundo[3] - mundo[2]) / alto_mundo)
    edad = np.full((gy, gx), -1e9)  # último momento en que se cubrió cada celda del mundo

    def celdas(x, y, w, h):
        x0 = int(np.clip((x - w / 2 - mundo[0]) / (mundo[1] - mundo[0]) * gx, 0, gx))
        x1 = int(np.clip((x + w / 2 - mundo[0]) / (mundo[1] - mundo[0]) * gx, 0, gx))
        y0 = int(np.clip((y - h / 2 - mundo[2]) / (mundo[3] - mundo[2]) * gy, 0, gy))
        y1 = int(np.clip((y + h / 2 - mundo[2]) / (mundo[3] - mundo[2]) * gy, 0, gy))
        return slice(y0, max(y0 + 1, y1)), slice(x0, max(x0 + 1, x1))

    piezas = []
    pieza_heroe: dict[int, int] = {}
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
        if "heroe" in en:
            entrada = 1  # llega volando desde el destacado: aparece de una
            pieza_heroe[en["heroe"]] = len(piezas)
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

    _marcar_tapadas(piezas, mundo)

    # ── 7. Momentos en cuadros ──────────────────────────────────────────────
    def a_pantalla(it, alto_max, ancho_max):
        """Lo más grande que cabe, sin pasar de su tamaño nativo."""
        alto_px = min(alto_max * H, it["h"], ancho_max * W / it["ratio"])
        return round(alto_px * it["ratio"], 1), round(alto_px, 1)

    momentos = []
    for ci, mo in sorted(momentos_cfg.items()):
        c = compases[ci]
        ini, fin = round(c["ini"] * fps), round(c["fin"] * fps)
        if mo["tipo"] == "destacado":
            it = heroe_de[ci]
            ancho_px, alto_px = a_pantalla(it, 0.86, 0.9)
            firma = bool(mo.get("firma"))
            if not firma and ci not in pieza_heroe:
                salir(f"el destacado del compás {ci} no tiene compás siguiente donde caer (¿firma?)")
            momentos.append(
                {
                    "tipo": "destacado",
                    "ini": ini,
                    # La firma (el logo al final) no aterriza: se queda hasta que termina el video.
                    "fin": math.ceil(D * fps) if firma else piezas[pieza_heroe[ci]]["ini"],
                    "entrada": mo.get("entrada", 8),
                    "salida": mo.get("salida", 10),
                    "oscuro": mo.get("oscuro", 0.75),
                    "id": it["id"],
                    "img": it["img"],
                    "ancho": ancho_px,
                    "alto": alto_px,
                    "pieza": -1 if firma else pieza_heroe[ci],
                }
            )
        elif mo["tipo"] == "rafaga":
            fotos = rafaga_de[ci]
            imagenes = []
            for j, it in enumerate(fotos):
                ancho_px, alto_px = a_pantalla(it, 1.0, 1.0)
                imagenes.append(
                    {"id": it["id"], "img": it["img"], "ini": round((c["ini"] + (c["fin"] - c["ini"]) * j / len(fotos)) * fps), "ancho": ancho_px, "alto": alto_px}
                )
            momentos.append({"tipo": "rafaga", "ini": ini, "fin": fin, "imagenes": imagenes})
        elif mo["tipo"] == "video":
            momentos.append(_momento_video(p, mo, compases, ci, fps, W, H))
        else:
            momentos.append({"tipo": "barrido", "ini": ini, "fin": ini + mo.get("cuadros", 10)})

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
    if momentos:
        timeline["momentos"] = momentos
    if p.cfg.get("logo"):
        from . import marca

        ocupado = [(mo["ini"], mo["fin"]) for mo in momentos if mo["tipo"] in ("destacado", "rafaga", "video")]
        timeline["logo"] = marca.timeline_logo(p, compases, fps, W, H, ocupado, rng)
    escribir(p.timeline, timeline)

    print(f"{n} imágenes en collage sobre {D:.1f} s a {m['bpm']} BPM → {p.timeline}")
    nombres = ["por compás", "por golpe", "por corchea", "por semicorchea"]
    for ci, c in enumerate(compases):
        mo = momentos_cfg.get(ci)
        if mo and mo["tipo"] == "destacado":
            nombre = "FIRMA     " if mo.get("firma") else "DESTACADO "
            ritmo = f"{nombre} {heroe_de[ci].get('titulo', heroe_de[ci]['id'])[:50]}"
        elif mo and mo["tipo"] == "rafaga":
            ritmo = f"RÁFAGA     {len(rafaga_de[ci])} imágenes a pantalla completa{' de ' + mo['de'] if mo.get('de') else ''}"
        elif ci in en_video:
            ritmo = f"VIDEO      {momentos_cfg[en_video[ci]]['src']}"
        elif c["nivel"] < 0:
            ritmo = "silencio: el collage se queda quieto"
        else:
            ritmo = f"{NIVELES[c['nivel']]:2d} {nombres[c['nivel']]}{'  (intro)' if c['intro'] else ''}"
            if mo:
                ritmo += "  + BARRIDO"
        print(f"  {ci:2d}  {c['ini']:6.2f} s  energía {c['e']:.2f}  caos {c['caos']:.2f}  {ritmo}")


def _marcar_tapadas(piezas: list[dict], mundo: tuple[float, float, float, float]) -> None:
    """Pone `tapada` (cuadro) en cada pieza que otras posteriores terminan cubriendo entera.

    Al final del collage hay cientos de papeles apilados y casi todos quedaron
    debajo: dibujarlos igual hace que cada cuadro tarde segundos. Se calcula en una
    rejilla del mundo, conservadora: la pieza tapada cuenta con su caja más un
    margen (por el giro y la sombra) y la que tapa sólo con su interior.
    """
    xmin, xmax, ymin, ymax = mundo
    # Celdas de ~1/640 del ancho del mundo base; si el mundo se agrandó por barridos, más celdas.
    gx = max(640, round(640 * (xmax - xmin) / (ymax - ymin) * 9 / 16))
    gy = round(gx * (ymax - ymin) / (xmax - xmin))

    def rect(p, factor):
        w, h = p["ancho"] * factor, p["alto"] * factor
        x0 = int(np.floor((p["x"] - w / 2 - xmin) / (xmax - xmin) * gx))
        x1 = int(np.ceil((p["x"] + w / 2 - xmin) / (xmax - xmin) * gx))
        y0 = int(np.floor((p["y"] - h / 2 - ymin) / (ymax - ymin) * gy))
        y1 = int(np.ceil((p["y"] + h / 2 - ymin) / (ymax - ymin) * gy))
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


def _momento_video(p: Proyecto, mo: dict, compases: list[dict], ci: int, fps: int, W: int, H: int) -> dict:
    """Un video (por ejemplo la intro hecha con Gemini) que ocupa `compases` compases.

    Se recorta la parte que importa (`recorte`: [x, y, ancho, alto] en píxeles del
    video), se agranda lo justo para caber en el cuadro y se ajusta su velocidad
    para que termine exactamente en el golpe donde arranca lo que sigue.
    """
    import json
    import subprocess

    ruta = p.medios / mo["src"]
    if not ruta.exists():
        salir(f"no encuentro el video {ruta}")
    info = json.loads(
        subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration", "-of", "json", str(ruta)],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    )
    vw, vh = info["streams"][0]["width"], info["streams"][0]["height"]
    dur = float(info["format"]["duration"])
    sx, sy, sw, sh = mo.get("recorte", [0, 0, vw, vh])
    k = min(W / sw, H / sh)
    c0 = compases[ci]
    c1 = compases[min(len(compases) - 1, ci + mo.get("compases", 1) - 1)]
    ini, fin = round(c0["ini"] * fps), round(c1["fin"] * fps)
    return {
        "tipo": "video",
        "ini": ini,
        "fin": fin,
        "src": mo["src"],
        "recorte": [sx, sy, sw, sh],
        "fuente": [vw, vh],
        "ancho": round(sw * k, 1),
        "alto": round(sh * k, 1),
        "velocidad": round(dur / ((fin - ini) / fps), 4),
        "volumen": mo.get("volumen", 0),
    }


def _heroe(p: Proyecto, items: list[dict], mo: dict, reservadas: set[str]) -> dict:
    """La imagen de un destacado. `img` puede ser:

    - `"marca"`: la siguiente imagen donde se lee Curiana Radio (orden de la curaduría);
    - `"logo:<versión>"`: el logo mismo (lockup_claro, lockup_oscuro, isotipo_claro…);
    - el slug de una imagen;
    - nada: la panorámica más presente —saturada y de luz media— que no se haya usado.
    """
    from . import marca

    pedida = mo.get("img")
    if pedida == "marca":
        for it in marca.destacadas_marca(p, items):
            if it["id"] not in reservadas:
                reservadas.add(it["id"])
                return it
        salir("no quedan imágenes de marca para el destacado")
    if pedida and pedida.startswith("logo:"):
        return marca.item_logo(p, pedida.split(":", 1)[1])
    if pedida:
        for it in items:
            if it["id"] == pedida:
                reservadas.add(it["id"])
                return it
        salir(f"no encuentro la imagen «{pedida}» del destacado")
    gens = {_generacion(r) for r in reservadas}
    candidatas = [it for it in items if it["familia"] == "panoramica" and it["id"] not in reservadas and _generacion(it["id"]) not in gens]
    it = max(candidatas, key=lambda it: it["sat"] * (1 - 1.5 * abs(it["luz"] - 0.42)))
    reservadas.add(it["id"])
    return it


def _rafaga(items: list[dict], cuantas: int, reservadas: set[str], rng, de: str | None = None) -> list[dict]:
    """Las imágenes de una ráfaga: una familia de color (tonos vecinos de una semilla
    saturada), sin variantes repetidas, para que el corte rápido tenga unidad.
    `de` la limita a un tipo de imagen («retrato», «paisaje», «abstracto»…) o a «marca»."""
    gens = {_generacion(r) for r in reservadas}

    def sirve(it):
        if de is None:
            return it["sat"] >= 0.2
        if de == "marca":
            return bool(it.get("marca"))
        return de in it.get("tipos", [])

    libres = [it for it in items if it["id"] not in reservadas and _generacion(it["id"]) not in gens and sirve(it)]
    if de == "marca":  # pocas y con variantes hermanas: aquí sí se aceptan generaciones repetidas
        libres = [it for it in items if it["id"] not in reservadas and it.get("marca")]
    if len(libres) < cuantas:
        salir(f"la ráfaga pide {cuantas} imágenes de «{de}» y sólo hay {len(libres)} libres")
    saturadas = sorted(libres, key=lambda it: -it["sat"])[:40]
    semilla = saturadas[int(rng.integers(len(saturadas)))]

    def distancia(it):
        d = abs(it["tono"] - semilla["tono"]) % 360
        return min(d, 360 - d)

    elegidas, usadas_gen = [], set()
    for it in sorted(libres, key=distancia):
        g = _generacion(it["id"])
        if g in usadas_gen:
            continue
        elegidas.append(it)
        usadas_gen.add(g)
        reservadas.add(it["id"])
        if len(elegidas) == cuantas:
            break
    rng.shuffle(elegidas)
    return elegidas


def _elegir(items: list[dict], entradas: list[dict], prm: dict, rng, reservadas: set[str] | None = None) -> list[dict]:
    """Una imagen por entrada: la luz sube con la energía y el tono encadena con la anterior.
    Se evita repetir variantes de una misma generación mientras queden otras. Las
    reservadas para momentos no entran al collage, salvo las fijas (la imagen de un
    destacado cayendo en su lugar)."""
    reservadas = reservadas or set()
    usadas_gen: set[str] = {_generacion(r) for r in reservadas}
    usadas: set[int] = {j for j, it in enumerate(items) if it["id"] in reservadas}
    luces = np.array([it["luz"] for it in items])
    lo, hi = np.percentile(luces, [5, 95])
    tono_previo = None
    elegidas = []
    for en in entradas:
        if "fija" in en:
            elegidas.append(en["fija"])
            if en["fija"]["sat"] >= 0.12:
                tono_previo = en["fija"]["tono"]
            continue
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
