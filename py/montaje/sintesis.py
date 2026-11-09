"""Capas hechas en código, al pulso de la canción (las dibuja src/Sintesis.tsx).

Van encima de cualquier montaje, salvo `campo`, que va de fondo. Se piden en
proyecto.json y `planificar` las agrega al timeline con lo que necesitan de la
canción (golpes, «uno», energía, espectro):

    "sintesis": [
      {"tipo": "recuerdo", "grano": 0.18, "vineta": 0.45, "calidez": 0.12, "parpadeo": 0.03, "temblor": 1.2, "halo": 0},
      {"tipo": "fugas", "cada_compases": 8, "golpes": 4, "fuerza": 0.45},
      {"tipo": "polvo", "motas": 70, "brillo": 0.6},
      {"tipo": "partitura", "y": 0.86, "alto": 0.12, "opacidad": 0.8},
      {"tipo": "campo", "opacidad": 1, "mezcla": "screen"},
      {"tipo": "tinta", "oscuro": "indigo", "claro": "oro", "fuerza": 0.85},
      {"tipo": "calima", "fuerza": 10, "golpe": 14},
      {"tipo": "tv", "lineas": 0.28, "corrimiento": 3, "curva": 0.06},
      {"tipo": "rotulos", "voz": "oraculo", "lugar": "abajo", "cada": "medio",
       "lineas": [{"t": 28, "texto": "la banda entra y el mar se llena"}, [41, "nadie se queda quieto"]]}
    ]

Tres más: `luz` (filtro: el brillo y el color del contenido siguen la energía de la
canción, con un latido en cada golpe), `barras` (las franjas negras del cine, que se
cierran al entrar y se abren al salir) y `rayas` (la película gastada: rayones
verticales que duran un rato y manchas de un cuadro).

`rotulos` son las frases del guion en pantalla: cada una entra en el golpe más cercano
a su `t`, palabra por palabra (`cada`: golpe, medio o todo), y se queda `dura` segundos
o hasta la siguiente. Con `tiempos` (un segundo por palabra) no usa los golpes: es por
donde van a entrar los subtítulos de una voz en off.

Cada una acepta `desde` y `hasta` (segundos del video) para ocupar sólo un tramo.
"""

from __future__ import annotations

import numpy as np

from . import musica
from .rutas import Proyecto, escribir_json, leer_json, salir

TINTAS = {"oro": "#e6b43c", "ocre": "#c36712", "rojo": "#b64924", "hueso": "#f3ead4",
          "indigo": "#26396a", "electrico": "#2154c5", "acido": "#c7c91c", "rubrica": "#8f3b26"}

POR_DEFECTO = {
    "recuerdo": {"grano": 0.18, "vineta": 0.45, "calidez": 0.12, "parpadeo": 0.03, "temblor": 1.2, "halo": 0.0, "semilla": 7, "fundido": 15},
    "fugas": {"cada_compases": 8, "golpes": 4, "fuerza": 0.45, "colores": ["oro", "ocre", "rojo", "hueso"], "semilla": 11},
    "polvo": {"motas": 70, "brillo": 0.6, "semilla": 5, "fundido": 30},
    "partitura": {"y": 0.86, "alto": 0.12, "opacidad": 0.8, "color": "#eee6d4", "bandas": 40, "fundido": 30},
    "campo": {"colores": ["indigo", "electrico", "ocre", "rubrica"], "opacidad": 1.0, "mezcla": "screen", "semilla": 3, "fundido": 30},
    "tinta": {"oscuro": "indigo", "claro": "oro", "fuerza": 0.85, "fundido": 24},
    "calima": {"fuerza": 10, "golpe": 14, "semilla": 9, "fundido": 24},
    "tv": {"lineas": 0.28, "corrimiento": 3, "curva": 0.06, "semilla": 13, "fundido": 12},
    "titulo": {"texto": "", "voz": "cartel", "tam": 0.11, "x": 0.5, "y": 0.5, "alinear": "centro", "color": "#eee6d4",
               "letras_golpes": 2, "dura": 6, "fundido": 18},
    "credito": {"lineas": ["", "sonando ahora"], "color": "#e6b43c", "dura": 7, "fundido": 14},
    "cuenta": {"numeros": 4, "semilla": 3, "fundido": 1},
    "pelicula": {"borde": 0.07, "velocidad": 1.5, "fundido": 12},
    "onda": {"fuerza": 40, "cada_compases": 2, "golpes_dura": 3, "fundido": 12},
    "foco": {"fuerza": 4, "cada": "golpe", "fundido": 12},
    "golpe": {"fuerza": 0.035, "cada": "compas", "fundido": 6},
    "luz": {"brillo": [0.8, 1.1], "color": [0.65, 1.15], "golpe": 0.05, "suave": 4, "fundido": 12},
    "barras": {"formato": 2.39, "abre_golpes": 4, "color": "#000000", "fundido": 0},
    "rayas": {"rayones": 0.5, "manchas": 0.5, "semilla": 21, "fundido": 12},
    "rotulos": {"lineas": [], "voz": "oraculo", "tam": 0.052, "lugar": "abajo", "color": "hueso", "cada": "medio", "dura": 4.0,
                "sombra": 0.5, "fundido": 10},
}


