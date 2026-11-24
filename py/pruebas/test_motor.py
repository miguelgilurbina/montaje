"""Pruebas del motor: lo que se puede comprobar sin abrir un video.

    python -m pytest py/pruebas -q

Las que necesitan medios (un catálogo de clips, el análisis de una canción) se
saltan solas si no están: Miguel borra las salidas después de publicar.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from montaje import estilos as estilos_mod  # noqa: E402
from montaje import aprender, clips, estilos, guion, por_tramos, proyector, pulso, revisar, seleccion, sintesis, tomas, transcribir, transformar, transiciones  # noqa: E402
from montaje.rutas import MEDIOS, PROYECTOS, Proyecto  # noqa: E402


def clip_falso(duracion=5.0, hz=10, cortes=(), nit=None, cx=0.5) -> dict:
    n = int(duracion * hz)
    return {
        "id": "falso", "w": 768, "h": 512, "fps": 72, "duracion": duracion, "hz": hz, "cortes": list(cortes),
        "curvas": {"mov": [0.01] * n, "camara": [0.0] * n, "temblor": [0.0] * n, "nit": nit or [0.01] * n,
                   "luz": [0.4] * n, "cx": [cx] * n, "cy": [0.5] * n},
    }


# ── Elegir los segundos de un clip ─────────────────────────────────────────

def test_mejor_tramo_respeta_borde_y_cabe():
    c = clip_falso(5.0)
    t = clips.mejor_tramo(c, 2.0, borde=0.35)
    assert 0.35 <= t <= 5.0 - 0.35 - 2.0 + 1e-6


def test_mejor_tramo_prefiere_lo_nitido():
    nit = [0.001] * 25 + [0.05] * 25  # la segunda mitad es nítida
    t = clips.mejor_tramo(clip_falso(5.0, nit=nit), 1.5, borde=0.1)
    assert t >= 2.4


def test_mejor_tramo_no_cruza_un_corte():
    t = clips.mejor_tramo(clip_falso(6.0, cortes=[3.0]), 2.0, borde=0.1)
    assert not (t < 3.0 < t + 2.0)


def test_mejor_tramo_evita_lo_usado():
    c = clip_falso(8.0)
    t = clips.mejor_tramo(c, 2.0, evitar=[(0.0, 4.0)], borde=0.1)
    assert t >= 4.0 - 1e-6


# ── Encuadres ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("encuadre,relleno", [("cubrir", False), ("contener", False), ("relleno", True), ("medio", True)])
def test_encaje(encuadre, relleno):
    c = clip_falso()
    W, H = 1080, 1920
    ancho, alto, r = pulso._encaje(c, W, H, encuadre)
    assert r is relleno
    assert math.isclose(ancho / alto, 768 / 512, rel_tol=0.01)
    if encuadre == "cubrir":
        assert ancho >= W - 1 and alto >= H - 1
    if encuadre in ("contener", "relleno"):
        assert ancho <= W + 1 and alto <= H + 1
    if encuadre == "medio":
        # Entre los dos: más grande que entero, más chico que recortado.
        assert pulso._encaje(c, W, H, "contener")[0] < ancho < pulso._encaje(c, W, H, "cubrir")[0]


def test_seguir_no_destapa_el_cuadro():
    W, H = 1080, 1920
    c = clip_falso(cx=0.05)  # el sujeto pegado a la izquierda
    ancho, alto, _ = pulso._encaje(c, W, H, "cubrir")
    x, y = pulso._seguir(c, 1.0, ancho, alto, W / 2, H / 2, W, H)
    assert x - ancho / 2 <= 0 + 1e-6 and x + ancho / 2 >= W - 1e-6  # sigue cubriendo
    assert x > W / 2  # se corrió hacia el sujeto (la caja a la derecha deja ver su izquierda)


def test_mitades_del_diptico():
    c = clip_falso()
    _, _, x0, _, m0 = pulso._mitad(c, 1620, 1080, 0)
    _, _, x1, _, m1 = pulso._mitad(c, 1620, 1080, 1)
    assert x0 < x1 and math.isclose(m0["ancho"], m1["ancho"])
    assert m0["x"] + m0["ancho"] / 2 < m1["x"] - m1["ancho"] / 2  # hay hueco entre las dos


# ── Síntesis ───────────────────────────────────────────────────────────────

def musica_falsa(bpm=120.0, compases=8) -> dict:
    golpe = 60 / bpm
    beats = [i * golpe for i in range(compases * 4)]
    return {"bpm": bpm, "beats": beats, "primeros_tiempos": beats[::4], "energia": [0.5] * len(beats), "duracion": compases * 4 * golpe}


def test_titulo_letras_en_orden_y_dentro():
    m = musica_falsa()
    g = sintesis._grafico("titulo", {**sintesis.POR_DEFECTO["titulo"], "texto": "Natalia"}, m, 24, 0, 24 * 16)
    assert len(g["letras"]) == len("Natalia")
    assert g["letras"] == sorted(g["letras"]) and g["ini"] <= g["letras"][0] and g["letras"][-1] < g["fin"]


def test_cuenta_un_numero_por_golpe():
    m = musica_falsa()
    g = sintesis._grafico("cuenta", sintesis.POR_DEFECTO["cuenta"], m, 24, 0, 24 * 16)
    assert [n for _, n in g["numeros"]] == [4, 3, 2, 1]
    pasos = {b[0] - a[0] for a, b in zip(g["numeros"], g["numeros"][1:])}
    assert pasos == {12}  # 120 BPM a 24 cps: un golpe son 12 cuadros


def test_rotulos_en_el_golpe_y_palabra_por_palabra():
    m = musica_falsa()  # 120 BPM: un golpe cada 0,5 s
    prm = {**sintesis.POR_DEFECTO["rotulos"], "cada": "golpe", "lineas": [{"t": 1.1, "texto": "uno dos tres"}, [4.0, "y después"]]}
    g = sintesis._rotulos(prm, m, 24, 24 * 16)
    primera, segunda = g["lineas"]
    assert primera["ini"] == 24  # 1,1 s cae en el golpe de 1,0 s
    assert [c for _, c in primera["palabras"]] == [24, 36, 48]  # una palabra por golpe
    assert primera["fin"] <= segunda["ini"]  # se va antes de que entre la siguiente
    assert g["ini"] == primera["ini"] and g["fin"] == segunda["fin"]


def test_rotulos_con_tiempos_propios_no_usa_los_golpes():
    # Por aquí entran los subtítulos de una voz en off: cada palabra trae su segundo.
    prm = {**sintesis.POR_DEFECTO["rotulos"], "lineas": [{"t": 0.3, "texto": "hola mundo", "tiempos": [0.3, 0.9]}]}
    g = sintesis._rotulos(prm, musica_falsa(), 30, 300)
    assert g["lineas"][0]["palabras"] == [["hola", 9], ["mundo", 27]]


def test_rotulos_sin_lineas_no_deja_capa():
    assert sintesis._rotulos({**sintesis.POR_DEFECTO["rotulos"], "lineas": [[1, "   "]]}, musica_falsa(), 24, 240) is None


# ── Transiciones entre clips ───────────────────────────────────────────────

def test_transicion_fundido_no_deja_marca():
    assert pulso._transicion({"transicion": "fundido", "transicion_dir": "alterna"}, 0) is None


def _galeria_de_transiciones(monkeypatch, rechazadas: set[str]) -> None:
    falsos = [{"id": f"transicion-{t}", "estado": "rechazado" if t in rechazadas else "aprobado"} for t in transiciones.RONDA]
    monkeypatch.setattr(estilos, "leer", lambda: falsos)
    pulso.en_ronda.cache_clear()


def test_transicion_ronda_las_recorre_y_alterna(monkeypatch):
    _galeria_de_transiciones(monkeypatch, set())
    prm = {"transicion": "ronda", "transicion_dir": "alterna"}
    seis = len(transiciones.RONDA)
    tipos = [pulso._transicion(prm, n)[0] for n in range(seis)]
    assert sorted(tipos) == sorted(transiciones.RONDA)  # todas las de la ronda, una vez
    assert pulso._transicion(prm, 0)[1] == [1, 0] and pulso._transicion(prm, 1)[1] == [-1, 0]
    # El mismo tipo, en la vuelta siguiente, sale para el otro lado (antes, cada tipo iba siempre al mismo).
    for n in range(seis):
        assert pulso._transicion(prm, n)[0] == pulso._transicion(prm, n + seis)[0]
        assert pulso._transicion(prm, n)[1] != pulso._transicion(prm, n + seis)[1]
    pulso.en_ronda.cache_clear()


def test_transicion_ronda_salta_lo_rechazado(monkeypatch):
    _galeria_de_transiciones(monkeypatch, {"persiana"})
    prm = {"transicion": "ronda", "transicion_dir": "alterna"}
    tipos = [pulso._transicion(prm, n)[0] for n in range(20)]
    assert "persiana" not in tipos and set(tipos) == set(transiciones.RONDA) - {"persiana"}
    # Con cinco (impar), cada tipo igual cambia de lado de una vuelta a la otra.
    assert pulso._transicion(prm, 0)[1] != pulso._transicion(prm, 5)[1]
    # La persiana sola, pedida por su nombre, sigue valiendo: lo rechazado no se borra, sólo no entra solo.
    assert pulso._transicion({"transicion": "persiana", "transicion_dir": "derecha"}, 0)[0] == "persiana"
    pulso.en_ronda.cache_clear()
    # Una sola transición alterna en cada cambio.
    una = {"transicion": "cortina", "transicion_dir": "alterna"}
    assert [pulso._transicion(una, n)[1] for n in range(3)] == [[1, 0], [-1, 0], [1, 0]]


def test_transicion_desconocida_avisa():
    with pytest.raises(SystemExit):
        pulso._transicion({"transicion": "voltereta", "transicion_dir": "derecha"}, 0)


def test_proyector_une_tramos():
    assert proyector._unir([(5, 8), (0, 2), (1, 3)]) == [(0, 3), (5, 8)]


# ── El catálogo de estilos ─────────────────────────────────────────────────

def test_estilos_validos():
    mal = {e["id"]: estilos.errores(e) for e in estilos.leer()}
    assert not {k: v for k, v in mal.items() if v}


# ── El veredicto ───────────────────────────────────────────────────────────

def test_la_cita_queda_en_una_linea_y_con_sus_comillas_de_adentro():
    assert estilos.limpiar_cita("  «Esta buenísimo»  ") == "Esta buenísimo"
    assert estilos.limpiar_cita("«lento» al entrar, pero el final «sí»") == "«lento» al entrar, pero el final «sí»"
    assert estilos.limpiar_cita('me gusta el "empuje"') == 'me gusta el "empuje"'
    assert estilos.limpiar_cita("bien\n\n## un título falso\n- y una viñeta") == "bien ## un título falso - y una viñeta"


def test_el_veredicto_no_cambia_nada_mas_del_estilo(tmp_path, monkeypatch):
    (tmp_path / "estilos").mkdir()
    (tmp_path / "direccion").mkdir()
    antes = {"nombre": "Prueba", "frase": "x", "para": ["abrir"], "material": "clips", "energia": "calma", "dura": "un compás",
             "tecnica": {"modo": "pulso", "zoom": 6.0}, "estado": "propuesta", "miguel": [], "visto_en": [], "evitar": [],
             "muestra": {"de": "x/render/y.mp4", "desde": 3.0, "hasta": 13.0}}
    ruta = tmp_path / "estilos" / "prueba.json"
    ruta.write_text(json.dumps(antes, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (tmp_path / "direccion" / "REGISTRO.md").write_text("# Registro\n", encoding="utf-8")
    monkeypatch.setattr(estilos, "ESTILOS", tmp_path / "estilos")
    monkeypatch.setattr(estilos, "RAIZ", tmp_path)

    # Un clic sin palabras: cambia el estado, deja la marca, y el estilo sigue siendo válido.
    estilos.veredicto("prueba", "aprobado", "", "galeria")
    e = json.loads(ruta.read_text(encoding="utf-8"))
    assert e["estado"] == "aprobado" and e["veredicto"]["via"] == "galeria" and e["miguel"] == []
    assert '"desde": 3.0' in ruta.read_text(encoding="utf-8")  # los números, como estaban
    assert (tmp_path / "direccion" / "REGISTRO.md").read_text(encoding="utf-8") == "# Registro\n"

    # Con palabras: van al estilo y al registro, en una línea.
    estilos.veredicto("prueba", "rechazado", "«no:\nmarea»", "galeria")
    e = json.loads(ruta.read_text(encoding="utf-8"))
    assert e["estado"] == "rechazado" and e["miguel"] == ["no: marea"]
    registro = (tmp_path / "direccion" / "REGISTRO.md").read_text(encoding="utf-8")
    assert registro.count("\n## ") == 1 and "- Prueba (`prueba`), rechazado: «no: marea»" in registro

    # Deshacer: vuelve a propuesta sin la marca; las palabras quedan. Y todo lo demás, igual que al principio.
    estilos.veredicto("prueba", "propuesta", "", "galeria")
    e = json.loads(ruta.read_text(encoding="utf-8"))
    assert {**e, "miguel": []} == antes

    with pytest.raises(SystemExit):
        estilos.veredicto("../proyectos", "aprobado")
    with pytest.raises(SystemExit):
        estilos.veredicto("prueba", "genial")


# ── Con medios en disco (si están) ─────────────────────────────────────────

def _proyecto_con_medios(nombre: str) -> Proyecto:
    if not (PROYECTOS / nombre / "proyecto.json").exists():
        pytest.skip(f"no está {nombre}")
    p = Proyecto(nombre)
    if not clips.ruta_catalogo(p).exists() or not (p.salidas / "analisis" / "musica.json").exists():
        pytest.skip("sin el catálogo de clips o el análisis de la canción")
    return p


@pytest.mark.parametrize("version", ["a", "b", "c"])
def test_ninguna_toma_pasa_del_clip(version, tmp_path, monkeypatch):
    p = _proyecto_con_medios("15-anoranza-de-natalia")
    p = Proyecto("15-anoranza-de-natalia", version)
    monkeypatch.setattr(Proyecto, "timeline", property(lambda self: tmp_path / "timeline.json"))
    pulso.planificar(p)
    tl = json.loads((tmp_path / "timeline.json").read_text(encoding="utf-8"))
    dur = {c["proxy"]: c["duracion"] for c in clips.cargar(p)}
    for c in tl["capas"]:
        v = c["video"]
        assert v["desde"] + (c["fin"] - c["ini"]) / tl["fps"] * v["velocidad"] <= dur[c["img"]] + 1e-3, c["id"]


def test_muro_sin_repetidos_a_la_vez(tmp_path, monkeypatch):
    _proyecto_con_medios("16-laboratorio-de-la-noche")
    p = Proyecto("16-laboratorio-de-la-noche", "muro")
    monkeypatch.setattr(Proyecto, "timeline", property(lambda self: tmp_path / "timeline.json"))
    pulso.planificar(p)
    tl = json.loads((tmp_path / "timeline.json").read_text(encoding="utf-8"))
    for f in range(0, tl["duracion"], 24):
        ids = [c["id"].split("#")[0] for c in tl["capas"] if c["ini"] + c["entrada"] <= f < c["fin"] - 4]
        assert len(ids) == len(set(ids)), f
    dur = {c["proxy"]: c["duracion"] for c in clips.cargar(p)}
    for c in tl["capas"]:
        v = c["video"]
        assert v["desde"] + (c["fin"] - c["ini"]) / tl["fps"] * v["velocidad"] <= dur[c["img"]] + 1e-6, c["id"]


def test_transiciones_en_el_timeline(tmp_path, monkeypatch):
    _proyecto_con_medios("21-laboratorio-de-la-manana")
    p = Proyecto("21-laboratorio-de-la-manana", "empuje")
    monkeypatch.setattr(Proyecto, "timeline", property(lambda self: tmp_path / "timeline.json"))
    pulso.planificar(p)
    capas = json.loads((tmp_path / "timeline.json").read_text(encoding="utf-8"))["capas"]
    entran = [c for c in capas if c.get("transicion")]
    assert entran and all(c["transicion"]["tipo"] == "empuje" and c["entrada"] > 0 for c in entran)
    assert "transicion" not in capas[0]  # el primero sale del negro
    # A cada clip que entra empujando le corresponde uno que sale, en los mismos cuadros y hacia el mismo lado.
    for c in entran:
        sale = [o for o in capas if o.get("empujada") and o["fin"] == c["ini"] + c["entrada"]]
        assert sale and all(o["empujada"] == {"cuadros": c["entrada"], "dir": c["transicion"]["dir"]} for o in sale), c["id"]


def test_una_version_dice_como_se_prueba():
    if not (PROYECTOS / "21-laboratorio-de-la-manana" / "proyecto.json").exists():
        pytest.skip("no está el 21")
    p = Proyecto("21-laboratorio-de-la-manana", "cortina")
    assert p.prueba and p.estilo == "transicion-cortina"
    # …y eso no se cuela entre las perillas del montaje.
    assert not {"prueba", "estilo", "muestra"} & set(p.cfg["montaje"])


def test_recorrido_pasa_primero_lo_aprobado():
    es = [{"id": "b", "estado": "propuesta", "visto_en": ["x"], "para": ["abrir"]},
          {"id": "a", "estado": "aprobado", "visto_en": ["x"], "para": ["cerrar"]},
          {"id": "c", "estado": "rechazado", "visto_en": ["y"], "para": ["abrir"]}]
    assert [e["id"] for e in estilos.elegir_para_recorrido(es, None, None, None)] == ["a", "b", "c"]
    assert [e["id"] for e in estilos.elegir_para_recorrido(es, "x", None, "abrir")] == ["b"]


# ── Lo que encontró la revisión del 2026-11-09 ─────────────────────────────

def _compases_falsos(n=16, largo=2.0, e=0.6):
    return [{"ini": i * largo, "fin": (i + 1) * largo, "e": e} for i in range(n)]


def test_el_borde_de_un_tramo_corta_la_frase():
    compases = _compases_falsos()
    # Sin cortes, frases de ocho: [0..7] y [8..15]. Un tramo que empieza en el compás 5 parte la primera.
    assert [len(f) for f in pulso._frases(compases, {"secciones": []}, 8)] == [8, 8]
    frases = pulso._frases(compases, {"secciones": []}, 8, largo_en=lambda i: (8, None), cortes={5})
    assert [f[0] for f in frases] == [0, 5, 13]


def test_un_borde_de_tramo_pegado_a_un_cambio_de_seccion_es_un_solo_corte():
    compases = _compases_falsos()  # compases de 2 s: el 6 empieza en el segundo 12
    m = {"secciones": [{"ini": 0.0}, {"ini": 12.0}]}
    de_a_cuatro = lambda i: (4, None)  # noqa: E731
    # Sólo la sección: corta en el 6.
    assert [f[0] for f in pulso._frases(compases, m, 4, largo_en=de_a_cuatro)] == [0, 4, 6, 10, 14]
    # El tramo empieza en el 5, a un compás de la sección: vale el del tramo y no queda una frase de un compás entre los dos.
    frases = pulso._frases(compases, m, 4, largo_en=de_a_cuatro, cortes={5})
    assert [f[0] for f in frases] == [0, 4, 5, 9, 13] and [5] not in frases
    # Lejos de un tramo, la sección sigue cortando.
    assert [f[0] for f in pulso._frases(compases, m, 4, largo_en=de_a_cuatro, cortes={10})] == [0, 4, 6, 10, 14]


def test_la_cuenta_cae_en_los_golpes_de_verdad():
    # Una canción que no es un metrónomo: golpes a 0,5 s salvo uno que se atrasa.
    m = {"bpm": 120.0, "beats": [0.0, 0.5, 1.1, 1.5, 2.0, 2.5]}
    g = sintesis._grafico("cuenta", sintesis.POR_DEFECTO["cuenta"], m, 20, 0, 400)
    assert [c for c, _ in g["numeros"]] == [0, 10, 22, 30]  # el 2 espera a su golpe
    assert g["ini"] == 0 and g["fin"] == 40


def test_las_copias_no_tocan_lo_que_ya_viene_interpolado():
    assert clips._cadencia(72.0) == 72.0  # antes lo llevaba a 60 y después lo interpolaba a 120
    assert clips._cadencia(29.93) == 29.97


def test_transformar_parte_de_los_originales():
    todos = [{"id": "a", "src": "clips/a.mp4"}, {"id": "a-eco", "src": "transformados/a-eco.mp4"}]
    assert [c["id"] for c in transformar.elegir(todos, None)] == ["a"]
    assert [c["id"] for c in transformar.elegir(todos, ["a-eco"])] == ["a-eco"]  # pidiéndolo, sí


def test_cada_experimento_ve_sus_carpetas_del_catalogo():
    class P:  # lo justo de un Proyecto
        cfg = {"clips": ["clips", "fotos"]}
        dir = Path("no-existe")
    todos = [{"src": "clips/a.mp4"}, {"src": "transformados/a-eco.mp4"}, {"src": "fotos/b.jpg"}, {"src": "clips-viejos/c.mp4"}]
    assert [c["src"] for c in clips.de_este_proyecto(P, todos)] == ["clips/a.mp4", "fotos/b.jpg"]


def test_el_doble_empalma_y_ninguna_estela_se_pierde(tmp_path, monkeypatch):
    _proyecto_con_medios("16-laboratorio-de-la-noche")
    p = Proyecto("16-laboratorio-de-la-noche", "doble-siempre")
    monkeypatch.setattr(Proyecto, "timeline", property(lambda self: tmp_path / "timeline.json"))
    pulso.planificar(p)
    tl = json.loads((tmp_path / "timeline.json").read_text(encoding="utf-8"))
    fps, capas = tl["fps"], tl["capas"]
    tomas = [c for c in capas if c["mezcla"] == "normal"]
    cambios = sum(a["img"] != b["img"] for a, b in zip(tomas, tomas[1:]))
    dobles = [c for c in capas if "#doble-" in c["id"] and not c["id"].endswith("b")]
    assert len(dobles) == cambios and sum("#estela-" in c["id"] for c in capas) == cambios
    for d in dobles:
        # Termina cuando la toma de verdad acabó de entrar o, si tuvo que ir más lento, justo en el cambio.
        real = next(c for c in tomas if c["img"] == d["img"] and (abs(c["ini"] + c["entrada"] - d["fin"]) <= 1 or c["ini"] == d["fin"]))
        va_por = d["video"]["desde"] + (real["ini"] - d["ini"]) / fps * d["video"]["velocidad"]
        # Cuando entra la toma de verdad, el fantasma va por el mismo segundo del clip (antes, hasta 1,7 s de salto).
        assert abs(va_por - real["video"]["desde"]) < 0.2, d["id"]
        if d["fin"] == real["ini"] and real["entrada"] >= 2:
            # …y desde el cambio lo releva otro tramo, pegado a la toma de verdad: mismo segundo, misma velocidad, sin parpadeo.
            relevo = next(c for c in capas if c["id"] == d["id"] + "b")
            assert relevo["ini"] == real["ini"] and relevo["entrada"] == 0 and d["salida"] == 0
            assert relevo["video"]["desde"] == real["video"]["desde"] and relevo["video"]["velocidad"] == real["video"]["velocidad"]


def test_los_fantasmas_van_donde_va_su_clip(tmp_path, monkeypatch):
    # En un vertical el recorte sigue al sujeto: la estela tiene que quedar encima de su clip, no al centro del cuadro.
    _proyecto_con_medios("20-anoranza-para-redes")
    p = Proyecto("20-anoranza-para-redes", "9-16")
    monkeypatch.setattr(Proyecto, "timeline", property(lambda self: tmp_path / "timeline.json"))
    pulso.planificar(p)
    capas = json.loads((tmp_path / "timeline.json").read_text(encoding="utf-8"))["capas"]
    estelas = [c for c in capas if "#estela-" in c["id"]]
    assert estelas
    corridas = 0
    for e in estelas:
        k = e["id"].split("#estela-")[1]
        real = next(c for c in capas if c["id"].endswith(f"#{k}"))
        avance = (e["ini"] - real["ini"]) / (real["fin"] - real["ini"])
        assert abs(e["x"] - (real["x"] + real["deriva"][0] * avance)) < 0.2 and e["ancho"] == real["ancho"], e["id"]
        corridas += abs(e["x"] - 540) > 5
    assert corridas  # si todas quedaran al centro, la prueba no estaría probando nada


# ── Fotos y clips juntos ───────────────────────────────────────────────────

def test_intercalar_un_clip_una_foto():
    c = lambda i, foto=False: {"id": i, **({"foto": True} if foto else {})}  # noqa: E731
    mezcla = pulso._intercalar([c("a"), c("b"), c("c"), c("f1", True), c("f2", True)])
    assert [x["id"] for x in mezcla] == ["a", "f1", "b", "f2", "c"]
    assert pulso._intercalar([c("a"), c("b")]) == [c("a"), c("b")]  # sin fotos, como estaba


def test_material_puede_pedir_solo_fotos_o_solo_clips():
    clip, foto = {"id": "natalia-06-playa-olas"}, {"id": "natalia-06-playa-olas-1", "foto": True}
    assert pulso._es_material(clip, "playa") and pulso._es_material(foto, "playa")
    assert pulso._es_material(foto, "foto:playa") and not pulso._es_material(clip, "foto:playa")
    assert pulso._es_material(clip, "clip:playa") and not pulso._es_material(foto, "clip:playa")


def test_una_foto_no_tiene_segundos_que_elegir():
    assert clips.mejor_tramo({**clip_falso(), "foto": True}, 30.0) == 0.0


def test_las_fotos_entran_solo_si_el_montaje_las_pide(tmp_path, monkeypatch):
    _proyecto_con_medios("21-laboratorio-de-la-manana")
    if not any(c.get("foto") for c in clips.cargar(Proyecto("21-laboratorio-de-la-manana"))):
        pytest.skip("el catálogo no tiene fotos")
    monkeypatch.setattr(Proyecto, "timeline", property(lambda self: tmp_path / f"timeline-{self.version}.json"))
    for version, con_fotos in (("cortina", False), ("mixto", True)):
        p = Proyecto("21-laboratorio-de-la-manana", version)
        pulso.planificar(p)
        capas = json.loads(p.timeline.read_text(encoding="utf-8"))["capas"]
        assert any(c["video"].get("foto") for c in capas) is con_fotos, version
        # Una foto empieza ya acercada: su deslizamiento nunca destapa el fondo.
        for c in capas:
            if c["video"].get("foto"):
                assert min(c["zoom"]) > 1 and abs(c["deriva"][0]) <= (max(c["zoom"][1], 1) - 1) / 2 * c["ancho"] + 1e-6, c["id"]


# ── Barrer una perilla ─────────────────────────────────────────────────────

def test_barrido_lee_numeros_palabras_y_si_no():
    from montaje import cli

    assert cli.valores_del_barrido("fundido_golpes=0.5,1, 2") == ("fundido_golpes", [0.5, 1, 2])
    assert cli.valores_del_barrido("transicion=cortina,iris") == ("transicion", ["cortina", "iris"])
    assert cli.valores_del_barrido("seguir=true,false") == ("seguir", [True, False])
    assert cli.valores_del_barrido("rejilla=[3,3,0.25];[2,2,0.5]") == ("rejilla", [[3, 3, 0.25], [2, 2, 0.5]])
    with pytest.raises(SystemExit):
        cli.valores_del_barrido("fundido_golpes")


def test_una_variante_no_escribe_en_el_repo():
    from montaje import cli
    from montaje.rutas import RAIZ

    if not (PROYECTOS / "21-laboratorio-de-la-manana" / "proyecto.json").exists():
        pytest.skip("no está el 21")
    v = cli._Variante("21-laboratorio-de-la-manana", "cortina", "fundido_golpes", 4)
    assert v.cfg["montaje"]["fundido_golpes"] == 4 and v.cfg["montaje"]["transicion"] == "cortina"
    assert RAIZ not in v.timeline.parents and v.timeline.name == "timeline-cortina-fundido_golpes-4.json"


# ── La mesa de selección ───────────────────────────────────────────────────

@pytest.mark.parametrize("texto,grupo", [
    ("Static shot of a Curiana Canoe adrift", "historia"),
    ("slice of life in Caracas", "ciudad"),
    ("a fishing boat at the distance", "mar"),
    ("still shot of a tree slowly moving", "campo"),
    ("Spaceship going through a wormhole", "ficción"),
    ("morbid oil vistas in Paraguana", "petróleo"),
    ("slice of life human interaction in a stilt house", "gente"),
    ("algo que no dice nada", "otros"),
])
def test_grupo_de_un_clip_por_su_nombre(texto, grupo):
    assert seleccion.grupo_de(texto) == grupo


def test_lo_elegido_manda_sobre_el_catalogo(tmp_path):
    (tmp_path / "seleccion.json").write_text(json.dumps({"elegidos": ["a"]}), encoding="utf-8")

    class P:
        cfg = {"clips": ["clips", "transformados"]}
        dir = tmp_path
    todos = [{"id": "a", "src": "clips/a.mp4"}, {"id": "b", "src": "clips/b.mp4"},
             {"id": "a-eco", "src": "transformados/a-eco.mp4"}, {"id": "b-eco", "src": "transformados/b-eco.mp4"}]
    assert [c["id"] for c in clips.de_este_proyecto(P, todos)] == ["a", "a-eco"]


# ── Transcribir ────────────────────────────────────────────────────────────

def _segmento(texto, ini=0.0, paso=0.5):
    ps = [{"p": p, "ini": round(ini + i * paso, 3), "fin": round(ini + (i + 1) * paso, 3), "prob": 0.9} for i, p in enumerate(texto.split())]
    return {"ini": ini, "fin": ps[-1]["fin"], "texto": texto, "palabras": ps}


def test_lineas_de_rotulos_cortan_y_guardan_cada_tiempo():
    s = _segmento("uno dos tres cuatro cinco seis siete ocho nueve diez")
    lineas = transcribir.lineas_de_rotulos([s], max_palabras=7)
    assert [len(x["texto"].split()) for x in lineas] == [7, 3]
    assert lineas[1]["t"] == 3.5 and lineas[1]["tiempos"] == [3.5, 4.0, 4.5]


def test_lineas_de_rotulos_prefieren_la_puntuacion_sin_dejar_sueltas():
    lineas = transcribir.lineas_de_rotulos([_segmento("vuelve el mar, despacio como una postal")])
    assert lineas[0]["texto"] == "vuelve el mar,"
    assert [x["texto"] for x in transcribir.lineas_de_rotulos([_segmento("vuelve el mar, ya")])] == ["vuelve el mar, ya"]


def test_las_lineas_entran_tal_cual_en_la_capa_rotulos():
    lineas = transcribir.lineas_de_rotulos([_segmento("hola a todos desde paraguana", ini=1.0)])
    g = sintesis._rotulos({**sintesis.POR_DEFECTO["rotulos"], "lineas": lineas}, musica_falsa(), 24, 24 * 16)
    assert g["lineas"][0]["palabras"][0] == ["hola", 24]  # con tiempos propios no se mueve al golpe


def test_srt_con_su_formato():
    assert "00:01:02,500 --> 00:01:03,000" in transcribir.srt([{"ini": 62.5, "fin": 63.0, "texto": "hola"}])


# ── Medir un render ────────────────────────────────────────────────────────

def _cuadros_falsos(n=240, fps=24.0):
    """Diez segundos de un video sano: luz pareja y cada cuadro distinto del anterior."""
    return np.full(n, 110.0), np.full(n - 1, 3.0), fps


def test_revisar_un_video_sano_no_avisa():
    luz, dif, fps = _cuadros_falsos()
    m = revisar.medir_cuadros(luz, dif, fps)
    assert m["negro_s"] == 0 and m["repetidos"] == 0 and m["destellos_max_por_s"] == 0
    assert revisar.avisos({**m, "pico_dbtp": -1.5}) == []


def test_revisar_negro_en_el_medio_y_no_en_los_bordes():
    luz, dif, fps = _cuadros_falsos()
    luz[96:144] = 2.0  # dos segundos de negro en el segundo 4
    m = revisar.medir_cuadros(luz, dif, fps)
    assert m["negro_mas_largo_s"] == 2.0 and m["negro_en_s"] == 4.0
    assert any("negro en el medio" in a for a in revisar.avisos(m))
    luz, dif, fps = _cuadros_falsos()
    luz[:48] = 2.0  # el fundido desde negro del comienzo no es un problema
    assert not any("negro" in a for a in revisar.avisos(revisar.medir_cuadros(luz, dif, fps)))


def test_revisar_camara_lenta_que_repite_cuadros():
    luz, dif, fps = _cuadros_falsos()
    dif[::5] = 0.0  # uno de cada cinco cuadros es igual al anterior
    m = revisar.medir_cuadros(luz, dif, fps)
    assert 0.19 < m["repetidos"] < 0.21
    assert any("repetidos" in a for a in revisar.avisos(m))


def test_revisar_cuenta_los_destellos_por_segundo():
    luz, dif, fps = _cuadros_falsos()
    luz[48:72:4] = 250.0  # seis fogonazos de un cuadro en un segundo
    m = revisar.medir_cuadros(luz, dif, fps)
    assert m["destellos_max_por_s"] > 3
    assert any("destellos" in a for a in revisar.avisos(m))
    # Un solo fogonazo (la transición `destello`) es un destello.
    luz, dif, fps = _cuadros_falsos()
    luz[60:64] = 250.0
    assert revisar.medir_cuadros(luz, dif, fps)["destellos_max_por_s"] == 1


def test_revisar_tres_destellos_son_tres_y_no_avisa():
    # Lo que la pauta permite: antes contaba cambios de sentido y decía cinco.
    luz = np.full(240, 60.0)
    luz[[30, 38, 46]] = 200.0
    assert revisar.destellos_por_segundo(luz, 24.0) == 3
    assert not any("destellos" in a for a in revisar.avisos(revisar.medir_cuadros(luz, np.full(239, 3.0), 24.0)))


def test_revisar_ve_los_destellos_en_rampa():
    # Un estrobo de 5 por segundo que sube y baja de a 20 por cuadro: ningún salto entre cuadros pasa el umbral, la ida y vuelta sí.
    t = np.arange(240) / 24.0
    luz = 110 + 60 * np.abs(((t * 5) % 1) * 2 - 1)
    assert np.abs(np.diff(luz)).max() < revisar.SALTO
    assert revisar.destellos_por_segundo(luz, 24.0) >= 4


def test_revisar_un_corte_a_una_escena_clara_no_es_un_destello():
    luz = np.concatenate([np.full(120, 40.0), np.full(120, 180.0)])
    assert revisar.destellos_por_segundo(luz, 24.0) == 0


def test_rotulos_dos_frases_en_el_mismo_golpe_no_pierden_ninguna(capsys):
    m = {"bpm": 100.0, "beats": [i * 0.6 for i in range(60)]}
    prm = {**sintesis.POR_DEFECTO["rotulos"], "cada": "golpe",
           "lineas": [[10.0, "hola"], [10.2, "mundo entero"], [14.0, "una frase de seis palabras largas"], [16.0, "sigue"]]}
    g = sintesis._rotulos(prm, m, 24, 24 * 40)
    assert [" ".join(p for p, _ in l["palabras"]) for l in g["lineas"]] == ["hola", "mundo entero", "una frase de seis palabras largas", "sigue"]
    for l in g["lineas"]:
        assert all(l["ini"] <= c < l["fin"] for _, c in l["palabras"]), l  # cada palabra llega a verse
    assert "se apura" in capsys.readouterr().out


# ── El esqueleto del guion ─────────────────────────────────────────────────

def test_guion_papel_de_cada_seccion():
    energias = [0.38, 0.71, 0.47, 0.72, 0.17, 0.25]  # la canción del 15
    papeles = [guion.papel(i, energias, 0.45, 0.8) for i in range(len(energias))]
    assert papeles == ["abrir", "subir la energía", "respirar", "subir la energía", "respirar", "cerrar"]


def test_guion_candidatos_aprobado_primero_y_nunca_rechazado():
    def e(id_, estado, para, energia="calma", material="clips", tecnica=None):
        return {"id": id_, "estado": estado, "para": para, "energia": energia, "material": material, "tecnica": tecnica or {"modo": "pulso"}}
    cat = [e("z-propuesta", "propuesta", ["abrir"]), e("a-rechazado", "rechazado", ["abrir"]), e("m-aprobado", "aprobado", ["abrir"], energia="alta"),
           e("de-fotos", "aprobado", ["abrir"], material="fotos"), e("capa", "propuesta", ["abrir"], material="cualquiera", tecnica={"capa": "recuerdo"}),
           e("otra-cosa", "aprobado", ["loop"], energia="alta")]
    base, encima = guion.candidatos(cat, "abrir", "calma", "clips")
    assert [x["id"] for x in base] == ["m-aprobado", "z-propuesta"]  # ni el rechazado, ni el de fotos, ni el que no sirve para abrir
    assert [x["id"] for x in encima] == ["capa"]


def test_guion_receta_de_un_estilo_para_un_tramo():
    pulso_ = {"tecnica": {"modo": "pulso", "corte": "frase", "congelar_golpes": 4, "reparto": "ronda"}}
    assert guion.receta_de_tramo(pulso_) == {"corte": "frase", "congelar_golpes": 4}  # lo global no va en un tramo
    con_nota = {"tecnica": {"modo": "pulso", "escala": 0.62, "sintesis": ["campo", "polvo"]}}
    assert guion.receta_de_tramo(con_nota) == {"escala": 0.62}  # una nota de la receta no es una perilla
    assert guion.receta_de_tramo({"tecnica": {"modo": "pulso", "muro": [3, 3]}}) is None
    assert guion.receta_de_tramo({"tecnica": {"modo": "collage"}}) is None
    capa = guion.capa_de({"tecnica": {"capa": "luz", "golpe": 0.06, "con": "otra cosa"}}, 10, 20)
    assert capa == {"tipo": "luz", "golpe": 0.06, "desde": 10, "hasta": 20}
    assert guion.capa_de({"tecnica": {"capa": "rotulos", "voz": "cartel"}}, 0, 5) is None  # pide un texto


def test_el_primer_armado_del_guion_se_puede_planificar(tmp_path, monkeypatch):
    _proyecto_con_medios("19-anoranza-con-guion")
    p = Proyecto("19-anoranza-con-guion")
    _, _, armado = guion.esqueleto(p)
    assert armado["tramos"] and all(t["hasta"] > t["desde"] for t in armado["tramos"])
    p.cfg["montaje"] = {**{k: v for k, v in p.cfg["montaje"].items() if k != "tramos"}, "tramos": armado["tramos"]}
    p.cfg["sintesis"] = armado["sintesis"]
    monkeypatch.setattr(Proyecto, "timeline", property(lambda self: tmp_path / "timeline.json"))
    from montaje import planificar

    planificar.planificar(p)
    tl = json.loads((tmp_path / "timeline.json").read_text(encoding="utf-8"))
    dur = {c["proxy"]: c["duracion"] for c in clips.cargar(p)}
    assert tl["capas"] and len(tl.get("sintesis", [])) == len(armado["sintesis"])
    for c in tl["capas"]:
        v = c["video"]
        assert c["fin"] > c["ini"] and v["desde"] + (c["fin"] - c["ini"]) / tl["fps"] * v["velocidad"] <= dur[c["img"]] + 1e-3, c["id"]


def test_material_en_orden_sigue_la_lista_del_guion():
    grupo = [{"id": "a-mar"}, {"id": "b-campo"}, {"id": "c-gente"}]
    assert [c["id"] for c in pulso._en_orden(grupo, ["gente", "mar", "campo"])] == ["c-gente", "a-mar", "b-campo"]


def test_lo_elegido_incluye_sus_transformados():
    elegidos = {"natalia-01", "mj-006"}
    assert clips._es_elegido("mj-006", False, elegidos)
    assert not clips._es_elegido("mj-007", False, elegidos)
    assert clips._es_elegido("natalia-01-eco", True, elegidos)
    assert not clips._es_elegido("natalia-01-eco", False, elegidos)  # sólo si de verdad está en transformados/


def test_por_tramos_parte_por_el_guion_y_corta_lo_largo():
    cfg = {"montaje": {"tramos": [{"desde": 0, "hasta": 10}, {"desde": 10, "hasta": 120}]}}
    marcas = por_tramos.bordes(cfg, 24, 120 * 24)
    assert marcas[0] == 0 and marcas[-1] == 2880 and 240 in marcas
    assert all(b - a <= por_tramos.LARGO_MAX * 24 for a, b in zip(marcas, marcas[1:]))
    assert por_tramos.bordes({}, 24, 240) == [0, 240]


def _linea_falsa() -> dict:
    return {"ancho": 100, "alto": 100, "fps": 24, "fondo": "#000", "duracion": 480, "meta": {"generado": "hoy"}, "audio": {"src": "x"},
            "capas": [{"id": "uno", "img": "a.mp4", "ini": 0, "fin": 240}, {"id": "dos", "img": "b.mp4", "ini": 240, "fin": 480}],
            "sintesis": [{"tipo": "recuerdo", "ini": 0, "fin": 480, "grano": 0.1}, {"tipo": "titulo", "ini": 0, "fin": 100, "texto": "hola"}]}


def test_por_tramos_cambiar_un_tramo_no_invalida_el_otro(tmp_path):
    tl = _linea_falsa()
    h = lambda t, a, b: por_tramos.huella(t, a, b, tmp_path, ["--scale=0.5"], "codigo")  # noqa: E731
    antes = h(tl, 0, 240), h(tl, 240, 480)
    tl["capas"][1]["img"] = "otro.mp4"
    tl["meta"]["generado"] = "mañana"
    assert h(tl, 0, 240) == antes[0] and h(tl, 240, 480) != antes[1]
    tl["sintesis"][1]["texto"] = "chao"
    assert h(tl, 0, 240) != antes[0]
    assert h(tl, 240, 480) == h(tl, 240, 480)
    # Otros ajustes o otro código: nada de lo guardado sirve.
    otra = _linea_falsa()
    assert por_tramos.huella(otra, 0, 240, tmp_path, ["--scale=1"], "codigo") != antes[0]
    assert por_tramos.huella(otra, 0, 240, tmp_path, ["--scale=0.5"], "otro") != antes[0]


def test_por_tramos_nota_si_el_archivo_cambia(tmp_path):
    (tmp_path / "a.mp4").write_bytes(b"123")
    tl = _linea_falsa()
    antes = por_tramos.huella(tl, 0, 240, tmp_path, [], "c")
    (tmp_path / "a.mp4").write_bytes(b"123456")
    assert por_tramos.huella(tl, 0, 240, tmp_path, [], "c") != antes


def test_por_tramos_no_parte_lo_que_tiene_sonido_propio():
    assert por_tramos.tiene_sonido_propio([{"video": {"volumen": 0.4}}])
    assert not por_tramos.tiene_sonido_propio([{"video": {"velocidad": 0.5}}, {"video": {"volumen": 0}}])


def test_rotulos_leen_un_srt_corregido_a_mano(tmp_path):
    srt = "1\n00:00:01,000 --> 00:00:03,500\nuno dos tres\n\n2\n00:00:05,000 --> 00:00:06,000\ncuatro\ncinco\n"
    (tmp_path / "x.srt").write_text(srt, encoding="utf-8")
    # El .json trae el segundo de cada palabra de la primera línea; la segunda se corrigió (otra cantidad de palabras).
    (tmp_path / "x.json").write_text(json.dumps({"rotulos": [{"t": 1.0, "texto": "uno dos tres", "tiempos": [1.0, 1.4, 2.9]},
                                                              {"t": 5.0, "texto": "cuatro", "tiempos": [5.0]}]}), encoding="utf-8")
    lineas = sintesis.lineas_de_transcripcion(str(tmp_path / "x.srt"))
    assert [l["texto"] for l in lineas] == ["uno dos tres", "cuatro cinco"]
    assert lineas[0]["tiempos"] == [1.0, 1.4, 2.9]
    assert lineas[1]["tiempos"][0] == 5.0 and 5.0 < lineas[1]["tiempos"][1] < 6.0


def test_tomas_proporcion_y_movimiento():
    assert tomas.proporcion(1620, 1080) == "3:2" and tomas.proporcion(1080, 1920) == "9:16" and tomas.proporcion(1080, 1350) == "4:5"
    assert tomas.movimiento(0.2, 0.45, 0.8)[1] == "low" and tomas.movimiento(0.9, 0.45, 0.8)[1] == "high"


def test_tomas_son_las_frases_del_montaje():
    # Una toma por frase: las mismas que después monta `pulso` (si están la canción y el timeline del 22).
    p = Proyecto("22-anoranza-con-mas-material", "lenta")
    if not (p.salidas / "analisis" / "musica.json").exists() or not p.timeline.exists():
        pytest.skip("faltan los medios del 22")
    ts, _, _ = tomas.lista(p)
    tl = json.loads(p.timeline.read_text(encoding="utf-8"))
    principales = [c for c in tl["capas"] if "video" in c and "#" in c["id"] and c["id"].split("#")[1].isdigit()]
    assert len(ts) == len({c["id"].split("#")[1] for c in principales})
    assert len({t["id"] for t in ts}) == len(ts)


LECCION_PRUEBA = {"id": "x", "cuando": {"energia": ["alta"], "modo": "pulso", "tono": ["recuerdo"]}, "perillas": {"velocidad": [0.4, 0.5]}}


def test_una_leccion_vale_solo_donde_dice():
    tramo = {"frase_compases": 1}
    assert aprender.sobre_tramo(tramo, "alta", "pulso", "recuerdo", [LECCION_PRUEBA]) == ["x"] and tramo["velocidad"] == [0.4, 0.5]
    for energia, tono in (("calma", "recuerdo"), ("alta", "fiesta"), ("alta", None)):
        otro = {}
        assert aprender.sobre_tramo(otro, energia, "pulso", tono, [LECCION_PRUEBA]) == [] and otro == {}
    # Sin tono en el proyecto no se impone: se avisa.
    assert [lc["id"] for lc in aprender.faltan_por_tono("alta", "pulso", None, [LECCION_PRUEBA])] == ["x"]
    assert aprender.faltan_por_tono("calma", "pulso", None, [LECCION_PRUEBA]) == []


def test_la_letra_entra_solo_si_esta_transcrita():
    leccion = {"id": "letra", "cuando": {"letra": True}, "capa": {"tipo": "rotulos", "lugar": "centro"}}
    assert aprender.capas({"musica": "musica/una cancion que no existe.wav"}, [leccion]) == []
    assert aprender.nombre_de_audio("musica/La Añoranza de Natalia.wav") == "la-anoranza-de-natalia"


def test_las_lecciones_del_repo_tienen_cita_y_regla():
    for lc in aprender.leer():
        assert lc["cita"] and lc["regla"] and lc["fecha"], lc["id"]
        assert lc.get("perillas") or lc.get("capa") or lc.get("consejo"), lc["id"]
        for k in lc.get("perillas", {}):
            assert k in pulso.POR_DEFECTO, f"{lc['id']}: {k} no es una perilla de pulso"


def test_comparar_veredictos():
    est = [{"estado": "aprobado", "tecnica": {"fundido_golpes": 2}}, {"estado": "aprobado", "tecnica": {"fundido_golpes": 4}},
           {"estado": "rechazado", "tecnica": {"fundido_golpes": 0.25}}, {"estado": "propuesta", "tecnica": {"fundido_golpes": 9}}]
    f = aprender.comparar(est)[0]
    assert f["perilla"] == "? · fundido_golpes" and f["aprobado"] == [2.0, 4.0] and f["otro"] == [0.25]


def test_aplicar_lo_que_cambio_en_la_mesa():
    estilos = {e["id"]: e for e in estilos_mod.leer()}
    tramos = [{"nombre": "gente", "desde": 0, "hasta": 10, "transicion": "iris", "fundido_golpes": 2, "frase_compases": 2,
               "velocidad": [0.4, 0.5], "material": ["a", "b"], "estilos": ["transicion-iris"]}]
    leccion = {"id": "flota", "cuando": {"energia": ["media"], "modo": "pulso"}, "perillas": {"velocidad": [0.4, 0.5]}}
    dicho = guion.aplicar_cambios(tramos, {"T1": {"orden": ["b", "a"], "estilo": "clip-por-compas", "pasa": "caras"}}, estilos,
                                  ["media"], None, [leccion], validos={"a", "b"})
    t = tramos[0]
    assert t["material"] == ["b", "a"] and t["material_en_orden"] and t["pasa"] == "caras"
    assert "transicion" not in t and t["frase_compases"] == 1 and t["estilos"][0] == "clip-por-compas"
    assert t["velocidad"] == [0.4, 0.5]  # la lección manda sobre la receta (que trae 0,55–0,75)
    assert len(dicho) == 3
    with pytest.raises(SystemExit):
        guion.aplicar_cambios(tramos, {"T1": {"orden": ["zzz"]}}, estilos, ["media"], None, [], validos={"a", "b"})


def test_traer_nombra_la_carpeta_por_la_serie():
    from montaje import traer

    assert traer.carpeta_de("Añoranza de Natalia") == "cantera-anoranza-de-natalia"
    assert traer.carpeta_de("  ") == "cantera-serie"


def test_medios_fuera_del_repo():
    # La regla de la casa: lo pesado vive fuera de OneDrive.
    assert "OneDrive" not in str(MEDIOS)


# ── El probador ────────────────────────────────────────────────────────────

def _cancion_entera() -> dict:
    """Una canción de mentira a 120 BPM: un golpe cada 0,5 s, el primero del compás en 0, 2, 4…; calma y después la banda."""
    beats = [round(0.5 * i, 3) for i in range(80)]
    return {"archivo": "musica/x.wav", "tramo": [0, 40.0], "duracion": 40.0, "bpm": 120.0, "golpes_intro": 0, "beats": beats,
            "energia": [0.3 if t < 20 else 0.8 for t in beats], "fase_compas": 0, "primeros_tiempos": beats[::4],
            "secciones": [{"beat_ini": 0, "beat_fin": 40, "ini": 0.0, "fin": 20.0, "energia": 0.3},
                          {"beat_ini": 40, "beat_fin": 80, "ini": 20.0, "fin": 40.0, "energia": 0.8}]}


def test_probador_corta_la_cancion_en_el_tramo_sin_reanalizarla():
    from montaje import probador

    # Escrito a mano, con dos decimales, cae cerca del primer tiempo: se ajusta a él.
    m = probador.cortar(_cancion_entera(), 15.99, 24.01)
    assert m["tramo"] == [16.0, 24.0] and m["duracion"] == 8.0
    assert m["beats"][0] == 0.0 and m["primeros_tiempos"] == [0.0, 2.0, 4.0, 6.0] and m["fase_compas"] == 0
    # La energía es la de la canción entera: la calma sigue siendo calma (analizar sólo el tramo la normalizaría).
    assert m["energia"][0] == 0.3 and m["energia"][-1] == 0.8
    assert [(s["ini"], s["fin"]) for s in m["secciones"]] == [(0.0, 4.0), (4.0, 8.0)]
    assert m["secciones"][0]["beat_fin"] == m["secciones"][1]["beat_ini"] == 8


def _banco() -> dict:
    return {"salida": {"ancho": 1620, "alto": 1080, "fps": 24}, "textos": {"titulo": "Banco", "rotulos": ["uno", "dos"], "credito": ["la canción", "sonando ahora"]}}


def test_probador_arma_la_receta_de_cada_tecnica(monkeypatch):
    from montaje import probador

    m = probador.cortar(_cancion_entera(), 16, 24)
    monkeypatch.setattr(probador, "_su_video", lambda e: {"sintesis": [
        {"tipo": "tinta", "oscuro": "rubrica", "claro": "hueso", "fuerza": 0.35, "desde": 120},
        {"tipo": "titulo", "texto": "lo que escribió Miguel", "tam": 0.1, "desde": 1.5}]})
    cfg = _banco()
    # Un estilo de pulso: sus perillas y su lienzo; lo que no es perilla (el modo, las notas) no pasa.
    r, _ = probador.receta({"tecnica": {"modo": "pulso", "frase_compases": 4, "salida": "1080x1920", "nota": "x"}}, cfg, m)
    assert r["montaje"] == {"frase_compases": 4} and r["salida"]["ancho"] == 1080 and r["salida"]["alto"] == 1920
    # Una capa: lo de su video, encima lo de la receta; las que acompañan en palabras toman sus valores de su video.
    r, _ = probador.receta({"tecnica": {"capa": "recuerdo", "grano": 0.3, "con": ["tinta rubrica/hueso 0.35", "nada"]}}, cfg, m)
    tipos = [c["tipo"] for c in r["sintesis"]]
    assert tipos == ["recuerdo", "tinta"] and r["sintesis"][0]["grano"] == 0.3
    tinta = r["sintesis"][1]
    assert tinta["oscuro"] == "rubrica" and tinta["fuerza"] == 0.35 and "desde" not in tinta  # el segundo 120 de su video no cabe
    # El texto es el del banco, nunca el de Miguel; el segundo en que entra, si cabe, se queda.
    r, _ = probador.receta({"tecnica": {"capa": "titulo", "letras_golpes": 3}}, cfg, m)
    assert r["sintesis"][0]["texto"] == "Banco" and r["sintesis"][0]["desde"] == 1.5 and r["sintesis"][0]["tam"] == 0.1
    r, _ = probador.receta({"tecnica": {"capa": "rotulos", "cada": "golpe"}}, cfg, m)
    assert r["sintesis"][0]["lineas"] == [[2.0, "uno"], [6.0, "dos"]]
    # Un efecto de tiempo: transformar los clips del banco y usar sólo esa variante.
    r, _ = probador.receta({"tecnica": {"comando": "transformar", "efecto": "eco", "fuerza": 0.6}}, cfg, m)
    assert r["montaje"] == {"transformados": "eco"} and r["transformar"] == ["eco", 0.6]
    # Lo que el banco todavía no sabe probar dice por qué.
    for tecnica in ({"modo": "collage"}, {"momento": "rafaga"}, {"comando": "sincronizar"}, {"comando": "senal"}):
        r, motivo = probador.receta({"tecnica": tecnica}, cfg, m)
        assert r is None and motivo


def test_probador_todas_las_recetas_de_la_galeria_se_arman_o_dicen_por_que():
    from montaje import probador

    m = probador.cortar(_cancion_entera(), 16, 24)
    for e in estilos_mod.leer():
        r, motivo = probador.receta(e, _banco(), m)
        assert (r is None) == bool(motivo), e["id"]
        if r:
            assert all(c["tipo"] in sintesis.POR_DEFECTO for c in r["sintesis"]), e["id"]
            assert all(k in pulso.POR_DEFECTO or k == "modo" for k in r["montaje"]), e["id"]


def test_transformados_con_el_nombre_de_un_efecto_usa_solo_esa_variante():
    # La perilla acepta los mismos nombres que `transformar`: el probador muestra un efecto solo.
    assert set(transformar.EFECTOS) <= set(pulso.EFECTOS_TRANSFORMAR)


def test_elegir_entre_dos_hace_un_orden_que_no_se_apura():
    t = estilos.puntajes([{"a": "x", "b": "y", "gana": "x"}, {"a": "x", "b": "z", "gana": "x"}, {"a": "y", "b": "z", "gana": "igual"}])
    assert t["x"]["ganadas"] == 2 and t["x"]["jugadas"] == 2 and t["x"]["puntaje"] == 0.75
    assert t["y"]["puntaje"] == t["z"]["puntaje"] == round(1.5 / 4, 3)
    # Con dos elecciones nadie llega a 1: dos no hacen un orden.
    assert max(v["puntaje"] for v in t.values()) < 1


def test_comparar_anota_y_valida(tmp_path, monkeypatch):
    monkeypatch.setattr(estilos, "COMPARACIONES", tmp_path / "COMPARACIONES.json")
    monkeypatch.setattr(estilos, "ESTILOS", tmp_path)
    for x in ("a", "b"):
        (tmp_path / f"{x}.json").write_text("{}", encoding="utf-8")
    estilos.comparar("a", "b", "b", via="galeria")
    assert estilos.comparaciones()[0]["gana"] == "b" and estilos.comparaciones()[0]["via"] == "galeria"
    for malo in (("a", "a", "a"), ("a", "b", "c"), ("a", "zzz", "a")):
        with pytest.raises(SystemExit):
            estilos.comparar(*malo)


# ── La galería de textos ──────────────────────────────────────────────────

def test_tipografias_del_registro_existen_con_su_licencia():
    from montaje import textos

    for familia, f in textos.registro().items():
        carpetas = {Path(a["archivo"]).parent for a in f["archivos"]}
        for a in f["archivos"]:
            assert (textos.FUENTES / a["archivo"]).is_file(), a["archivo"]
            assert a["peso"][0] <= a["peso"][1]
        # Libres: cada carpeta lleva su licencia al lado.
        assert all(any((textos.FUENTES / c / n).is_file() for n in ("OFL.txt", "LICENSE.txt")) for c in carpetas), familia


def test_galeria_de_textos_valida_y_usa_todas_las_tipografias():
    from montaje import textos

    todos = textos.leer()
    assert len(todos) >= 20
    assert {e["familia"] for e in todos} == set(textos.FAMILIAS)
    malos = {e["id"]: textos.errores(e) for e in todos if textos.errores(e)}
    assert not malos, malos
    usadas = {x["fuente"] for e in todos for x in (e, e.get("secundario") or {}) if x.get("fuente")}
    assert usadas == set(textos.registro())


def test_letrero_avisa_lo_que_no_existe():
    from montaje import textos

    base = {"nombre": "x", "familia": "titulos", "frase": "x", "para": ["abrir"], "fuente": "Lora", "tamano": 0.1, "color": "#ffffff",
            "lugar": "centro", "ejemplo": {"texto": "x"}, "fondo": "oscuro", "estado": "propuesta", "miguel": []}
    assert textos.errores(base) == []
    assert any("no está en fuentes" in m for m in textos.errores({**base, "fuente": "Comic Sans"}))
    assert any("peso 900" in m for m in textos.errores({**base, "peso": 900}))  # Lora llega a 700
    assert any("cursiva" in m for m in textos.errores({**base, "fuente": "Anton", "cursiva": True}))
    assert any("lugar" in m for m in textos.errores({**base, "lugar": "en todas partes"}))
    assert any("tamano" in m for m in textos.errores({**base, "tamano": 2}))


def test_planos_resuelve_el_letrero_y_pide_sus_tipografias():
    from montaje import planos, textos

    t = planos.texto_a_timeline(1, {"texto": "Hola", "letrero": "nombre-y-cargo", "secundario": "quien habla"}, 3, 90)
    assert t["ini"] == 3 and t["fin"] == 90 and t["secundario"] == "quien habla"
    e = t["letrero"]
    assert e["id"] == "nombre-y-cargo" and e["fuente"] == "Atkinson Hyperlegible Next"
    # Al timeline va sólo la forma, no lo de la galería.
    assert "nombre" not in e and "ejemplo" not in e and "estado" not in e
    archivos = textos.archivos([e])
    assert "atkinson-hyperlegible-next/AtkinsonHyperlegibleNext.ttf" in archivos and "ibm-plex-mono/IBMPlexMono-Regular.ttf" not in archivos
    # Sin letrero, siguen los estilos propios del modo.
    assert "letrero" not in planos.texto_a_timeline(1, {"texto": "x", "estilo": "cita"}, 0, 10)
    with pytest.raises(SystemExit):
        planos.texto_a_timeline(1, {"texto": "x", "letrero": "no-existe"}, 0, 10)


def test_el_veredicto_llega_a_los_letreros(tmp_path, monkeypatch):
    from montaje import textos

    (tmp_path / "estilos").mkdir()
    (tmp_path / "textos").mkdir()
    monkeypatch.setattr(estilos, "ESTILOS", tmp_path / "estilos")
    monkeypatch.setattr(textos, "TEXTOS", tmp_path / "textos")
    (tmp_path / "textos" / "un-letrero.json").write_text(json.dumps({"nombre": "Uno", "estado": "propuesta", "miguel": []}), encoding="utf-8")
    estilos.veredicto("un-letrero", "aprobado", via="galeria")
    e = json.loads((tmp_path / "textos" / "un-letrero.json").read_text(encoding="utf-8"))
    assert e["estado"] == "aprobado" and e["veredicto"]["via"] == "galeria"
    # El mismo nombre en las dos galerías no se adivina: se avisa.
    (tmp_path / "estilos" / "un-letrero.json").write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit):
        estilos.veredicto("un-letrero", "rechazado")


def test_apretar_una_tipografia_aprieta_todo_lo_horizontal(tmp_path):
    from fontTools.ttLib import TTFont

    from montaje import tipografias

    origen = tipografias.FUENTES / "archivo-black" / "ArchivoBlack-Regular.ttf"
    destino = tmp_path / "prueba" / "Prueba-Regular.ttf"
    tipografias.apretar(origen, destino, 0.5, "Prueba Angosta", "de prueba")
    o, n = TTFont(origen), TTFont(destino)
    assert n["name"].getDebugName(1) == "Prueba Angosta" and n["name"].getDebugName(6) == "PruebaAngosta-Regular"
    assert "Archivo Black" in n["name"].getDebugName(0)  # el aviso de la original sigue
    for g in ("A", "W", "space", "Aacute"):
        assert abs(n["hmtx"][g][0] - o["hmtx"][g][0] * 0.5) <= 0.5
    # El alto no cambia; el ancho sí.
    assert n["glyf"]["H"].yMax == o["glyf"]["H"].yMax and abs(n["glyf"]["H"].xMax - o["glyf"]["H"].xMax * 0.5) <= 1
    assert "fpgm" not in n  # sin el hinting de la original


def test_curiana_cartel_es_archivo_black_al_082():
    from fontTools.ttLib import TTFont

    from montaje import textos

    familias = textos.registro()
    assert "Curiana Cartel" in familias
    o = TTFont(textos.FUENTES / "archivo-black" / "ArchivoBlack-Regular.ttf")
    n = TTFont(textos.FUENTES / familias["Curiana Cartel"]["archivos"][0]["archivo"])
    assert all(abs(n["hmtx"][g][0] - o["hmtx"][g][0] * 0.82) <= 0.5 for g in o.getGlyphOrder())
    assert (textos.FUENTES / "curiana-cartel" / "OFL.txt").is_file()


def test_el_latido_toma_el_tempo_del_proyecto():
    from montaje import textos

    e = textos.estilo("latido-golpe", bpm=96)
    assert e["latido"]["bpm"] == 96.0
    with pytest.raises(SystemExit):
        textos.estilo("latido-golpe")  # late con la canción y no hay tempo


def test_los_subtitulos_saben_cuando_se_dice_cada_palabra(tmp_path, monkeypatch):
    import types

    from montaje import planos, rutas

    (tmp_path / "transcripciones").mkdir()
    palabras = [{"p": " Hola", "ini": 0.5, "fin": 0.9}, {"p": " radio.", "ini": 1.0, "fin": 1.4}]
    (tmp_path / "transcripciones" / "voz-1.json").write_text(json.dumps({"segmentos": [{"palabras": palabras}]}), encoding="utf-8")
    monkeypatch.setattr(rutas, "MEDIOS", tmp_path)
    p = types.SimpleNamespace(cfg={})
    subs = planos.subtitulos(p, [{"voz": {"archivo": "voz/voz-1-limpia.wav", "desde": 0.0}}], [(10.0, 20.0)])
    assert len(subs) == 1 and subs[0]["texto"] == "Hola radio."
    # El plano empieza en el segundo 10: las palabras se corren con él.
    assert subs[0]["palabras"] == [(10.5, 10.9), (11.0, 11.4)]
