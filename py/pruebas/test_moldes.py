"""Pruebas de los moldes de trabajo (2026-11-22): las recetas guardadas, las plantillas de piezas y el molde de
experimento; y el dial que se sintoniza al empezar (lo pide la cortina de radio).

    python -m pytest py/pruebas -q
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from montaje import analogo as A  # noqa: E402
from montaje import estilos as catalogo  # noqa: E402
from montaje import experimento  # noqa: E402
from montaje import plantillas  # noqa: E402
from montaje import radio as RA  # noqa: E402
from montaje import recetas  # noqa: E402
from montaje import ruidos as R  # noqa: E402

SR = 48000


def test_las_recetas_de_la_galeria_son_validas():
    estilos = catalogo.leer()
    hay = recetas.leer()
    assert hay, "no hay recetas"
    for r in hay:
        assert recetas.errores(r, estilos) == [], r["id"]


def test_una_receta_es_su_base_con_sus_gestos():
    cadena, nombre = A.resolver_cadena("la-familia-en-super-8")
    aparatos = [a["aparato"] for a in cadena["aparatos"]]
    assert aparatos[0] == "pelicula" and aparatos.count("rollo") == 2
    assert nombre == "la-familia-en-super-8"
    # Y se le pueden sumar gestos, como a cualquier cadena.
    cadena, nombre = A.resolver_cadena("la-familia-en-super-8", ["pausa-del-vhs"])
    assert "casetera" in [a["aparato"] for a in cadena["aparatos"]] and nombre.endswith("+pausa-del-vhs")
    assert A.errores(cadena) == []


def test_una_receta_vale_lo_peor_de_sus_partes():
    estilos = [{"id": "b", "estado": "aprobado", "tecnica": {"comando": "analogo", "cadena": []}},
               {"id": "g", "estado": "rechazado", "tecnica": {"comando": "analogo", "gesto": True, "cadena": []}}]
    assert recetas.estado({"base": "b", "gestos": ["g"]}, estilos) == "rechazado"
    assert recetas.errores({"id": "b", "nombre": "x", "frase": "y", "base": "b", "gestos": ["g"]}, estilos) == [
        "se llama como un estilo («b»): una receta necesita un nombre propio"]


def test_las_plantillas_son_validas():
    estilos = catalogo.leer()
    hay = plantillas.leer()
    assert hay, "no hay plantillas"
    for pl in hay:
        assert plantillas.errores(pl, estilos) == [], pl["id"]


def test_una_plantilla_con_huecos_no_pasa():
    estilos = catalogo.leer()
    pl = {**plantillas.buscar("cortina-de-radio")}
    pl["tramos"] = [{**pl["tramos"][0], "parte": [0, 0.3]}, {**pl["tramos"][2], "parte": [0.4, 1]}]
    mal = plantillas.errores(pl, estilos)
    assert any("empieza en 0.4" in m for m in mal)


def test_la_plantilla_cae_en_los_segundos_de_la_cancion():
    from montaje.rutas import MEDIOS, Proyecto

    if not (MEDIOS / "probador" / "analisis" / "musica.json").exists():
        pytest.skip("sin el análisis del banco del probador")
    p = Proyecto("probador")
    armado = plantillas.armar(p, plantillas.buscar("cortina-de-radio"))
    tramos = armado["tramos"]
    assert tramos[0]["desde"] == 0 and abs(tramos[-1]["hasta"] - armado["dura"]) < 0.01
    assert all(a["hasta"] == b["desde"] for a, b in zip(tramos, tramos[1:]))
    # Cada tramo lleva la receta de su estilo; la mesa va encadenada y en sus ventanas.
    assert tramos[1].get("tartamudeo")
    assert armado["mesa"][0]["comando"].endswith("--salida <render>-mesa-1.mp4")
    assert armado["mesa"][1]["comando"].startswith("python montaje.py analogo <render>-mesa-1.mp4")


def test_el_molde_numera_lo_que_sigue():
    with pytest.raises(SystemExit):
        experimento.nuevo("01-otra-cosa", "Otra", "una idea")        # el número no es el que sigue
    with pytest.raises(SystemExit):
        experimento.nuevo("Mal Nombre", "Otra", "una idea")
    assert experimento.siguiente() >= 32
    texto = experimento.ficha(32, "Pantallas", "la idea", "lo que dijo", "2026-11-23")
    for seccion in ("## Idea", "## Lo que se hizo", "## Lo que midió Claude (que no oye)", "## Lo que dijo Miguel", "«lo que dijo»"):
        assert seccion in texto


def test_el_dial_al_empezar_se_sintoniza_una_vez_al_principio():
    p = {**RA.POR_DEFECTO["dial"], "inicio": True, "dura": 2.0}
    assert RA.movimiento(p, 0.5, 0.0, 100)[1] == RA.INICIO
    assert RA.movimiento(p, 2.5, 0.0, 100) is None                    # sin `sintonizar`, una sola vez
    assert RA.movimiento(p, 10.5, 10.0, 100)[0] == pytest.approx(0.25)  # al principio de la salida, no del video
    x = np.stack([0.25 * np.sin(2 * np.pi * 220 * np.arange(4 * SR) / SR)] * 2, 1).astype(np.float32)
    y = R.dial(x, {**p, "sonido": "sintonia", "_paso": 0}, 1, 0.0, SR, 0)
    medio = slice(int(0.9 * SR), int(1.1 * SR))
    assert np.corrcoef(y[medio, 0], x[medio, 0])[0, 1] < 0.5             # en medio de la búsqueda, la canción se va
    assert np.allclose(y[int(2.5 * SR):], x[int(2.5 * SR):], atol=1e-5)  # y vuelve
