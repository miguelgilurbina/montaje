"""Sincronizar: volver a poner al pulso una ráfaga dentro de un video que ya existe.

Para videos hechos afuera (un preeditado, una colaboración) en los que una
ráfaga de imágenes corre a su propio reloj y no al de la canción. No se toca el
audio ni el resto del video: las piezas de la ráfaga se rescatan del propio
video (el cuadro más nítido de cada una, recortado de su rectángulo) y se
vuelven a pegar en el mismo lugar, cada una entrando en la rejilla de la música.

Configuración en proyecto.json:

    "sincronizar": {
      "video": "archivo.mp4",              # relativo a los medios (la biblioteca)
      "nombre_salida": "con-rafaga-al-pulso",
      "crf": 14,                           # calidad de la única recodificación
      "rafagas": [{
        "nombre": "retratos de 1:15",
        "rect": [x, y, ancho, alto],       # dónde está cada pieza en el cuadro (px del video)
        "piezas": [t0, t1, ...],           # segundo en que entra cada pieza en el original
        "fin": t,                          # primer segundo sin ráfaga en el original
        "ancla": t,                        # un «uno» seguro (p. ej. donde vuelve el bajo)
        "subdivision": 3,                  # partes por golpe: 2 corcheas, 3 tresillo, 4 semicorcheas
        "inicio": -14,                     # entrada de la primera pieza, en subdivisiones desde el ancla
        "reloj": [[1, 2], [4, 3], [9, 1], [1, 0]]
      }]
    }

`reloj` es una lista de tramos `[piezas, duración]`: cuántas piezas seguidas y
cuántas subdivisiones dura cada una; 0 = la última se queda hasta `fin`. La
ventana que se reescribe es la del original, de la primera pieza a `fin`: fuera
de ella no cambia ni un cuadro, y dentro sólo el rectángulo. Por eso la ráfaga
nueva no puede destapar antes de `fin` lo que el original tapaba.

El período de la subdivisión se mide en los ataques de la música alrededor de la
ráfaga, con la fase fija en el ancla (se puede forzar con `periodo`).

Sirve sólo para piezas fijas. Cada pieza se pega como UN cuadro: si en el original
se mueve (un clip, un personaje que gira la cabeza), aquí queda congelada y se
pierde ese movimiento. Por eso, si alguna cambia entre su primer y su último
cuadro, el comando se detiene antes de escribir nada, salvo que la ráfaga diga
`"congelar_movimiento": true`. Pasó en el experimento 14: ver su FICHA.
"""

from __future__ import annotations

import subprocess
from fractions import Fraction
from pathlib import Path

import numpy as np

from .rutas import Proyecto, salir

# Diferencia media (0-255) entre el primer y el último cuadro de una pieza a partir
# de la cual es un clip y no una imagen. Medido en el 14: las piezas quietas dan
# hasta 2; las dos que se mueven, 20 y 36.
UMBRAL_MOVIMIENTO = 5.0


def _probar(video: Path) -> tuple[int, int, Fraction, int]:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate,nb_frames",
         "-of", "default=nw=1:nk=1", str(video)],
        capture_output=True, text=True, check=True,
    )
    w, h, fr, n = r.stdout.split()
    return int(w), int(h), Fraction(fr), int(n)


def _cuadros(video: Path, w: int, h: int):
    """Todos los cuadros del video, uno a uno, en RGB."""
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(video), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                            stdout=subprocess.PIPE)
    tam = w * h * 3
    try:
        while True:
            buf = proc.stdout.read(tam)
            if len(buf) < tam:
                break
            yield np.frombuffer(buf, dtype=np.uint8).reshape(h, w, 3)
    finally:
        proc.stdout.close()
        proc.wait()


def _nitidez(img: np.ndarray) -> float:
    g = img.astype(np.float32).mean(axis=2)
    lap = g[1:-1, 1:-1] * 4 - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:]
    return float(lap.var())


