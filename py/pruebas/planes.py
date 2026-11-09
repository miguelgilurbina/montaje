"""La red para cambiar el motor: planificar todo en una carpeta aparte y comparar antes y después.

Un cambio en `pulso.py` o `clips.py` puede cambiarle la planificación a versiones que ya
se renderizaron y que Miguel ya juzgó, sin que ninguna prueba lo note. Esto planifica
todas las versiones de todos los experimentos con clips **fuera del repo** (no toca
ningún timeline) y dice, versión por versión, qué capas cambiaron y en qué.

    python py/pruebas/planes.py foto <carpeta>          # planifica todo y lo guarda ahí
    python py/pruebas/planes.py comparar <antes> <despues>
    python py/pruebas/planes.py repo <carpeta>          # una foto contra los timelines del repo

El uso: una foto antes de tocar el motor, otra después, y `comparar`. Lo que cambie se
explica con medidas, se replanifica en el repo y se vuelve a renderizar con otro nombre.
El 2026-11-09 detectó, entre otras cosas, un arreglo que cambiaba sin querer una pieza
que no tenía nada que ver.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "py"))


def proyectos_con_clips() -> list[str]:
    """Los experimentos que planifican clips y tienen con qué (su análisis de música y el catálogo)."""
    from montaje import clips
    from montaje.rutas import PROYECTOS, Proyecto

    nombres = []
    for carpeta in sorted(PROYECTOS.iterdir()):
        archivo = carpeta / "proyecto.json"
        if not archivo.exists():
            continue
        cfg = json.loads(archivo.read_text(encoding="utf-8"))
        if not cfg.get("clips"):
            continue
        p = Proyecto(carpeta.name)
        if clips.ruta_catalogo(p).exists() and (p.salidas / "analisis" / "musica.json").exists():
            nombres.append(carpeta.name)
    return nombres


def limpio(tl: dict) -> dict:
    tl = json.loads(json.dumps(tl))
    tl.get("meta", {}).pop("generado", None)
    return tl


def foto(destino: Path) -> None:
    from montaje import planificar as plan
    from montaje.rutas import Proyecto

    destino.mkdir(parents=True, exist_ok=True)
    original = Proyecto.timeline
    try:
        for nombre in proyectos_con_clips():
            cfg = json.loads((RAIZ / "proyectos" / nombre / "proyecto.json").read_text(encoding="utf-8"))
            for v in [None, *cfg.get("versiones", {})]:
                salida = destino / f"{nombre}__{v or 'base'}.json"
                Proyecto.timeline = property(lambda self, s=salida: s)  # nada se escribe en el repo
                try:
                    with contextlib.redirect_stdout(io.StringIO()):
                        plan.planificar(Proyecto(nombre, v))
                except SystemExit as e:
                    salida.write_text(json.dumps({"error": str(e)}), encoding="utf-8")
                except Exception as e:  # noqa: BLE001  una versión rota también es un dato
                    salida.write_text(json.dumps({"error": repr(e)}), encoding="utf-8")
    finally:
        Proyecto.timeline = original
    print(f"{len(list(destino.glob('*.json')))} planes en {destino}")


def diferencias(a: dict, b: dict) -> str:
    """En qué difieren dos planes, en una línea; vacío si son el mismo."""
    if a == b:
        return ""
    if "error" in a or "error" in b:
        return f"error: {a.get('error')} → {b.get('error')}"
    ca, cb = {c["id"]: c for c in a.get("capas", [])}, {c["id"]: c for c in b.get("capas", [])}
    salen, entran = sorted(set(ca) - set(cb)), sorted(set(cb) - set(ca))
    cambiadas = [i for i in ca if i in cb and ca[i] != cb[i]]
    fantasmas = [i for i in cambiadas if "#doble-" in i or "#estela-" in i]
    claves = sorted({k for i in cambiadas for k in set(ca[i]) | set(cb[i]) if ca[i].get(k) != cb[i].get(k)})
    otros = [k for k in sorted(set(a) | set(b)) if k != "capas" and a.get(k) != b.get(k)]
    return (f"capas {len(ca)}→{len(cb)} · cambiadas {len(cambiadas)} (de ellas, fantasmas {len(fantasmas)}) · salen {len(salen)} · entran {len(entran)}"
            f" · claves {claves}" + (f" · además {otros}" if otros else ""))


def comparar(antes: Path, despues: Path) -> int:
    iguales, distintos = 0, 0
    for f in sorted(antes.glob("*.json")):
        g = despues / f.name
        if not g.exists():
            print(f"{f.stem}: falta en {despues}")
            distintos += 1
            continue
        d = diferencias(limpio(json.loads(f.read_text(encoding="utf-8"))), limpio(json.loads(g.read_text(encoding="utf-8"))))
        if d:
            print(f"{f.stem}: {d}")
            distintos += 1
        else:
            iguales += 1
    print(f"{iguales} iguales, {distintos} distintos")
    return distintos


def con_repo(carpeta: Path) -> int:
    iguales, distintos = 0, 0
    for f in sorted(carpeta.glob("*.json")):
        nombre, v = f.stem.split("__")
        repo = RAIZ / "proyectos" / nombre / ("timeline.json" if v == "base" else f"timeline-{v}.json")
        if not repo.exists():
            continue
        d = diferencias(limpio(json.loads(repo.read_text(encoding="utf-8"))), limpio(json.loads(f.read_text(encoding="utf-8"))))
        if d:
            print(f"{f.stem}: {d}")
            distintos += 1
        else:
            iguales += 1
    print(f"{iguales} iguales al repo, {distintos} distintos")
    return distintos


if __name__ == "__main__":
    orden = sys.argv[1:]
    if len(orden) == 2 and orden[0] == "foto":
        foto(Path(orden[1]))
    elif len(orden) == 3 and orden[0] == "comparar":
        comparar(Path(orden[1]), Path(orden[2]))
    elif len(orden) == 2 and orden[0] == "repo":
        con_repo(Path(orden[1]))
    else:
        raise SystemExit(__doc__)
