"""Comandos de montaje. Cada uno hace una cosa y dice dónde dejó el resultado."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .rutas import RAIZ, Proyecto, leer_json, salir


def _remotion() -> str:
    exe = RAIZ / "node_modules" / ".bin" / ("remotion.cmd" if sys.platform == "win32" else "remotion")
    if not exe.exists():
        salir("falta Remotion; corre `npm install` en la raíz del repo")
    return str(exe)


def _base_remotion(p: Proyecto) -> list[str]:
    if not p.timeline.exists():
        salir("falta el timeline; corre primero: python montaje.py planificar " + p.nombre)
    return [f"--props={p.timeline}", f"--public-dir={p.medios}"]


def cmd_render(p: Proyecto, a) -> None:
    tl = leer_json(p.timeline)
    fps = tl["fps"]
    nombre = a.salida or ("preview" if a.preview else "final")
    if a.desde is not None or a.hasta is not None:
        desde = round((a.desde or 0) * fps)
        hasta = min(tl["duracion"] - 1, round(a.hasta * fps) if a.hasta is not None else tl["duracion"] - 1)
        rango = [f"--frames={desde}-{hasta}"]
        nombre += f"-{a.desde or 0:g}-{format(a.hasta, 'g') if a.hasta is not None else 'fin'}"
    else:
        rango = []
    destino = p.salida("render", f"{nombre}.mp4")
    calidad = ["--scale=0.5", "--crf=28", "--jpeg-quality=70"] if a.preview else ["--crf=16", "--jpeg-quality=95"]
    orden = [_remotion(), "render", "src/index.ts", "Montaje", str(destino), *_base_remotion(p), *calidad, *rango]
    print(" ".join(orden))
    subprocess.run(orden, cwd=RAIZ, check=True)
    print(f"→ {destino}")


def cmd_studio(p: Proyecto, a) -> None:
    orden = [_remotion(), "studio", "src/index.ts", *_base_remotion(p), f"--port={a.puerto}"]
    if a.sin_abrir:
        orden.append("--no-open")
    print(" ".join(orden))
    subprocess.run(orden, cwd=RAIZ, check=True)


def cmd_hoja(p: Proyecto, a) -> None:
    """Hojas de contacto de un render: lo que Claude mira para juzgar el montaje."""
    from PIL import Image, ImageDraw

    video = p.salidas / "render" / a.video
    if not video.exists():
        salir(f"no existe {video}")
    if not shutil.which("ffmpeg"):
        salir("falta ffmpeg en el PATH")
    desde = a.desde or 0.0
    with tempfile.TemporaryDirectory() as tmp:
        orden = ["ffmpeg", "-v", "error", "-ss", str(desde), "-i", str(video)]
        if a.hasta is not None:
            orden += ["-t", str(a.hasta - desde)]
        orden += ["-vf", f"fps=1/{a.cada},scale={a.ancho}:-2", str(Path(tmp) / "c%05d.png")]
        subprocess.run(orden, check=True)
        cuadros = sorted(Path(tmp).glob("c*.png"))
        if not cuadros:
            salir("ffmpeg no sacó ningún cuadro")
        cols, filas = a.columnas, a.filas
        w, h = Image.open(cuadros[0]).size
        por_hoja = cols * filas
        salidas = []
        for n_hoja in range(0, len(cuadros), por_hoja):
            hoja = Image.new("RGB", (cols * w, filas * (h + 18)), (20, 20, 20))
            d = ImageDraw.Draw(hoja)
            for k, ruta in enumerate(cuadros[n_hoja : n_hoja + por_hoja]):
                i = n_hoja + k
                t = desde + i * a.cada
                x, y = (k % cols) * w, (k // cols) * (h + 18)
                hoja.paste(Image.open(ruta), (x, y + 18))
                d.text((x + 4, y + 3), f"{int(t // 60)}:{t % 60:05.2f}", fill=(230, 230, 230))
            destino = p.salida("hojas", f"{video.stem}-{n_hoja // por_hoja + 1:02d}.png")
            hoja.save(destino)
            salidas.append(destino)
    print(f"{len(cuadros)} cuadros cada {a.cada} s en {len(salidas)} hojas:")
    for s in salidas:
        print(f"  {s}")


def main() -> None:
    from . import catalogo, musica, planificar

    ap = argparse.ArgumentParser(prog="montaje", description=__doc__)
    sub = ap.add_subparsers(dest="comando", required=True)

    def nuevo(nombre: str, ayuda: str):
        s = sub.add_parser(nombre, help=ayuda, description=ayuda)
        s.add_argument("proyecto")
        return s

    nuevo("catalogo", "reúne las imágenes de las fuentes del proyecto en analisis/catalogo.json")

    s = nuevo("imagenes", "pone las imágenes en disco (medios/imagenes)")
    g = s.add_mutually_exclusive_group(required=True)
    g.add_argument("--prueba", action="store_true", help="genera rellenos con la proporción y el color reales")
    g.add_argument("--medir", action="store_true", help="dice cuánto pesa bajarlas, sin bajar nada")
    g.add_argument("--bajar", action="store_true", help="baja las imágenes reales de su origen")
    g.add_argument("--miniaturas", action="store_true", help="genera las versiones chicas para la pared (de las ya bajadas)")

    s = nuevo("pista-prueba", "sintetiza una pista con pulso para probar sin la canción")
    s.add_argument("--bpm", type=float, default=112.0)
    s.add_argument("--duracion", type=float, default=180.0)

    s = nuevo("musica", "analiza la canción: pulso, energía, secciones → analisis/musica.json + .png")
    s.add_argument("--archivo", help="ruta relativa a los medios (por defecto, `musica` del proyecto)")

    nuevo("planificar", "catálogo + partitura → proyectos/<p>/timeline.json")

    nuevo("ensamblar", "programa (render de otro experimento) + interludios con su audio → medios/<p>/render")

    s = nuevo("render", "renderiza el timeline a medios/render/*.mp4")
    s.add_argument("--preview", action="store_true", help="mitad de resolución y compresión rápida")
    s.add_argument("--desde", type=float, help="segundo inicial")
    s.add_argument("--hasta", type=float, help="segundo final")
    s.add_argument("--salida", help="nombre del archivo, sin extensión")

    s = nuevo("studio", "abre Remotion Studio con el timeline del proyecto")
    s.add_argument("--puerto", type=int, default=3300)
    s.add_argument("--sin-abrir", action="store_true", help="no abrir el navegador del sistema")

    s = nuevo("hoja", "hojas de contacto de un render (medios/hojas/*.png)")
    s.add_argument("video", help="nombre del archivo dentro de medios/render")
    s.add_argument("--cada", type=float, default=2.0, help="segundos entre cuadros")
    s.add_argument("--desde", type=float)
    s.add_argument("--hasta", type=float)
    s.add_argument("--ancho", type=int, default=384)
    s.add_argument("--columnas", type=int, default=5)
    s.add_argument("--filas", type=int, default=6)

    a = ap.parse_args()
    p = Proyecto(a.proyecto)
    if a.comando == "catalogo":
        catalogo.construir(p)
    elif a.comando == "imagenes":
        if a.prueba:
            catalogo.generar_prueba(p)
        elif a.medir:
            catalogo.medir(p)
        elif a.miniaturas:
            catalogo.generar_miniaturas(p)
        else:
            catalogo.bajar(p)
    elif a.comando == "pista-prueba":
        musica.pista_prueba(p, a.bpm, a.duracion)
    elif a.comando == "musica":
        musica.analizar(p, a.archivo)
    elif a.comando == "planificar":
        planificar.planificar(p)
    elif a.comando == "ensamblar":
        from . import ensamblar

        ensamblar.ensamblar(p)
    elif a.comando == "render":
        cmd_render(p, a)
    elif a.comando == "studio":
        cmd_studio(p, a)
    elif a.comando == "hoja":
        cmd_hoja(p, a)
