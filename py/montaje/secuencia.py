"""Secuencia: las imágenes una tras otra, a pantalla completa, al pulso.

Para una serie que comparte forma —las variaciones de una misma imagen hechas en
el editor de Midjourney, por ejemplo—. No hay collage: cada imagen reemplaza a la
anterior ocupando todo el cuadro, y el ritmo de cortes sigue a la canción. Como
todas comparten la composición, en los cortes rápidos la imagen parece
transformarse: animación por variaciones.

- **Orden por parecido.** Un recorrido que va siempre a la imagen más parecida
  (forma y color, comparadas en miniaturas de 16×16) entre las que quedan, y se
  pule después; así el corte rápido se lee como metamorfosis y no como saltos.
- **La original vuelve.** Abre el video, cae en el «uno» de los compases que se
  pidan (el inicio de cada frase) y lo cierra.
- **Todas entran.** La densidad de cortes por compás sigue a la energía de la
  canción y se escala para que se usen todas las imágenes, una vez cada una. Los
  cortes caen en la rejilla del golpe (1 a 4 por golpe: negra, corchea, tresillo,
  semicorchea); dentro de un compás, los golpes del final llevan más cortes.
- **En la calma, fundido encadenado; con ritmo, corte seco.**

proyecto.json:

    "montaje": {
      "modo": "secuencia",
      "original": "midjourney-editor-1792552364848",  # id o nombre de archivo
      "original_en": [0, 4, 12, 20],                   # compases donde vuelve
      "original_golpes": 1,                            # cuánto dura cada vuelta
      "cierre_golpes": 4,                              # la original al final
      "umbral_calma": 0.3,                             # bajo esta energía: un corte por compás, con fundido
      "fundido_calma": 0.4,                            # segundos del fundido encadenado
      "contraste": 2.0                                 # cuánto más rápido va lo fuerte que lo suave
    }
"""

from __future__ import annotations

import datetime as dt
import math

import numpy as np

from . import catalogo, musica, transiciones
from .planificar import audio_de, escribir
from .rutas import Proyecto, salir

POR_DEFECTO = {
    "original": None,
    "original_en": [0],
    "original_golpes": 1,
    "cierre_golpes": 4,
    "umbral_calma": 0.3,
    "fundido_calma": 0.4,
    "contraste": 2.0,
    "max_por_golpe": 4,
    # Cómo entra cada imagen sobre la anterior (2026-11-23): sin esto (o con "corte"), corte seco (y fundido en la calma). Una de
    # transiciones.py (cortina, iris, luz, doble, pixeles, cinta…) o "ronda"; dura `transicion_golpes` golpes (nunca
    # más de la mitad de lo que se ve la imagen).
    "transicion": None,
    "transicion_golpes": 1.0,
    "transicion_dir": "alterna",
}


# ── Orden por parecido ─────────────────────────────────────────────────────

def _rasgos(p: Proyecto, items: list[dict]) -> np.ndarray:
    """Forma (luz normalizada) y color de cada imagen, en 16×16, como un vector."""
    from PIL import Image

    filas = []
    for it in items:
        ruta = p.medios / it["mini"]
        if not ruta.exists():
            ruta = p.medios / it["img"]
        with Image.open(ruta) as im:
            rgb = np.asarray(im.convert("RGB").resize((16, 16), Image.Resampling.BOX), dtype=float) / 255
        luz = rgb @ np.array([0.2126, 0.7152, 0.0722])
        forma = (luz - luz.mean()) / (luz.std() + 1e-6)
        filas.append(np.concatenate([forma.ravel() * 0.6, rgb.ravel() * 2.0]))
    return np.array(filas)


