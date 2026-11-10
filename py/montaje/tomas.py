"""La lista de tomas: lo que hay que producir para un guion, antes de tener el material.

El 22 sacó un 6 de 10 y Miguel dio la razón: «estamos usando material ya hecho, nada producido
específicamente para este video». Esto invierte el orden. Con la canción analizada y el guion en
`tramos` (cada uno con lo que tiene que pasar en `pasa`, en palabras de Miguel, y sus `estilos`),
el motor parte la canción en las mismas frases que después monta (`pulso.frases_del_guion`) y dice,
por cada una, qué toma hace falta:

- su número (`T3-02`: tramo 3, segunda toma), con el que se nombra el archivo;
- cuánto dura en pantalla y cuántos segundos de clip pide (a la velocidad que va a ir);
- qué movimiento pide la música (la energía de esa frase) y cómo se va a ver en cámara lenta;
- cómo entra y cómo sale (la transición del tramo, el fantasma, la foto que despierta) y lo que eso
  le pide a la imagen;
- lo que los estilos del tramo piden evitar.

    python montaje.py tomas <p> [--version v]      → proyectos/<p>/TOMAS.md
    python montaje.py tomas <p> --estado           qué tomas ya llegaron a las carpetas de clips

Lo que se ve en cada toma lo decide Miguel: la lista sólo dice lo que la música y el montaje le
piden. Los clips se nombran empezando por su número («T3-02 pareja en la playa.mp4») y van a una
carpeta de `clips` del proyecto; en `tramos`, `"material": ["T3-"]` los toma en orden.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path

import numpy as np

from . import estilos as catalogo
from . import musica, pulso
from .clips import EXTENSIONES, carpetas
from .rutas import Proyecto

#: Los segundos que trae un clip de video de Midjourney (V1); con «extend», unos 4 más cada vez.
CLIP_MJ = 5.2

#: Lo que cada transición le pide a la imagen que entra.
PIDE_LA_ENTRADA = {
    "fundido": "",
    "cortina": "un borde que barre: mejor si lo importante no está pegado a ese lado",
    "iris": "un sujeto claro: el círculo se abre desde él",
    "empuje": "entra empujando: que se lea aunque entre de lado",
    "destello": "entra con un fogonazo: aguanta bien una luz fuerte",
    "zoom": "llega desde cerca: que el centro tenga detalle",
    "persiana": "entra en franjas",
}


def proporcion(w: int, h: int) -> str:
    """1620×1080 → «3:2»; 1080×1920 → «9:16»."""
    g = math.gcd(int(w), int(h)) or 1
    return f"{int(w) // g}:{int(h) // g}"


def movimiento(e: float, calma: float, pico: float) -> tuple[str, str]:
    """Qué movimiento pide la música (en palabras) y el ajuste de movimiento de Midjourney que le va."""
    if e < calma:
        return "casi quieta: algo que respira, un paneo muy lento", "low"
    if e >= pico:
        return "viva: alguien que camina, agua, viento, la cámara que se mueve", "high"
    return "suave y continua: un paneo, un acercamiento, gente que conversa", "high" if e > (calma + pico) / 2 else "low"


def lista(p: Proyecto) -> tuple[list[dict], list[dict], dict]:
    """Las tomas, los tramos del guion y la canción."""
    prm = {**pulso.POR_DEFECTO, **p.cfg.get("montaje", {})}
    m = musica.cargar(p)
    compases = pulso._compases(m)
    frases, tramo_de, prm_compas = pulso.frases_del_guion(m, prm, compases)
    golpe = 60 / m["bpm"]
    tramos = prm.get("tramos") or []
    tomas: list[dict] = []
    n_en: Counter = Counter()
    for fi, frase in enumerate(frases):
        pf = prm_compas(frase[0])
        k = tramo_de(frase[0])
        t0, t1 = compases[frase[0]]["ini"], compases[frase[-1]]["fin"]
        e = float(np.mean([compases[i]["e"] for i in frase]))
        calma = e < pf["umbral_calma"]
        segs = pulso._segmentos(compases, frase, pf)
        vels = [pulso._velocidad(ee, pf) for _, _, ee in segs]
        largo = sum(b - a for a, b, _ in segs)
        v = sum((b - a) * vv for (a, b, _), vv in zip(segs, vels)) / max(1e-6, largo)
        pisado = golpe * ((pf["fundido_calma_golpes"] if calma else pf["fundido_golpes"]) + pf["estela_golpes"])
        material = sum((b - a) * vv for (a, b, _), vv in zip(segs, vels)) + pisado * max(vels) + 2 * pf["borde_toma"]
        n_en[k] += 1
        mov, mj = movimiento(e, pf["umbral_calma"], pf["umbral_pico"])
        entra = "sale del negro" if fi == 0 else (pf.get("transicion") or "fundido")
        notas = []
        if fi and PIDE_LA_ENTRADA.get(entra):
            notas.append(PIDE_LA_ENTRADA[entra])
        if float(pf.get("congelar_golpes") or 0) > 0:
            notas.append("entra quieta y arranca en el golpe: el primer cuadro tiene que valer como foto")
        if float(pf.get("doble_golpes") or 0) > 0:
            notas.append("va en doble exposición con la siguiente: zonas oscuras o un cielo liso dejan ver la otra")
        if float(pf.get("estela_golpes") or 0) > 0:
            notas.append("se queda un momento como estela sobre la que sigue")
        tomas.append({
            "id": f"T{k + 1}-{n_en[k]:02d}" if k >= 0 else f"T0-{n_en[k]:02d}",
            "tramo": k, "desde": round(t0, 2), "hasta": round(t1, 2), "compases": len(frase), "energia": round(e, 2),
            "musica": "calma" if calma else "alta" if e >= pf["umbral_pico"] else "media",
            "velocidad": round(v, 2), "segundos_de_clip": round(material, 1), "alcanza_mj": material <= CLIP_MJ,
            "movimiento": mov, "motion": mj, "entra": entra, "notas": notas,
        })
    return tomas, tramos, m


def _mmss(t: float) -> str:
    return f"{int(t // 60)}:{t % 60:04.1f}".replace(".", ",")


def _n(x: float, d: int = 1) -> str:
    return f"{x:.{d}f}".replace(".", ",")


#: Las capas de texto: lo que piden evitar (letras, tamaños) no tiene que ver con producir imágenes.
CAPAS_DE_TEXTO = {"titulo", "credito", "rotulos", "cuenta"}


def escribir(p: Proyecto) -> Path:
    tomas, tramos, m = lista(p)
    estilos = {e["id"]: e for e in catalogo.leer()}
    out = p.cfg.get("salida", {})
    ar = proporcion(out.get("ancho", 1920), out.get("alto", 1080))
    cortas = sum(not t["alcanza_mj"] for t in tomas)
    filas = [
        f"# {p.cfg.get('titulo', p.nombre)} · lista de tomas",
        "",
        "> **La escribe `python montaje.py tomas`**: no se corrige a mano (se corrige el guion y se vuelve a",
        "> correr). Dice lo que la música y el montaje le piden a cada toma; lo que se ve lo decide Miguel.",
        "",
        f"{len(tomas)} tomas para {m['archivo']} ({_mmss(m['duracion'])}, {m['bpm']:.0f} BPM), en {ar}"
        + (f" (versión {p.version}). " if p.version else ". ")
        + (f"{cortas} usan más de {_n(CLIP_MJ)} s de clip (lo que trae uno de Midjourney): hay que extenderlas o irán más lentas."
           if cortas else f"A todas les alcanza un clip de Midjourney ({_n(CLIP_MJ)} s)."),
        "",
        "**En pantalla** es la velocidad a la que va a ir cada toma: a ×0,45 lo que dura un segundo se ve en dos, y lo que se",
        "mueve se ve flotando. Por eso en la banda conviene generar con más movimiento del que se quiere ver. **Se usan** son",
        "los segundos del clip que entran al video (con los fundidos); `--motion` es el ajuste de movimiento de Midjourney.",
        "",
        "**Cómo nombrar los archivos:** empezando por el número de la toma («T3-02 pareja en la playa.mp4»), en una",
        f"carpeta de `clips` del proyecto. `python montaje.py tomas {p.nombre} --estado` dice cuáles faltan.",
        "",
    ]
    grupos: dict[int, list[dict]] = {}
    for t in tomas:
        grupos.setdefault(t["tramo"], []).append(t)
    for k, ts in grupos.items():
        tr = tramos[k] if 0 <= k < len(tramos) else {}
        nombre = tr.get("nombre", "fuera de los tramos del guion")
        filas += [f"## T{k + 1} · {nombre}", "", f"{_mmss(ts[0]['desde'])}–{_mmss(ts[-1]['hasta'])} · {len(ts)} {'toma' if len(ts) == 1 else 'tomas'}"]
        if tr.get("pasa"):
            filas += ["", f"**Lo que pasa:** {tr['pasa']}"]
        evitar = [f"{x} ({i})" for i in tr.get("estilos") or [] if (estilos.get(i, {}).get("tecnica") or {}).get("capa") not in CAPAS_DE_TEXTO
                  for x in (estilos.get(i, {}).get("evitar") or [])]
        if tr.get("estilos"):
            filas += ["", f"**Estilos:** {', '.join(f'`{i}`' for i in tr['estilos'])}"]
        if evitar:
            filas += ["", "**Evitar:** " + "; ".join(evitar)]
        filas += ["", "| Toma | Canción | Compases | Música | En pantalla | Se usan | Movimiento | Entra | Ojo |",
                  "|---|---|---|---|---|---|---|---|---|"]
        for t in ts:
            usa = f"{_n(t['segundos_de_clip'])} s{'' if t['alcanza_mj'] else ' · extender'}"
            filas.append(f"| **{t['id']}** | {_mmss(t['desde'])}–{_mmss(t['hasta'])} | {t['compases']} | {t['musica']} | ×{_n(t['velocidad'], 2)} | "
                         f"{usa} | {t['movimiento']} · `--motion {t['motion']}` | {t['entra']} | {'; '.join(t['notas'])} |")
        filas.append("")
    filas += ["## Para el montaje", "", "Con los clips en su carpeta, cada tramo los toma en orden:", "", "```json"]
    filas += [f'{{"nombre": "{(tramos[k] if 0 <= k < len(tramos) else {}).get("nombre", "")}", "material": ["T{k + 1}-"]}},' for k in grupos if k >= 0]
    filas += ["```", ""]
    destino = p.dir / ("TOMAS.md" if not p.version else f"TOMAS-{p.version}.md")
    destino.write_text("\n".join(filas), encoding="utf-8")
    print(f"{len(tomas)} tomas en {len(grupos)} tramos; {cortas} piden extender el clip → {destino}")
    return destino


PATRON = re.compile(r"^T(\d+)-(\d+)\b", re.IGNORECASE)


def estado(p: Proyecto) -> None:
    """Qué tomas ya tienen su clip en las carpetas del proyecto, cuáles faltan y qué archivos no son de ninguna."""
    tomas, _, _ = lista(p)
    ids = {t["id"].upper() for t in tomas}
    hay: dict[str, list[str]] = {}
    sueltos = []
    for carpeta in carpetas(p):
        for f in sorted(carpeta.iterdir()):
            if not f.is_file() or f.suffix.lower() not in EXTENSIONES:
                continue
            mt = PATRON.match(f.stem)
            clave = f"T{int(mt.group(1))}-{int(mt.group(2)):02d}" if mt else None
            if clave and clave in ids:
                hay.setdefault(clave, []).append(f.name)
            elif mt:
                sueltos.append(f.name)
    faltan = [t["id"] for t in tomas if t["id"].upper() not in hay]
    print(f"{len(hay)} de {len(tomas)} tomas tienen clip; faltan {len(faltan)}")
    if faltan:
        print("  faltan: " + ", ".join(faltan))
    dobles = {k: v for k, v in hay.items() if len(v) > 1}
    if dobles:
        print("  con más de un clip (entra el primero por nombre): " + ", ".join(f"{k} ({len(v)})" for k, v in dobles.items()))
    if sueltos:
        print("  numerados pero sin toma en este guion: " + ", ".join(sueltos))
