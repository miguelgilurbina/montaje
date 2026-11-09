"""El esqueleto de un guion: la canción partida en tramos, con los estilos que sirven en cada uno.

El guion lo escribe Miguel **en palabras**; esto sólo le prepara la mesa. Lee las
secciones de la canción (`analisis/musica.json`) y el catálogo de estilos, y arma la
tabla de tramos con tres columnas ya llenas: los segundos, la energía y los estilos
de la galería que sirven ahí (por su `para`, su `energia` y su `material`; primero
los aprobados, nunca un rechazado). Lo que tiene que pasar y el material de cada
tramo quedan en blanco: eso es el guion.

    python montaje.py guion <p>

Si el proyecto no tiene `GUION.md`, lo escribe; si ya lo tiene, no lo toca y muestra
la tabla en la consola. Al final imprime los `tramos` para pegar en `montaje` y, además,
**un primer armado**: los mismos tramos con la receta del primer estilo que sirve en cada
uno, y sus capas de síntesis con sus segundos. Es un punto de partida para planificar y
mirar, no una decisión: mientras más veredictos tenga la galería, mejor elige (primero
lo aprobado). No escribe nada en proyecto.json.
"""

from __future__ import annotations

import json

from . import estilos as catalogo
from . import musica, pulso, sintesis
from .rutas import Proyecto

#: Lo que hace cada tramo en el video, en las palabras del catálogo (`PARA`).
PAPELES = ("abrir", "cerrar", "respirar", "subir la energía", "mostrar el archivo")


def energia_de(e: float, calma: float, pico: float) -> str:
    return "calma" if e < calma else "alta" if e >= pico else "media"


def papel(i: int, energias: list[float], calma: float, pico: float) -> str:
    """Qué le toca a la sección `i`: abre, cierra, baja (respira), sube o sostiene."""
    if i == 0:
        return "abrir"
    if i == len(energias) - 1:
        return "cerrar"
    e, antes = energias[i], energias[i - 1]
    if e < calma or e < antes - 0.15:
        return "respirar"
    if e >= pico or e > antes + 0.15:
        return "subir la energía"
    return "mostrar el archivo"


def candidatos(estilos: list[dict], papel_: str, energia: str, material: str, bases: int = 3, capas: int = 2) -> tuple[list[dict], list[dict]]:
    """Los estilos que sirven en un tramo: (los que arman el tramo, las capas que van encima).

    Sirve el que trabaja con ese material (o con cualquiera) y no está rechazado. Primero
    los que dicen servir para ese papel y, entre ellos, lo que Miguel ya aprobó; después,
    los que comparten la energía.
    """
    para = lambda e: papel_ in e["para"]  # noqa: E731
    misma = lambda e: e["energia"] in (energia, "sigue")  # noqa: E731
    orden = list(catalogo.ESTADOS)
    sirven = [e for e in estilos if e["estado"] != "rechazado" and e["material"] in (material, "cualquiera", "mixto") and (para(e) or misma(e))]
    sirven.sort(key=lambda e: (not para(e), orden.index(e["estado"]), not misma(e), e["id"]))
    es_capa = lambda e: "capa" in e["tecnica"] or "comando" in e["tecnica"]  # noqa: E731
    return [e for e in sirven if not es_capa(e)][:bases], [e for e in sirven if es_capa(e)][:capas]


#: Perillas de un estilo que valen para el montaje entero, no para un tramo.
SOLO_GLOBALES = {"modo", "orden", "reparto", "max_por_clip", "mezclar_fotos"}
#: Capas que necesitan un texto que sólo Miguel puede escribir: no se arman solas.
CON_TEXTO = {"rotulos", "titulo", "credito"}


def receta_de_tramo(e: dict) -> dict | None:
    """Las perillas que un estilo le pone a un tramo de `pulso`, o None si el estilo no se puede usar por tramo."""
    t = e["tecnica"]
    if t.get("modo") != "pulso" or "muro" in t:  # el muro se planifica aparte: es todo el video o nada
        return None
    # Sólo perillas de verdad: la receta de un estilo también lleva notas (qué capas lo acompañan).
    return {k: v for k, v in t.items() if k in pulso.POR_DEFECTO and k not in SOLO_GLOBALES}


def capa_de(e: dict, desde: float, hasta: float) -> dict | None:
    """La capa de síntesis de un estilo, para esos segundos; None si no es una capa o pide un texto."""
    t = e["tecnica"]
    capa = t.get("capa")
    if capa not in sintesis.POR_DEFECTO or capa in CON_TEXTO:
        return None
    return {"tipo": capa, **{k: v for k, v in t.items() if k in sintesis.POR_DEFECTO[capa]}, "desde": desde, "hasta": hasta}


def _marca(e: dict) -> str:
    return f"`{e['id']}`" + (" ✓" if e["estado"] == "aprobado" else " (a medias)" if e["estado"] == "a medias" else "")