def _periodo(audio: Path, ancla: float, sub: int, ventana: tuple[float, float], forzado: float | None) -> tuple[float, float]:
    """Período de la subdivisión que mejor calza con los ataques, con fase en el ancla.
    Devuelve (período, error mediano en s)."""
    import librosa

    y, sr = librosa.load(audio, sr=22050, mono=True)
    ataques = librosa.onset.onset_detect(y=y, sr=sr, units="time")
    ataques = ataques[(ataques >= ventana[0]) & (ataques <= ventana[1])]
    if len(ataques) < 6:
        salir(f"sólo hay {len(ataques)} ataques alrededor de la ráfaga; fija `periodo` a mano")

    def error(p: float) -> float:
        k = np.round((ataques - ancla) / p)
        return float(np.median(np.abs(ataques - (ancla + k * p))))

    if forzado:
        return forzado, error(forzado)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    p0 = 60.0 / float(np.atleast_1d(tempo)[0]) / sub
    candidatos = np.arange(p0 * 0.85, p0 * 1.15, 0.0001)
    mejor = min(candidatos, key=error)
    return float(mejor), error(float(mejor))


def sincronizar(p: Proyecto) -> Path:
    cfg = p.cfg.get("sincronizar") or salir("falta `sincronizar` en proyecto.json")
    video = p.medios / cfg["video"]
    if not video.exists():
        salir(f"no existe el video {video}")
    w, h, fps, n = _probar(video)
    t_de = lambda i: float(i / fps)  # noqa: E731
    i_de = lambda t: int(round(t * fps))  # noqa: E731

    audio = p.salida("analisis", "audio.wav")
    if not audio.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "22050", str(audio)], check=True)

    # --- el plan de cada ráfaga: qué pieza va en cada cuadro de su ventana
    planes = []
    for r in cfg["rafagas"]:
        x, y, rw, rh = r["rect"]
        piezas, fin, ancla, sub = r["piezas"], r["fin"], r["ancla"], r.get("subdivision", 3)
        per, err = _periodo(audio, ancla, sub, (piezas[0] - 3, fin + 3), r.get("periodo"))
        golpe = per * sub
        print(f"«{r['nombre']}»: subdivisión {per:.4f} s ({60 / golpe:.1f} BPM, {sub} por golpe); "
              f"los ataques caen a {err * 1000:.0f} ms medianos de la rejilla")

        duraciones = [d for cuantas, d in r["reloj"] for _ in range(cuantas)]
        if len(duraciones) != len(piezas):
            salir(f"«{r['nombre']}»: el reloj reparte {len(duraciones)} piezas y hay {len(piezas)}")
        entradas, pos = [], r["inicio"]
        for d in duraciones:
            entradas.append(ancla + pos * per)
            pos += d if d else 0
        if abs(entradas[0] - piezas[0]) > 1.5 / float(fps):
            print(f"  ojo: la primera pieza entra en {entradas[0]:.3f} s y en el original en {piezas[0]:.3f} s; "
                  "la ventana empieza en la del original")
        if entradas[-1] >= fin:
            salir(f"«{r['nombre']}»: la última pieza entraría en {entradas[-1]:.3f} s, después de `fin` ({fin} s)")
        ini_v, fin_v = i_de(piezas[0]), i_de(fin)
        cuadro_pieza = {}
        for i in range(ini_v, fin_v):
            k = max([j for j, e in enumerate(entradas) if i_de(e) <= i] or [0])
            cuadro_pieza[i] = k
        planes.append(dict(r=r, rect=(x, y, rw, rh), piezas=piezas, fin=fin, entradas=entradas,
                           ventana=(ini_v, fin_v), cuadro_pieza=cuadro_pieza, per=per, ancla=ancla, sub=sub))

    # --- pasada 1: el mejor cuadro de cada pieza en el original
    origen = {}  # (n.º de ráfaga, pieza) → índice de cuadro en el original
    for nr, pl in enumerate(planes):
        for k, t in enumerate(pl["piezas"]):
            hasta = pl["piezas"][k + 1] if k + 1 < len(pl["piezas"]) else pl["fin"]
            for i in range(i_de(t), i_de(hasta)):
                origen.setdefault((nr, k), []).append(i)
    buscados = {i: key for key, idx in origen.items() for i in idx}
    mejores: dict = {}
    extremos: dict = {}
    for i, img in enumerate(_cuadros(video, w, h)):
        key = buscados.get(i)
        if key is None:
            continue
        x, y, rw, rh = planes[key[0]]["rect"]
        recorte = img[y:y + rh, x:x + rw]
        extremos.setdefault(key, [recorte.copy(), None])[1] = recorte.copy()
        nit = _nitidez(recorte)
        if key not in mejores or nit > mejores[key][0]:
            mejores[key] = (nit, recorte.copy(), i)

    for nr, pl in enumerate(planes):
        moviles = []
        for k in range(len(pl["piezas"])):
            primero, ultimo = extremos[(nr, k)]
            cambio = float(np.abs(primero.astype(np.float32) - ultimo.astype(np.float32)).mean())
            if cambio > UMBRAL_MOVIMIENTO:
                moviles.append(f"{k + 1} ({cambio:.0f})")
        if moviles and not pl["r"].get("congelar_movimiento"):
            salir(f"«{pl['r']['nombre']}»: estas piezas se mueven en el original y quedarían congeladas: "
                  f"{', '.join(moviles)}. Sacarlas de la ráfaga o, si es a propósito, poner `congelar_movimiento`.")

    for nr, pl in enumerate(planes):
        print("\n  pieza  original   nueva      dura      rejilla (golpe.parte desde el ancla)   cuadro rescatado")
        for k, e in enumerate(pl["entradas"]):
            sig = pl["entradas"][k + 1] if k + 1 < len(pl["entradas"]) else pl["fin"]
            cuadros = i_de(sig) - i_de(max(e, pl["piezas"][0]))
            pos = round((e - pl["ancla"]) / pl["per"])
            g, s = divmod(pos, pl["sub"])
            print(f"  {k + 1:4d}  {pl['piezas'][k]:8.3f}  {e:8.3f}  {cuadros:3d} cuadros   {g:+3d}.{s + 1}"
                  f"                               {t_de(mejores[(nr, k)][2]):.3f} s")

    # --- pasada 2: reescribir sólo la ventana y sólo el rectángulo; el audio se copia tal cual
    nombre = cfg.get("nombre_salida", video.stem + "-sincronizado")
    final = p.salida("render", f"{nombre}.mp4")
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", f"{fps.numerator}/{fps.denominator}",
         "-i", "-", "-i", str(video), "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", str(cfg.get("crf", 14)),
         "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", str(final)],
        stdin=subprocess.PIPE,
    )
    escritos = 0
    for i, img in enumerate(_cuadros(video, w, h)):
        for nr, pl in enumerate(planes):
            if i in pl["cuadro_pieza"]:
                img = img.copy()
                x, y, rw, rh = pl["rect"]
                img[y:y + rh, x:x + rw] = mejores[(nr, pl["cuadro_pieza"][i])][1]
        enc.stdin.write(img.tobytes())
        escritos += 1
    enc.stdin.close()
    if enc.wait():
        salir("ffmpeg falló al escribir el video")
    if escritos != n:
        print(f"ojo: el original dice {n} cuadros y se escribieron {escritos}")

    # --- antes y después de la ráfaga, uno sobre otro, para mirar y para mandar
    for nr, pl in enumerate(planes):
        a = max(0.0, t_de(pl["ventana"][0]) - 2.5)
        b = t_de(pl["ventana"][1]) + 3.0
        comp = p.salida("render", f"{nombre}-comparar-{nr + 1}.mp4")
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", str(video), "-ss", f"{a:.3f}", "-to", f"{b:.3f}",
             "-i", str(final), "-filter_complex", "[0:v][1:v]vstack[v]", "-map", "[v]", "-map", "1:a", "-c:v", "libx264",
             "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(comp)],
            check=True,
        )
        print(f"comparación (arriba el original, abajo el nuevo): {comp}")
    print(f"→ {final}")
    return final
