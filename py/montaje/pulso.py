"""Pulso: clips al pulso de la canción, con fundidos de recuerdo.

Para un puñado de clips (no cientos de imágenes): cada clip ocupa una o más
**frases** de la canción (grupos de compases que respetan sus secciones) y, dentro
de su frase, **salta al pulso**: muestra varios momentos del mismo clip, siempre
hacia adelante en su tiempo, cortando en los compases o en los golpes según la
energía. Entre un clip y el siguiente, **fundido**; más largo cuando la música
está en calma.

Dos fantasmas, opcionales, para que se sienta como recuerdo (doble exposición en
`screen`, encima de todo):

- **doble**: en una frase tranquila, el clip que viene aparece unos golpes antes de
  llegar, transparente, y sigue sin salto cuando entra de verdad;
- **estela**: el clip que se va se queda unos golpes como un brillo que se apaga.

Qué segundos de cada clip: los elige `clips.mejor_tramo` (nítidos, sin temblor,
lejos del arranque y el final de la toma) y, si hay, con el movimiento que pide la
música: quietos en la calma, con movimiento en el pico. En la calma el clip va un
poco más lento (`velocidad`).

proyecto.json:

    "montaje": {
      "modo": "pulso",
      "corte": "energia",            # frase | compas | golpe | energia
      "frase_compases": 4,
      "umbral_calma": 0.35,          # bajo esto, la frase no salta: una toma larga
      "umbral_pico": 0.7,            # desde esto, `pico_por_compas` saltos por compás
      "pico_por_compas": 2,
      "fundido_golpes": 1,           # entre clips
      "fundido_calma_golpes": 3,     # entre clips, si una de las dos frases es calma
      "fundido_dentro_golpes": 0,    # entre momentos del mismo clip (0 = corte seco)
      "transicion": "fundido",       # entre clips: fundido | cortina | iris | empuje | destello | zoom | persiana | ronda
      "transicion_dir": "alterna",   # hacia dónde: derecha | izquierda | arriba | abajo | alterna
      "mezclar_fotos": false,        # las fotos del proyecto (`"fotos": "<carpeta>"`) entran al reparto, intercaladas: un clip, una foto
                                     # en `material` de un tramo: "foto:campo" = sólo fotos con esa palabra; "clip:playa" = sólo clips
      "zoom_foto": 0.08,             # cuánto se mueve cada foto mientras está en pantalla (0 o más; una se acerca, la siguiente se aleja)
      "doble_golpes": 0, "doble_opacidad": 0.45,
      "estela_golpes": 0, "estela_opacidad": 0.35,
      "velocidad": [0.8, 1.0],       # en la calma y en el pico
      "orden": "fecha",              # fecha | nombre | movimiento
      "encuadre": "auto",            # cubrir | contener | relleno | medio | auto
      "zoom": 0.03,                  # acercamiento lento de cada toma
      "frase_compases_calma": 4,     # frases más largas donde la música está en calma
      "reparto": "seguido",          # seguido: cada clip sus frases juntas · ronda: vuelven en orden
      "borde_toma": 0.35,            # segundos del arranque y final de cada toma que no se usan
      "espejo": 4,                   # caleidoscopio: 2 mitades o 4 cuartos en espejo (0 = no)
      "rejilla": [3, 3, 0.25],       # mosaico de tiempo: columnas, filas, segundos de atraso por celda
                                     # con "material_en_orden": true en el tramo, los clips entran en el orden de esa lista
      "tramos": [                    # el guion: cada tramo cambia perillas entre dos segundos
        {"nombre": "abre", "desde": 0, "hasta": 27, "frase_compases": 4, "congelar_golpes": 4, "material": ["lanchas"]},
        {"nombre": "pleno", "desde": 27, "hasta": 74, "frase_compases": 1, "fundido_golpes": 0.25}
      ]
    }

`versiones` en proyecto.json guarda variantes con nombre de estos parámetros
(`planificar <p> --version b`).
"""

from __future__ import annotations

import datetime as dt
import math

import numpy as np

from . import clips as catalogo_clips
from . import musica
from .planificar import audio_de, escribir
from .rutas import Proyecto, salir
from .secuencia import _compases

POR_DEFECTO = {
    "corte": "energia",
    "frase_compases": 4,
    "umbral_calma": 0.35,
    "umbral_pico": 0.7,
    "pico_por_compas": 2,
    "fundido_golpes": 1.0,
    "fundido_calma_golpes": 3.0,
    "fundido_dentro_golpes": 0.0,
    "doble_golpes": 0.0,
    "doble_opacidad": 0.45,
    "estela_golpes": 0.0,
    "estela_opacidad": 0.35,
    "velocidad": [0.8, 1.0],
    "velocidad_min": 0.5,
    "orden": "fecha",
    "encuadre": "auto",
    "zoom": 0.03,
    "max_por_clip": 3,
    "reparto": "seguido",
    "frase_compases_calma": None,
    "borde_toma": 0.35,
    "espejo": 0,
    "rejilla": None,
    "congelar_golpes": 0.0,
    "doble_en": "calma",
    "dividir": 1,
    "escala": 1.0,
    "sombra": 0.0,
    "transformados": None,
    "seguir": True,
    "muro": None,
    "muro_golpes": 4,
    "fundido_inicio_golpes": 2.0,
    "fundido_final_golpes": 4.0,
    "transicion": "fundido",
    "transicion_dir": "alterna",
    "mezclar_fotos": False,
    "zoom_foto": 0.08,
}

CORTES = ("frase", "compas", "golpe", "energia")


# ── Frases ─────────────────────────────────────────────────────────────────

#: Cómo entra un clip sobre el que se va (dura lo que el fundido entre clips).
TRANSICIONES = ("fundido", "cortina", "iris", "empuje", "destello", "zoom", "persiana")
DIRECCIONES = {"derecha": [1, 0], "izquierda": [-1, 0], "abajo": [0, 1], "arriba": [0, -1]}


