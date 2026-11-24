"""Pruebas del etalonaje (2026-11-23): las tablas de color de la mesa y los `.cube` de otros editores.

    python -m pytest py/pruebas -q
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from montaje import analogo as A  # noqa: E402
from montaje import etalonaje as E  # noqa: E402


def _imagen(alto=40, ancho=60, semilla=1):
    return np.random.default_rng(semilla).random((alto, ancho, 3)).astype(np.float32)


def test_la_tabla_identidad_no_cambia_nada():
    img = _imagen()
    assert np.abs(E.aplicar(img, E.grilla(17)) - img).max() < 1e-5


def test_un_cube_escrito_se_lee_igual(tmp_path):
    for nombre in E.TABLAS:
        t = E.tabla_de({"tabla": nombre, "archivo": ""})
        E.escribir_cube(t, tmp_path / f"{nombre}.cube", nombre)
        assert np.abs(E.leer_cube(tmp_path / f"{nombre}.cube") - t).max() < 1e-5, nombre


def test_el_orden_del_cube_es_el_de_los_otros_editores(tmp_path):
    # ffmpeg (`lut3d`) lee el .cube por su cuenta: si el orden de los canales estuviera al revés, la imagen saldría
    # otra. Se compara sobre una imagen de prueba.
    if not shutil.which("ffmpeg"):
        pytest.skip("sin ffmpeg")
    from PIL import Image

    img = (_imagen(36, 48) * 255).astype(np.uint8)
    Image.fromarray(img).save(tmp_path / "entra.png")
    E.escribir_cube(E.tabla_de({"tabla": "proceso-cruzado", "archivo": ""}), tmp_path / "t.cube", "t")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "entra.png", "-vf", "lut3d=file=t.cube:interp=trilinear",
                    "-pix_fmt", "rgb24", "sale.png"], cwd=tmp_path, check=True)
    ffmpeg = np.asarray(Image.open(tmp_path / "sale.png").convert("RGB"), np.float32)
    nuestro = E.aplicar(img.astype(np.float32) / 255, E.tabla_de({"tabla": "proceso-cruzado", "archivo": ""})) * 255
    assert np.abs(ffmpeg - nuestro).mean() < 1.5


def test_un_cube_que_no_sirve_no_pasa(tmp_path):
    (tmp_path / "corto.cube").write_text("LUT_3D_SIZE 2\n0 0 0\n1 1 1\n", encoding="utf-8")
    (tmp_path / "plano.cube").write_text("LUT_1D_SIZE 2\n0 0 0\n1 1 1\n", encoding="utf-8")
    assert A.errores({"aparatos": [{"aparato": "color", "tabla": "archivo"}]})                       # sin archivo
    assert A.errores({"aparatos": [{"aparato": "color", "tabla": "archivo", "archivo": str(tmp_path / "no.cube")}]})
    assert A.errores({"aparatos": [{"aparato": "color", "tabla": "archivo", "archivo": str(tmp_path / "corto.cube")}]})
    assert A.errores({"aparatos": [{"aparato": "color", "tabla": "archivo", "archivo": str(tmp_path / "plano.cube")}]})


def test_un_cube_de_afuera_entra_a_la_mesa(tmp_path):
    # Una tabla que invierte el color, escrita como la escribiría otro editor (2 puntos por lado).
    filas = [f"{1 - r} {1 - g} {1 - b}" for b in (0, 1) for g in (0, 1) for r in (0, 1)]
    (tmp_path / "negativo.cube").write_text('TITLE "negativo"\nLUT_3D_SIZE 2\n' + "\n".join(filas) + "\n", encoding="utf-8")
    cadena = {"aparatos": [{"aparato": "color", "tabla": "archivo", "archivo": str(tmp_path / "negativo.cube")}]}
    assert A.errores(cadena) == []
    pasos, captura, semilla = A.preparar(cadena)
    img = np.zeros((8, 8, 3), np.uint8)
    img[..., 0] = 200
    ctx = A.Contexto(semilla, 24.0, 8, 8)
    sale = A.procesar_cuadro(img, pasos, captura, ctx)[0, 0]
    assert abs(int(sale[0]) - 55) <= 1 and sale[1] >= 254 and sale[2] >= 254


def test_la_fuerza_se_graba():
    cadena = {"aparatos": [{"aparato": "color", "tabla": "noche-americana"}],
              "automatizacion": [{"paso": 0, "perilla": "fuerza", "puntos": [[0, 0], [2, 1]]}]}
    pasos, captura, semilla = A.preparar(json.loads(json.dumps(cadena)))
    img = np.full((8, 8, 3), 180, np.uint8)
    ctx = A.Contexto(semilla, 24.0, 8, 8)
    brillo = []
    for t in (0.0, 1.0, 2.0):
        ctx.t = t
        brillo.append(float(A.procesar_cuadro(img, pasos, captura, ctx).mean()))
    assert abs(brillo[0] - 180) < 1 and brillo[0] > brillo[1] > brillo[2]   # la noche americana oscurece


def test_la_consola_recibe_la_tabla():
    assert "color" in A.aparatos_json()
    assert A.aparatos_json()["color"]["perillas"]["tabla"]["rango"][-1] == "archivo"
