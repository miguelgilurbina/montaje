"""Montaje en actos: de una imagen a la vez al caos, construyendo una pared.

La forma, contada como la pidió Miguel:

- Se abre con las de mayor formato (panorámicas), una a una. Cada imagen es
  protagonista un rato y luego vuela a su lugar en una pared que se va armando
  al fondo: lo que pasó queda en pantalla.
- A medida que avanza, el caos sube: entran más rápido, conviven más
  protagonistas, se mezclan los formatos, la pared crece y la cámara se aleja
  hasta que la pared desborda el cuadro (la composición «infinita»).
- Montaje sobre montaje: con el caos alto, la pared misma se vuelve materia;
  copias de ella (ecos) a otras escalas, giradas y con desfase de tiempo, en
  doble exposición sobre sí misma, con las protagonistas encima.
- Coda: ya no entra nada, los ecos se apagan y la cámara se aleja hasta que se
  ve el archivo entero.

El caos es una sola curva, `caos(t)` entre 0 y 1: crece con el avance del video
y la modula la energía de la canción. Todo lo demás (ritmo de entradas, capas a
la vez, tamaño, mezcla, ecos, cámara) se lee de esa curva.
"""

from __future__ import annotations

import datetime as dt
import math

import numpy as np

from . import catalogo, musica
from .planificar import _rejilla, audio_de, escribir, repartir
from .rutas import Proyecto

POR_DEFECTO = {
    "subdivision": 2,
    "semilla": 7,
    "capas_max": 5,  # protagonistas a la vez con caos 1
    "curva_caos": 1.3,  # cómo crece el caos con el avance (exponente)
    "peso_energia": 0.25,  # cuánto modula la energía al caos
    "densidad_calma": 0.02,  # peso de entrada con caos 0, relativo al de caos 1
    "curva_densidad": 2.0,
    "coda": 0.07,  # fracción final sin entradas
    "vida_golpes": [1, 16],  # vida de una protagonista antes de volar: mínimo, máximo en calma
    "alto": [0.92, 0.4],  # alto de la protagonista (fracción del cuadro): en calma → en caos
    "vuelo_golpes": [2.0, 0.5],  # duración del vuelo a la pared: en calma → en caos
    "borde": 0.12,
    "borde_pared": 0.06,
    "fila": 100,  # alto de una fila de la pared, en unidades de pared
    "hueco": 4,
    "encuadre": [0.75, 1.35, 0.92],  # cuántos cuadros ocupa la pared: al inicio, en el caos, al final
    "luz_pared": [0.95, 0.55],  # opacidad de la pared: en calma → en caos
    "ecos": [0.45, 0.65, 0.85],  # caos a partir del cual hay 1, 2 y 3 ecos
    "golpe_camara": 0.035,  # empujón de zoom en cada primer tiempo, con caos 1
    "umbral_silencio": 0.35,  # una sección con menos energía que esto es un respiro
    "compases_calma": True,  # en el acto I las entradas caen parejas en primeros tiempos (montaje métrico)
    "entrada_primera_golpes": 6,  # la primera imagen aparece despacio, sobre la intro
}

FAMILIA_RANGO = {
    "panoramica": 0,
    "horizontal-3-2": 1,
    "horizontal-4-3": 2,
    "cuadrada": 3,
    "vertical-4-5": 4,
    "vertical-9-16": 5,
}

ACTOS = [("I", 0.0), ("II", 0.2), ("III", 0.45), ("IV", 0.75)]


def _lerp(a: float, b: float, u: float) -> float:
    return a + (b - a) * u


