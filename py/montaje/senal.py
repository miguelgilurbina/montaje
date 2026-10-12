"""Señal: fallas de transmisión en las transiciones, como una cinta o una antena que se pierden.

Miguel propuso un flujo «Video Glitch»: un aparato que rompe la señal (Carena
MVP-4000) y otro que la estabiliza (JVC KM-250, como un TBC). No los tiene, así
que se hace en digital, con ffmpeg, sobre un render cerrado:

- **romper:** canales de color separados, filas desgarradas que saltan de lado,
  una ondulación horizontal, ruido de croma, líneas de barrido y, en la falla
  mayor, la imagen que rueda en vertical (se pierde el sincronismo);
- **estabilizar:** cada falla dura una ventana y vuelve limpia en el golpe. Fuera
  de sus ventanas el video no se toca.

Las imágenes protagonistas (destacados, carrusel) nunca se averían: la regla de
Miguel es que se vean al 100 %. Las fallas van donde el video cambia de estado:

| Dónde | Falla |
|---|---|
| entra el salvapantallas | la grande: la señal se cae en el silencio, rueda, y el logo aparece entre la interferencia |
| sale el salvapantallas | la señal vuelve (coincide con el barrido) |
| un barrido suelto | un golpe corto |
| la firma | el logo llega averiado y se estabiliza: el TBC que engancha |
| un `video` (cortina dentro del montaje) | un golpe al entrar y al salir, como cambiar de canal |

El sonido acompaña: zumbido de cabezal, ráfagas de ruido y cortes de la canción
de un cuadro, con la misma envolvente que la imagen.

Configuración en proyecto.json (todo opcional):

    "base": {"proyecto": "09-sonido-curiana", "render": "curiana-3x2-sonido.mp4"},
    "senal": {
      "intensidad": 1.0,
      "no": ["barrido"],                          # dónde no poner fallas
      "extra": [{"t": 12.3, "dur": 0.4, "forma": "golpe", "intensidad": 0.6}]
    }

Las fallas salen del timeline del primero de la cadena de `base` que lo tenga.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

from .rutas import Proyecto, escribir_json, salir, timeline_de
from .sonido import SR, _banda, _leer_audio, _pasabajos

# Formas de la envolvente (u va de 0 a 1 dentro de la ventana).
FORMAS = {
    "golpe": "pow(sin(PI*ld(9))\\,0.6)",  # sube y baja
    "vuelve": "pow(1-ld(9)\\,1.4)",       # empieza rota y engancha limpia al final
    "cae": "pow(ld(9)\\,1.4)",            # se va rompiendo
}


def _np_forma(forma: str, u: np.ndarray) -> np.ndarray:
    u = np.clip(u, 0, 1)
    return {"golpe": np.sin(np.pi * u) ** 0.6, "vuelve": (1 - u) ** 1.4, "cae": u**1.4}[forma]


def fallas(tl: dict, cfg: dict) -> list[dict]:
    """Dónde se rompe la señal, según los momentos y el logo del timeline."""
    fps = tl["fps"]
    I = cfg.get("intensidad", 1.0)
    no = set(cfg.get("no", []))
    lista = []
    logo = tl.get("logo") or {}
    finales_salva = set()
    if "salvapantallas" not in no:
        for s in logo.get("salvapantallas", []):
            ini, fin = s["ini"] / fps, s["fin"] / fps
            lista.append({"que": "entra el salvapantallas", "t": ini - 0.55, "dur": 1.1, "forma": "golpe", "intensidad": I, "rueda": 0.35})
            lista.append({"que": "sale el salvapantallas", "t": fin - 0.3, "dur": 0.6, "forma": "golpe", "intensidad": 0.8 * I, "rueda": 0.0})
            finales_salva.add(s["fin"])
    for mo in tl.get("momentos", []):
        ini, fin = mo["ini"] / fps, mo["fin"] / fps
        if mo["tipo"] == "barrido" and "barrido" not in no and mo["ini"] not in finales_salva:
            lista.append({"que": "barrido", "t": (ini + fin) / 2 - 0.15, "dur": 0.3, "forma": "golpe", "intensidad": 0.7 * I, "rueda": 0.0})
        elif mo["tipo"] == "destacado" and mo.get("pieza", 0) < 0 and not mo.get("desde") and "firma" not in no:
            lista.append({"que": "firma: el logo engancha", "t": ini, "dur": 0.5, "forma": "vuelve", "intensidad": I, "rueda": 0.0})
        elif mo["tipo"] == "video" and "video" not in no:
            for t in (ini, fin):
                lista.append({"que": "cambio de canal", "t": t - 0.2, "dur": 0.4, "forma": "golpe", "intensidad": 0.8 * I, "rueda": 0.15})
    for e in cfg.get("extra", []):
        lista.append({"que": e.get("que", "a mano"), "rueda": 0.0, "forma": "golpe", "intensidad": I, **e})
    lista.sort(key=lambda f: f["t"])
    for a, b in zip(lista, lista[1:]):
        if b["t"] < a["t"] + a["dur"]:
            salir(f"dos fallas se pisan: «{a['que']}» ({a['t']:.2f} s) y «{b['que']}» ({b['t']:.2f} s); quita una con `senal.no`")
    return lista


def _geq(f: dict) -> str:
    """Un filtro geq que rompe la imagen dentro de la ventana de la falla."""
    a, b, I = f["t"], f["t"] + f["dur"], f["intensidad"]
    # ld(9) = avance en la ventana; ld(0) = intensidad; ld(1) = desplazamiento de la fila; ld(2) = fila de origen.
    avance = f"st(9\\,clip((T-{a:.4f})/{f['dur']:.4f}\\,0\\,1))"
    env = f"st(0\\,{I:.3f}*{FORMAS[f['forma']]})"
    # Cada banda de 5 filas tira su propio dado en cada cuadro: con la intensidad, más bandas saltan y más lejos.
    dado = "mod(abs(sin(floor(Y/5)*12.9898+N*78.233))*43758.5453\\,1)"
    desgarro = f"if(lt({dado}\\,0.28*ld(0))\\,({dado}/(0.28*ld(0)+0.0001)-0.5)*280*ld(0)\\,0)"
    ondula = "24*ld(0)*sin(Y/37+T*40)"
    desplaza = f"st(1\\,{desgarro}+{ondula})"
    rueda = f"st(2\\,mod(Y+H*{f['rueda']:.3f}*pow(max(0\\,ld(0)-0.7)/0.3\\,2)\\,H))" if f.get("rueda") else "st(2\\,Y)"
    previo = f"{avance};{env};{desplaza};{rueda}"
    s = "16*ld(0)"
    # Nieve: el mismo dado por píxel en los tres canales, para que sea gris como la de un televisor.
    nieve = "mod(abs(sin(X*12.9898+Y*78.233+N*37.719))*43758.5453\\,1)"
    cola = f"+({nieve}-0.5)*80*ld(0)+28*pow(ld(0)\\,3))*(1-0.2*ld(0)*mod(Y\\,2))"
    # geq no recorta: un valor bajo 0 da la vuelta y sale blanco. El clip es lo que deja la imagen
    # siempre legible (lo que el documento de Miguel le pedía al JVC).
    canales = {
        "r": f"{previo};clip((r(X+ld(1)+{s}\\,ld(2)){cola}\\,0\\,255)",
        "g": f"{previo};clip((g(X+ld(1)\\,ld(2)){cola}\\,0\\,255)",
        "b": f"{previo};clip((b(X+ld(1)-{s}\\,ld(2)){cola}\\,0\\,255)",
    }
    expr = ":".join(f"{c}='{e}'" for c, e in canales.items())
    return f"geq={expr}:enable='between(t\\,{a:.4f}\\,{b:.4f})'"


def _interferencia(n: int, lista: list[dict], rng) -> tuple[np.ndarray, np.ndarray]:
    """El sonido de la falla: (lo que se suma, la ganancia de la canción con sus cortes de un cuadro)."""
    t = np.arange(n) / SR
    suma = np.zeros(n)
    ganancia = np.ones(n)
    cuadro = int(SR / 30)
    for f in lista:
        a, b = int(f["t"] * SR), min(n, int((f["t"] + f["dur"]) * SR))
        if b <= a:
            continue
        tt = t[a:b]
        env = f["intensidad"] * _np_forma(f["forma"], (tt - f["t"]) / f["dur"])
        # Zumbido de cabezal: diente de sierra a 59,94 Hz, sus armónicos hasta 3 kHz.
        zumbido = _pasabajos(2 * ((tt * 59.94) % 1) - 1, 3000, 4) * 0.5
        por_cuadro = env[::cuadro]
        # Ruido que se abre y se cierra cuadro a cuadro, como las bandas que saltan.
        bloques = rng.random(len(por_cuadro)) < 0.35 + 0.5 * por_cuadro
        compuerta = np.repeat(bloques, cuadro)[: len(tt)].astype(float)
        ruido = _banda(rng.standard_normal(len(tt)), 700, 6500) * compuerta
        suma[a:b] += env * (0.6 * zumbido + 0.9 * ruido)
        # La canción se corta un cuadro aquí y allá, más cuanto más rota está la señal.
        cortes = rng.random(len(por_cuadro)) < 0.45 * por_cuadro**2
        hueco = np.repeat(cortes, cuadro)[: len(tt)].astype(float)
        ganancia[a:b] *= 1 - 0.85 * hueco
    # Bordes suaves para que los cortes no chasqueen.
    k = int(0.004 * SR)
    ganancia = np.convolve(ganancia, np.ones(k) / k, mode="same")
    pico = np.max(np.abs(suma))
    return (suma / pico if pico else suma), ganancia


def senal(p: Proyecto) -> Path:
    cfg = p.cfg.get("senal", {})
    if not p.cfg.get("base"):
        salir("falta `base`: el render al que se le ponen las fallas")
    base = Proyecto(p.cfg["base"]["proyecto"])
    video = base.salidas / "render" / p.cfg["base"]["render"]
    if not video.exists():
        salir(f"no existe el render {video}")
    origen, tl = timeline_de(base)
    lista = fallas(tl, cfg)
    if not lista:
        salir("el timeline no tiene dónde poner fallas (ni salvapantallas, ni barridos, ni firma, ni videos)")
    rng = np.random.default_rng(cfg.get("semilla", 11))

    filtro = ",".join(["format=gbrp", *(_geq(f) for f in lista), "format=yuv420p"])
    nombre = p.cfg.get("nombre_salida", f"{Path(video.name).stem}-senal")
    final = p.salida("render", f"{nombre}.mp4")
    with tempfile.TemporaryDirectory() as tmp:
        cancion = _leer_audio(video, Path(tmp) / "audio.wav")
        suma, ganancia = _interferencia(len(cancion), lista, rng)
        nivel = 10 ** (cfg.get("nivel_sonido", -13.0) / 20)
        mezcla = cancion * ganancia[:, None] + (suma * nivel)[:, None] * np.array([1.0, 0.92])
        ruta_mezcla = Path(tmp) / "mezcla.wav"
        sf.write(str(ruta_mezcla), mezcla.astype(np.float32), SR, subtype="FLOAT")
        guion = Path(tmp) / "filtro.txt"
        guion.write_text(filtro, encoding="utf-8")
        r = subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(ruta_mezcla), "-map", "0:v", "-map", "1:a",
             "-/vf", str(guion), "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p",
             "-af", "alimiter=limit=0.891:attack=5:release=60:level=false:latency=1",
             "-c:a", "aac", "-b:a", "320k", "-ar", str(SR), "-movflags", "+faststart", "-shortest", str(final)],
            capture_output=True, text=True,
        )
        if r.returncode:
            salir(f"ffmpeg falló: {r.stderr.strip()[-800:]}")
    escribir_json(p.salida("senal", "fallas.json"), lista)
    print(f"render: {video.name} · fallas según el timeline de {origen.nombre}:")
    for f in lista:
        print(f"  {f['t']:6.2f}–{f['t'] + f['dur']:.2f} s  {f['forma']:<7} {f['intensidad']:.2f}  {f['que']}")
    print(f"→ {final}")
    return final