def _recorrido(r: np.ndarray, inicio: int) -> list[int]:
    """Vecino más cercano desde `inicio` y luego 2-opt: un camino corto por parecido."""
    n = len(r)
    d = np.sqrt(((r[:, None, :] - r[None, :, :]) ** 2).sum(-1))
    camino = [inicio]
    libre = np.ones(n, bool)
    libre[inicio] = False
    for _ in range(n - 1):
        dist = np.where(libre, d[camino[-1]], np.inf)
        k = int(np.argmin(dist))
        camino.append(k)
        libre[k] = False
    camino = np.array(camino)
    # 2-opt sobre el camino abierto: invertir tramos mientras acorte.
    for _ in range(30):
        mejoro = False
        for i in range(1, n - 2):
            a, b = camino[i - 1], camino[i]
            c, e = camino[i + 1 :], np.append(camino[i + 2 :], -1)
            actual = d[a, b] + np.where(e >= 0, d[c, e.clip(0)], 0)
            nuevo = d[a, c] + np.where(e >= 0, d[b, e.clip(0)], 0)
            j = int(np.argmax(actual - nuevo))
            if actual[j] - nuevo[j] > 1e-9:
                camino[i : i + 2 + j] = camino[i : i + 2 + j][::-1]
                mejoro = True
        if not mejoro:
            break
    return [int(k) for k in camino]


# ── Ritmo ──────────────────────────────────────────────────────────────────

def _compases(m: dict) -> list[dict]:
    """Cada compás con sus golpes (tiempos) y su energía media. El primero arranca en 0."""
    beats = np.array(m["beats"])
    energia = np.array(m["energia"])
    inicios = list(m["primeros_tiempos"])
    if not inicios or inicios[0] > 0.3:
        inicios = [0.0] + inicios
    inicios[0] = 0.0
    limites = inicios + [m["duracion"]]
    salida = []
    for i in range(len(inicios)):
        t0, t1 = limites[i], limites[i + 1]
        sel = (beats >= t0 - 0.03) & (beats < t1 - 0.03)
        golpes = [t0] + [float(b) for b in beats[sel] if b > t0 + 0.08]
        salida.append({"ini": t0, "fin": t1, "golpes": golpes, "e": float(energia[sel].mean()) if sel.any() else 0.0})
    return salida


def _repartir(pesos: np.ndarray, total: int, minimo: np.ndarray, maximo: np.ndarray) -> np.ndarray:
    """Cortes por compás proporcionales a `pesos`, entre `minimo` y `maximo`, que sumen `total`."""
    if total < minimo.sum() or total > maximo.sum():
        return None
    lo, hi = 0.0, 1e6
    for _ in range(80):
        esc = (lo + hi) / 2
        k = np.clip(np.floor(pesos * esc), minimo, maximo)
        if k.sum() > total:
            hi = esc
        else:
            lo = esc
    k = np.clip(np.floor(pesos * lo), minimo, maximo).astype(int)
    resto = pesos * lo - np.floor(pesos * lo)
    for i in np.argsort(-resto):
        if k.sum() >= total:
            break
        if k[i] < maximo[i]:
            k[i] += 1
    while k.sum() < total:  # por si el redondeo dejó corto
        i = int(np.argmax(np.where(k < maximo, pesos, -1)))
        k[i] += 1
    return k


def _cortes_del_compas(golpes: list[float], fin: float, k: int, tope: int) -> list[float]:
    """`k` cortes dentro de un compás: en la rejilla de cada golpe, con más cortes hacia el final."""
    if k <= 0:
        return []
    n = len(golpes)
    if k < n:
        paso = n / k
        return [golpes[int(round(j * paso))] for j in range(k)]
    base, extra = divmod(k, n)
    por_golpe = [min(tope, base + (1 if j >= n - extra else 0)) for j in range(n)]
    cortes = []
    limites = golpes + [fin]
    for j, s in enumerate(por_golpe):
        a, b = limites[j], limites[j + 1]
        cortes += [a + (b - a) * q / s for q in range(s)]
    return cortes


# ── Plan ───────────────────────────────────────────────────────────────────