def _suave(u: float) -> float:
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def planificar(p: Proyecto) -> None:
    prm = {**POR_DEFECTO, **p.cfg.get("montaje", {})}
    out = {"ancho": 1920, "alto": 1080, "fps": 30, "fondo": "#08080a", **p.cfg.get("salida", {})}
    W, H, fps = out["ancho"], out["alto"], out["fps"]
    items = catalogo.cargar(p)
    m = musica.cargar(p)
    rng = np.random.default_rng(prm["semilla"])
    n = len(items)
    D = m["duracion"]
    golpe_s = 60 / m["bpm"]
    beats = np.array(m["beats"])
    energia_beats = np.array(m["energia"])
    primeros = np.array(m["primeros_tiempos"])

    def energia(t):
        return np.interp(t, beats, energia_beats)

    t_coda = D * (1 - prm["coda"])

    def avance(t):
        return np.clip(np.asarray(t) / t_coda, 0, 1)

    def caos_base(t):
        return avance(t) ** prm["curva_caos"]

    # Los respiros de la canción son sus secciones bajas (la intro sin batería, un
    # corte): se leen por sección y no golpe a golpe, porque la energía suavizada
    # desdibuja un corte de pocos segundos.
    respiros = [(s["ini"], s["fin"]) for s in m["secciones"] if s["energia"] < prm["umbral_silencio"]]

    def silencio(t):
        """1 dentro de un respiro de la canción, 0 donde suena; rampa de un golpe en los bordes."""
        t = np.asarray(t, dtype=float)
        valor = np.zeros_like(t)
        for a, b in respiros:
            valor = np.maximum(valor, np.clip(np.minimum(t - a, b - t) / golpe_s + 0.5, 0, 1))
        return valor

    def caos(t):
        pe = prm["peso_energia"]
        return np.clip(caos_base(t) * ((1 - pe) + pe * energia(t)) * (1 - silencio(t)), 0, 1)

    # ── 1. Cuándo entra cada imagen ─────────────────────────────────────────
    # Rejilla en semicorcheas, pero el caos decide cuáles se usan: en la calma sólo
    # los golpes; las corcheas se abren con caos 0.3 y las semicorcheas con 0.6.
    # Y cuántas entradas pueden coincidir en un mismo punto: 1 en la calma, 4 en el caos.
    vuelo_max = prm["vuelo_golpes"][0] * golpe_s
    t_ultima = t_coda - vuelo_max - golpe_s
    sub = 4
    t, golpe, acento = _rejilla(m, sub)
    fraccion = np.tile(np.arange(sub), len(beats))[: len(t)]
    c = caos(t)
    e = energia_beats[golpe]
    abierta = (fraccion == 0) | ((fraccion == 2) & (c >= 0.3)) | (c >= 0.6)
    peso = (prm["densidad_calma"] + c ** prm["curva_densidad"]) * (0.6 + 0.4 * e) * np.where(fraccion == 0, acento, 0.35)
    peso *= 1 - 0.97 * silencio(t)  # en el silencio no entra nada: la pared respira
    peso[(t > t_ultima) | ~abierta] = 0
    tope = 1 + np.floor(3 * c)
    idx = repartir(peso, n, tope)
    # La primera imagen abre el video en el primer primer-tiempo.
    primer = int(np.argmax(acento == 1.0))
    if idx[0] > primer:
        idx[0] = primer
    idx = np.sort(idx)
    if prm["compases_calma"]:
        # Acto I métrico: las entradas de la calma se reparten parejas entre los primeros
        # tiempos que suenan (la primera queda sobre la intro, sola).
        tt = np.linspace(0, t_coda, 2000)
        fin_i = float(tt[np.argmax(caos_base(tt) >= ACTOS[1][1])])
        en_i = np.flatnonzero(t[idx] < fin_i)
        compases = [primer] + [j for j in np.flatnonzero(acento == 1.0) if primer < t[j] < fin_i and silencio(t[j]) < 0.5]
        if 1 < len(en_i) <= len(compases):
            elegidos = np.unique(np.round(np.linspace(0, len(compases) - 1, len(en_i))).astype(int))
            if len(elegidos) == len(en_i):
                idx[en_i] = np.array(compases)[elegidos]
    idx = _anclar_a_eventos(idx, t, acento, m, golpe_s, t_ultima)
    t_ini = t[idx]
    c_ini = caos(t_ini)
    e_ini = energia(t_ini)

    # ── 2. Qué imagen entra: primero el mayor formato, cada vez más mezclado ─
    secuencia = _elegir(items, c_ini, e_ini, rng)

    # ── 3. Protagonistas: cuánto viven y cuándo vuelan a la pared ───────────
    ventana = 4 * golpe_s
    ritmo = np.array([((t_ini > a - ventana) & (t_ini < a + ventana)).sum() / (2 * ventana) for a in t_ini])
    prot = []
    activas: list[dict] = []
    for i in range(n):
        a, ci, ei = float(t_ini[i]), float(c_ini[i]), float(e_ini[i])
        tope = 1 + round(ci * (prm["capas_max"] - 1))
        vida_max = _lerp(prm["vida_golpes"][1], 3, ci) * golpe_s
        vida = np.clip(tope * (0.5 + 0.5 * ei) / max(ritmo[i], 1e-6), prm["vida_golpes"][0] * golpe_s, vida_max)
        if tope == 1:
            # Una a una: la protagonista se queda hasta que entra la siguiente (relevo).
            vida = 32 * golpe_s
        vuelo = _lerp(*prm["vuelo_golpes"], ci) * golpe_s
        entrada = _lerp(1.0, 0.25, ci) * golpe_s
        x = {"i": i, "ini": a, "c": ci, "e": ei, "tope": tope, "vuelo": vuelo, "entrada": entrada, "desde": a + vida}

        activas = [q for q in activas if q["desde"] > a]
        while len(activas) >= tope:
            vieja = min(activas, key=lambda q: q["ini"])
            vieja["desde"] = max(a, vieja["ini"] + vieja["entrada"] + golpe_s / 2)
            activas.remove(vieja)
        prot.append(x)
        activas.append(x)
    limite = D - 0.5
    for x in prot:
        x["desde"] = min(x["desde"], limite - x["vuelo"])
        x["llega"] = x["desde"] + x["vuelo"]

    # ── 4. La pared: cada pieza en el orden en que llega ────────────────────
    orden_llegada = sorted(range(n), key=lambda k: prot[k]["llega"])
    pared = _Pared(prm["fila"], prm["hueco"], W / H, rng)
    piezas = []
    pieza_de = {}
    for k in orden_llegada:
        it = secuencia[k]
        cx, cy, w, h = pared.poner(it["ratio"])
        pieza_de[k] = len(piezas)
        piezas.append(
            {
                "id": it["id"],
                "img": it["img"],
                "mini": it["mini"],
                "x": round(cx, 1),
                "y": round(cy, 1),
                "ancho": round(w, 1),
                "alto": round(h, 1),
                "llega": round(prot[k]["llega"] * fps),
            }
        )

    # ── 5. Cámara sobre la pared ─────────────────────────────────────────────
    duracion = math.ceil(D * fps)
    camara, luz = _camara(prm, prot, piezas, pieza_de, caos, silencio, primeros, t_coda, duracion, fps, W, H)

    # ── 6. Ecos: montaje sobre montaje (que callan cuando calla la canción) ──
    silencios = _intervalos_silencio(silencio, D)
    ecos = _ecos(prm, caos, primeros, t_coda, golpe_s, fps, W, H, rng, silencios)

    # ── 7. Protagonistas en cuadros ─────────────────────────────────────────
    capas = []
    for k, x in enumerate(prot):
        it = secuencia[k]
        ci = x["c"]
        alto = np.clip(_lerp(*prm["alto"], ci) + rng.uniform(-0.05, 0.05), 0.2, 0.95) * H
        ancho = alto * it["ratio"]
        if ancho > 0.96 * W:
            alto *= 0.96 * W / ancho
            ancho = 0.96 * W
        cx = W / 2 + rng.uniform(-1, 1) * (W - ancho) / 2 * ci
        cy = H / 2 + rng.uniform(-1, 1) * (H - alto) / 2 * ci
        ini = round(x["ini"] * fps)
        desde = max(ini + 1, round(x["desde"] * fps))
        fin = max(desde + 1, round(x["llega"] * fps))
        if k == 0:
            x["entrada"] = prm["entrada_primera_golpes"] * golpe_s
        capas.append(
            {
                "id": it["id"],
                "img": it["img"],
                "ini": ini,
                "fin": fin,
                "entrada": max(1, min(round(x["entrada"] * fps), desde - ini)),
                "salida": 0,
                "x": round(cx, 1),
                "y": round(cy, 1),
                "ancho": round(ancho, 1),
                "alto": round(alto, 1),
                # En doble exposición lo claro quema: las protagonistas bajan con el caos y
                # las de fondo claro bajan más, para que el pico no sea un borrón blanco.
                # Y cuantas más protagonistas conviven, menos aporta cada una.
                "opacidad": 1.0
                if ci < 0.3
                else round(rng.uniform(0.55, 0.85) * (0.6 if it["luz"] > 0.5 else 1.0) / (1 + 0.25 * (x["tope"] - 1)), 3),
                "zoom": [1.0, round(1 + rng.uniform(0.02, 0.06), 4)],
                "deriva": [round(rng.uniform(-1, 1) * 0.01 * W, 1), round(rng.uniform(-1, 1) * 0.01 * H, 1)],
                "mezcla": "normal" if ci < 0.3 else "screen",
                "borde": prm["borde"],
                "seccion": 0,
                "vuelo": {"desde": desde, "pieza": pieza_de[k]},
            }
        )
        piezas[pieza_de[k]]["llega"] = fin  # la pieza aparece en la pared justo cuando aterriza

    # Actos (para leer el resumen y ubicarse en el Studio).
    cortes = []
    tt = np.linspace(0, t_coda, 2000)
    cb = caos_base(tt)
    for nombre, umbral in ACTOS:
        cortes.append((nombre, float(tt[np.argmax(cb >= umbral)]) if (cb >= umbral).any() else t_coda))
    actos = []
    for j, (nombre, ini_s) in enumerate(cortes):
        fin_s = cortes[j + 1][1] if j + 1 < len(cortes) else t_coda
        actos.append({"nombre": nombre, "ini": round(ini_s * fps), "fin": round(fin_s * fps)})
    actos.append({"nombre": "coda", "ini": round(t_coda * fps), "fin": duracion})

    timeline = {
        "version": 2,
        "modo": "actos",
        "proyecto": p.nombre,
        **{k: out[k] for k in ("ancho", "alto", "fps", "fondo")},
        "duracion": duracion,
        "audio": audio_de(p, m),
        "meta": {
            "generado": dt.datetime.now().isoformat(timespec="seconds"),
            "bpm": m["bpm"],
            "imagenes": n,
            "subdivision": sub,
            "parametros": prm,
        },
        "actos": actos,
        "mural": {"borde": prm["borde_pared"], "luz": luz, "piezas": piezas},
        "camara": camara,
        "ecos": ecos,
        "capas": capas,
    }
    escribir(p.timeline, timeline)
    _resumen(p, m, actos, capas, ecos, piezas, fps, secuencia, prot)


