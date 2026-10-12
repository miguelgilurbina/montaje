"""Cinta: un feed vertical de imágenes que sube un paso por golpe, en loop sin costura.

Pensado para reels: las imágenes van en columna, nítidas (nunca más grandes que
su tamaño nativo), y la cinta avanza una imagen por paso. Cada compás dice
cuántos pasos da (4 = por golpe, 8 = por corchea: doble tiempo) o qué momento
ocupa su lugar (un destacado que saca la imagen del centro al frente, una ráfaga
a pantalla completa); durante un momento la cinta se detiene.

**Loop:** la cinta es cíclica. En el último cuadro termina de llegar la imagen
que sigue a la última, que es la primera: el video empalma consigo mismo y el
reel se repite sin que se note el corte. El orden de las imágenes recorre el
círculo de color, así que el color también vuelve a donde empezó.

Configuración en proyecto.json:

    "montaje": {"modo": "cinta", "ancho": 0.84, "alto_max": 0.62, "hueco": 0.025},
    "compases": [{"pasos": 4}, {"pasos": 8}, {"momento": "destacado", "img": "marca"},
                 {"momento": "rafaga", "por_compas": 16, "de": "marca"}, ...],
    "logo": {"sello": {...}, "en_cinta": [16]}
"""

from __future__ import annotations

import datetime as dt

import numpy as np

from . import catalogo, marca, musica
from .collage import _generacion, _heroe, _rafaga
from .planificar import audio_de, escribir
from .rutas import Proyecto, salir

POR_DEFECTO = {
    "semilla": 21,
    "ancho": 0.84,  # ancho de las imágenes de la cinta (fracción del cuadro)
    "alto_max": 0.62,  # alto máximo (las verticales se achican para que entren varias)
    "hueco": 0.025,  # espacio entre imágenes (fracción del alto del cuadro)
    "paso_cuadros": 7,  # cuánto dura cada paso de la cinta
    "sombra": 0.5,
}


