"""El material de prueba: clips hechos con código, sin derechos de nadie, para probar la consola, la mesa y el
flujo sin material propio.

    python montaje.py demo                 # → <medios>/demo/clips/*.mp4
    python montaje.py demo --segundos 4 --alto 360

Cada clip tiene algo que los aparatos hacen notar: un cielo con sol (el destello, el halo, la viñeta), la carta de
prueba que se mueve (el corrimiento del color de la cinta), las barras de color (el croma, el tubo), un fractal que se
acerca (el detalle fino: la trama, el moiré) y el juego de la vida (bordes duros, para la compresión y el mosaico).
El sonido es un pulso sintetizado a 120 por minuto, para lo que va al pulso.

Lo genera ffmpeg con sus fuentes de prueba (`testsrc2`, `smptehdbars`, `mandelbrot`, `life`) y numpy (el cielo).
Quien lo genera es su autor: se puede usar y repartir sin pedir nada (CC0).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np

from .rutas import MEDIOS

CARPETA = MEDIOS / "demo" / "clips"
FPS = 30
# Un golpe grave cada medio segundo y un acorde quieto debajo (estéreo).
PULSO = ("0.5*sin(2*PI*55*t)*exp(-9*mod(t,0.5))+0.06*sin(2*PI*220*t)+0.04*sin(2*PI*277.2*t)+0.03*sin(2*PI*329.6*t)"
         "|0.5*sin(2*PI*55*t)*exp(-9*mod(t,0.5))+0.06*sin(2*PI*220.6*t)+0.04*sin(2*PI*277.8*t)+0.03*sin(2*PI*330.2*t)")


def _ffmpeg(entrada_video: list[str], destino: Path, segundos: float, filtro: str | None = None,
            stdin: bytes | None = None) -> None:
    cmd = ["ffmpeg", "-v", "error", "-y", *entrada_video,
           "-f", "lavfi", "-i", f"aevalsrc='{PULSO}':s=48000:d={segundos}",   # entre comillas: las comas son del filtro
           "-t", f"{segundos}", "-map", "0:v", "-map", "1:a"]
    if filtro:
        cmd += ["-vf", filtro]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS),
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(destino)]
    subprocess.run(cmd, input=stdin, check=True)


def _cielo(segundos: float, ancho: int, alto: int) -> bytes:
    """Un atardecer: el cielo de azul a ámbar, nubes que pasan, el sol que baja un poco y lomas oscuras."""
    from scipy import ndimage

    rng = np.random.default_rng(7)
    y = np.linspace(0, 1, alto, dtype=np.float32)[:, None]
    x = np.linspace(0, 1, ancho, dtype=np.float32)[None, :]
    arriba = np.array([0.149, 0.224, 0.416], np.float32)
    abajo = np.array([0.902, 0.706, 0.235], np.float32)
    cielo = arriba + (abajo - arriba) * (y ** 1.6)[..., None]
    # Las nubes: ruido suave, el doble de ancho para que pasen.
    nubes = ndimage.gaussian_filter(rng.random((alto // 4, ancho // 2)).astype(np.float32), (alto / 60, ancho / 50), mode="wrap")
    nubes = (nubes - nubes.min()) / (np.ptp(nubes) + 1e-6)
    nubes = np.clip((nubes - 0.5) * 3, 0, 1)
    nubes = ndimage.zoom(nubes, (alto / nubes.shape[0], ancho / nubes.shape[1] * 2), order=1)[:alto]
    cuadros = []
    total = int(round(segundos * FPS))
    for k in range(total):
        t = k / FPS
        sx, sy = 0.70 - 0.01 * t, 0.34 + 0.012 * t
        d = np.sqrt(((x - sx) * ancho / alto) ** 2 + (y - sy) ** 2)
        img = cielo.copy()
        corrida = int(t * ancho * 0.02) % ancho
        n = np.roll(nubes, -corrida, axis=1)[:, :ancho] * (1 - y) ** 0.5
        img = img * (1 - 0.35 * n[..., None]) + np.array([0.95, 0.8, 0.7], np.float32) * 0.35 * n[..., None]
        img += np.array([1.0, 0.85, 0.6], np.float32) * (0.5 * np.exp(-d / 0.12))[..., None]
        img = np.where((d < 0.045)[..., None], np.array([1.0, 0.97, 0.88], np.float32), img)
        loma = 0.74 + 0.05 * np.sin(x * 5.5 + 0.8) + 0.02 * np.sin(x * 19 + t * 0.2)
        img = np.where((y > loma)[..., None], np.array([0.027, 0.035, 0.051], np.float32) + 0.04 * (y - loma)[..., None], img)
        cuadros.append((np.clip(img, 0, 1) * 255).astype(np.uint8))
    return np.stack(cuadros).tobytes()


def generar(segundos: float = 8.0, alto: int = 720, carpeta: Path | None = None) -> list[Path]:
    carpeta = Path(carpeta) if carpeta is not None else CARPETA
    carpeta.mkdir(parents=True, exist_ok=True)
    ancho = int(round(alto * 16 / 9 / 2)) * 2
    tam = f"{ancho}x{alto}"
    hechos = []
    destino = carpeta / "cielo-con-sol.mp4"
    _ffmpeg(["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", tam, "-r", str(FPS), "-i", "-"], destino, segundos,
            stdin=_cielo(segundos, ancho, alto))
    hechos.append(destino)
    fuentes = {
        "carta-que-se-mueve": (f"testsrc2=s={tam}:r={FPS}", None),
        "barras-de-color": (f"smptehdbars=s={tam}:r={FPS}", None),
        "fractal-que-se-acerca": (f"mandelbrot=s={ancho // 2}x{alto // 2}:r={FPS}:maxiter=400", f"scale={tam}:flags=bicubic"),
        "juego-de-la-vida": (f"life=s={ancho // 8}x{alto // 8}:r={FPS}:mold=12:ratio=0.12:life_color=#e6b43c:death_color=#c36712"
                             ":mold_color=#26396a", f"scale={tam}:flags=neighbor"),
    }
    for nombre, (fuente, filtro) in fuentes.items():
        destino = carpeta / f"{nombre}.mp4"
        _ffmpeg(["-f", "lavfi", "-i", fuente], destino, segundos, filtro)
        hechos.append(destino)
    (carpeta / "LICENCIA.txt").write_text(
        "Estos clips los genera `python montaje.py demo` con código (ffmpeg y numpy). Son CC0: se pueden usar, cambiar\n"
        "y repartir sin pedir permiso ni dar crédito.\n", encoding="utf-8")
    return hechos


def cmd(a) -> None:
    for p in generar(a.segundos, a.alto):
        print(f"→ {p}")
    print("Para tocarlos: python montaje.py panel <proyecto> (o npm run panel) y abre /consola.")