def _anclar_a_eventos(idx: np.ndarray, t: np.ndarray, acento: np.ndarray, m: dict, golpe_s: float, t_ultima: float) -> np.ndarray:
    """Los momentos de la canción traen imagen nueva: cuando entra la batería y
    cuando empieza cada sección. Si ninguna entrada cae a un golpe de ese momento,
    la más cercana se corre a su primer tiempo."""
    entra_bateria = m["beats"][m.get("golpes_intro", 0)]
    # Las secciones de la intro no cuentan: la intro es de la primera imagen, sola.
    eventos = [entra_bateria] + [s["ini"] for s in m["secciones"][1:] if s["ini"] >= entra_bateria]
    idx = np.sort(idx.copy())
    ancladas: set[int] = {0}
    for T in eventos:
        if T > t_ultima:
            continue
        candidatos = np.flatnonzero((acento == 1.0) & (t >= T - golpe_s / 2))
        if not len(candidatos):
            continue
        j = int(candidatos[0])
        if np.any(np.abs(t[idx] - t[j]) <= golpe_s):
            continue
        libres = [k for k in range(len(idx)) if k not in ancladas]
        k = min(libres, key=lambda q: abs(t[idx[q]] - t[j]))
        idx[k] = j
        ancladas.add(k)
        orden = np.argsort(idx, kind="stable")
        idx = idx[orden]
        posicion = {int(v): i for i, v in enumerate(orden)}
        ancladas = {posicion[a] for a in ancladas}
    return idx


