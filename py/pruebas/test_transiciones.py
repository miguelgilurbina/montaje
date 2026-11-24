"""Pruebas de las transiciones del 2026-11-23: las nuevas se piden por nombre, la ronda no cambia, la que se va
recibe lo que necesita, y el primer clip de un tramo puede entrar distinto.

    python -m pytest py/pruebas -q
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from montaje import pulso, transiciones as T  # noqa: E402

NUEVAS = ("luz", "desenfoque", "doble", "quemado", "sacudon", "separacion", "pixeles", "latigazo", "cinta")


def test_las_nuevas_se_piden_por_nombre():
    for t in NUEVAS:
        assert T.elegir(t, "derecha", 0) == (t, [1, 0])


def test_la_ronda_no_cambia():
    # Si las nuevas entraran a la ronda, cambiaría lo que Miguel ya juzgó (el 21 tiene una ronda).
    assert T.RONDA == ("cortina", "iris", "empuje", "destello", "zoom", "persiana")
    vistas = {T.elegir("ronda", "alterna", n)[0] for n in range(60)}
    assert vistas <= set(T.RONDA) and not vistas & set(NUEVAS)


def test_la_que_se_va():
    assert T.para_la_que_se_va(("latigazo", [1, 0]), 12) == {"empujada": {"cuadros": 12, "dir": [1, 0]}}
    assert T.para_la_que_se_va(("empuje", [-1, 0]), 8)["empujada"]["dir"] == [-1, 0]
    assert T.para_la_que_se_va(("luz", [1, 0]), 20) == {"salida": 9}       # se apaga al final de la entrada
    assert T.para_la_que_se_va(("doble", [1, 0]), 10) == {"salida": 4}
    assert T.para_la_que_se_va(("cortina", [1, 0]), 10) == {}
    assert T.para_la_que_se_va(None, 10) == {}


def test_el_primer_clip_de_un_tramo():
    prm = {"transicion": "cortina", "transicion_dir": "derecha", "transicion_tramo": "quemado"}
    assert pulso._transicion(prm, 3)[0] == "cortina"
    assert pulso._transicion(prm, 3, tramo_nuevo=True)[0] == "quemado"
    sin = {"transicion": "cortina", "transicion_dir": "derecha"}
    assert pulso._transicion(sin, 3, tramo_nuevo=True)[0] == "cortina"   # sin `transicion_tramo`, la de siempre
