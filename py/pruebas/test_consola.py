"""Pruebas de la automatización de perillas (2026-11-23): lo que la consola del panel graba con los diales y el motor
repite al renderizar.

    python -m pytest py/pruebas -q
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from montaje import analogo as A  # noqa: E402


def test_el_valor_se_mueve_entre_los_puntos():
    pista = {"paso": 0, "perilla": "fuerza", "puntos": [[1.0, 0.0], [3.0, 1.0]]}
    assert A.valor_en(pista, 0.0) == 0.0          # antes del primer punto, su valor
    assert abs(A.valor_en(pista, 2.0) - 0.5) < 1e-9
    assert A.valor_en(pista, 9.0) == 1.0          # después del último, su valor
    assert A.valor_en({**pista, "curva": "escalon"}, 2.9) == 0.0
    opciones = {"paso": 0, "perilla": "modo", "puntos": [[0.0, "tintado"], [1.0, "virado"]]}
    assert A.valor_en(opciones, 0.5) == "tintado" and A.valor_en(opciones, 1.5) == "virado"


def test_una_automatizacion_mal_escrita_no_pasa():
    base = {"aparatos": [{"aparato": "tinte"}]}
    assert A.errores({**base, "automatizacion": [{"paso": 3, "perilla": "fuerza", "puntos": [[0, 1]]}]})
    assert A.errores({**base, "automatizacion": [{"paso": 0, "perilla": "nieve", "puntos": [[0, 1]]}]})
    assert A.errores({**base, "automatizacion": [{"paso": 0, "perilla": "fuerza", "puntos": [[0, 5]]}]})       # fuera de rango
    assert A.errores({**base, "automatizacion": [{"paso": 0, "perilla": "fuerza", "puntos": [[2, 0], [1, 1]]}]})  # desordenados
    assert A.errores({**base, "automatizacion": [{"paso": 0, "perilla": "fuerza", "puntos": [[0, 0.2], [1, 0.9]]}]}) == []


def test_la_imagen_sigue_a_la_perilla():
    cadena = {"aparatos": [{"aparato": "tinte", "modo": "tintado", "tinta": "azul"}],
              "automatizacion": [{"paso": 0, "perilla": "fuerza", "puntos": [[0.0, 0.0], [2.0, 1.0]]}]}
    pasos, captura, semilla = A.preparar(cadena)
    img = (np.ones((24, 32, 3)) * 200).astype(np.uint8)
    ctx = A.Contexto(semilla, 24.0, 24, 32)
    salidas = []
    for t in (0.0, 1.0, 2.0):
        ctx.t, ctx.k = t, int(t * 24)
        salidas.append(A.procesar_cuadro(img, pasos, captura, ctx)[0, 0].astype(float))
    azulidad = [s[2] - s[0] for s in salidas]
    assert azulidad[0] < 2 and azulidad[0] < azulidad[1] < azulidad[2]   # sin tinte al principio, todo azul al final
    # La cadena no se tocó: lo que suena sigue leyendo el primer valor.
    assert pasos[0][1]["fuerza"] == 0.0


def test_los_aparatos_para_la_consola():
    aparatos = A.aparatos_json()
    assert "antena" in aparatos and "tinte" in aparatos
    nieve = aparatos["antena"]["perillas"]["nieve"]
    assert nieve["rango"] == [0, 1] and isinstance(nieve["defecto"], float)
    json.dumps(aparatos)   # se puede mandar al panel tal cual


def test_lo_que_llega_del_navegador_no_se_vuelve_entero():
    # JSON no distingue 1.0 de 1: una perilla de coma (el grano) grabada de 1 a 0 tiene que pasar por 0,5, y una
    # entera (las líneas del cabezal) tiene que seguir entera.
    # Así llega del navegador: `JSON.stringify(1.0)` es "1".
    cadena = json.loads('{"aparatos": [{"aparato": "cinta"}], "automatizacion": ['
                        '{"paso": 0, "perilla": "temblor", "puntos": [[0, 1], [2, 0]]},'
                        '{"paso": 0, "perilla": "cabezal_lineas", "puntos": [[0, 8], [2, 13]]}]}')
    pasos, _, _ = A.preparar(cadena)
    pistas = {x["perilla"]: x for x in pasos[0][1]["_auto"]}
    assert abs(A.valor_en(pistas["temblor"], 1.0) - 0.5) < 1e-9
    assert isinstance(A.valor_en(pistas["cabezal_lineas"], 1.0), int)
    assert A.aparatos_json()["cinta"]["perillas"]["cabezal_lineas"]["entero"] is True
    assert A.aparatos_json()["cinta"]["perillas"]["temblor"]["entero"] is False


def test_cada_aparato_de_senal_dice_que_es():
    aparatos = A.aparatos_json()
    for nombre in [n for n in A.APARATOS if A._modulo(n) is None]:   # los que viven en analogo.py
        assert nombre in A.DESCRIPCION, nombre
        assert aparatos[nombre]["doc"] == A.DESCRIPCION[nombre]


def test_el_material_de_prueba_sale_con_imagen_y_sonido(tmp_path):
    import shutil
    import subprocess

    import pytest

    if not shutil.which("ffmpeg"):
        pytest.skip("sin ffmpeg")
    from montaje import demo

    hechos = demo.generar(segundos=1.0, alto=90, carpeta=tmp_path)
    assert {p.stem for p in hechos} == {"cielo-con-sol", "carta-que-se-mueve", "barras-de-color", "fractal-que-se-acerca",
                                        "juego-de-la-vida"}
    for p in hechos:
        info = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(p)],
                              capture_output=True, text=True).stdout.split()
        assert "video" in info and "audio" in info, p.name
    assert (tmp_path / "LICENCIA.txt").exists()


def test_la_barra_del_mezclador():
    # Un tinte azul fuerte y después la barra: en 0 sale el cuadro como entró, en 1 el tinte, y grabada de 0 a 1 en
    # dos segundos, pasa de uno a otro.
    cadena = {"aparatos": [{"aparato": "tinte", "modo": "tintado", "tinta": "azul", "fuerza": 1.0}, {"aparato": "cruce"}],
              "automatizacion": [{"paso": 1, "perilla": "cantidad", "puntos": [[0.0, 0.0], [2.0, 1.0]]}]}
    pasos, captura, semilla = A.preparar(cadena)
    img = np.zeros((24, 32, 3), np.uint8)
    img[..., 0] = 220   # rojo: el tinte azul lo cambia mucho
    ctx = A.Contexto(semilla, 24.0, 24, 32)
    salen = []
    for t in (0.0, 1.0, 2.0):
        ctx.t, ctx.k = t, int(t * 24)
        salen.append(A.procesar_cuadro(img, pasos, captura, ctx)[0, 0].astype(float))
    assert abs(salen[0][0] - 220) <= 1 and salen[0][2] <= 1          # tal cual
    assert salen[0][0] > salen[1][0] > salen[2][0]                     # el rojo se va
    assert salen[0][2] < salen[1][2] < salen[2][2]                     # el azul llega