def _intervalos_silencio(silencio, D: float) -> list[tuple[float, float]]:
    tt = np.arange(0, D, 0.1)
    callado = silencio(tt) > 0.5
    tramos, ini = [], None
    for x, c in zip(tt, callado):
        if c and ini is None:
            ini = x
        elif not c and ini is not None:
            tramos.append((ini, x))
            ini = None
    if ini is not None:
        tramos.append((ini, D))
    return tramos


def _elegir(items: list[dict], c: np.ndarray, e: np.ndarray, rng) -> list[dict]:
    """Primero el mayor formato; con el caos, cada vez más elecciones al azar.

    Fuera del azar, de la familia de mayor formato que quede se toma la imagen
    cuya luz se acerca a la energía del momento y cuyo tono sigue al de la
    anterior, para que lo que se encadena sea pariente.
    """
    resto = list(range(len(items)))
    elegidas = []
    tono_previo = None
    for ci, ei in zip(c, e):
        if rng.random() < ci**1.5:
            k = resto[int(rng.integers(len(resto)))]
        else:
            rango = min(FAMILIA_RANGO.get(items[j]["familia"], 9) for j in resto)
            candidatas = [j for j in resto if FAMILIA_RANGO.get(items[j]["familia"], 9) == rango]
            luces = np.array([items[j]["luz"] for j in candidatas])
            objetivo = luces.min() + ei * (luces.max() - luces.min())

            def puntaje(j):
                it = items[j]
                d_luz = abs(it["luz"] - objetivo) * 2
                if tono_previo is None or it["sat"] < 0.12:
                    return d_luz
                d = abs(it["tono"] - tono_previo) % 360
                return d_luz + min(d, 360 - d) / 180 * 0.5

            k = min(candidatas, key=puntaje)
        resto.remove(k)
        elegidas.append(items[k])
        if items[k]["sat"] >= 0.12:
            tono_previo = items[k]["tono"]
    return elegidas


