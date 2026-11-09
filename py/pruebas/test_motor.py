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

from montaje import clips, estilos, guion, proyector, pulso, revisar, sintesis, transformar  # noqa: E402
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


def test_transicion_ronda_las_recorre_y_alterna():
    prm = {"transicion": "ronda", "transicion_dir": "alterna"}
    seis = len(pulso.TRANSICIONES) - 1
    tipos = [pulso._transicion(prm, n)[0] for n in range(seis)]
    assert sorted(tipos) == sorted(pulso.TRANSICIONES[1:])  # todas, una vez
    assert pulso._transicion(prm, 0)[1] == [1, 0] and pulso._transicion(prm, 1)[1] == [-1, 0]
    # El mismo tipo, en la vuelta siguiente, sale para el otro lado (antes, cada tipo iba siempre al mismo).
    for n in range(seis):
        assert pulso._transicion(prm, n)[0] == pulso._transicion(prm, n + seis)[0]
        assert pulso._transicion(prm, n)[1] != pulso._transicion(prm, n + seis)[1]
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


def test_medios_fuera_del_repo():
    # La regla de la casa: lo pesado vive fuera de OneDrive.
    assert "OneDrive" not in str(MEDIOS)
