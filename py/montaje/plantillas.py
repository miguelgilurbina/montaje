"""Las plantillas de piezas: un tipo de video ya pensado (el archivo de la familia, el reel vertical, la cortina de
radio), que se le pone a un proyecto con su canción y su material y deja la pieza armada por tramos.

Miguel, el 2026-11-22: «También armar templates de trabajo para poder armar trabajo más adelante». Eligió los tres
moldes: estas plantillas, las recetas guardadas (`recetas.py`) y el molde de experimento (`experimento.py`).

Una plantilla es `plantillas/<id>.json` (ver `plantillas/README.md`): los tramos de la pieza en partes de la canción
(de 0 a 1), cada uno con los estilos de la galería que lo arman y lo que pasa; las capas que van sobre todo; los
textos que faltan escribir; y la mesa analógica que va después del render (en ventanas). El guion (`guion.py`) elige
solo, tramo por tramo, el primer estilo que sirve; una plantilla es una decisión tomada de antemano.

    python montaje.py plantillas                          # las lista y las valida
    python montaje.py plantilla <p> <id> --crear          # un proyecto nuevo con la plantilla (falta la canción)
    python montaje.py plantilla <p> <id>                  # con la canción analizada: los tramos en sus segundos

Sin `--escribir` muestra lo que pondría; con `--escribir` lo deja en proyecto.json (`montaje.tramos` y `sintesis`)
y escribe `PIEZA.md`: los tramos, los textos que faltan y los comandos de la mesa analógica para después del render.
Si el proyecto ya tiene tramos, no los pisa sin `--forzar`.
"""

from __future__ import annotations

import json
import re
import shlex

from . import estilos as catalogo
from .rutas import PROYECTOS, RAIZ, Proyecto, escribir_json, salir

PLANTILLAS = RAIZ / "plantillas"
CAMPOS = ("nombre", "frase", "material", "salida", "montaje", "tramos")