class _Pared:
    """Mosaico de filas que crece desde el centro en elipse (con la proporción del cuadro).

    Cada pieza nueva va al hueco libre más cercano al centro: al extremo
    izquierdo o derecho de una fila existente, o a una fila nueva arriba o abajo.
    """

    def __init__(self, fila: float, hueco: float, aspecto: float, rng):
        self.fila, self.hueco, self.aspecto, self.rng = fila, hueco, aspecto, rng
        self.filas: dict[int, list[float]] = {}

    def poner(self, ratio: float):
        h, g = self.fila, self.hueco
        w = h * ratio
        paso = h + g
        opciones = []
        for k, (izq, der) in self.filas.items():
            opciones.append((k, der + g + w / 2))
            opciones.append((k, izq - g - w / 2))
        if self.filas:
            arriba, abajo = min(self.filas) - 1, max(self.filas) + 1
            desplazamiento = self.rng.uniform(-0.3, 0.3) * w
            opciones.append((arriba, desplazamiento))
            opciones.append((abajo, desplazamiento))
        else:
            opciones.append((0, 0.0))

        def distancia(op):
            k, cx = op
            return math.hypot(cx / self.aspecto, k * paso)

        k, cx = min(opciones, key=distancia)
        izq, der = cx - w / 2, cx + w / 2
        if k in self.filas:
            self.filas[k] = [min(self.filas[k][0], izq), max(self.filas[k][1], der)]
        else:
            self.filas[k] = [izq, der]
        return cx, k * paso, w, h