def planificar(p: Proyecto) -> None:
    prm = {**POR_DEFECTO, **p.cfg.get("montaje", {})}
    out = {"ancho": 1080, "alto": 1920, "fps": 30, "fondo": "#08080a", **p.cfg.get("salida", {})}
    W, H, fps = out["ancho"], out["alto"], out["fps"]
    items = catalogo.cargar(p)
    m = musica.cargar(p)
    rng = np.random.default_rng(prm["semilla"])
    plan = p.cfg.get("compases")
    if not plan:
        salir("la cinta necesita `compases` en proyecto.json")

    # ── 1. Compases y pasos ──────────────────────────────────────────────────
    beats = np.array(m["beats"])
    fase = m["fase_compas"]
    D = m["duracion"]
    compases = []
    for i in range(fase, len(beats), 4):
        fin = beats[i + 4] if i + 4 < len(beats) else D
        compases.append({"ini": float(beats[i]), "fin": float(fin)})
    if len(compases) < len(plan):
        salir(f"el tramo tiene {len(compases)} compases y el plan pide {len(plan)}")
    compases = compases[: len(plan)]
    compases[0]["ini"] = 0.0  # el loop empieza en el primer cuadro
    fin_loop = compases[-1]["fin"]

    rejilla = []  # momentos en que una imagen queda centrada
    for c, cfg in zip(compases, plan):
        k = cfg.get("pasos", 0) if "momento" not in cfg else 0
        rejilla += [c["ini"] + (c["fin"] - c["ini"]) * j / k for j in range(k)]
    if not rejilla or rejilla[0] > 1e-6:
        salir("el primer compás de la cinta tiene que dar pasos (el loop arranca con la cinta en marcha)")
    n = len(rejilla)

    # ── 2. Qué imagen en cada lugar ─────────────────────────────────────────
    reservadas: set[str] = set()
    fijas: dict[int, dict] = {}
    for c, cfg in zip(compases, plan):
        if cfg.get("momento") == "destacado":
            # La imagen centrada durante el compás es la última que llegó antes de él.
            k = sum(1 for t in rejilla if t <= c["ini"] + 1e-6) - 1
            fijas[k % n] = _heroe(p, items, cfg, reservadas)
    for k in (p.cfg.get("logo") or {}).get("en_cinta", []):
        fijas[k % n] = marca.item_logo(p, "lockup_claro")
    rafagas = {}
    for ci, cfg in enumerate(plan):
        if cfg.get("momento") == "rafaga":
            rafagas[ci] = _rafaga(items, cfg.get("por_compas", 8), reservadas, rng, cfg.get("de"))

    resto = _rueda_de_color(items, n - len(fijas), reservadas, rng)
    cinta, j = [], 0
    for k in range(n):
        if k in fijas:
            cinta.append(fijas[k])
        else:
            cinta.append(resto[j])
            j += 1

    # ── 3. Geometría de la cinta ────────────────────────────────────────────
    hueco = prm["hueco"] * H
    medidas = []
    for it in cinta:
        ancho = min(prm["ancho"] * W, it["w"])
        alto = ancho / it["ratio"]
        if alto > prm["alto_max"] * H:
            alto = prm["alto_max"] * H
            ancho = alto * it["ratio"]
        medidas.append((ancho, alto))
    ys = [0.0]
    for k in range(n):
        siguiente = medidas[(k + 1) % n][1]
        ys.append(ys[-1] + medidas[k][1] / 2 + hueco + siguiente / 2)
    largo = ys[n]

    # ── 4. Desplazamiento: llega a cada imagen justo en su golpe ─────────────
    llegadas = rejilla[1:] + [fin_loop]  # la imagen k+1 queda centrada en llegadas[k]
    duracion = round(fin_loop * fps)
    desplazamiento = []
    for f in range(duracion + 1):
        t = f / fps
        k = sum(1 for x in llegadas if x <= t + 1e-9)  # imágenes que ya llegaron
        if k >= n:
            desplazamiento.append([f, round(largo, 2)])
            continue
        objetivo = llegadas[k]
        previa = rejilla[k]
        d = min(prm["paso_cuadros"] / fps, 0.8 * (objetivo - previa))
        if t < objetivo - d:
            y = ys[k]
        else:
            u = (t - (objetivo - d)) / d
            u = 2 * u * u if u < 0.5 else 1 - (-2 * u + 2) ** 2 / 2
            y = ys[k] + (ys[k + 1] - ys[k]) * u
        desplazamiento.append([f, round(y, 2)])

    # ── 5. Momentos ──────────────────────────────────────────────────────────
    momentos, ocupado = [], []
    for ci, (c, cfg) in enumerate(zip(compases, plan)):
        ini, fin = round(c["ini"] * fps), round(c["fin"] * fps)
        if cfg.get("momento") == "destacado":
            k = sum(1 for t in rejilla if t <= c["ini"] + 1e-6) - 1
            it = cinta[k % n]
            # En vertical una horizontal ya ocupa el ancho: el destacado la lleva a su tamaño
            # nativo (1:1, todo su detalle) aunque se salga un poco por los lados.
            alto = min(0.8 * H, it["h"])
            ancho_i, alto_i = medidas[k % n]
            momentos.append(
                {
                    "tipo": "destacado",
                    "ini": ini,
                    "fin": fin,
                    "entrada": cfg.get("entrada", 7),
                    "salida": cfg.get("salida", 7),
                    "oscuro": cfg.get("oscuro", 0.7),
                    "id": it["id"],
                    "img": it["img"],
                    "ancho": round(alto * it["ratio"], 1),
                    "alto": round(alto, 1),
                    "pieza": -1,
                    "desde": {"x": W / 2, "y": H / 2, "ancho": round(ancho_i, 1), "alto": round(alto_i, 1)},
                }
            )
            ocupado.append((ini, fin))
        elif cfg.get("momento") == "rafaga":
            fotos = rafagas[ci]
            imagenes = []
            for j, it in enumerate(fotos):
                alto = min(H, it["h"], W / it["ratio"])
                t = c["ini"] + (c["fin"] - c["ini"]) * j / len(fotos)
                imagenes.append({"id": it["id"], "img": it["img"], "ini": round(t * fps), "ancho": round(alto * it["ratio"], 1), "alto": round(alto, 1)})
            momentos.append({"tipo": "rafaga", "ini": ini, "fin": fin, "imagenes": imagenes})
            ocupado.append((ini, fin))

    timeline = {
        "version": 4,
        "modo": "cinta",
        "proyecto": p.nombre,
        **{k: out[k] for k in ("ancho", "alto", "fps", "fondo")},
        "duracion": duracion,
        "audio": audio_de(p, m),
        "meta": {"generado": dt.datetime.now().isoformat(timespec="seconds"), "bpm": m["bpm"], "imagenes": n, "parametros": prm},
        "cinta": {
            "items": [
                {"id": it["id"], "img": it["img"], "y": round(ys[k], 2), "ancho": round(medidas[k][0], 1), "alto": round(medidas[k][1], 1)}
                for k, it in enumerate(cinta)
            ],
            "largo": round(largo, 2),
            "desplazamiento": desplazamiento,
            "sombra": prm["sombra"],
        },
        "capas": [],
    }
    if momentos:
        timeline["momentos"] = momentos
    logo = marca.timeline_logo(p, compases, fps, W, H, ocupado, rng)
    if logo:
        timeline["logo"] = logo
    escribir(p.timeline, timeline)

    print(f"cinta de {n} imágenes sobre {fin_loop:.2f} s ({len(plan)} compases a {m['bpm']} BPM), loop → {p.timeline}")
    for ci, (c, cfg) in enumerate(zip(compases, plan)):
        if cfg.get("momento") == "destacado":
            k = sum(1 for t in rejilla if t <= c["ini"] + 1e-6) - 1
            que = f"DESTACADO  {cinta[k % n].get('titulo', cinta[k % n]['id'])[:48]}"
        elif cfg.get("momento") == "rafaga":
            que = f"RÁFAGA     {len(rafagas[ci])} a pantalla completa{' de ' + cfg['de'] if cfg.get('de') else ''}"
        else:
            que = {4: "por golpe", 8: "por corchea (doble tiempo)", 2: "medio tiempo", 1: "un paso"}.get(cfg.get("pasos"), f"{cfg.get('pasos')} pasos")
        print(f"  {ci}  {c['ini']:6.2f} s  {que}")


def _rueda_de_color(items: list[dict], cuantas: int, reservadas: set[str], rng) -> list[dict]:
    """Imágenes saturadas, una por generación, ordenadas alrededor del círculo de color:
    al final de la cinta el color vuelve a donde empezó (el loop también es cromático)."""
    gens = {_generacion(r) for r in reservadas}
    candidatas = [it for it in items if it["id"] not in reservadas and it["sat"] >= 0.25 and not it.get("marca") and 0.15 <= it["luz"] <= 0.75]
    rng.shuffle(candidatas)
    elegidas, usadas = [], set(gens)
    # Repartidas por el círculo: se toma la más cercana a cada tono objetivo.
    for k in range(cuantas):
        objetivo = 360 * k / max(1, cuantas)

        def distancia(it):
            d = abs(it["tono"] - objetivo) % 360
            return min(d, 360 - d)

        libres = [it for it in candidatas if _generacion(it["id"]) not in usadas]
        if not libres:
            salir("no alcanzan las imágenes para la cinta")
        it = min(libres, key=distancia)
        elegidas.append(it)
        usadas.add(_generacion(it["id"]))
    return elegidas
