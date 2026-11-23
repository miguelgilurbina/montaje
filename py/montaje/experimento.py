"""El molde de un experimento: arma la carpeta, la ficha y la fila de la bitácora de un experimento nuevo de la galería,
siempre igual, y muestra los pasos que siguen (`direccion/MOLDE.md`).

Miguel, el 2026-11-22: «También armar templates de trabajo para poder armar trabajo más adelante». Es uno de los tres
moldes que eligió (con las plantillas de piezas y las recetas guardadas).

    python montaje.py experimento 32-pantallas --titulo "Pantallas" --idea "…" --cita "lo que dijo Miguel"
"""

from __future__ import annotations

import datetime as dt
import re

from .rutas import PROYECTOS, RAIZ, escribir_json, salir

BITACORA = RAIZ / "EXPERIMENTOS.md"
MOLDE = RAIZ / "direccion" / "MOLDE.md"


def siguiente() -> int:
    hechos = [int(m.group(1)) for p in PROYECTOS.iterdir() if (m := re.match(r"(\d\d)-", p.name))]
    return max(hechos, default=0) + 1


def ficha(numero: int, titulo: str, idea: str, cita: str | None, fecha: str) -> str:
    dijo = f"- «{cita}»" if cita else "- (sus palabras, tal cual)"
    return f"""# {numero:02d} · {titulo}

**Fecha:** {fecha}

## Idea

{idea}

## Material

El banco del probador (La Añoranza).

## Lo que se hizo

(el aparato o la capa, sus perillas, su sonido, los estilos)

## Lo que midió Claude (que no oye)

(las hojas, los espectrogramas, las pruebas: con los números de la medida)

## Lo que dijo Miguel

{dijo}
"""


def nuevo(nombre: str, titulo: str, idea: str, cita: str | None = None) -> None:
    m = re.fullmatch(r"(\d\d)-[a-z0-9]+(-[a-z0-9]+)*", nombre)
    if not m:
        salir("el nombre va con su número y en minúsculas, con guiones: 32-pantallas")
    numero = int(m.group(1))
    if numero != siguiente():
        salir(f"el experimento que sigue es el {siguiente():02d} (un experimento nuevo nunca pisa a otro)")
    carpeta = PROYECTOS / nombre
    if carpeta.exists():
        salir(f"ya existe {carpeta}")
    fecha = dt.date.today().isoformat()
    escribir_json(carpeta / "proyecto.json", {
        "titulo": f"{numero:02d} · {titulo}",
        "idea": idea + (f" Miguel: «{cita}»." if cita else ""),
        "biblioteca": "probador",
        "nota": "No tiene montaje propio: los estilos se muestran sobre el banco del probador (sus muestras en /estilos y en la mesa).",
        "cadenas": [],
    })
    (carpeta / "FICHA.md").write_text(ficha(numero, titulo, idea, cita, fecha), encoding="utf-8")
    texto = BITACORA.read_text(encoding="utf-8")
    filas = list(re.finditer(r"^\| \d\d \|.*$", texto, re.M))
    if not filas:
        salir("no encontré la tabla de EXPERIMENTOS.md")
    fila = f"| {numero:02d} | [{titulo}](proyectos/{nombre}/FICHA.md) | {fecha} | el banco del probador (La Añoranza) | {idea} | — |"
    fin = filas[-1].end()
    BITACORA.write_text(texto[:fin] + "\n" + fila + texto[fin:], encoding="utf-8")
    print(f"→ {carpeta / 'proyecto.json'}\n→ {carpeta / 'FICHA.md'}\n→ una fila en {BITACORA.name}")
    print("\nLos pasos que siguen (direccion/MOLDE.md):")
    for linea in MOLDE.read_text(encoding="utf-8").splitlines():
        if re.match(r"\d+\. \*\*", linea):
            print("  " + re.sub(r"\*\*(.+?)\*\*.*", r"\1", linea))