def _camara(prm, prot, piezas, pieza_de, caos, silencio, primeros, t_coda, duracion, fps, W, H):
    """Cámara suavizada sobre la pared: sigue a la pieza más nueva al principio y
    encuadra la pared entera al final. Claves cada 3 cuadros: [cuadro, cx, cy, escala]."""
    paso = 3
    desde = np.array([x["desde"] for x in prot])
    orden = np.argsort(desde)
    desde_ord = desde[orden]
    caja = None  # [xmin, xmax, ymin, ymax] de las piezas ya en vuelo o en la pared
    ultima = 0
    cam = None
    claves, luces = [], []
    enc0, enc1, enc2 = prm["encuadre"]
    for f in range(0, duracion + paso, paso):
        s_t = f / fps
        while ultima < len(orden) and desde_ord[ultima] <= s_t:
            pz = piezas[pieza_de[int(orden[ultima])]]
            borde = [pz["x"] - pz["ancho"] / 2, pz["x"] + pz["ancho"] / 2, pz["y"] - pz["alto"] / 2, pz["y"] + pz["alto"] / 2]
            caja = borde if caja is None else [min(caja[0], borde[0]), max(caja[1], borde[1]), min(caja[2], borde[2]), max(caja[3], borde[3])]
            ultima += 1
        nueva = piezas[pieza_de[int(orden[max(0, ultima - 1)])]]
        cj = caja or [nueva["x"] - nueva["ancho"] / 2, nueva["x"] + nueva["ancho"] / 2, nueva["y"] - nueva["alto"] / 2, nueva["y"] + nueva["alto"] / 2]
        c = float(caos(s_t))
        en_coda = _suave((s_t - t_coda) / max(1e-6, (duracion / fps - t_coda) * 0.7))
        k = _lerp(_lerp(enc0, enc1, _suave(c / 0.6)), enc2, en_coda)
        bw, bh = cj[1] - cj[0], cj[3] - cj[2]
        escala = min(W * k / bw, H * k / bh)
        centro_caja = ((cj[0] + cj[1]) / 2, (cj[2] + cj[3]) / 2)
        peso_caja = _lerp(0.5 * _suave(c), 1.0, en_coda)
        objetivo = (_lerp(nueva["x"], centro_caja[0], peso_caja), _lerp(nueva["y"], centro_caja[1], peso_caja), math.log(escala))
        callado = float(silencio(s_t))
        if cam is None:
            cam = list(objetivo)
        else:
            tau = _lerp(_lerp(1.5, 0.6, c), 6.0, callado)  # en el silencio la cámara casi se detiene
            a = 1 - math.exp(-(paso / fps) / tau)
            cam = [cam[j] + (objetivo[j] - cam[j]) * a for j in range(3)]
        # Empujón en los primeros tiempos, que crece con el caos (y se apaga en la coda).
        previos = primeros[primeros <= s_t]
        empujon = 0.0
        if len(previos):
            empujon = prm["golpe_camara"] * c * (1 - en_coda) * math.exp(-(s_t - previos[-1]) / 0.18)
        claves.append([f, round(cam[0], 2), round(cam[1], 2), round(math.exp(cam[2]) * (1 + empujon), 5)])
        if f % 15 == 0:
            luz = _lerp(_lerp(*prm["luz_pared"], c), 1.0, en_coda) * (1 - 0.55 * callado * (1 - en_coda))
            luces.append([f, round(luz, 3)])
    return claves, luces


