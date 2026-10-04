"""Del catálogo y la partitura a un timeline.json: el montaje superpuesto.

La idea, en cuatro reglas:

1. Las entradas caen en la rejilla de la canción (golpes y sus mitades), más
   densas donde hay más energía y con preferencia por los primeros tiempos.
2. Cuántas capas conviven sigue a la energía: 1 en la calma, `capas_max` en el
   pico. La vida de cada imagen sale de ahí (capas ÷ ritmo de entradas).
3. Qué imagen va dónde: las oscuras a la calma y las claras a los picos
   (emparejamiento por rango), y dentro de cada sección se ordenan por tono para
   que lo que se superpone sea de la misma familia de color.
4. Cada imagen entra completa, en su proporción, sobre fondo oscuro; mezcla
   `screen` (doble exposición), bordes difuminados para que las capas se fundan
   en vez de apilarse como rectángulos, un zoom lento y una deriva leve.

Todo es determinista para una `semilla`: el mismo proyecto da el mismo montaje.
"""

from __future__ import annotations

import datetime as dt
import json
import math

import numpy as np

from . import catalogo, musica
from .rutas import Proyecto, salir

POR_DEFECTO = {
    "capas_max": 4,
    "subdivision": 2,
    "mezcla": "screen",
    "piso_densidad": 0.15,
    "curva": 1.5,
    "vida_golpes": [1.5, 16],
    "alto": [0.5, 0.95],
    "opacidad": [0.7, 1.0],
    "zoom": [0.02, 0.08],
    "deriva": 0.02,
    "borde": 0.12,
    "orden": "luz-y-tono",
    "semilla": 7,
    "margen_final_s": 1.5,
}


def _param(p: Proyecto) -> dict:
    return {**POR_DEFECTO, **p.cfg.get("montaje", {})}


def _rejilla(m: dict, sub: int):
    """Tiempos de la rejilla, golpe al que pertenece cada punto y su acento."""
    beats = np.array(m["beats"])
    fin = np.append(beats[1:], m["duracion"])
    primeros = set(range(m["fase_compas"], len(beats), 4))
    tiempos, golpe, acento = [], [], []
    for i, (a, b) in enumerate(zip(beats, fin)):
        for k in range(sub):
            tiempos.append(a + (b - a) * k / sub)
            golpe.append(i)
            acento.append(1.0 if (k == 0 and i in primeros) else 0.8 if k == 0 else 0.45)
    return np.array(tiempos), np.array(golpe), np.array(acento)