def _transicion(prm: dict, n: int) -> tuple[str, list[int]] | None:
    """La transición del `n`-ésimo cambio de clip: (tipo, hacia dónde). None = fundido.

    `ronda` las recorre todas, una por cambio; `alterna` va a la derecha y a la izquierda.
    """
    tipo = prm["transicion"]
    if tipo == "ronda":
        tipo = TRANSICIONES[1:][n % (len(TRANSICIONES) - 1)]
    if tipo not in TRANSICIONES:
        salir(f"transicion desconocida: {tipo} (hay: {', '.join(TRANSICIONES)}, ronda)")
    if tipo == "fundido":
        return None
    d = prm["transicion_dir"]
    if d == "alterna":
        # En ronda hay seis tipos: si el lado dependiera sólo de `n`, cada tipo saldría siempre para el
        # mismo lado. Cada vuelta de la ronda empieza por el otro.
        vuelta = n // (len(TRANSICIONES) - 1) if prm["transicion"] == "ronda" else 0
        d = ("derecha", "izquierda")[(n + vuelta) % 2]
    if d not in DIRECCIONES:
        salir(f"transicion_dir desconocida: {d} (hay: {', '.join(DIRECCIONES)}, alterna)")
    return tipo, DIRECCIONES[d]


def _es_material(c: dict, palabra: str) -> bool:
    """¿El clip `c` es del material que pide `palabra`? Una palabra de su nombre; con
    `foto:` o `clip:` adelante, sólo las fotos o sólo los clips que la llevan."""
    if palabra.startswith("foto:"):
        return bool(c.get("foto")) and palabra[5:] in c["id"]
    if palabra.startswith("clip:"):
        return not c.get("foto") and palabra[5:] in c["id"]
    return palabra in c["id"]


def _en_orden(grupo: list[dict], material: list[str]) -> list[dict]:
    """Los clips en el orden que dice la lista del guion: cada uno, en el lugar de la primera palabra que lo nombra."""
    return sorted(grupo, key=lambda c: min((i for i, pal in enumerate(material) if _es_material(c, pal)), default=len(material)))


def _intercalar(lista: list[dict]) -> list[dict]:
    """Un clip, una foto, un clip, una foto…, cada grupo en su orden; lo que sobra de uno, al final."""
    clips_, fotos = [c for c in lista if not c.get("foto")], [c for c in lista if c.get("foto")]
    if not clips_ or not fotos:
        return lista
    mezcla = [x for par in zip(clips_, fotos) for x in par]
    return mezcla + clips_[len(fotos):] + fotos[len(clips_):]


def _frases(compases: list[dict], m: dict, n: int, n_calma: int | None = None, umbral: float = 0.0, largo_en=None,
            cortes: frozenset[int] | set[int] = frozenset()) -> list[list[int]]:
    """Compases agrupados de a `n` (de a `n_calma` donde la música está en calma), empezando
    de nuevo en cada sección y en cada compás de `cortes` (donde empieza un tramo del guion).
    Una frase de un compás se une a la anterior (salvo con `n` = 1)."""
    inicios = np.array([c["ini"] for c in compases])
    cortes_seccion = {int(np.argmin(np.abs(inicios - s["ini"]))) for s in m.get("secciones", [])}
    # Un primer compás corto es la anacrusa (lo que suena antes del primer «uno»): va con la
    # primera frase pero no cuenta como uno de sus compases.
    largo_tipico = float(np.median([c["fin"] - c["ini"] for c in compases]))
    anacrusa = len(compases) > 1 and (compases[0]["fin"] - compases[0]["ini"]) < 0.6 * largo_tipico
    cortes_seccion.discard(1 if anacrusa else -1)
    # El guion manda: si el borde de un tramo cae a un compás de un cambio de sección, el corte es uno
    # solo, el del tramo. Con los dos, entre medio quedaba una frase de un compás: un clip que entraba y
    # ya se estaba yendo.
    cortes_seccion -= {i for i in cortes_seccion if any(abs(i - c) == 1 for c in cortes)}
    frases: list[list[int]] = []
    cuenta, objetivo = 0, n
    for i in range(len(compases)):
        if i == 0 or ((i in cortes_seccion or i in cortes) and cuenta > 0) or cuenta == objetivo:
            frases.append([])
            cuenta = 0
            # Qué largo tiene esta frase: el de su tramo del guion, y el de la calma si lo que viene está en calma.
            n_i, n_calma_i = largo_en(i) if largo_en else (n, n_calma)
            proximos = [c["e"] for c in compases[i : i + (n_calma_i or n_i)]]
            objetivo = n_calma_i if n_calma_i and float(np.mean(proximos)) < umbral else n_i
        frases[-1].append(i)
        cuenta += 0 if (i == 0 and anacrusa) else 1
    if min(n, n_calma or n) == 1 or largo_en:
        return frases
    # Frases de un solo compás: se pegan a la anterior (salvo la primera).
    unidas: list[list[int]] = []
    for f in frases:
        if len(f) == 1 and unidas:
            unidas[-1] += f
        else:
            unidas.append(f)
    return unidas


def _repartir_clips(clips: list[dict], n_huecos: int, maximo: int) -> list[int]:
    """Cuántas frases recibe cada clip: proporcional a su material útil, al menos una, a lo sumo `maximo`."""
    util = np.array([max(0.5, c["duracion"] - 2 * catalogo_clips.BORDE_TOMA) for c in clips])
    k = np.ones(len(clips), dtype=int)
    tope = max(maximo, math.ceil(n_huecos / len(clips)))
    while k.sum() < n_huecos:
        # El que más material tiene por frase asignada recibe la siguiente.
        i = int(np.argmax(np.where(k < tope, util / k, -1)))
        k[i] += 1
    return [int(v) for v in k]


# ── Plan ───────────────────────────────────────────────────────────────────

def _encaje(c: dict, W: int, H: int, encuadre: str) -> tuple[float, float, bool]:
    """Tamaño del clip en pantalla y si lleva relleno (el mismo clip, desenfocado, detrás)."""
    r_clip, r_lienzo = c["w"] / c["h"], W / H
    if encuadre == "auto":
        encuadre = "cubrir" if abs(math.log(r_clip / r_lienzo)) < math.log(1.3) else "relleno"
    if encuadre == "cubrir":
        s = max(W / c["w"], H / c["h"])
        return round(c["w"] * s, 1), round(c["h"] * s, 1), False
    if encuadre == "medio":
        # A mitad de camino (geométrica) entre entero y recortado, con relleno donde falta:
        # en un 9:16 desde un 3:2 se ve el 61 % del ancho en vez del 37 %.
        s = math.sqrt(max(W / c["w"], H / c["h"]) * min(W / c["w"], H / c["h"]))
        return round(c["w"] * s, 1), round(c["h"] * s, 1), True
    s = min(W / c["w"], H / c["h"])
    return round(c["w"] * s, 1), round(c["h"] * s, 1), encuadre == "relleno"


