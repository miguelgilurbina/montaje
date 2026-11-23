"""Las recetas guardadas: combinaciones con nombre de una base de la mesa analógica y sus gestos, para pedirlas de una
vez («la familia en Super 8», «la película en la pared que se quema»).

Miguel, el 2026-11-22: «También armar templates de trabajo para poder armar trabajo más adelante», y en la tarjeta
eligió los tres moldes: las plantillas de piezas (`plantillas.py`), las recetas guardadas (esto) y el molde de
experimento (`experimento.py`).

Una receta es `recetas/<id>.json`:

    {"nombre": "La familia en Super 8", "frase": "…", "para": ["mostrar el archivo"],
     "base": "super-8-de-la-familia", "gestos": ["el-empalme", "se-acaba-el-rollo"]}

`base` es un estilo analógico que no es gesto; `gestos`, estilos gesto, en el orden en que se ponen. Se pide como
cualquier cadena de la galería:

    python montaje.py analogo <video> --cadena la-familia-en-super-8
    python montaje.py recetas            # las lista y las valida

Una receta no tiene veredicto propio: vale lo que valen su base y sus gestos (si alguno está rechazado, la receta lo
dice). Lo que se junta queda donde va cada aparato (`analogo.componer`).
"""

from __future__ import annotations

import json
from pathlib import Path

from .rutas import RAIZ, salir

RECETAS = RAIZ / "recetas"
CAMPOS = ("nombre", "frase", "base", "gestos")


def leer() -> list[dict]:
    if not RECETAS.exists():
        return []
    sale = []
    for f in sorted(RECETAS.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        d["id"] = f.stem
        sale.append(d)
    return sale


def buscar(ident: str) -> dict | None:
    f = RECETAS / f"{ident}.json"
    if not f.exists():
        return None
    d = json.loads(f.read_text(encoding="utf-8"))
    d["id"] = ident
    return d


def errores(r: dict, estilos: list[dict]) -> list[str]:
    """Lo que está mal en una receta. Vacío = se puede usar."""
    por_id = {e["id"]: e for e in estilos}
    mal = [f"falta `{c}`" for c in CAMPOS if c not in r]
    if mal:
        return mal
    if r["id"] in por_id:
        mal.append(f"se llama como un estilo («{r['id']}»): una receta necesita un nombre propio")
    base = por_id.get(r["base"])
    if base is None or base["tecnica"].get("comando") != "analogo" or base["tecnica"].get("gesto"):
        mal.append(f"`base`: «{r['base']}» no es un estilo analógico que no sea gesto")
    if not isinstance(r["gestos"], list) or not r["gestos"]:
        mal.append("`gestos`: una lista de estilos gesto (al menos uno; sin gestos, la receta es su base)")
    else:
        for g in r["gestos"]:
            eg = por_id.get(g)
            if eg is None or not eg["tecnica"].get("gesto"):
                mal.append(f"`gestos`: «{g}» no es un gesto de la galería")
    return mal


def estado(r: dict, estilos: list[dict]) -> str:
    """Lo que vale la receta: lo peor entre su base y sus gestos (rechazado < a medias < propuesta < aprobado)."""
    orden = {"rechazado": 0, "a medias": 1, "propuesta": 2, "pedido": 2, "aprobado": 3}
    por_id = {e["id"]: e for e in estilos}
    partes = [por_id[i] for i in [r["base"], *r["gestos"]] if i in por_id]
    if not partes:
        return "propuesta"
    return min((p["estado"] for p in partes), key=lambda x: orden.get(x, 2))


def cadena(ident: str):
    """La cadena lista para `procesar`, y su nombre: la base con sus gestos encima."""
    from . import analogo

    r = buscar(ident)
    if r is None:
        salir(f"no hay una receta «{ident}» en recetas/")
    return analogo.resolver_cadena(r["base"], r["gestos"])[0], ident


def listar() -> int:
    """Las recetas, con lo que valen; devuelve cuántas tienen errores."""
    from . import estilos as galeria

    estilos = galeria.leer()
    recetas = leer()
    con_errores = 0
    for r in recetas:
        mal = errores(r, estilos)
        if mal:
            con_errores += 1
            print(f"✗ {r['id']}")
            for m in mal:
                print(f"    {m}")
            continue
        print(f"{estado(r, estilos):10s} {r['id']:36s} {r['base']} + {' + '.join(r['gestos'])}")
        print(f"           {r['frase']}")
    print(f"\n{len(recetas)} recetas en {RECETAS}" + (f" · {con_errores} con errores" if con_errores else ""))
    return con_errores
