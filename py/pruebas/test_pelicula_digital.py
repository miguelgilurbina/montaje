"""Pruebas de los aparatos de imagen de la mesa (`pelicula.py`, `digital.py`) y de los gestos de tiempo de `pulso`.

    python -m pytest py/pruebas -q
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from montaje import analogo as A  # noqa: E402
from montaje import digital as D  # noqa: E402
from montaje import pelicula as P  # noqa: E402
from montaje import pulso  # noqa: E402

H, W = 120, 160
QUIETA = {"grano": 0.0, "polvo": 0.0, "rayas": 0.0, "vineta": 0.0, "halo": 0.0, "parpadeo": 0.0, "vaiven": 0.0}


def correr(cadena, cuadros: list[np.ndarray], k0: int = 0, fps: float = 30.0, semilla: int | None = None):
    """Los cuadros (RGB 8 bits) por la cadena, uno tras otro desde el cuadro k0."""
    pasos, captura, s = A.preparar(cadena)
    ctx = A.Contexto(semilla or s, fps, cuadros[0].shape[0], cuadros[0].shape[1])
    sale = []
    for n, c in enumerate(cuadros):
        ctx.k, ctx.t = k0 + n, (k0 + n) / fps
        sale.append(A.procesar_cuadro(c, pasos, captura, ctx))
    return sale


def gris(v: float, h: int = H, w: int = W) -> np.ndarray:
    return np.full((h, w, 3), int(round(v * 255)), np.uint8)


def azar(semilla: int = 1, h: int = H, w: int = W) -> np.ndarray:
    return (np.random.default_rng(semilla).random((h, w, 3)) * 255).astype(np.uint8)


# ── La película ────────────────────────────────────────────────────────────

def test_a_18_cuadros_cada_uno_dura_dos_o_uno_del_video():
    vistos = [P.cuadro_de_pelicula(k, 30, 18) for k in range(10)]
    assert vistos == [0, 0, 1, 1, 2, 3, 3, 4, 4, 5]
    assert P.cuadro_de_pelicula(7, 30, 0) == 7 and P.cuadro_de_pelicula(7, 24, 30) == 7


def test_el_cuadro_de_pelicula_se_repite_con_su_grano_y_el_siguiente_cambia():
    img = azar()
    a, b, c = correr([{"aparato": "pelicula"}], [img, img, img])
    assert np.array_equal(a, b)
    assert not np.array_equal(b, c)


def test_el_gris_medio_queda_cerca_y_el_blanco_se_dobla_sin_recortar():
    medio = correr([{"aparato": "pelicula", **QUIETA}], [gris(0.46)])[0].mean() / 255
    assert abs(medio - 0.46) < 0.08
    blanco = correr([{"aparato": "pelicula", **QUIETA}], [gris(1.0)])[0].mean() / 255
    assert 0.8 < blanco < 0.97


def test_la_copia_destenida_tira_al_rojo():
    sana = correr([{"aparato": "pelicula", **QUIETA}], [gris(0.5)])[0].reshape(-1, 3).mean(axis=0)
    vieja = correr([{"aparato": "pelicula", **QUIETA, "desvanecido": 1.0}], [gris(0.5)])[0].reshape(-1, 3).mean(axis=0)
    assert vieja[0] > vieja[1] + 15 and vieja[0] > vieja[2] + 8
    assert abs(sana[0] - sana[2]) < abs(vieja[0] - vieja[2])


def test_el_halo_es_rojo_alrededor_de_la_luz():
    img = gris(0.08)
    img[50:70, 70:90] = 255
    sin = correr([{"aparato": "pelicula", **QUIETA}], [img])[0].astype(float)
    con = correr([{"aparato": "pelicula", **QUIETA, "halo": 2.0}], [img])[0].astype(float)
    anillo = np.zeros((H, W), bool)
    anillo[42:78, 62:98] = True
    anillo[48:72, 68:92] = False
    suma = (con - sin)[anillo].mean(axis=0)
    assert suma[0] > 2 and suma[0] > 3 * max(suma[2], 0.1)


def test_la_ventanilla_deja_las_esquinas_negras():
    sale = correr([{"aparato": "pelicula", "marco": "ventanilla"}], [gris(0.6)])[0]
    assert sale[0, 0].max() == 0 and sale[-1, -1].max() == 0
    assert sale[H // 2, W // 2].mean() > 60


def test_el_blanco_y_negro_es_gris_y_la_fecha_se_valida():
    sale = correr([{"aparato": "pelicula", "emulsion": "blanco-y-negro", "fecha": "'94 10 12"}], [azar()])[0].astype(int)
    assert np.abs(sale[..., 0] - sale[..., 1]).max() <= 1
    assert A.errores([{"aparato": "pelicula", "fecha": "hoy"}])
    assert not A.errores([{"aparato": "pelicula", "fecha": "'94 10 12"}])


def test_la_pelicula_sin_costura_entre_pedazos():
    """Un pedazo que empieza a mitad de un cuadro de película, calentado, ve lo mismo que el video seguido."""
    cuadros = [azar(s) for s in range(8)]
    cadena = [{"aparato": "pelicula", "polvo": 2.0, "rayas": 2.0, "pelo": 6.0}]
    seguido = correr(cadena, cuadros)
    pasos, _, _ = A.preparar(cadena)
    cal = A.calentar(pasos, 30.0)
    assert cal >= 2
    suelto = correr(cadena, cuadros[7 - cal:], k0=7 - cal)
    assert np.array_equal(seguido[7], suelto[-1])


# ── Lo digital ─────────────────────────────────────────────────────────────

def test_el_sensor_captura_a_sus_cuadros_y_pierde_algunas():
    p = {**A.POR_DEFECTO["sensor"], "cuadros": 15, "irregular": 1.0}
    ctx = A.Contexto(3, 30, H, W)
    capturas = []
    for k in range(400):
        ctx.k = k
        capturas.append(D.captura(ctx, p, 7))
    assert capturas[:2] == [capturas[0]] * 2
    assert (np.diff(capturas) >= 0).all()   # repite la anterior, nunca vuelve atrás
    assert all(c <= k * 15 / 30 + 1e-6 for k, c in enumerate(capturas))
    ideal = [int(k * 15 / 30) for k in range(400)]
    atrasos = [i - c for i, c in zip(ideal, capturas)]
    assert max(atrasos) <= 2 and any(atrasos)


def test_el_celular_sale_chico_con_barras_o_llenando():
    img = azar(2, 180, 320)
    con_barras = correr([{"aparato": "sensor", "resolucion": [176, 144]}], [img])[0]
    assert con_barras.shape == (180, 320, 3)
    assert con_barras[:, :20].max() == 0 and con_barras[:, -20:].max() == 0
    lleno = correr([{"aparato": "sensor", "resolucion": [176, 144], "encuadre": "llenar"}], [img])[0]
    assert lleno[:, :20].max() > 0


def gris_azar(semilla: int, h: int = H, w: int = W) -> np.ndarray:
    """Detalle sin color: lo que pierde el códec es por su cuantización, no por achicar el color."""
    v = (np.random.default_rng(semilla).random((h, w)) * 255).astype(np.uint8)
    return np.repeat(v[..., None], 3, axis=2)


def test_con_menos_calidad_se_pierde_mas():
    img = gris_azar(4)
    error = {q: np.abs(correr([{"aparato": "compresion", "modo": "jpeg", "calidad": q}], [img])[0].astype(float) - img).mean()
             for q in (0.1, 0.9)}
    assert error[0.1] > 2 * error[0.9]
    assert error[0.9] < 12


def test_sin_residuo_el_corte_se_derrite():
    """El datamosh: después de un corte sin cuadro clave, sin residuo el códec sigue moviendo lo de antes."""
    antes, despues = gris_azar(5, 128, 160), gris_azar(9, 128, 160)
    cuadros = [antes] * 3 + [np.roll(despues, 2 * n, axis=1) for n in range(4)]
    def lejos(residuo: float) -> float:
        sale = correr([{"aparato": "compresion", "calidad": 0.7, "gop": 30, "residuo": residuo}], cuadros)
        return float(np.abs(sale[-1].astype(float) - cuadros[-1]).mean())
    assert lejos(0.0) > 3 * lejos(1.0)


def test_sin_residuo_el_error_queda_hasta_el_cuadro_clave():
    img = azar(6, 64, 96)
    cadena = lambda e: [{"aparato": "compresion", "calidad": 0.6, "gop": 4, "residuo": 0.0, "errores": e}]  # noqa: E731
    limpio = correr(cadena(0.0), [img] * 12, semilla=1)
    roto = correr(cadena(1.0), [img] * 12, semilla=1)
    pasos, _, semilla = A.preparar(cadena(1.0))
    error_en = [np.random.default_rng([1 * 100 + 0, A._num("codec"), k]).random() < 0.35 for k in range(12)]
    vivo = False
    for k in range(12):
        if k % 4 == 0:
            vivo = False
        vivo = vivo or error_en[k]
        assert (not np.array_equal(limpio[k], roto[k])) == vivo, k


def test_lo_digital_sin_costura_entre_pedazos():
    cuadros = [np.roll(azar(7, 96, 128), 2 * n, axis=0) for n in range(30)]
    cadena = [{"aparato": "sensor", "resolucion": [96, 72], "cuadros": 15, "irregular": 0.6, "rodar": 1.0},
              {"aparato": "compresion", "gop": 5, "errores": 0.5}]
    seguido = correr(cadena, cuadros)
    pasos, _, _ = A.preparar(cadena)
    cal = A.calentar(pasos, 30.0)
    assert 10 <= cal < 29
    suelto = correr(cadena, cuadros[29 - cal:], k0=29 - cal)
    assert np.array_equal(seguido[29], suelto[-1])


def test_el_microfono_del_celular_corta_los_agudos():
    sr = A.SR_AUDIO
    t = np.arange(sr * 2) / sr
    p = {**A.POR_DEFECTO["sensor"], "sonido": "celular"}
    nivel = {}
    for f in (1000, 6000):
        x = np.stack([0.3 * np.sin(2 * np.pi * f * t)] * 2, axis=1).astype(np.float32)
        y = D.sonido("sensor", x, p, 1, 0.0, sr, 0)
        nivel[f] = np.sqrt(np.mean(y[sr // 2:, 0] ** 2))
    assert nivel[6000] < 0.2 * nivel[1000]
    assert D.sonido("sensor", x, {**p, "sonido": "ninguno"}, 1, 0.0, sr, 0) is x


def test_las_perillas_de_lo_digital_se_validan():
    assert A.errores([{"aparato": "sensor", "resolucion": [176, 144]}, {"aparato": "compresion"}]) == []
    mal = " ".join(A.errores([{"aparato": "sensor", "resolucion": [10, 5000]}, {"aparato": "compresion", "modo": "divx"}]))
    assert "resolucion" in mal and "divx" in mal


def test_una_pelicula_pasada_a_vhs():
    """Los dos mundos en una cadena: la película entra a la señal, y la cinta la recibe."""
    sale = correr([{"aparato": "pelicula"}, {"aparato": "cinta"}, {"aparato": "pantalla"}], [azar(8, 180, 320)])[0]
    assert sale.shape == (180, 320, 3) and sale.mean() > 10


# ── Lo que encontró la revisión (2026-11-21) ───────────────────────────────

def _sin_costura(cadena, cuadros, desde: int, fps: float = 30.0, cada: int = 1) -> list[int]:
    """Los cuadros (desde `desde`, cada `cada`) que salen distinto empezando un pedazo ahí, calentado, que en el
    video seguido."""
    seguido = correr(cadena, cuadros, fps=fps)
    pasos, _, _ = A.preparar(cadena)
    cal = A.calentar(pasos, fps)
    malos = []
    for k in range(desde, len(cuadros), cada):
        a = max(0, k - cal)
        if not np.array_equal(seguido[k], correr(cadena, cuadros[a:k + 1], k0=a, fps=fps)[-1]):
            malos.append(k)
    return malos


def test_el_sensor_irregular_no_se_cae_en_el_primer_cuadro():
    for semilla in range(1, 21):
        correr({"aparatos": [{"aparato": "sensor", "resolucion": [64, 48], "irregular": 1.0}], "semilla": semilla},
               [azar(semilla, 48, 64)] * 3)


def test_el_escaneo_cabe_en_una_salida_vertical_o_cuadrada():
    for h, w in ((320, 180), (200, 200)):
        for formato in P.FORMATOS:
            sale = correr([{"aparato": "pelicula", "marco": "escaneo", "formato": formato}], [azar(1, h, w)])[0]
            assert sale.shape == (h, w, 3)


def test_el_codigo_que_no_alcanza_a_calentarse_se_rechaza():
    assert A.errores([{"aparato": "sensor", "cuadros": 10}, {"aparato": "compresion", "gop": 120}])
    assert not A.errores([{"aparato": "sensor", "cuadros": 15}, {"aparato": "compresion", "gop": 30}])


def test_sin_costura_con_capturas_perdidas_y_obturador_rodante():
    cuadros = [np.roll(gris_azar(3, 48, 64), 2 * n, axis=1) for n in range(70)]
    cadena = {"aparatos": [{"aparato": "sensor", "resolucion": [64, 48], "cuadros": 10, "irregular": 0.8, "rodar": 1.0},
                           {"aparato": "compresion", "gop": 4}], "semilla": 5}
    assert _sin_costura(cadena, cuadros, 20) == []


def test_sin_costura_con_los_dropouts_de_la_minidv():
    cuadros = [gris_azar(s, 32, 64) for s in range(40)]
    for semilla in (1, 3):
        cadena = {"aparatos": [{"aparato": "compresion", "modo": "dv", "errores": 1.0}], "semilla": semilla}
        assert _sin_costura(cadena, cuadros, 3) == []


def test_la_fecha_es_naranja_en_la_pelicula_de_color():
    import colorsys

    for emulsion in ("kodachrome", "ektachrome"):
        sale = correr([{"aparato": "pelicula", **QUIETA, "emulsion": emulsion, "fecha": "88"}], [gris(0.05, 270, 480)])[0]
        brillo = sale.astype(float).sum(axis=2)
        r, g, b = sale[brillo > np.percentile(brillo, 99.7)].mean(axis=0) / 255
        tono = colorsys.rgb_to_hsv(r, g, b)[0] * 360
        assert 10 < tono < 42, (emulsion, tono, (r, g, b))


def test_el_codec_antes_del_sensor_ve_cada_cuadro():
    cuadros = [gris(v) for v in (0.1, 0.35, 0.6, 0.85)]
    sale = correr([{"aparato": "compresion", "modo": "jpeg", "calidad": 0.9}, {"aparato": "sensor", "resolucion": [W, H],
                   "ruido": 0.0, "rango": 0.0, "detalle": 0.0, "aliasing": 0.0}], cuadros)
    medias = [s.mean() / 255 for s in sale]
    assert all(abs(m - v) < 0.05 for m, v in zip(medias, (0.1, 0.35, 0.6, 0.85))), medias


def test_mas_perillas_que_se_validan():
    assert A.errores([{"aparato": "compresion", "busqueda": 2.5}])
    assert A.errores({"aparatos": [{"aparato": "pelicula"}], "semilla": -1})


# ── La casetera y la consola ───────────────────────────────────────────────

def rampa(n: int, h: int = H, w: int = W) -> list[np.ndarray]:
    """Cuadros cada vez más claros: lo que se ve dice de qué momento es."""
    return [gris(0.15 + 0.7 * k / (n - 1), h, w) for k in range(n)]


def _en_evento(semilla_cadena: int, paso: int, nombre: str, por_minuto: float, dura: float, fps: float, n: int):
    s = semilla_cadena * 100 + paso
    return [P.evento_con_id(s, nombre, k / fps, por_minuto, dura) for k in range(n)]


def test_la_pausa_retiene_el_cuadro_donde_empezo():
    cuadros = rampa(120)
    # Una semilla que tenga una pausa entera en estos cuatro segundos.
    semilla = next(s for s in range(1, 60) if any(e is not None and e[0] > 0.5 and k > 35
                                                  for k, e in enumerate(_en_evento(s, 0, "pausa", 10.0, 1.0, 30, 120))))
    sale = correr({"aparatos": [{"aparato": "casetera", "pausa": 10.0, "pausa_dura": 1.0}], "semilla": semilla}, cuadros)
    ev = _en_evento(semilla, 0, "pausa", 10.0, 1.0, 30, 120)
    k = next(k for k, e in enumerate(ev) if e is not None and e[0] > 0.5 and k > 35)
    inicio = k - next(j for j in range(k + 1) if ev[k - j] is None or ev[k - j][1] != ev[k][1])
    media = sale[k][:H // 2].mean() / 255   # arriba de la barra
    assert abs(media - cuadros[inicio + 1][0, 0, 0] / 255) < 0.06 and media < cuadros[k][0, 0, 0] / 255 - 0.05


def test_rebobinar_muestra_lo_de_antes():
    cuadros = rampa(150)
    sale = correr({"aparatos": [{"aparato": "casetera", "rebobinar": 10.0, "rebobinar_dura": 1.2}], "semilla": 4}, cuadros)
    ev = _en_evento(4, 0, "rebobinar", 10.0, 1.2, 30, 150)
    tarde = [k for k, e in enumerate(ev) if e is not None and e[0] > 0.6]
    assert tarde
    for k in tarde[:5]:
        assert sale[k].mean() / 255 < cuadros[k][0, 0, 0] / 255 - 0.1


def test_la_casetera_arranca_en_azul_con_play():
    sale = correr([{"aparato": "casetera", "inicio": 1.0}], [gris(0.5)] * 3)[0].reshape(-1, 3).mean(axis=0)
    assert sale[2] > sale[0] + 60


def test_el_entrelazado_peina_lo_que_se_mueve():
    a, b = gris_azar(1), gris_azar(2)
    sale = correr([{"aparato": "casetera", "entrelazado": 1.0}], [a, b])[1].astype(float)
    impares, pares = sale[1::2].mean(), sale[0::2].mean()
    assert abs(np.corrcoef(sale[1:H // 2:2, :, 0].ravel(), a[1:H // 2:2, :, 0].ravel())[0, 1]) > \
        abs(np.corrcoef(sale[1:H // 2:2, :, 0].ravel(), b[1:H // 2:2, :, 0].ravel())[0, 1])
    assert abs(impares - pares) < 20


def test_la_casetera_sin_costura():
    cuadros = [np.roll(gris_azar(5, 48, 64), 2 * n, axis=1) for n in range(160)]
    cadena = {"aparatos": [{"aparato": "casetera", "pausa": 12.0, "rebobinar": 12.0, "rebobinar_dura": 0.8,
                            "entrelazado": 0.6}], "semilla": 3}
    assert _sin_costura(cadena, cuadros[:160], 100, cada=11) == []


def test_el_estrobo_retiene_cada_tantos_cuadros():
    sale = correr([{"aparato": "consola", "efecto": "estrobo", "cada": 3}], rampa(9))
    assert np.array_equal(sale[0], sale[2]) and not np.array_equal(sale[2], sale[3]) and np.array_equal(sale[3], sale[5])


def test_el_multi_llena_sus_celdas_con_momentos_distintos():
    sale = correr([{"aparato": "consola", "efecto": "multi", "celdas": 2, "cada": 1}], rampa(4))[-1].astype(float)
    celdas = [sale[:H // 2, :W // 2], sale[:H // 2, W // 2:], sale[H // 2:, :W // 2], sale[H // 2:, W // 2:]]
    medias = [c[4:-4, 4:-4].mean() for c in celdas]
    assert medias == sorted(medias) and medias[-1] - medias[0] > 100


def test_a_ratos_la_consola_deja_pasar_la_imagen():
    cuadros = [gris_azar(s) for s in range(60)]
    sale = correr({"aparatos": [{"aparato": "consola", "efecto": "negativo", "cuando": "a ratos", "por_minuto": 6.0,
                                 "dura": 1.0}], "semilla": 2}, cuadros)
    activo = [A.evento(200, "consola", k / 30, 6.0, 1.0) is not None for k in range(60)]
    for k in range(60):
        igual = np.array_equal(sale[k], cuadros[k])
        assert igual != activo[k], k


def test_la_llave_y_el_multi_sin_costura():
    cuadros = [gris_azar(s, 48, 64) for s in range(60)]
    for aparato in ({"aparato": "consola", "efecto": "llave", "memoria": 0.5},
                    {"aparato": "consola", "efecto": "multi", "celdas": 3, "cada": 2}):
        assert _sin_costura([aparato], cuadros, 25) == []


# ── El tiempo al pulso ─────────────────────────────────────────────────────

def test_los_gestos_de_tiempo_caen_en_los_golpes():
    # Energía baja con un golpe fuerte de cada cuatro (2,5 · 4,5 · 6,5 s…): el pico es el cuarto de más energía.
    m = {"beats": [i * 0.5 for i in range(16)], "primeros_tiempos": [0.0, 2.0, 4.0, 6.0],
         "energia": [0.3, 0.35, 0.4, 0.38, 0.33, 0.62, 0.31, 0.36] * 2}
    pe = {**pulso.POR_DEFECTO, "congelar_golpe": 0.5, "congelar_cada": "compas", "tartamudeo": 3,
          "tartamudeo_golpes": 0.25, "tartamudeo_cada": "pico", "paso_de_cuadro": 2}
    t = pulso.tiempo_de_toma(pe, m, 30, 60, 180, 0.5)   # la toma va del cuadro 60 (2 s) al 180 (6 s)
    assert t["paso"] == 2
    assert t["congelados"] == [[0, 8], [60, 8]]          # los compases de 2 y 4 s; el de 6 s ya es de la otra toma
    # el cuarto de más energía: 1 s (0,40), 2,5 s (0,62), 5 s (0,40), 6,5 s (0,62); en la toma, 2,5 y 5 s
    assert [x[0] for x in t["tartamudeos"]] == [15, 90]
    assert all(x[1] == 4 and x[2] == 3 for x in t["tartamudeos"])
    assert pulso.tiempo_de_toma(pulso.POR_DEFECTO, m, 30, 60, 180, 0.5) is None
    # Mientras la toma entra (o la foto despierta) no hay gestos: el del cuadro 0 se cae, el del 60 queda.
    assert pulso.tiempo_de_toma(pe, m, 30, 60, 180, 0.5, desde=20)["congelados"] == [[60, 8]]