def _ordenar(clips: list[dict], orden: str) -> list[dict]:
    if orden == "fecha":
        return clips  # el catálogo ya viene por fecha
    if orden == "nombre":
        return sorted(clips, key=lambda c: c["id"])
    if orden == "movimiento":
        return sorted(clips, key=lambda c: c["resumen"]["movimiento"])
    salir(f"orden desconocido: {orden} (hay: fecha, nombre, movimiento)")


def _segmentos(compases: list[dict], frase: list[int], prm: dict) -> list[tuple[float, float, float]]:
    """Los tramos de una frase: (inicio, fin, energía), en segundos de la canción."""
    corte = prm["corte"]
    tramos: list[tuple[float, float, float]] = []
    if corte == "frase":
        e = float(np.mean([compases[i]["e"] for i in frase]))
        return [(compases[frase[0]]["ini"], compases[frase[-1]]["fin"], e)]
    for i in frase:
        c = compases[i]
        golpes = c["golpes"] + [c["fin"]]
        if corte == "golpe":
            tramos += [(golpes[j], golpes[j + 1], c["e"]) for j in range(len(golpes) - 1)]
        elif corte == "compas":
            tramos.append((c["ini"], c["fin"], c["e"]))
        else:  # energía: la calma no salta, lo medio salta por compás, el pico más
            if c["e"] < prm["umbral_calma"] and tramos and tramos[-1][2] < prm["umbral_calma"]:
                a, _, e = tramos[-1]
                tramos[-1] = (a, c["fin"], (e + c["e"]) / 2)
            elif c["e"] >= prm["umbral_pico"]:
                k = max(1, int(prm["pico_por_compas"]))
                bordes = [c["ini"] + (c["fin"] - c["ini"]) * q / k for q in range(k + 1)]
                # En la rejilla del golpe si se puede.
                if len(golpes) - 1 >= k and (len(golpes) - 1) % k == 0:
                    paso = (len(golpes) - 1) // k
                    bordes = golpes[::paso]
                tramos += [(bordes[q], bordes[q + 1], c["e"]) for q in range(len(bordes) - 1)]
            else:
                tramos.append((c["ini"], c["fin"], c["e"]))
    return tramos


def _velocidad(e: float, prm: dict) -> float:
    calma, pico = prm["velocidad"]
    u = np.clip((e - prm["umbral_calma"]) / max(1e-6, prm["umbral_pico"] - prm["umbral_calma"]), 0, 1)
    return round(float(calma + (pico - calma) * u), 3)


def frases_del_guion(m: dict, prm: dict, compases: list[dict]):
    """La canción en frases según el guion: cada frase es un clip (una toma). Devuelve las frases (listas de
    compases), en qué tramo cae cada compás y las perillas que valen en él. La usan `planificar` y `tomas`."""
    tramos_guion = prm.get("tramos") or []
    for tr in tramos_guion:
        # Lo que se escribe a mano: una palabra suelta en `material` vale como lista de una, y un corte que no existe no pasa callado.
        if isinstance(tr.get("material"), str):
            tr["material"] = [tr["material"]]
        if tr.get("corte", prm["corte"]) not in CORTES:
            salir(f"tramo «{tr.get('nombre', '?')}»: corte desconocido: {tr['corte']} (hay: {', '.join(CORTES)})")

    def tramo_de(i: int) -> int:
        """En qué tramo del guion cae el compás `i` (por su punto medio; -1 = en ninguno)."""
        t = (compases[i]["ini"] + compases[i]["fin"]) / 2
        return next((k for k, tr in enumerate(tramos_guion) if tr.get("desde", 0) <= t < tr.get("hasta", math.inf)), -1)

    def prm_compas(i: int) -> dict:
        """Las perillas que valen en el compás `i`: las del montaje y, encima, las de su tramo del guion."""
        k = tramo_de(i)
        return prm if k < 0 else {**prm, **{c: v for c, v in tramos_guion[k].items() if c not in ("desde", "hasta", "nombre")}}

    def largo_en(i: int) -> tuple[int, int | None]:
        pt = prm_compas(i)
        return int(pt["frase_compases"]), (int(pt["frase_compases_calma"]) if pt["frase_compases_calma"] else None)

    n_calma = int(prm["frase_compases_calma"]) if prm["frase_compases_calma"] else None
    # Donde empieza otro tramo del guion empieza otra frase: si no, el tramo valdría recién desde
    # la primera frase que arranca dentro de él (y uno corto, entre dos frases largas, no valdría nunca).
    cortes_tramo = {i for i in range(1, len(compases)) if tramo_de(i) != tramo_de(i - 1)} if tramos_guion else set()
    frases = _frases(compases, m, int(prm["frase_compases"]), n_calma, prm["umbral_calma"], largo_en if tramos_guion else None, cortes_tramo)
    for k, tr in enumerate(tramos_guion):
        if not any(tramo_de(f[0]) == k for f in frases):
            print(f"aviso: el tramo «{tr.get('nombre', k + 1)}» ({tr.get('desde', 0):g}–{tr.get('hasta', m['duracion']):g} s) no alcanza a tener un compás propio: no vale en ningún lado")
    return frases, tramo_de, prm_compas