def _cubrir(it: dict, W: int, H: int) -> tuple[float, float]:
    """Tamaño para cubrir el cuadro entero (se recorta lo que sobre)."""
    s = max(W / it["w"], H / it["h"])
    return round(it["w"] * s, 1), round(it["h"] * s, 1)


def planificar(p: Proyecto) -> None:
    prm = {**POR_DEFECTO, **p.cfg.get("montaje", {})}
    out = {"ancho": 1080, "alto": 1080, "fps": 30, "fondo": "#000000", **p.cfg.get("salida", {})}
    W, H, fps = out["ancho"], out["alto"], out["fps"]
    items = catalogo.cargar(p)
    m = musica.cargar(p)

    pedida = prm["original"]
    original = next((it for it in items if pedida and (it["id"] == pedida or it["img"].rsplit("/", 1)[-1].rsplit(".", 1)[0] == pedida)), None)
    if pedida and not original:
        salir(f"no encuentro la original «{pedida}» en el catálogo")
    variaciones = [it for it in items if it is not original]

    # El orden: desde la variación más parecida a la original, siempre a la siguiente más parecida.
    rasgos = _rasgos(p, variaciones + ([original] if original else []))
    r_var = rasgos[: len(variaciones)]
    inicio = int(np.argmin(((r_var - rasgos[-1]) ** 2).sum(1))) if original else 0
    orden = [variaciones[k] for k in _recorrido(r_var, inicio)]

    # Los compases, cuáles llevan la original, y el cierre.
    compases = _compases(m)
    n_c = len(compases)
    con_original = {c for c in prm["original_en"] if 0 <= c < n_c} if original else set()
    calma = np.array([c["e"] < prm["umbral_calma"] for c in compases])

    # Golpes libres por compás (los que no ocupa la original) y el cierre al final.
    libres = []
    for i, c in enumerate(compases):
        golpes = c["golpes"]
        if i in con_original:
            # En la calma la original se queda el compás entero; con ritmo, sólo sus golpes.
            golpes = [] if calma[i] else golpes[prm["original_golpes"] :]
        libres.append(golpes)
    cierre_t = None
    if original and prm["cierre_golpes"] > 0:
        todos = [g for c in compases for g in c["golpes"]]
        cierre_t = todos[-prm["cierre_golpes"]] if len(todos) > prm["cierre_golpes"] else todos[0]
        for i, c in enumerate(compases):
            libres[i] = [g for g in libres[i] if g < cierre_t - 1e-6]

    # Cuántos cortes por compás: siguen a la energía (con contraste) y suman todas las variaciones.
    pesos = np.array([max(c["e"], 0.02) ** prm["contraste"] for c in compases])
    minimo = np.array([1 if libres[i] else 0 for i in range(n_c)])
    maximo = np.array([1 if calma[i] and libres[i] else len(libres[i]) * prm["max_por_golpe"] for i in range(n_c)])
    k = _repartir(pesos, len(orden), minimo, maximo)
    if k is None:
        salir(f"no entran {len(orden)} imágenes en {n_c} compases con un máximo de {prm['max_por_golpe']} cortes por golpe "
              f"(caben entre {minimo.sum()} y {maximo.sum()}): sube max_por_golpe o elige un tramo más largo")

    # Los cortes en el tiempo.
    eventos = []  # (t, item, es_original, fundido)
    for i, c in enumerate(compases):
        if i in con_original:
            eventos.append((c["ini"] if i else 0.0, original, True, False))
        fin_libre = cierre_t if cierre_t is not None and c["fin"] > cierre_t else c["fin"]
        for t in _cortes_del_compas(libres[i], fin_libre, int(k[i]), prm["max_por_golpe"]):
            eventos.append((t, None, False, bool(calma[i])))
    if cierre_t is not None:
        eventos.append((cierre_t, original, True, False))
    eventos.sort(key=lambda e: e[0])
    cola = iter(orden)
    eventos = [(t, it if it is not None else next(cola), es_o, f) for t, it, es_o, f in eventos]

    # Las capas: cada una hasta el corte siguiente (o hasta que la siguiente termine de aparecer).
    duracion = math.ceil(m["duracion"] * fps)
    fundido = max(1, round(prm["fundido_calma"] * fps))
    capas = []
    inis = [round(t * fps) for t, *_ in eventos]
    # Cuánto tarda en aparecer cada una y, si hay, con qué transición.
    entradas = [fundido if f and j > 0 else 0 for j, (_, _, _, f) in enumerate(eventos)]
    trs: list = [None] * len(eventos)
    if prm["transicion"] and prm["transicion"] != "corte":   # «corte» (el formulario del panel) = sin transición
        golpe = max(1, round(60 / max(m.get("bpm") or 120, 1) * fps * prm["transicion_golpes"]))
        for j in range(1, len(eventos)):
            visible = (inis[j + 1] if j + 1 < len(eventos) else duracion) - inis[j]
            trs[j] = transiciones.elegir(prm["transicion"], prm["transicion_dir"], j - 1)
            if trs[j]:
                entradas[j] = max(1, min(golpe, visible // 2))
    for j, (t, it, es_o, f) in enumerate(eventos):
        ini = inis[j]
        siguiente = inis[j + 1] if j + 1 < len(eventos) else duracion
        entra = entradas[j]
        entra_sig = entradas[j + 1] if j + 1 < len(eventos) else 0
        fin = min(duracion, siguiente + entra_sig)
        para_irse = transiciones.para_la_que_se_va(trs[j + 1], entra_sig) if j + 1 < len(eventos) else {}
        ancho, alto = _cubrir(it, W, H)
        ultima = j == len(eventos) - 1
        capas.append({
            "id": f"{it['id']}#{j}",
            "img": it["img"],
            "ini": ini,
            "fin": fin,
            "entrada": entra,
            "salida": para_irse.get("salida", 0),
            **({"transicion": {"tipo": trs[j][0], "dir": trs[j][1]}} if trs[j] else {}),
            **({"empujada": para_irse["empujada"]} if "empujada" in para_irse else {}),
            "x": W / 2,
            "y": H / 2,
            "ancho": ancho,
            "alto": alto,
            "opacidad": 1,
            # La original del cierre respira un poco mientras la canción se apaga.
            "zoom": [1, 1.04] if ultima and es_o else [1, 1],
            "deriva": [0, 0],
            "mezcla": "normal",
            "borde": 0,
            "seccion": next(i for i, c in enumerate(compases) if c["ini"] <= t < c["fin"] or i == n_c - 1),
        })

    timeline = {
        "version": 3,
        "modo": "secuencia",
        "proyecto": p.nombre,
        **{k_: out[k_] for k_ in ("ancho", "alto", "fps", "fondo")},
        "duracion": duracion,
        "audio": audio_de(p, m),
        "meta": {
            "generado": dt.datetime.now().isoformat(timespec="seconds"),
            "bpm": m["bpm"],
            "imagenes": len(orden) + (1 if original else 0),
            "parametros": prm,
        },
        "capas": capas,
    }
    escribir(p.timeline, timeline)

    # Resumen por compás.
    vidas = np.diff(inis + [duracion])
    print(f"{len(orden)} variaciones + la original ({len(con_original) + (1 if cierre_t is not None else 0)} veces) en {len(capas)} cortes, "
          f"{m['duracion']:.1f} s a {m['bpm']:.1f} BPM → {p.timeline}")
    print(f"la imagen más breve dura {vidas.min()} cuadros ({vidas.min() / fps:.2f} s)")
    for i, c in enumerate(compases):
        marca = "  ORIGINAL" if i in con_original else ""
        ritmo = "fundido" if calma[i] else f"{k[i]:>2} cortes"
        print(f"  {i:>3} {c['ini']:7.2f} s  energía {c['e']:.2f}  {ritmo}{marca}")
    if cierre_t is not None:
        print(f"  cierre {cierre_t:7.2f} s  la original hasta el final")