def esqueleto(p: Proyecto) -> tuple[str, list[dict], dict]:
    """El GUION.md en borrador, los `tramos` vacíos para proyecto.json y un primer armado (`tramos` + `sintesis`)."""
    m = musica.cargar(p)
    prm = p.cfg.get("montaje", {})
    calma, pico = float(prm.get("umbral_calma", 0.35)), float(prm.get("umbral_pico", 0.7))
    material = "clips" if p.cfg.get("clips") else "fotos"
    estilos = catalogo.leer()
    secciones = m.get("secciones") or [{"ini": 0.0, "fin": m["duracion"], "energia": 0.5}]
    energias = [s["energia"] for s in secciones]
    # Los bordes van al «uno» más cercano: un tramo vale por compases enteros, y así las capas de
    # síntesis que copien estos segundos entran junto con el primer clip del tramo.
    unos = m.get("primeros_tiempos") or []
    al_uno = lambda t: min(unos, key=lambda u: abs(u - t)) if unos else t  # noqa: E731
    secciones = [{**s, "ini": al_uno(s["ini"]) if i else s["ini"], "fin": al_uno(s["fin"]) if i < len(secciones) - 1 else s["fin"]}
                 for i, s in enumerate(secciones)]
    filas, tramos = [], []
    armado: dict = {"tramos": [], "sintesis": []}
    for i, s in enumerate(secciones):
        en, pa = energia_de(s["energia"], calma, pico), papel(i, energias, calma, pico)
        desde, hasta = (round(s["ini"], 2) if i else 0), round(s["fin"], 2)
        # El armado: el primer estilo que sirve y se puede poner por tramo, y la primera capa que no pide texto.
        muchos, capas = candidatos(estilos, pa, en, material, bases=12, capas=6)
        elegido = next(((e, receta_de_tramo(e)) for e in muchos if receta_de_tramo(e) is not None), None)
        usados = []
        if elegido:
            armado["tramos"].append({"nombre": f"{pa} · {elegido[0]['id']}", "desde": desde, "hasta": hasta, **elegido[1]})
            usados.append(elegido[0])
            # Las capas que el estilo dice que lo acompañan (la ventana va sobre un campo de color).
            for nombre in elegido[0]["tecnica"].get("sintesis") or []:
                if nombre in sintesis.POR_DEFECTO and nombre not in CON_TEXTO:
                    armado["sintesis"].append({"tipo": nombre, "desde": desde, "hasta": hasta})
        con_capa = next(((e, capa_de(e, desde, hasta)) for e in capas if capa_de(e, desde, hasta)), None)
        if con_capa and not any(c["tipo"] == con_capa[1]["tipo"] and c["desde"] == desde for c in armado["sintesis"]):
            armado["sintesis"].append(con_capa[1])
            usados.append(con_capa[0])
        # Lo que cada estilo elegido pide evitar: el armado no lo sabe leer, quien lo use sí.
        armado.setdefault("ojo", []).extend(f"{e['id']} ({desde:g}–{hasta:g} s): {x}" for e in usados for x in e.get("evitar", []))
        base, encima = candidatos(estilos, pa, en, material)
        sirven = ", ".join(_marca(e) for e in base) or "ninguno todavía: es un ejercicio"
        if encima:
            sirven += " · encima: " + ", ".join(_marca(e) for e in encima)
        filas.append(f"| {i + 1} | {s['ini']:.0f}–{s['fin']:.0f} | {en} ({s['energia']:.2f}) · {pa} |  |  | {sirven} |")
        tramos.append({"nombre": f"tramo {i + 1}", "desde": desde, "hasta": hasta})
    titulo = p.cfg.get("titulo", p.nombre)
    texto = "\n".join([
        f"# {titulo} · guion",
        "",
        "> **Borrador de `python montaje.py guion`.** Los tramos salen de las secciones de la canción",
        f"> ({m['archivo']}, {m['bpm']:.0f} BPM) y la última columna, del catálogo de estilos (✓ = aprobado).",
        "> Lo que tiene que pasar y el material los escribe Miguel.",
        "",
        "## El guion, en palabras",
        "",
        "(lo escribe Miguel)",
        "",
        "## Los tramos",
        "",
        f"Material del proyecto: {material}. La columna «Material» va a `material` de cada tramo: las palabras del nombre de los clips que entran.",
        "",
        "| Tramo | Segundos | La canción | Lo que tiene que pasar | Material | Estilos que sirven |",
        "|---|---|---|---|---|---|",
        *filas,
        "",
    ])
    return texto, tramos, armado


def escribir(p: Proyecto) -> None:
    texto, tramos, armado = esqueleto(p)
    destino = p.dir / "GUION.md"
    if destino.exists():
        print(f"{destino} ya existe y no se toca; el borrador:\n")
        print(texto)
    else:
        destino.write_text(texto, encoding="utf-8")
        print(texto)
        print(f"→ {destino}")
    print("`tramos` para `montaje` en proyecto.json (cada uno recibe las perillas de su estilo y su `material`):")
    print(json.dumps(tramos, ensure_ascii=False))
    if armado["tramos"]:
        print("\nUn primer armado, para planificar y mirar (el primer estilo que sirve en cada tramo; falta el `material`):")
        print('"tramos": [')
        print(",\n".join("  " + json.dumps(t, ensure_ascii=False) for t in armado["tramos"]))
        print("]")
        if armado["sintesis"]:
            print('"sintesis": [')
            print(",\n".join("  " + json.dumps(c, ensure_ascii=False) for c in armado["sintesis"]))
            print("]")
        vistos: set[str] = set()
        for aviso in armado.get("ojo", []):
            if aviso.split(" (")[0] + aviso.split("): ")[1] not in vistos:  # una vez por estilo y por aviso
                print(f"  ojo · {aviso}")
            vistos.add(aviso.split(" (")[0] + aviso.split("): ")[1])