def planificar(p: Proyecto) -> None:
    prm = {**POR_DEFECTO, **p.cfg.get("montaje", {})}
    if prm["corte"] not in CORTES:
        salir(f"corte desconocido: {prm['corte']} (hay: {', '.join(CORTES)})")
    catalogo = catalogo_clips.cargar(p)
    # Las fotos del catálogo entran sólo si el montaje las pide: sin eso, sumarle fotos a un proyecto no le cambia nada.
    todos = _ordenar([c for c in catalogo if not c["src"].startswith("transformados/") and (prm["mezclar_fotos"] or not c.get("foto"))], prm["orden"])
    # Las variantes transformadas de cada clip (estela, eco, barrido…), por si se piden.
    variantes: dict[str, list[dict]] = {}
    for c in catalogo:
        if c["src"].startswith("transformados/"):
            base = next((o["id"] for o in todos if c["id"].startswith(o["id"] + "-")), None)
            if base:
                variantes.setdefault(base, []).append(c)
    if not todos:
        salir("el catálogo no tiene clips propios (sólo transformados): `clips` del proyecto tiene que incluir la carpeta de los originales")
    m = musica.cargar(p)

    # El lienzo: el de proyecto.json o, si no dice, el de la mayoría de los clips.
    verticales = sum(c["ratio"] < 0.9 for c in todos)
    por_defecto = {"ancho": 1080, "alto": 1920} if verticales > len(todos) / 2 else {"ancho": 1920, "alto": 1080}
    out = {**por_defecto, "fps": 30, "fondo": "#07090d", **p.cfg.get("salida", {})}
    W, H, fps = out["ancho"], out["alto"], out["fps"]
    golpe_s = 60 / m["bpm"]

    compases = _compases(m)
    if prm["muro"]:
        _muro(p, prm, todos, m, out, golpe_s)
        return

    frases, tramo_de, prm_compas = frases_del_guion(m, prm, compases)
    # Menos frases que clips: se parten las más enérgicas por la mitad mientras se pueda.
    # Si el guion dice el material de cada tramo, manda él: no se parte ni se deja afuera nada.
    con_material = any("material" in tr for tr in prm.get("tramos") or [])
    while len(frases) < len(todos) and not con_material:
        partibles = [i for i, f in enumerate(frases) if len(f) >= 2]
        if not partibles:
            break
        i = max(partibles, key=lambda i: np.mean([compases[k]["e"] for k in frases[i]]) + len(frases[i]))
        f = frases[i]
        frases[i : i + 1] = [f[: len(f) // 2], f[len(f) // 2 :]]
    if prm["mezclar_fotos"]:
        todos = _intercalar(todos)
    usados = todos
    if len(frases) < len(todos) and not con_material:
        # Ni partiendo alcanza: entran los mejores, en su orden.
        mejores = sorted(todos, key=lambda c: -c["resumen"]["nitidez"] + c["resumen"]["temblor"])[: len(frases)]
        usados = [c for c in todos if c in mejores]
        print(f"aviso: {len(todos)} clips y sólo {len(frases)} frases; quedan afuera: "
              f"{', '.join(c['id'] for c in todos if c not in mejores)}")
    if con_material:
        # El guion dice qué material va en cada tramo («el campo», «vuelve el mar»): en cada
        # tramo, en ronda, los clips cuyo nombre lleva alguna de esas palabras. Cada grupo
        # sigue donde quedó, así un material que vuelve muestra otros clips.
        cuenta: dict[str, int] = {}
        clip_de_frase = []
        for frase in frases:
            material = prm_compas(frase[0]).get("material")
            grupo = [c for c in usados if not material or any(_es_material(c, pal) for pal in material)] or usados
            if material and prm_compas(frase[0]).get("material_en_orden"):
                grupo = _en_orden(grupo, material)
            if prm["mezclar_fotos"]:
                grupo = _intercalar(grupo)
            clave = ",".join(material or [])
            clip_de_frase.append(grupo[cuenta.get(clave, 0) % len(grupo)])
            cuenta[clave] = cuenta.get(clave, 0) + 1
    elif prm["reparto"] == "ronda":
        # Los clips vuelven en orden, cada vuelta con otros momentos: un recuerdo que regresa.
        clip_de_frase = [usados[i % len(usados)] for i in range(len(frases))]
    elif prm["reparto"] == "seguido":
        reparto = _repartir_clips(usados, len(frases), int(prm["max_por_clip"]))
        clip_de_frase = [c for c, k in zip(usados, reparto) for _ in range(k)]
    else:
        salir(f"reparto desconocido: {prm['reparto']} (hay: seguido, ronda)")

    # Cada frase: sus tramos, su velocidad y los segundos del clip que muestra.
    fundido = lambda golpes: max(0, round(golpes * golpe_s * fps))  # noqa: E731
    eventos = []  # dict por tramo, en orden de tiempo
    ya_usado: dict[str, list[tuple[float, float]]] = {}
    anterior_id = None
    for fi, frase in enumerate(frases):
        c = clip_de_frase[fi]
        pf = prm_compas(frase[0])
        tramos = _segmentos(compases, frase, pf)
        e_frase = float(np.mean([compases[i]["e"] for i in frase]))
        calma = e_frase < pf["umbral_calma"]
        # Clips transformados: en la calma (o siempre), la variante en vez del original.
        if pf["transformados"] not in (None, "no", False) and variantes.get(c["id"]) and (calma or pf["transformados"] == "todo"):
            c = variantes[c["id"]][fi % len(variantes[c["id"]])]
        # Se compara el archivo que de verdad se ve: pasar de un clip a su variante transformada también es un cambio.
        nuevo_clip = c["id"] != anterior_id
        anterior_id = c["id"]
        largos = [(b - a) for a, b, _ in tramos]
        vels = [_velocidad(e, pf) for _, _, e in tramos]
        # El material que hace falta (con lo que se pisa en los fundidos); si no alcanza, más lento.
        util = c["duracion"] - 2 * pf["borde_toma"]
        # Lo que se pisa con la frase siguiente: su fundido de entrada y la estela de éste.
        pisado = golpe_s * ((pf["fundido_calma_golpes"] if calma else pf["fundido_golpes"]) + pf["estela_golpes"])
        necesario = sum(l * v for l, v in zip(largos, vels)) + pisado * max(vels)
        if necesario > util > 0 and not c.get("foto"):  # a una foto no se le acaba el material
            k = min(1.0, max(pf["velocidad_min"] / max(vels), util / necesario))
            vels = [round(v * k, 3) for v in vels]
        usado = ya_usado.setdefault(c["id"], [])
        cursor = 0.0
        resto = sum(l * v for l, v in zip(largos, vels))
        for j, ((a, b, e), v) in enumerate(zip(tramos, vels)):
            largo_src = (b - a) * v
            resto -= largo_src
            hasta = max(cursor + largo_src, c["duracion"] - resto)
            mov = float(np.clip((e - 0.2) / 0.6, 0, 1))
            desde = catalogo_clips.mejor_tramo(c, largo_src, desde=cursor, hasta=hasta, movimiento_buscado=mov, evitar=usado,
                                               borde=pf["borde_toma"])
            usado.append((desde, desde + largo_src))
            cursor = desde + largo_src
            eventos.append({
                "t": a, "t_fin": b, "e": e, "clip": c, "desde": desde, "v": v,
                "frase": fi, "nuevo_clip": nuevo_clip and j == 0, "calma": calma, "prm": pf,
            })

    # Fundidos de entrada de cada tramo.
    for k, ev in enumerate(eventos):
        if k == 0:
            ev["entrada"] = fundido(ev["prm"]["fundido_inicio_golpes"])
        elif ev["nuevo_clip"]:
            calma = ev["calma"] or eventos[k - 1]["calma"]
            ev["entrada"] = fundido(ev["prm"]["fundido_calma_golpes"] if calma else ev["prm"]["fundido_golpes"])
        else:
            ev["entrada"] = fundido(ev["prm"]["fundido_dentro_golpes"])
    # Cómo entra cada clip nuevo sobre el que se va. El primero siempre sale del negro.
    cambios = 0
    for k, ev in enumerate(eventos):
        if k and ev["nuevo_clip"]:
            ev["transicion"] = _transicion(ev["prm"], cambios) if ev["entrada"] > 0 else None
            cambios += 1

    duracion = math.ceil(m["duracion"] * fps)
    # Los cuadros de cada toma y, antes de dibujar nada, que quepa entera en su clip con lo que
    # comparte con la siguiente en el fundido: si no cabe, empieza antes; si ni así, va más lenta.
    # Nunca pasa del final. Va en su propia pasada porque de dónde quedó cada toma dependen el
    # recorte que sigue al sujeto y los fantasmas: el doble tiene que empalmar con el `desde`
    # definitivo de la toma que viene, no con el que tenía antes de acomodarse.
    for k, ev in enumerate(eventos):
        c = ev["clip"]
        ev["ini"] = round(ev["t"] * fps)
        ev["sig"] = round(eventos[k + 1]["t"] * fps) if k + 1 < len(eventos) else duracion
        ev["fin"] = min(duracion, ev["sig"] + (eventos[k + 1]["entrada"] if k + 1 < len(eventos) else 0))
        vida_s = (ev["fin"] - ev["ini"]) / fps
        if c.get("foto"):
            ev["desde"], ev["v"] = 0.0, 1.0
            continue
        tope = c["duracion"] - 1 / max(fps, c["fps"])
        if ev["desde"] + vida_s * ev["v"] > tope:
            ev["desde"] = round(max(0.0, tope - vida_s * ev["v"]), 3)
            if vida_s * ev["v"] > tope:
                ev["v"] = round(tope / vida_s, 3)

    capas, fantasmas = [], []
    fotos_vistas = 0
    for k, ev in enumerate(eventos):
        c = ev["clip"]
        pe = ev["prm"]
        ini, fin = ev["ini"], ev["fin"]
        ancho, alto, relleno = _encaje(c, W, H, pe["encuadre"])
        x, y, marco = W / 2, H / 2, None
        if pe["dividir"] == 2:
            # Díptico: este clip en la mitad izquierda (o de arriba, en un vertical); su pareja, en la otra.
            ancho, alto, x, y, marco = _mitad(c, W, H, 0)
            relleno = False
        elif pe["escala"] < 1:
            ancho, alto = round(ancho * pe["escala"], 1), round(alto * pe["escala"], 1)
            relleno = False
        vida_s = (fin - ini) / fps
        deriva = [0, 0]
        if pe["seguir"] and "cx" in c["curvas"] and pe["escala"] >= 1:
            # El recorte sigue al sujeto: donde el clip sobra (otro formato), se corre para
            # dejar al centro lo que importa, y se desliza si el sujeto se mueve.
            mw, mh = (marco["ancho"], marco["alto"]) if marco else (W, H)
            (x, y), (x2, y2) = (_seguir(c, t, ancho, alto, x, y, mw, mh) for t in (ev["desde"], ev["desde"] + vida_s * ev["v"]))
            deriva = [round(x2 - x, 1), round(y2 - y, 1)]
        z = pe["zoom"] * min(1.0, vida_s / 6)
        zoom = [1, round(1 + z, 4)]
        if c.get("foto"):
            # Una foto no se mueve sola: se acerca despacio (una sí, una no se aleja) y se desliza un
            # poco de lado, siempre dentro de lo que el acercamiento deja de sobra para no destapar el fondo.
            zf = max(0.0, float(pe["zoom_foto"]))  # negativo dejaría la foto más chica que el cuadro
            entra, sale = (1.04, 1.04 + zf) if fotos_vistas % 2 == 0 else (1.04 + zf, 1.04)
            zoom = [round(entra, 4), round(sale, 4)]
            lado = 1 if (fotos_vistas // 2) % 2 == 0 else -1
            deriva = [round(deriva[0] + lado * 0.8 * (sale - 1) / 2 * ancho, 1), deriva[1]]
            fotos_vistas += 1
        ultima = k == len(eventos) - 1
        transicion = None
        if ev.get("transicion"):
            tipo, hacia = ev["transicion"]
            transicion = {"tipo": tipo, "dir": hacia}
            if tipo == "iris":
                # El iris se abre desde lo que importa del clip (su centro de interés), no desde el centro del cuadro.
                i = min(len(c["curvas"].get("cx", [])) - 1, int(ev["desde"] * c["hz"]))
                cx, cy = (c["curvas"]["cx"][i], c["curvas"]["cy"][i]) if i >= 0 else (0.5, 0.5)
                transicion["centro"] = [round(float(np.clip(x - ancho / 2 + cx * ancho, 0, W)), 1),
                                        round(float(np.clip(y - alto / 2 + cy * alto, 0, H)), 1)]
        # Empuje: el que entra corre al que se va, que sale por el otro lado en los mismos cuadros.
        sig_tr = eventos[k + 1].get("transicion") if k + 1 < len(eventos) else None
        empujada = None
        if sig_tr and sig_tr[0] == "empuje":
            # Los mismos cuadros que de verdad tarda en entrar la que empuja (su entrada tiene tope: lo que dura su toma).
            llega = eventos[k + 1]
            empujada = {"cuadros": int(min(llega["entrada"], max(0, (llega["fin"] - llega["ini"]) - 2))), "dir": sig_tr[1]}
        capas.append({
            "id": f"{c['id']}#{k}",
            "img": c["proxy"],
            "video": {"desde": ev["desde"], "velocidad": ev["v"], "fuente": [c["w"], c["h"]], **({"foto": True} if c.get("foto") else {}),
                      **({"relleno": True} if relleno else {}),
                      **({"espejo": int(pe["espejo"])} if pe["espejo"] in (2, 4) else {}),
                      **({"rejilla": {"columnas": int(pe["rejilla"][0]), "filas": int(pe["rejilla"][1]), "desfase": float(pe["rejilla"][2])}}
                         if pe["rejilla"] else {}),
                      **({"congelar": fundido(pe["congelar_golpes"])} if pe["congelar_golpes"] and ev["nuevo_clip"] else {})},
            "ini": ini,
            "fin": fin,
            "entrada": int(min(ev["entrada"], max(0, (fin - ini) - 2))),
            "salida": int(min(fundido(pe["fundido_final_golpes"]), max(0, (fin - ini) - 2))) if ultima else 0,
            "x": x,
            "y": y,
            "ancho": ancho,
            "alto": alto,
            **({"marco": marco} if marco else {}),
            **({"sombra": pe["sombra"]} if pe["sombra"] else {}),
            **({"transicion": transicion} if transicion else {}),
            **({"empujada": empujada} if empujada else {}),
            "opacidad": 1,
            "zoom": zoom,
            "deriva": deriva,
            "mezcla": "normal",
            "borde": 0,
            "seccion": ev["frase"],
        })
        ev["capa"] = capas[-1]
        if pe["dividir"] == 2:
            pareja = todos[(todos.index(next(o for o in todos if c["id"].startswith(o["id"]))) + len(todos) // 2) % len(todos)]
            pw, ph, px, py, pm = _mitad(pareja, W, H, 1)
            desde_p = catalogo_clips.mejor_tramo(pareja, min(vida_s * ev["v"], pareja["duracion"] - 0.05), borde=pe["borde_toma"])
            v_p = ev["v"] if desde_p + vida_s * ev["v"] <= pareja["duracion"] else round((pareja["duracion"] - 0.05 - desde_p) / vida_s, 3)
            deriva_p = [0, 0]
            if pe["seguir"] and "cx" in pareja["curvas"]:
                (px, py), (px2, py2) = (_seguir(pareja, t, pw, ph, pm["x"], pm["y"], pm["ancho"], pm["alto"]) for t in (desde_p, desde_p + vida_s * v_p))
                deriva_p = [round(px2 - px, 1), round(py2 - py, 1)]
            capas.append({**capas[-1], "id": f"{pareja['id']}#par{k}", "img": pareja["proxy"], "x": px, "y": py, "ancho": pw, "alto": ph,
                          "marco": pm, "deriva": deriva_p, "zoom": [1, round(1 + z, 4)],
                          "video": {"desde": desde_p, "velocidad": v_p, "fuente": [pareja["w"], pareja["h"]], **({"foto": True} if pareja.get("foto") else {})}})

    # Los fantasmas van en otra pasada: cada uno copia el lugar de la capa de verdad que acompaña
    # (la estela, el de la que se va; el doble, el de la que viene), y esa ya tiene que existir.
    # Antes iban siempre a pantalla completa y al centro: con un recorte que sigue al sujeto, una
    # ventana o un díptico, el fantasma quedaba corrido respecto de su clip.
    for k, ev in enumerate(eventos):
        if k + 1 >= len(eventos) or not eventos[k + 1]["nuevo_clip"]:
            continue
        c, pe, ini = ev["clip"], ev["prm"], ev["ini"]
        cambio, siguiente = ev["sig"], eventos[k + 1]
        # Estela: el clip que se va sigue un poco, como un brillo que se apaga.
        if pe["estela_golpes"] > 0:
            # Aparece mientras el clip se funde (así no salta) y se apaga en `estela_golpes`.
            largo = fundido(pe["estela_golpes"])
            entra = max(1, siguiente["entrada"])
            seguido = ev["desde"] + (cambio - ini) / fps * ev["v"]
            vida = entra + largo
            # Si al clip no le queda material para toda la estela, la estela va más lenta (es un
            # brillo que se apaga: no se nota) en vez de no salir. Antes se perdía sin aviso.
            queda = c["duracion"] - 1 / max(fps, c["fps"]) - seguido
            v_estela = ev["v"] if c.get("foto") else min(ev["v"], round(queda / (vida / fps), 3))
            if v_estela > 0.02:
                fantasmas.append(_fantasma(c, f"estela-{k}", seguido, v_estela, cambio, min(duracion, cambio + vida),
                                           entra, largo, pe["estela_opacidad"], W, H, pe, ev["frase"],
                                           como=ev["capa"], avance=(cambio - ini) / max(1, ev["fin"] - ini)))
        # Doble: en la calma, el clip que viene se asoma antes de llegar y empalma con su entrada.
        if pe["doble_golpes"] > 0 and (ev["calma"] or pe["doble_en"] == "todo"):
            largo = fundido(pe["doble_golpes"])
            c2 = siguiente["clip"]
            # El fantasma tiene que llegar al cambio en el mismo segundo del clip en que entra la toma
            # de verdad (`siguiente["desde"]`): si no, al entrar la imagen salta. Lo normal es correr
            # a su misma velocidad desde `largo` antes. Pero con clips cortos la toma suele arrancar
            # al principio del clip y antes no hay material: ahí el fantasma va más lento (casi una
            # foto que empieza a moverse) para llegar justo. 0,07 es lo más lento que el reproductor
            # del panel acepta; con eso, lo que queda sin empalmar en el cambio es menos de dos décimas.
            asoma = (cambio - max(0, cambio - largo)) / fps
            v_doble = siguiente["v"]
            if asoma > 0 and siguiente["desde"] < asoma * v_doble and not c2.get("foto"):
                v_doble = max(0.07, math.floor(siguiente["desde"] / asoma * 1000) / 1000)
            previo = max(0.0, siguiente["desde"] - asoma * v_doble)
            ini_doble, fin_doble = max(0, cambio - largo), min(duracion, cambio + siguiente["entrada"])
            if v_doble == siguiente["v"] or c2.get("foto"):
                # Después del cambio sigue (apagándose) lo que dura la entrada: que tampoco pase del clip.
                vida_doble = asoma + siguiente["entrada"] / fps
                if c2.get("foto") or previo + vida_doble * v_doble <= c2["duracion"]:
                    fantasmas.append(_fantasma(c2, f"doble-{k}", previo, v_doble, ini_doble, fin_doble, largo // 2, siguiente["entrada"],
                                               pe["doble_opacidad"], W, H, pe, ev["frase"], como=siguiente["capa"]))
            else:
                # Tuvo que asomarse más lento: va en dos tramos. Hasta el cambio, lento; desde el cambio,
                # pegado a la toma de verdad (mismo segundo, misma velocidad) mientras se apaga. Si siguiera
                # lento, se iría quedando atrás de la toma y se vería doble.
                fantasmas.append(_fantasma(c2, f"doble-{k}", previo, v_doble, ini_doble, cambio, largo // 2, 0,
                                           pe["doble_opacidad"], W, H, pe, ev["frase"], como=siguiente["capa"]))
                if fin_doble - cambio >= 2:
                    fantasmas.append(_fantasma(c2, f"doble-{k}b", siguiente["desde"], siguiente["v"], cambio, fin_doble, 0, fin_doble - cambio,
                                               pe["doble_opacidad"], W, H, pe, ev["frase"], como=siguiente["capa"], entrada_minima=0))

    timeline = {
        "version": 4,
        "modo": "pulso",
        "proyecto": p.nombre,
        **{k_: out[k_] for k_ in ("ancho", "alto", "fps", "fondo")},
        "duracion": duracion,
        "audio": audio_de(p, m),
        "meta": {
            "generado": dt.datetime.now().isoformat(timespec="seconds"),
            "bpm": m["bpm"],
            "clips": len(usados),
            "version": p.version,
            "parametros": prm,
        },
        # Los fantasmas van al final: arriba de todo, en `screen`.
        "capas": capas + fantasmas,
    }
    escribir(p.timeline, timeline)
    _resumen(p, m, compases, frases, clip_de_frase, eventos, capas, fantasmas, fps, prm)


def _muro(p: Proyecto, prm: dict, todos: list[dict], m: dict, out: dict, golpe_s: float) -> None:
    """El muro de recuerdos: una cuadrícula de clips distintos que corren a la vez. Cada
    celda cambia de clip cada `muro_golpes` golpes, una celda un golpe después de la
    otra (en diagonal), así los cambios recorren el muro como una ola; nunca hay dos
    celdas con el mismo clip a la vez."""
    W, H, fps = out["ancho"], out["alto"], out["fps"]
    cols, filas = int(prm["muro"][0]), int(prm["muro"][1])
    if int(prm["muro_golpes"]) < 1 or cols < 1 or filas < 1:
        salir("muro: hacen falta al menos una columna, una fila y `muro_golpes` de 1 o más")
    hueco = max(4, round(min(W, H) * 0.008))
    cw, ch = (W - hueco * (cols - 1)) / cols, (H - hueco * (filas - 1)) / filas
    beats = list(m["beats"]) + [m["duracion"]]
    duracion = math.ceil(m["duracion"] * fps)
    n = len(todos)
    # Primero los cambios de todas las celdas; después, en orden de tiempo, el clip de cada
    # cambio: el siguiente de la ronda que no esté ya en otra celda del muro.
    cambios_todos = []
    for j in range(filas):
        for i in range(cols):
            desfase = (i + j) % int(prm["muro_golpes"])
            cambios = [0] + list(range(desfase or int(prm["muro_golpes"]), len(beats) - 1, int(prm["muro_golpes"])))
            for k, b0 in enumerate(cambios):
                b1 = cambios[k + 1] if k + 1 < len(cambios) else len(beats) - 1
                cambios_todos.append((beats[b0] if b0 else 0.0, beats[b1], i, j, k))
    cambios_todos.sort()
    en_muro: dict[tuple[int, int], str] = {}
    ronda = 0
    capas = []
    ultimo_desde: dict[str, float] = {}
    for t0, t1, i, j, k in cambios_todos:
        ocupados = {cid for celda, cid in en_muro.items() if celda != (i, j)}
        for _ in range(n):
            c = todos[ronda % n]
            ronda += 1
            if c["id"] not in ocupados:
                break
        en_muro[(i, j)] = c["id"]
        mx, my = cw / 2 + i * (cw + hueco), ch / 2 + j * (ch + hueco)
        marco = {"x": round(mx, 1), "y": round(my, 1), "ancho": round(cw, 1), "alto": round(ch, 1)}
        ini, fin = round(t0 * fps), min(duracion, round(t1 * fps) + 4)
        vida = (fin - ini) / fps
        v = min(1.0, max(0.4, (c["duracion"] - 0.2) / max(vida, 0.1)))
        previo = ultimo_desde.get(c["id"], -99.0)
        desde = catalogo_clips.mejor_tramo(c, vida * v, evitar=[(previo, previo + vida * v)], borde=prm["borde_toma"])
        # Como en las frases: la toma no pasa del final de su clip (empieza antes; si ni así, va más lenta).
        tope = c["duracion"] - 1 / max(fps, c["fps"])
        if desde + vida * v > tope:
            desde = round(max(0.0, tope - vida * v), 3)
            if vida * v > tope:
                v = tope / vida
        v = math.floor(v * 1000) / 1000  # hacia abajo: redondear hacia arriba la pasaba por milésimas
        ultimo_desde[c["id"]] = desde
        s_ = max(cw / c["w"], ch / c["h"])
        aw, ah = round(c["w"] * s_, 1), round(c["h"] * s_, 1)
        x, y = mx, my
        if prm["seguir"] and "cx" in c["curvas"]:
            x, y = _seguir(c, desde, aw, ah, mx, my, cw, ch)
        capas.append({
            "id": f"{c['id']}#muro{i}{j}-{k}", "img": c["proxy"],
            "video": {"desde": desde, "velocidad": round(v, 3), "fuente": [c["w"], c["h"]], **({"foto": True} if c.get("foto") else {})},
            "ini": ini, "fin": fin, "entrada": 4 if k else round(golpe_s * fps), "salida": 0,
            "x": x, "y": y, "ancho": aw, "alto": ah, "marco": marco,
            "opacidad": 1, "zoom": [1, 1.03], "deriva": [0, 0], "mezcla": "normal", "borde": 0, "seccion": k,
        })
    capas.sort(key=lambda c: c["ini"])
    timeline = {
        "version": 4, "modo": "pulso", "proyecto": p.nombre, **{k_: out[k_] for k_ in ("ancho", "alto", "fps", "fondo")},
        "duracion": duracion, "audio": audio_de(p, m),
        "meta": {"generado": dt.datetime.now().isoformat(timespec="seconds"), "bpm": m["bpm"], "clips": n, "version": p.version, "parametros": prm},
        "capas": capas,
    }
    escribir(p.timeline, timeline)
    print(f"muro de {cols}×{filas}: {len(capas)} tomas de {n} clips, un cambio cada {prm['muro_golpes']} golpes por celda → {p.timeline}")


def _seguir(c: dict, t: float, ancho: float, alto: float, x0: float, y0: float, mw: float, mh: float) -> tuple[float, float]:
    """Dónde poner el centro de la caja del clip para que su centro de interés (en el
    segundo `t`) quede al medio del marco, sin destapar nada: lo que sobra del clip es
    todo lo que se puede correr."""
    i = min(len(c["curvas"]["cx"]) - 1, max(0, int(round(t * c["hz"]))))
    cx, cy = c["curvas"]["cx"][i], c["curvas"]["cy"][i]
    sobra_x, sobra_y = max(0.0, ancho - mw) / 2, max(0.0, alto - mh) / 2
    x = x0 + float(np.clip((0.5 - cx) * ancho, -sobra_x, sobra_x))
    y = y0 + float(np.clip((0.5 - cy) * alto, -sobra_y, sobra_y))
    return round(x, 1), round(y, 1)


def _mitad(c: dict, W: int, H: int, lado: int) -> tuple[float, float, float, float, dict]:
    """Una mitad del lienzo (izquierda/derecha; arriba/abajo si es vertical), con un hueco al medio,
    y el clip cubriéndola: (ancho, alto, x, y, marco)."""
    hueco = max(4, round(min(W, H) * 0.008))
    if W >= H:
        mw, mh = (W - hueco) / 2, H
        mx, my = mw / 2 + lado * (mw + hueco), H / 2
    else:
        mw, mh = W, (H - hueco) / 2
        mx, my = W / 2, mh / 2 + lado * (mh + hueco)
    s = max(mw / c["w"], mh / c["h"])
    return round(c["w"] * s, 1), round(c["h"] * s, 1), mx, my, {"x": round(mx, 1), "y": round(my, 1), "ancho": round(mw, 1), "alto": round(mh, 1)}


def _fantasma(c: dict, nombre: str, desde: float, v: float, ini: int, fin: int, entrada: int, salida: int | None,
              opacidad: float, W: int, H: int, prm: dict, seccion: int, como: dict | None = None, avance: float = 0.0,
              entrada_minima: int = 1) -> dict:
    """Una capa en `screen` encima de todo. Con `como` (la capa de verdad que acompaña) va en su
    mismo lugar y tamaño, donde esa capa está cuando lleva `avance` (0..1) de su vida."""
    ancho, alto, relleno = _encaje(c, W, H, prm["encuadre"])
    x, y, zoom, marco = W / 2, H / 2, [1, 1], None
    if como:
        z = round(como["zoom"][0] + (como["zoom"][1] - como["zoom"][0]) * avance, 4)
        ancho, alto, zoom, marco = como["ancho"], como["alto"], [z, z], como.get("marco")
        x, y = round(como["x"] + como["deriva"][0] * avance, 1), round(como["y"] + como["deriva"][1] * avance, 1)
    vida = max(2, fin - ini)
    return {
        "id": f"{c['id']}#{nombre}",
        "img": c["proxy"],
        # Sin relleno: el fantasma es sólo el clip, encima, en `screen`.
        "video": {"desde": round(max(0.0, desde), 3), "velocidad": v, "fuente": [c["w"], c["h"]], **({"foto": True} if c.get("foto") else {})},
        "ini": ini,
        "fin": fin,
        "entrada": int(min(max(entrada_minima, entrada), vida - 1)),
        "salida": int(min(salida if salida is not None else vida - max(1, entrada), vida - 1)),
        "x": x,
        "y": y,
        "ancho": ancho,
        "alto": alto,
        **({"marco": marco} if marco else {}),
        "opacidad": opacidad,
        "zoom": zoom,
        "deriva": [0, 0],
        "mezcla": "screen",
        "borde": 0,
        "seccion": seccion,
    }


def _resumen(p, m, compases, frases, clip_de_frase, eventos, capas, fantasmas, fps, prm) -> None:
    vidas = np.array([(c["fin"] - c["ini"]) / fps for c in capas])
    print(f"{len(capas)} tomas de {len({c['id'] for c in clip_de_frase})} clips en {len(frases)} frases, "
          f"{m['duracion']:.1f} s a {m['bpm']:.1f} BPM → {p.timeline}")
    print(f"  la toma más breve dura {vidas.min():.2f} s; mediana {np.median(vidas):.2f} s; "
          f"{len(fantasmas)} fantasmas (doble/estela)")
    for fi, f in enumerate(frases):
        evs = [e for e in eventos if e["frase"] == fi]
        e = np.mean([compases[i]["e"] for i in f])
        c = clip_de_frase[fi]
        print(f"  frase {fi:>2} {compases[f[0]]['ini']:6.1f} s  {len(f)} compases  energía {e:.2f}  "
              f"{c['id'][:26]:26}  {len(evs):>2} tomas  ×{evs[0]['v']:.2f}  entra con {evs[0]['entrada']} cuadros"
              f"{'  calma' if evs[0]['calma'] else ''}")