def _llegadas(m: dict, prm: dict, n: int):
    """Reparte n entradas sobre la rejilla. Devuelve índices de rejilla por entrada."""
    sub = prm["subdivision"]
    while True:
        t, golpe, acento = _rejilla(m, sub)
        e = np.array(m["energia"])[golpe]
        peso = (prm["piso_densidad"] + e ** prm["curva"]) * acento
        corte = m["duracion"] - prm["margen_final_s"] - 60 / m["bpm"] * prm["vida_golpes"][0]
        peso[t > corte] = 0
        usables = int((peso > 0).sum())
        max_por_punto = max(1, prm["capas_max"] // 2)
        if n <= usables * max_por_punto or sub >= 8:
            break
        sub *= 2  # no caben: se afina la rejilla
    if n > usables * max_por_punto:
        salir(f"{n} imágenes no caben en {usables} puntos de rejilla; la canción es corta para este archivo")
    return t, golpe, acento, repartir(peso, n, max_por_punto), sub


def repartir(peso: np.ndarray, n: int, max_por_punto) -> np.ndarray:
    """n entradas sobre los puntos de la rejilla, con densidad proporcional a `peso`.

    Como mucho `max_por_punto` entradas simultáneas (un número, o uno por
    punto). Primero se recorta el peso de los puntos que pedirían más que eso
    (y se reparte lo recortado entre los demás); lo que aún sobre por redondeo
    va al punto libre más cercano. Devuelve los índices ordenados en el tiempo.
    """
    tope_punto = np.broadcast_to(np.asarray(max_por_punto, dtype=float), peso.shape)
    usables = np.flatnonzero(peso > 0)
    if n > tope_punto[usables].sum():
        salir(f"{n} entradas no caben en {len(usables)} puntos de rejilla; la canción es corta para este archivo")
    w = peso.astype(float).copy()
    for _ in range(100):
        tope = tope_punto * 0.95 * w.sum() / n
        exceso = w > tope
        if not exceso.any():
            break
        w[exceso] = tope[exceso]

    acumulado = np.cumsum(w) / w.sum()
    idx = np.searchsorted(acumulado, (np.arange(n) + 0.5) / n)
    ocupado = np.zeros(len(peso), dtype=int)
    finales = []
    for j in idx:
        libres = usables[ocupado[usables] < tope_punto[usables]]
        k = int(libres[np.argmin(np.abs(libres - j))])
        ocupado[k] += 1
        finales.append(k)
    return np.sort(np.array(finales))


def _seccion_de(m: dict, golpe: int) -> int:
    for i, s in enumerate(m["secciones"]):
        if s["beat_ini"] <= golpe < s["beat_fin"]:
            return i
    return len(m["secciones"]) - 1


def _asignar(items: list[dict], energia_llegada: np.ndarray, seccion: np.ndarray, orden: str, rng) -> list[dict]:
    n = len(items)
    if orden == "aleatorio":
        return [items[i] for i in rng.permutation(n)]
    if orden != "luz-y-tono":
        salir(f"orden desconocido: {orden}")

    # Rango contra rango: la k-ésima entrada menos enérgica recibe la k-ésima imagen más oscura.
    por_energia = np.argsort(energia_llegada, kind="stable")
    por_luz = sorted(range(n), key=lambda i: items[i]["luz"])
    asignada = [None] * n
    for k, llegada in enumerate(por_energia):
        asignada[llegada] = items[por_luz[k]]

    # Dentro de cada sección: mismo conjunto de imágenes, reordenado por tono.
    # Los grises (poca saturación) no tienen tono que ordenar: van al borde de la sección.
    for s in np.unique(seccion):
        llegadas = np.where(seccion == s)[0]
        grupo = [asignada[i] for i in llegadas]
        clave = lambda it: it["tono"] + (0 if it["sat"] > 0.12 else 1000)  # noqa: E731
        grupo.sort(key=clave, reverse=bool(s % 2))
        for i, it in zip(llegadas, grupo):
            asignada[i] = it
    return asignada


def planificar(p: Proyecto) -> None:
    modo = p.cfg.get("montaje", {}).get("modo", "superposicion")
    if modo == "actos":
        from . import actos

        actos.planificar(p)
    elif modo == "superposicion":
        _superposicion(p)
    else:
        salir(f"modo de montaje desconocido: {modo} (hay: superposicion, actos)")


def _superposicion(p: Proyecto) -> None:
    prm = _param(p)
    out = {"ancho": 1920, "alto": 1080, "fps": 30, "fondo": "#08080a", **p.cfg.get("salida", {})}
    W, H, fps = out["ancho"], out["alto"], out["fps"]
    items = catalogo.cargar(p)
    m = musica.cargar(p)
    rng = np.random.default_rng(prm["semilla"])
    n = len(items)
    golpe_s = 60 / m["bpm"]

    t, golpe, acento, idx, sub = _llegadas(m, prm, n)
    energia = np.array(m["energia"])
    t_ini = t[idx]
    e_ini = energia[golpe[idx]]
    seccion = np.array([_seccion_de(m, g) for g in golpe[idx]])
    asignadas = _asignar(items, e_ini, seccion, prm["orden"], rng)

    # Ritmo local de entradas (por segundo) en una ventana de ±4 golpes.
    ventana = 4 * golpe_s
    ritmo = np.array([((t_ini > a - ventana) & (t_ini < a + ventana)).sum() / (2 * ventana) for a in t_ini])
    capas_obj = 1 + (prm["capas_max"] - 1) * e_ini
    vida_min, vida_max = (g * golpe_s for g in prm["vida_golpes"])
    vida = np.clip(capas_obj / np.maximum(ritmo, 1e-6), vida_min, vida_max)

    fin_cancion = m["duracion"] - 0.05
    capas = []
    activas: list[dict] = []
    for i in range(n):
        it = asignadas[i]
        a = float(t_ini[i])
        b = min(a + float(vida[i]), fin_cancion)
        b = float(t[min(np.searchsorted(t, b), len(t) - 1)]) if b < t[-1] else b  # el final también cae en rejilla
        e = float(e_ini[i])

        # Tope de capas: si ya hay `capas_max`, la más vieja se despide al entrar esta.
        activas = [c for c in activas if c["_fin"] > a]
        while len(activas) >= prm["capas_max"]:
            vieja = min(activas, key=lambda c: c["_ini"])
            vieja["_fin"] = max(a + golpe_s / 4, vieja["_ini"] + golpe_s / 2)
            activas.remove(vieja)

        # Tamaño: grande en la calma, más chica cuando hay muchas capas.
        a_min, a_max = prm["alto"]
        alto = np.clip(a_max - (a_max - a_min) * e + rng.uniform(-0.05, 0.05), a_min, a_max) * H
        ancho = alto * it["ratio"]
        if ancho > 0.96 * W:
            alto *= 0.96 * W / ancho
            ancho = 0.96 * W
        dispersion = 0.25 + 0.75 * e
        x = W / 2 + rng.uniform(-1, 1) * (W - ancho) / 2 * dispersion
        y = H / 2 + rng.uniform(-1, 1) * (H - alto) / 2 * dispersion

        z = rng.uniform(*prm["zoom"])
        zoom = [1.0, 1.0 + z] if rng.random() < 0.6 else [1.0 + z, 1.0]
        ang = rng.uniform(0, 2 * math.pi)
        deriva = [prm["deriva"] * W * math.cos(ang), prm["deriva"] * W * math.sin(ang)]
        o_min, o_max = prm["opacidad"]
        opacidad = o_max if acento[idx[i]] == 1.0 else rng.uniform(o_min, o_max)

        capa = {
            "id": it["id"],
            "img": it["img"],
            "_ini": a,
            "_fin": b,
            "_e": e,
            "x": round(x, 1),
            "y": round(y, 1),
            "ancho": round(ancho, 1),
            "alto": round(alto, 1),
            "opacidad": round(opacidad, 3),
            "zoom": [round(v, 4) for v in zoom],
            "deriva": [round(v, 1) for v in deriva],
            "mezcla": prm["mezcla"],
            "borde": prm["borde"],
            "seccion": int(seccion[i]),
        }
        capas.append(capa)
        activas.append(capa)

    # A cuadros, con fundidos que dependen de la energía y nunca se comen la vida entera.
    for c in capas:
        ini = round(c["_ini"] * fps)
        fin = max(ini + 2, round(c["_fin"] * fps))
        vida_c = fin - ini
        e = c.pop("_e")
        entrada = round(fps * golpe_s * (0.6 - 0.5 * e))
        salida = round(fps * golpe_s * (1.0 - 0.5 * e))
        c["ini"], c["fin"] = ini, fin
        c["entrada"] = int(np.clip(entrada, 1, max(1, vida_c * 0.35)))
        c["salida"] = int(np.clip(salida, 1, max(1, vida_c * 0.45)))
        del c["_ini"], c["_fin"]

    duracion = math.ceil(m["duracion"] * fps)
    timeline = {
        "version": 1,
        "proyecto": p.nombre,
        **{k: out[k] for k in ("ancho", "alto", "fps", "fondo")},
        "duracion": duracion,
        "audio": {"src": m["archivo"], "desde": 0},
        "meta": {
            "generado": dt.datetime.now().isoformat(timespec="seconds"),
            "bpm": m["bpm"],
            "imagenes": n,
            "subdivision": sub,
            "parametros": prm,
        },
        "capas": capas,
    }
    escribir(p.timeline, timeline)

    # Resumen legible: capas simultáneas (sin contar las que se están yendo) y vida típica por sección.
    simultaneas = np.zeros(duracion + 1, dtype=int)
    for c in capas:
        simultaneas[c["ini"] : c["fin"] - c["salida"]] += 1
    vidas = np.array([(c["fin"] - c["ini"]) / fps for c in capas])
    print(f"{n} capas sobre {m['duracion']:.0f} s a {m['bpm']} BPM (rejilla 1/{sub}) → {p.timeline}")
    print(f"  ritmo medio: {n / m['duracion']:.1f} imágenes nuevas por segundo")
    print(f"  vida por imagen: mediana {np.median(vidas):.2f} s (de {vidas.min():.2f} a {vidas.max():.2f} s)")
    print(f"  capas plenas a la vez: mediana {int(np.median(simultaneas[:duracion]))}, máximo {simultaneas.max()}")
    for i, s in enumerate(m["secciones"]):
        sel = [c for c in capas if c["seccion"] == i]
        tramo = simultaneas[round(s["ini"] * fps) : round(s["fin"] * fps)]
        print(
            f"  S{i + 1} {s['ini']:6.1f}–{s['fin']:6.1f} s  energía {s['energia']:.2f}  "
            f"{len(sel):4d} imágenes  capas ~{tramo.mean() if len(tramo) else 0:.1f}"
        )


LISTAS_POR_LINEA = ("capas", "piezas", "ecos", "camara", "luz", "actos")


def escribir(ruta, timeline: dict) -> None:
    """Cabecera legible y un elemento por línea en las listas largas: el diff de git dice qué cambió."""

    def compacto(x) -> str:
        return json.dumps(x, ensure_ascii=False, separators=(",", ":"))

    def objeto(d: dict, sangria: str) -> str:
        filas = [f'{sangria} {json.dumps(k)}: {valor(k, v, sangria + " ")}' for k, v in d.items()]
        return "{\n" + ",\n".join(filas) + f"\n{sangria}}}"

    def valor(clave: str, v, sangria: str) -> str:
        if isinstance(v, list) and clave in LISTAS_POR_LINEA:
            if not v:
                return "[]"
            return "[\n" + ",\n".join(f"{sangria} {compacto(x)}" for x in v) + f"\n{sangria}]"
        if isinstance(v, dict) and any(k in LISTAS_POR_LINEA for k in v):
            return objeto(v, sangria)
        return compacto(v)

    ruta.write_text(objeto(timeline, "") + "\n", encoding="utf-8")