def leer() -> list[dict]:
    if not PLANTILLAS.exists():
        return []
    sale = []
    for f in sorted(PLANTILLAS.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        d["id"] = f.stem
        sale.append(d)
    return sale


def buscar(ident: str) -> dict:
    f = PLANTILLAS / f"{ident}.json"
    if not f.exists():
        hay = ", ".join(x["id"] for x in leer()) or "ninguna"
        salir(f"no hay una plantilla «{ident}» en plantillas/ (hay: {hay})")
    d = json.loads(f.read_text(encoding="utf-8"))
    d["id"] = ident
    return d


def _parte(x) -> bool:
    return isinstance(x, list) and len(x) == 2 and all(isinstance(v, (int, float)) for v in x) and 0 <= x[0] < x[1] <= 1


def _cadena_valida(c, estilos: dict[str, dict]) -> bool:
    from . import recetas

    if isinstance(c, list):
        return True
    e = estilos.get(c)
    return (e is not None and e["tecnica"].get("comando") == "analogo") or recetas.buscar(c) is not None


def errores(pl: dict, estilos: list[dict]) -> list[str]:
    """Lo que está mal en una plantilla. Vacío = se puede usar."""
    from .guion import capa_de, receta_de_tramo

    por_id = {e["id"]: e for e in estilos}
    mal = [f"falta `{c}`" for c in CAMPOS if c not in pl]
    if mal:
        return mal
    fin = 0.0
    for n, t in enumerate(pl["tramos"]):
        nombre = t.get("nombre", f"tramo {n + 1}")
        if not _parte(t.get("parte")):
            mal.append(f"{nombre}: `parte` es [desde, hasta] entre 0 y 1")
            continue
        if abs(t["parte"][0] - fin) > 1e-6:
            mal.append(f"{nombre}: empieza en {t['parte'][0]}, y el anterior terminó en {fin} (los tramos van seguidos)")
        fin = t["parte"][1]
        ids = t.get("estilos") or []
        for i in ids:
            if i not in por_id:
                mal.append(f"{nombre}: no hay un estilo «{i}»")
            elif por_id[i]["estado"] == "rechazado":
                mal.append(f"{nombre}: «{i}» está rechazado")
        if not any(i in por_id and receta_de_tramo(por_id[i]) is not None for i in ids):
            mal.append(f"{nombre}: ningún estilo arma el tramo (hace falta uno de `pulso`)")
    if pl["tramos"] and abs(fin - 1) > 1e-6:
        mal.append(f"los tramos terminan en {fin}: tienen que llegar a 1 (el final de la canción)")
    for i in pl.get("capas", []):
        if i not in por_id or capa_de(por_id[i], 0, 1) is None:
            mal.append(f"`capas`: «{i}» no es una capa de la galería que vaya sola (sin texto)")
    for x in pl.get("textos", []):
        if x.get("estilo") not in por_id or not _parte(x.get("parte")) or not x.get("texto"):
            mal.append(f"`textos`: cada uno con `estilo`, `parte` y `texto` (lo que falta escribir): {x}")
    for x in pl.get("analogo", []):
        if not _parte(x.get("parte")) or not _cadena_valida(x.get("cadena"), por_id):
            mal.append(f"`analogo`: «{x.get('cadena')}» no es un estilo analógico ni una receta, o falta `parte`")
    f = pl.get("formato")
    if f is not None and (f not in por_id or not isinstance(por_id[f]["tecnica"].get("salida"), str)):
        mal.append(f"`formato`: «{f}» no es un estilo de formato (con `salida`)")
    return mal


def _medidas(salida: str) -> tuple[int, int]:
    m = re.fullmatch(r"(\d+)x(\d+)", salida)
    if not m:
        salir(f"no entiendo la salida «{salida}» (ancho x alto)")
    return int(m.group(1)), int(m.group(2))


def crear(nombre: str, pl: dict) -> None:
    """Un proyecto nuevo con lo de la plantilla. Falta la canción y el material: eso lo pone quien lo hace."""
    carpeta = PROYECTOS / nombre
    if (carpeta / "proyecto.json").exists():
        salir(f"el proyecto «{nombre}» ya existe: sin --crear, la plantilla se le pone encima")
    salida = dict(pl["salida"])
    montaje = dict(pl["montaje"])
    if pl.get("formato"):
        from .guion import receta_de_tramo

        f = next(e for e in catalogo.leer() if e["id"] == pl["formato"])
        salida["ancho"], salida["alto"] = _medidas(f["tecnica"]["salida"])
        montaje.update({k: v for k, v in (receta_de_tramo(f) or {}).items() if k in ("encuadre", "seguir")})
    cfg = {"titulo": f"{nombre} · {pl['nombre']}", "idea": pl["frase"], "plantilla": pl["id"], "biblioteca": nombre,
           "musica": "", "salida": salida, "montaje": montaje}
    if pl.get("tono"):
        cfg["tono"] = pl["tono"]
    if pl["material"] in ("clips", "mixto"):
        cfg["clips"] = ["clips"]
    escribir_json(carpeta / "proyecto.json", cfg)
    print(f"→ {carpeta / 'proyecto.json'}")
    print("Lo que sigue:")
    print(f"  1. la canción en ~/Videos/montaje/{nombre}/ y su ruta en `musica` (dentro de la biblioteca)")
    if pl["material"] in ("clips", "mixto"):
        print(f"  2. los clips en ~/Videos/montaje/{nombre}/clips/, y: python montaje.py clips {nombre}")
    print(f"  3. python montaje.py musica {nombre}")
    print(f"  4. python montaje.py plantilla {nombre} {pl['id']} --escribir")


def armar(p: Proyecto, pl: dict) -> dict:
    """Los tramos y las capas de la plantilla en los segundos de la canción del proyecto, los textos que faltan y los
    comandos de la mesa para después del render."""
    from . import musica
    from .guion import capa_de, receta_de_tramo

    m = musica.cargar(p)
    dura = float(m["duracion"])
    unos = [float(u) for u in (m.get("primeros_tiempos") or [])]

    def seg(x: float) -> float:
        """Una parte de la canción en segundos, en el «uno» más cercano (los tramos valen por compases enteros)."""
        if x <= 0:
            return 0.0
        if x >= 1:
            return round(dura, 2)
        s = x * dura
        return round(min(unos, key=lambda u: abs(u - s)) if unos else s, 2)

    estilos = {e["id"]: e for e in catalogo.leer()}
    tramos, sintesis = [], []
    for t in pl["tramos"]:
        desde, hasta = seg(t["parte"][0]), seg(t["parte"][1])
        principal = next(estilos[i] for i in t["estilos"] if receta_de_tramo(estilos[i]) is not None)
        tramo = {"nombre": t["nombre"], "desde": desde, "hasta": hasta, **receta_de_tramo(principal),
                 "estilos": t["estilos"], "pasa": t.get("pasa", "")}
        tramos.append(tramo)
        for i in t["estilos"]:
            capa = capa_de(estilos[i], desde, hasta)
            if capa is not None:
                sintesis.append(capa)
    for i in pl.get("capas", []):
        sintesis.append(capa_de(estilos[i], 0.0, round(dura, 2)))
    textos = [{**x, "desde": seg(x["parte"][0]), "hasta": seg(x["parte"][1])} for x in pl.get("textos", [])]
    mesa = []
    # Encadenados: cada paso de la mesa parte de lo que dejó el anterior, y el último deja `<render>-mesa.mp4`.
    entrada = "<render>.mp4"
    pasos = pl.get("analogo", [])
    for n, x in enumerate(pasos):
        cadena = x["cadena"] if isinstance(x["cadena"], str) else json.dumps(x["cadena"], ensure_ascii=False)
        a, b = seg(x["parte"][0]), seg(x["parte"][1])
        sale = "<render>-mesa.mp4" if n == len(pasos) - 1 else f"<render>-mesa-{n + 1}.mp4"
        mesa.append({**x, "desde": a, "hasta": b,
                     "comando": f"python montaje.py analogo {entrada} --cadena {shlex.quote(cadena)} --ventana {a:g} {b:g} "
                                f"--golpes {p.nombre} --salida {sale}"})
        entrada = sale
    return {"tramos": tramos, "sintesis": sintesis, "textos": textos, "mesa": mesa, "dura": dura}


def pieza_md(p: Proyecto, pl: dict, armado: dict) -> str:
    estilos = {e["id"]: e for e in catalogo.leer()}
    nombre = lambda i: estilos[i]["nombre"] if i in estilos else i  # noqa: E731
    filas = [f"| {t['nombre']} | {t['desde']:g}–{t['hasta']:g} | {t['pasa']} | {', '.join(nombre(i) for i in t['estilos'])} |"
             for t in armado["tramos"]]
    lineas = [
        f"# {p.cfg.get('titulo', p.nombre)} · la pieza",
        "",
        f"> De la plantilla **{pl['nombre']}** (`plantillas/{pl['id']}.json`): {pl['frase']}",
        "> Los tramos ya están en proyecto.json; lo que pasa en cada uno se puede reescribir aquí y en `pasa`.",
        "",
        "## Los tramos",
        "",
        "| Tramo | Segundos | Lo que pasa | Estilos |",
        "|---|---|---|---|",
        *filas,
        "",
    ]
    if armado["textos"]:
        lineas += ["## Los textos que faltan", "",
                   *[f"- **{nombre(x['estilo'])}** ({x['desde']:g}–{x['hasta']:g} s): {x['texto']}. Va en `sintesis` con su texto."
                     for x in armado["textos"]], ""]
    if armado["mesa"]:
        lineas += ["## Después del render: la mesa analógica", "",
                   "Sólo en estas ventanas (una imagen protagonista de la galería no lleva efectos analógicos encima). "
                   "`<render>` es el render del proyecto, sin la extensión; los pasos van en orden, cada uno sobre el "
                   "anterior:", "",
                   *[f"- {nombre(x['cadena']) if isinstance(x['cadena'], str) else 'cadena propia'} "
                     f"({x['desde']:g}–{x['hasta']:g} s):\n\n  ```\n  {x['comando']}\n  ```" for x in armado["mesa"]], ""]
    lineas += ["## Los pasos", "",
               "0. El material de cada tramo (`material` en proyecto.json: las palabras del nombre de los clips que entran). "
               "Sin él, si hay más clips que frases, el motor parte las frases para que entren todos, y las tomas largas "
               "de la plantilla se acortan.",
               f"1. `python montaje.py planificar {p.nombre}`", f"2. `python montaje.py render {p.nombre} --preview`"]
    if armado["mesa"]:
        lineas.append("3. la mesa analógica, arriba")
    lineas += [*[f"- {x}" for x in pl.get("pasos", [])], ""]
    return "\n".join(lineas)


def aplicar(nombre: str, ident: str, crear_: bool = False, escribir: bool = False, forzar: bool = False) -> None:
    pl = buscar(ident)
    mal = errores(pl, catalogo.leer())
    if mal:
        salir(f"la plantilla «{ident}» tiene errores:\n  " + "\n  ".join(mal))
    if crear_:
        crear(nombre, pl)
        return
    p = Proyecto(nombre)
    armado = armar(p, pl)
    print(f"«{pl['nombre']}» en {p.nombre} ({armado['dura']:.1f} s de canción):")
    for t in armado["tramos"]:
        print(f"  {t['desde']:6.2f}–{t['hasta']:6.2f}  {t['nombre']}: {', '.join(t['estilos'])}")
    for c in armado["sintesis"]:
        print(f"  capa {c['tipo']} {c['desde']:g}–{c['hasta']:g}")
    for x in armado["textos"]:
        print(f"  falta el texto · {x['estilo']} {x['desde']:g}–{x['hasta']:g}: {x['texto']}")
    for x in armado["mesa"]:
        print(f"  después · {x['comando']}")
    if not escribir:
        print("\n(sin --escribir no se toca nada)")
        return
    cfg = json.loads((p.dir / "proyecto.json").read_text(encoding="utf-8"))
    if cfg.get("montaje", {}).get("tramos") and not forzar:
        salir(f"{p.nombre} ya tiene tramos en proyecto.json: para reemplazarlos, --forzar")
    cfg["montaje"] = {**cfg.get("montaje", {}), "tramos": armado["tramos"]}
    cfg["sintesis"] = armado["sintesis"]
    cfg["plantilla"] = ident
    escribir_json(p.dir / "proyecto.json", cfg)
    (p.dir / "PIEZA.md").write_text(pieza_md(p, pl, armado), encoding="utf-8")
    print(f"→ {p.dir / 'proyecto.json'}\n→ {p.dir / 'PIEZA.md'}")


def listar() -> int:
    estilos = catalogo.leer()
    plantillas = leer()
    con_errores = 0
    for pl in plantillas:
        mal = errores(pl, estilos)
        if mal:
            con_errores += 1
            print(f"✗ {pl['id']}")
            for x in mal:
                print(f"    {x}")
            continue
        partes = " → ".join(t["nombre"] for t in pl["tramos"])
        print(f"{pl['id']:24s} {pl['material']:7s} {pl.get('dura', ''):22s} {partes}")
        print(f"{'':24s} {pl['frase']}")
    print(f"\n{len(plantillas)} plantillas en {PLANTILLAS}" + (f" · {con_errores} con errores" if con_errores else ""))
    return con_errores