def aplicar(p: Proyecto, tl: dict) -> dict:
    """Agrega al timeline las capas de `sintesis` de proyecto.json (o las quita si ya no hay)."""
    pedidas = p.cfg.get("sintesis") or []
    if not pedidas:
        tl.pop("sintesis", None)
        return tl
    m = musica.cargar(p)
    fps, total = tl["fps"], tl["duracion"]
    capas = []
    for pedida in pedidas:
        tipo = pedida.get("tipo")
        if tipo not in POR_DEFECTO:
            salir(f"sintesis: tipo desconocido «{tipo}» (hay: {', '.join(POR_DEFECTO)})")
        prm = {**POR_DEFECTO[tipo], **pedida}
        ini = round(prm.get("desde", 0) * fps)
        fin = min(total, round(prm["hasta"] * fps)) if "hasta" in prm else total
        base = {"tipo": tipo, "ini": ini, "fin": fin}
        if "fundido" in prm:
            base["fundido"] = prm["fundido"]
        if tipo == "recuerdo":
            capas.append({**base, **{k: prm[k] for k in ("grano", "vineta", "calidez", "parpadeo", "temblor", "halo", "semilla")}})
        elif tipo == "fugas":
            capas.append({**base, "destellos": _fugas(m, prm, fps, ini, fin)})
        elif tipo == "polvo":
            golpes = [round(b * fps) for b in m["beats"] if ini <= b * fps < fin]
            capas.append({**base, "motas": prm["motas"], "golpes": golpes, "brillo": prm["brillo"], "semilla": prm["semilla"]})
        elif tipo == "partitura":
            capas.append({**base, "espectro": espectro(p, m, fps, prm["bandas"]), "desde": m.get("tramo", [0])[0],
                          "color": TINTAS.get(prm["color"], prm["color"]), "y": prm["y"], "alto": prm["alto"], "opacidad": prm["opacidad"]})
        elif tipo == "campo":
            energia = [[round(b * fps), round(float(e), 3)] for b, e in zip(m["beats"], m["energia"])]
            unos = [round(t * fps) for t in m["primeros_tiempos"] if ini <= t * fps < fin]
            capas.append({**base, "colores": [TINTAS.get(c, c) for c in prm["colores"]], "energia": energia, "golpes": unos,
                          "opacidad": prm["opacidad"], "mezcla": prm["mezcla"], "semilla": prm["semilla"]})
        elif tipo == "tinta":
            capas.append({**base, "oscuro": TINTAS.get(prm["oscuro"], prm["oscuro"]), "claro": TINTAS.get(prm["claro"], prm["claro"]),
                          "fuerza": prm["fuerza"]})
        elif tipo == "calima":
            golpes = [round(b * fps) for b in m["beats"] if ini <= b * fps < fin]
            capas.append({**base, "fuerza": prm["fuerza"], "golpe": prm["golpe"], "golpes": golpes, "semilla": prm["semilla"]})
        elif tipo in ("titulo", "credito", "cuenta"):
            capas.append(_grafico(tipo, prm, m, fps, ini, total))
        elif tipo == "luz":
            # La energía, suavizada sobre unos golpes: la luz sigue a la canción, no a cada nota.
            n = max(1, int(prm["suave"]))
            e = np.convolve(np.pad(np.array(m["energia"], dtype=float), (n // 2, n - 1 - n // 2), mode="edge"), np.ones(n) / n, mode="valid")
            capas.append({**base, "energia": [[round(b * fps), round(float(v), 3)] for b, v in zip(m["beats"], e)],
                          "golpes": [round(b * fps) for b in m["beats"] if ini <= b * fps < fin],
                          "brillo": prm["brillo"], "color": prm["color"], "golpe": prm["golpe"]})
        elif tipo == "barras":
            capas.append({**base, "formato": prm["formato"], "abre": round(prm["abre_golpes"] * 60 / m["bpm"] * fps), "color": prm["color"]})
        elif tipo == "rayas":
            capas.append({**base, "rayones": prm["rayones"], "manchas": prm["manchas"], "semilla": prm["semilla"]})
        elif tipo == "rotulos":
            capa = _rotulos(prm, m, fps, total)
            if capa:
                capas.append(capa)
        elif tipo in ("onda", "foco", "golpe"):
            golpe = 60 / m["bpm"]
            if tipo == "onda":
                cuando = m["primeros_tiempos"][:: max(1, int(prm["cada_compases"]))]
            else:
                cuando = m["primeros_tiempos"] if prm["cada"] == "compas" else m["beats"]
            golpes = [round(t * fps) for t in cuando if ini <= t * fps < fin]
            extra = {"dura": round(prm["golpes_dura"] * golpe * fps)} if tipo == "onda" else {}
            capas.append({**base, "golpes": golpes, "fuerza": prm["fuerza"], **extra})
        elif tipo == "pelicula":
            capas.append({**base, "borde": prm["borde"], "velocidad": prm["velocidad"]})
        elif tipo == "tv":
            capas.append({**base, "lineas": prm["lineas"], "corrimiento": prm["corrimiento"], "curva": prm["curva"], "semilla": prm["semilla"]})
    tl["sintesis"] = capas
    print(f"  síntesis: {', '.join(c['tipo'] for c in capas)}")
    return tl


def _grafico(tipo: str, prm: dict, m: dict, fps: int, ini: int, total: int) -> dict:
    """Título, crédito o cuenta regresiva, con sus tiempos puestos en los golpes de la canción."""
    beats = [round(b * fps) for b in m["beats"]]
    primero = next((b for b in beats if b >= ini), ini)  # el primer golpe desde `desde`
    golpe = int(np.median(np.diff(beats))) if len(beats) > 1 else fps // 2
    if tipo == "cuenta":
        n = int(prm["numeros"])
        # Cada número en su golpe de verdad (la canción no es un metrónomo: con la mediana, el «1» llegaba tarde);
        # si los golpes se acaban, sigue con el paso típico.
        desde_golpe = next((i for i, b in enumerate(beats) if b >= ini), len(beats))
        cuando = [beats[desde_golpe + k] if desde_golpe + k < len(beats) else primero + k * golpe for k in range(n + 1)]
        numeros = [[cuando[k], n - k] for k in range(n)]
        # Empieza con su primer número: entre `desde` y ese golpe no hay nada que dibujar.
        return {"tipo": "cuenta", "ini": cuando[0], "fin": cuando[n], "fundido": prm["fundido"], "numeros": numeros, "semilla": prm["semilla"]}
    fin = min(total, primero + round(prm["dura"] * fps))
    if tipo == "credito":
        return {"tipo": "credito", "ini": primero, "fin": fin, "fundido": prm["fundido"], "lineas": prm["lineas"], "color": TINTAS.get(prm["color"], prm["color"])}
    # Las letras se reparten en `letras_golpes` golpes, en la rejilla de la semicorchea.
    texto = prm["texto"]
    paso = max(1, round(golpe * prm["letras_golpes"] / max(1, len(texto))))
    letras = [primero + i * paso for i in range(len(texto))]
    return {"tipo": "titulo", "ini": primero, "fin": fin, "fundido": prm["fundido"], "texto": texto, "voz": prm["voz"], "tam": prm["tam"],
            "x": prm["x"], "y": prm["y"], "alinear": prm["alinear"], "color": TINTAS.get(prm["color"], prm["color"]), "letras": letras}


def _rotulos(prm: dict, m: dict, fps: int, total: int) -> dict | None:
    """Las frases del guion, cada una en su golpe y sus palabras en la rejilla del pulso."""
    beats = np.array(m["beats"], dtype=float)
    golpe = 60 / m["bpm"]
    if prm["cada"] not in ("golpe", "medio", "todo"):
        salir(f"rotulos: `cada` es golpe, medio o todo (no «{prm['cada']}»)")
    paso = {"golpe": golpe, "medio": golpe / 2, "todo": 0.0}[prm["cada"]]
    crudas = sorted(({"t": l[0], "texto": l[1]} if isinstance(l, (list, tuple)) else dict(l) for l in prm["lineas"]), key=lambda l: l["t"])
    crudas = [l for l in crudas if str(l.get("texto", "")).split()]
    # Cada frase arranca en el golpe más cercano a su `t` (con `tiempos`, donde diga).
    inicios = [float(beats[np.argmin(np.abs(beats - l["t"]))]) if len(beats) and "tiempos" not in l else float(l["t"]) for l in crudas]
    # Dos frases que caen en el mismo golpe: la segunda se corre al siguiente (antes, la primera desaparecía).
    for i in range(1, len(inicios)):
        if inicios[i] <= inicios[i - 1] and "tiempos" not in crudas[i]:
            despues = beats[beats > inicios[i - 1] + 1e-6]
            inicios[i] = float(despues[0]) if len(despues) else inicios[i - 1] + golpe
    lineas = []
    for i, (l, t0) in enumerate(zip(crudas, inicios)):
        palabras = str(l["texto"]).split()
        tiempos = l.get("tiempos") or [t0 + k * paso for k in range(len(palabras))]
        if len(tiempos) != len(palabras):
            salir(f"rotulos: «{l['texto']}» tiene {len(palabras)} palabras y {len(tiempos)} tiempos")
        # Si la frase que sigue llega antes de que ésta termine de escribirse, sus palabras se apuran
        # para caber y quedar completas al menos un golpe (antes, las últimas no llegaban a verse).
        if i + 1 < len(crudas) and "tiempos" not in l and len(palabras) > 1:
            ultima = inicios[i + 1] - 0.1 - max(0.6, golpe)
            if tiempos[-1] > ultima:
                if ultima > t0:
                    tiempos = [t0 + k * (ultima - t0) / (len(palabras) - 1) for k in range(len(palabras))]
                    print(f"  aviso: el rótulo «{l['texto']}» se apura para caber antes del siguiente")
                else:
                    print(f"  aviso: el rótulo «{l['texto']}» no cabe antes del siguiente ({inicios[i + 1] - t0:.1f} s): se corta")
        # Completa, se queda al menos dos golpes (o segundo y medio): si no, la última palabra no se alcanza a leer.
        t1 = max(tiempos[-1] + max(1.5, 2 * golpe), t0 + float(l.get("dura", prm["dura"])))
        if i + 1 < len(crudas):
            t1 = min(t1, inicios[i + 1] - 0.1)  # se va antes de que entre la siguiente
        ini, fin = round(t0 * fps), min(total, round(t1 * fps))
        if fin - ini < 2 or ini >= total:
            print(f"  aviso: el rótulo «{l['texto']}» queda fuera (no tiene ni dos cuadros): no se dibuja")
            continue
        lineas.append({"ini": ini, "fin": fin, "palabras": [[p, round(t * fps)] for p, t in zip(palabras, tiempos)]})
    if not lineas:
        return None
    return {"tipo": "rotulos", "ini": lineas[0]["ini"], "fin": max(l["fin"] for l in lineas), "fundido": prm["fundido"],
            "voz": prm["voz"], "tam": prm["tam"], "lugar": prm["lugar"], "color": TINTAS.get(prm["color"], prm["color"]),
            "sombra": prm["sombra"], "lineas": lineas}


def _fugas(m: dict, prm: dict, fps: int, ini: int, fin: int) -> list[dict]:
    """Una fuga de luz en el «uno» de cada `cada_compases` compases, más fuerte con más energía; entra por un borde."""
    rng = np.random.default_rng(prm["semilla"])
    beats = np.array(m["beats"])
    energia = np.array(m["energia"])
    golpe = 60 / m["bpm"]
    unos = m["primeros_tiempos"][:: max(1, int(prm["cada_compases"]))]
    destellos = []
    for k, t in enumerate(unos):
        a = round(t * fps)
        if not ini <= a < fin:
            continue
        e = float(energia[min(len(energia) - 1, int(np.searchsorted(beats, t)))])
        borde = rng.integers(4)
        x, y = [(rng.uniform(0.1, 0.9), -0.05), (1.05, rng.uniform(0.1, 0.9)), (rng.uniform(0.1, 0.9), 1.05), (-0.05, rng.uniform(0.1, 0.9))][borde]
        # Cruza hacia el centro un poco.
        dx, dy = (0.5 - x) * rng.uniform(0.15, 0.35), (0.5 - y) * rng.uniform(0.15, 0.35)
        destellos.append({
            "ini": a,
            "fin": min(fin, a + round(prm["golpes"] * golpe * fps)),
            "x": round(float(x), 3), "y": round(float(y), 3), "dx": round(float(dx), 3), "dy": round(float(dy), 3),
            "radio": round(float(rng.uniform(0.28, 0.45)), 3),
            "giro": round(float(rng.uniform(-40, 40)), 1),
            "color": TINTAS.get(prm["colores"][k % len(prm["colores"])], prm["colores"][k % len(prm["colores"])]),
            "fuerza": round(float(prm["fuerza"] * (0.55 + 0.6 * e)), 3),
        })
    return destellos


def espectro(p: Proyecto, m: dict, fps: int, bandas: int) -> str:
    """El espectro de la canción entera, cuadro a cuadro (0..99 por banda), en la biblioteca. Se calcula una vez."""
    import librosa

    import re
    import unicodedata

    origen = p.medios / m["archivo"]
    # Sin espacios ni tildes: el nombre viaja en una URL.
    limpio = re.sub(r"[^a-z0-9]+", "-", unicodedata.normalize("NFKD", origen.stem).encode("ascii", "ignore").decode().lower()).strip("-")
    rel = f"analisis/espectro-{limpio}-{fps}-{bandas}.json"
    destino = p.medios / rel
    if destino.exists() and destino.stat().st_mtime >= origen.stat().st_mtime:
        return rel
    y, sr = librosa.load(origen, sr=22050, mono=True)
    salto = int(round(sr / fps))
    mel = librosa.feature.melspectrogram(y=y, sr=sr, n_fft=2048, hop_length=salto, n_mels=bandas, fmin=40, fmax=9000)
    db = librosa.power_to_db(mel, ref=np.max)
    # Cada banda en su propio rango (si no, los graves tapan todo) y un vúmetro: sube rápido, baja despacio.
    bajo = np.percentile(db, 10, axis=1, keepdims=True)
    alto = np.percentile(db, 99, axis=1, keepdims=True)
    v = np.clip((db - bajo) / (alto - bajo + 1e-9), 0, 1)
    for i in range(1, v.shape[1]):
        v[:, i] = np.maximum(v[:, i], v[:, i - 1] * 0.86)
    valores = (v.T * 99).round().astype(int).tolist()
    escribir_json(destino, {"fps": fps, "bandas": bandas, "valores": valores}, compacto=True)
    print(f"  espectro: {len(valores)} cuadros × {bandas} bandas → {destino}")
    return rel


def aplicar_y_escribir(p: Proyecto) -> None:
    """Para `planificar`: después del modo, suma las capas al timeline recién escrito."""
    if not p.cfg.get("sintesis") and not p.timeline.exists():
        return
    from .planificar import escribir

    tl = leer_json(p.timeline)
    if not p.cfg.get("sintesis") and "sintesis" not in tl:
        return
    escribir(p.timeline, aplicar(p, tl))
