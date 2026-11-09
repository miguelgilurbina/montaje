"""Clips nuevos hechos de los clips: el tiempo del clip, transformado en código.

Parten de la copia de trabajo (ya girada y en SDR) y dejan un clip nuevo en
`transformados/<clip>-<efecto>.mp4` de la biblioteca. Los originales no se tocan.
Para usarlos en un montaje, agregar `"transformados"` a `clips` en proyecto.json
(`"clips": ["clips", "transformados"]`) y volver a correr `clips`.

- **estela** — lo claro deja rastro y se apaga despacio (`lagfun`): luces que se
  arrastran, como una foto de exposición larga que se mueve. Mejor con fondo oscuro.
- **eco** — cada cuadro lleva encima los anteriores, cada vez más tenues (`tmix`):
  el movimiento deja fantasmas, como un recuerdo que repite.
- **barrido** — barrido temporal (*slit-scan*): cada fila de la imagen es de otro
  momento; arriba el presente y hacia abajo hasta `retardo` segundos atrás. Lo que
  se mueve se estira y se dobla; lo quieto queda igual.
- **lento** — cámara lenta suave (`minterpolate`): inventa los cuadros que faltan
  en vez de repetirlos. A la mitad de velocidad por defecto.
- **reversa** — el clip hacia atrás.
- **ida-y-vuelta** — hacia adelante y de regreso (*boomerang*): dura el doble y
  empalma consigo mismo.

    python montaje.py transformar <p> --efecto barrido [--clip <id> …] [--fuerza 1.5]

`--fuerza`: estela = segundos en que el rastro se apaga a la mitad, eco = segundos
de pasado que se suman, barrido = segundos de retardo de arriba a abajo, lento =
cuántas veces más lento.
"""

from __future__ import annotations

import subprocess

import numpy as np

from . import clips as catalogo_clips
from .rutas import Proyecto, salir

EFECTOS = ("estela", "eco", "barrido", "lento", "reversa", "ida-y-vuelta")
#: En segundos (salvo `lento`): así valen igual para un clip de 24 cps que para una copia de 72.
POR_DEFECTO = {"estela": 0.5, "eco": 0.5, "barrido": 1.2, "lento": 2.0, "reversa": 1.0, "ida-y-vuelta": 1.0}


def elegir(todos: list[dict], ids: list[str] | None) -> list[dict]:
    """Qué clips se transforman: los pedidos o, sin pedir ninguno, sólo los originales.

    Transformar lo ya transformado («…-eco-reversa») se puede, pero pidiéndolo por su id:
    por defecto llenaba la carpeta de combinaciones que después entraban solas al montaje.
    """
    return [c for c in todos if not c.get("foto") and (c["id"] in ids if ids else not c["src"].startswith("transformados/"))]


def transformar(p: Proyecto, efecto: str, ids: list[str] | None, fuerza: float | None) -> None:
    if efecto not in EFECTOS:
        salir(f"efecto desconocido: {efecto} (hay: {', '.join(EFECTOS)})")
    todos = catalogo_clips.cargar(p)
    elegidos = elegir(todos, ids)
    if ids and len(elegidos) != len(set(ids)):
        salir(f"no encuentro {sorted(set(ids) - {c['id'] for c in elegidos})} en el catálogo de clips")
    k = POR_DEFECTO[efecto] if fuerza is None else fuerza
    for c in elegidos:
        origen = p.medios / c["proxy"]
        destino = p.medio("transformados", f"{c['id']}-{efecto}.mp4")
        print(f"  {c['id']} → {efecto} ({k:g})", flush=True)
        if efecto == "barrido":
            _barrido(origen, destino, c, k)
        else:
            fps = c["fps"]
            n_eco = int(max(2, min(64, round(k * fps))))
            filtro = {
                # Cuánto queda del rastro en cada cuadro para que se apague a la mitad en `k` segundos.
                "estela": f"lagfun=decay={min(0.999, max(0.5, 0.5 ** (1 / max(1.0, k * fps)))):.5f}",
                # Los cuadros de atrás pesan menos cuanto más viejos (la mitad a mitad de camino).
                "eco": f"tmix=frames={n_eco}:weights='{' '.join(str(round(0.5 ** (2 * i / n_eco), 4)) for i in range(n_eco))}'",
                "lento": f"minterpolate=fps={round(c['fps'] * k)}:mi_mode=mci:mc_mode=aobmc:vsbmc=1,setpts={k}*PTS,fps={round(c['fps'])}",
                # El tiempo al revés: el mar que se retira, el perro que camina hacia atrás.
                "reversa": "reverse",
                # Ida y vuelta (boomerang): hacia adelante y de regreso, sin costura.
                "ida-y-vuelta": "split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1:a=0",
            }[efecto]
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(origen), "-an", "-vf", f"{filtro},format=yuv420p",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-g", str(int(c["fps"] // 2)),
                            "-movflags", "+faststart", str(destino)], check=True)
        print(f"    → {destino}")


def _barrido(origen, destino, c: dict, retardo: float) -> None:
    """Slit-scan: la fila y del cuadro t sale del cuadro t − retardo·y/alto. Un anillo de cuadros en memoria."""
    w, h, fps = c["w"], c["h"], c["fps"]
    # A lo sumo 1280 de ancho: el anillo entero vive en memoria.
    k = min(1.0, 1280 / max(w, h))
    w2, h2 = int(round(w * k / 2)) * 2, int(round(h * k / 2)) * 2
    n_ret = max(2, int(round(retardo * fps)))
    lector = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(origen), "-vf", f"scale={w2}:{h2}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                              stdout=subprocess.PIPE)
    escritor = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w2}x{h2}", "-r", str(fps),
                                 "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
                                 "-g", str(int(fps // 2)), "-movflags", "+faststart", str(destino)], stdin=subprocess.PIPE)
    anillo = np.zeros((n_ret, h2, w2, 3), dtype=np.uint8)
    # Qué cuadro de atrás le toca a cada fila (0 = el actual).
    atras = np.round(np.linspace(0, n_ret - 1, h2)).astype(int)
    tam = w2 * h2 * 3
    t = 0
    while True:
        crudo = lector.stdout.read(tam)
        if len(crudo) < tam:
            break
        cuadro = np.frombuffer(crudo, dtype=np.uint8).reshape(h2, w2, 3)
        if t == 0:
            anillo[:] = cuadro  # al principio, el pasado es el primer cuadro
        anillo[t % n_ret] = cuadro
        idx = (t - atras) % n_ret
        salida = anillo[idx, np.arange(h2)]
        escritor.stdin.write(salida.tobytes())
        t += 1
    escritor.stdin.close()
    escritor.wait()
    lector.wait()
    if escritor.returncode:
        salir("ffmpeg no pudo escribir el barrido")