def _ecos(prm, caos, primeros, t_coda, golpe_s, fps, W, H, rng, silencios):
    """Copias de la pared sobre la pared, desde que el caos pasa el primer umbral.
    Un eco que alcanza un silencio de la canción se apaga cuando empieza el silencio."""
    ecos = []
    for d in primeros:
        if d >= t_coda - 2 * golpe_s:
            break
        c = float(caos(d))
        cuantos = sum(c >= u for u in prm["ecos"])
        vivos = [e for e in ecos if e["fin"] > d * fps]
        if cuantos == 0 or len(vivos) >= cuantos:
            continue
        vida = _lerp(16, 6, c) * golpe_s * rng.uniform(0.8, 1.2)
        fin_s = min(d + vida, t_coda + 4 * golpe_s)  # en la coda se apagan
        for s_ini, _ in silencios:
            if d < s_ini < fin_s:
                fin_s = s_ini + golpe_s / 2
                break
        tipo = rng.choice(["lejos", "cerca", "girado"])
        if tipo == "lejos":
            e0 = rng.uniform(0.35, 0.55)
            escala = [e0, e0 * 1.08]
            r0 = rng.uniform(-10, 10) * c
            rot = [r0, r0 + rng.uniform(-6, 6)]
            dx0, dy0 = rng.uniform(-0.3, 0.3) * W, rng.uniform(-0.25, 0.25) * H
        elif tipo == "cerca":
            e0 = rng.uniform(1.6, 2.4)
            escala = [e0, e0 * 0.92]
            r0 = rng.uniform(-4, 4)
            rot = [r0, r0 + rng.uniform(-3, 3)]
            dx0, dy0 = rng.uniform(-0.1, 0.1) * W, rng.uniform(-0.1, 0.1) * H
        else:
            e0 = rng.uniform(0.75, 0.95)
            escala = [e0, e0 * 1.05]
            r0 = rng.uniform(-25, 25)
            rot = [r0, r0 + rng.uniform(-10, 10)]
            dx0, dy0 = rng.uniform(-0.15, 0.15) * W, rng.uniform(-0.15, 0.15) * H
        deriva = rng.uniform(-0.05, 0.05, size=2) * np.array([W, H])
        ini = round(d * fps)
        fin = max(ini + 4, round(fin_s * fps))
        borde_f = round(_lerp(2, 1, c) * golpe_s * fps)
        ecos.append(
            {
                "tipo": str(tipo),
                "ini": ini,
                "fin": fin,
                "entrada": min(borde_f, (fin - ini) // 3),
                "salida": min(round(2 * golpe_s * fps), (fin - ini) // 3),
                "desfase": int(round(rng.choice([0, 4, 8, 16]) * golpe_s * fps)),
                "escala": [round(v, 4) for v in escala],
                "rot": [round(v, 2) for v in rot],
                "dx": [round(dx0, 1), round(dx0 + deriva[0], 1)],
                "dy": [round(dy0, 1), round(dy0 + deriva[1], 1)],
                "opacidad": round(rng.uniform(0.3, 0.55), 3),
                # `lighten` y no `screen`: el eco se queda con lo más claro de cada punto en
                # vez de sumar luz, y la pared no se lava cuando se apilan dos o tres ecos.
                "mezcla": "lighten",
            }
        )
    return ecos


def _resumen(p, m, actos, capas, ecos, piezas, fps, secuencia, prot) -> None:
    print(f"{len(capas)} imágenes en actos sobre {m['duracion']:.0f} s a {m['bpm']} BPM → {p.timeline}")
    print(f"  pared final: {len(piezas)} piezas · {len(ecos)} ecos")
    for a in actos:
        dentro = [k for k, c in enumerate(capas) if a["ini"] <= c["ini"] < a["fin"]]
        dur = (a["fin"] - a["ini"]) / fps
        if not dur:
            continue
        familias: dict[str, int] = {}
        for k in dentro:
            f = secuencia[k]["familia"]
            familias[f] = familias.get(f, 0) + 1
        top = ", ".join(f"{f} {v}" for f, v in sorted(familias.items(), key=lambda x: -x[1])[:3])
        vidas = [(capas[k]["vuelo"]["desde"] - capas[k]["ini"]) / fps for k in dentro]
        ecos_a = sum(1 for e in ecos if a["ini"] <= e["ini"] < a["fin"])
        print(
            f"  {a['nombre']:>4}  {a['ini'] / fps:6.1f}–{a['fin'] / fps:6.1f} s  {len(dentro):4d} imágenes "
            f"({len(dentro) / dur:.1f}/s)  protagonista ~{np.median(vidas) if vidas else 0:.1f} s  ecos {ecos_a}  [{top}]"
        )
