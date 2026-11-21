"""Comandos de montaje. Cada uno hace una cosa y dice dónde dejó el resultado."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from . import clips, por_tramos
from .rutas import RAIZ, Proyecto, leer_json, salir


def _remotion() -> str:
    exe = RAIZ / "node_modules" / ".bin" / ("remotion.cmd" if sys.platform == "win32" else "remotion")
    if not exe.exists():
        salir("falta Remotion; corre `npm install` en la raíz del repo")
    return str(exe)


def _base_remotion(p: Proyecto) -> list[str]:
    if not p.timeline.exists():
        salir("falta el timeline; corre primero: python montaje.py planificar " + p.nombre)
    tl = leer_json(p.timeline)
    if any("video" in c for c in [*tl.get("capas", []), *tl.get("planos", [])]) or tl.get("sintesis") or tl.get("fuentes"):
        return [f"--props={p.timeline}", f"--public-dir={_publico(p, tl)}",
                # Los clips: sin tope, la caché de cuadros del compositor crece hasta quedarse sin memoria.
                "--offthreadvideo-cache-size-in-bytes=1500000000"]
    return [f"--props={p.timeline}", f"--public-dir={p.medios}"]


def _publico(p: Proyecto, tl: dict) -> Path:
    """Una carpeta con sólo lo que el timeline usa, en vínculos duros.

    Remotion copia la carpeta pública entera en cada render, y la biblioteca de clips
    trae los originales del teléfono (gigas): así copia sólo las copias de trabajo y
    el audio. Vínculos duros y no simbólicos: su servidor no sirve un enlace que
    apunta fuera de la carpeta (404). En el disco no ocupan nada aparte.
    """
    rutas: set[str] = set()
    _faltantes: set[str] = set()

    def juntar(x) -> None:
        if isinstance(x, dict):
            for v in x.values():
                juntar(v)
        elif isinstance(x, list):
            for v in x:
                juntar(v)
        elif isinstance(x, str) and 0 < len(x) < 400 and not x.startswith(("#", "http")):
            try:
                if (p.medios / x).is_file():
                    rutas.add(x)
                    # La pared de `actos` dibuja las miniaturas, que no están escritas en el timeline.
                    if x.startswith("imagenes/") and (p.medios / "miniaturas" / x[len("imagenes/"):]).is_file():
                        rutas.add("miniaturas/" + x[len("imagenes/"):])
                elif x.startswith("proxies/") and (p.medios / "borradores" / Path(x).name).is_file():
                    _faltantes.add(x)
            except (OSError, ValueError):  # un texto cualquiera (un título, un color) no es una ruta
                pass

    juntar({k: v for k, v in tl.items() if k != "meta"})
    # Una por versión: dos renders a la vez no se pisan la carpeta.
    destino = p.salida(f".publico-{p.version}" if p.version else ".publico", "x").parent
    shutil.rmtree(destino, ignore_errors=True)
    for r in sorted(rutas):
        enlace = destino / r
        enlace.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(p.medios / r, enlace)
        except OSError:  # otra unidad: no queda más que copiar
            shutil.copy2(p.medios / r, enlace)
    # Las tipografías de los letreros viven en el repo (fuentes/), no en la biblioteca: Letrero.tsx las pide a la carpeta pública.
    for f in tl.get("fuentes", []):
        origen = RAIZ / "fuentes" / f
        if not origen.is_file():
            salir(f"falta la tipografía fuentes/{f}")
        enlace = destino / "fuentes" / f
        enlace.parent.mkdir(parents=True, exist_ok=True)
        # Copia y no vínculo: el repo vive en OneDrive, que no se lleva bien con vínculos duros a sus archivos. Pesan poco.
        shutil.copy2(origen, enlace)
    # La copia interpolada que todavía no existe: con su mismo nombre, el borrador. El timeline no se entera.
    for r in sorted(_faltantes):
        enlace = destino / r
        enlace.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(p.medios / "borradores" / Path(r).name, enlace)
        except OSError:
            shutil.copy2(p.medios / "borradores" / Path(r).name, enlace)
    return destino


def cmd_render(p: Proyecto, a) -> Path:
    if not p.timeline.exists():
        salir("falta el timeline; corre primero: python montaje.py planificar " + p.nombre)
    tl = leer_json(p.timeline)
    if not a.preview:
        # El final va con la cámara lenta fluida: aquí se inventan los cuadros de lo que quedó en el video.
        clips.asegurar_copias(p, {c["img"] for c in tl.get("capas", []) if "video" in c and str(c.get("img", "")).startswith("proxies/")})
    fps = tl["fps"]
    nombre = a.salida or ("preview" if a.preview else "final")
    if p.version and not a.salida:
        nombre = f"{p.version}-{nombre}"
    if a.desde is not None or a.hasta is not None:
        desde = round((a.desde or 0) * fps)
        # `--frames` incluye el último: hasta el segundo 42 es hasta el cuadro anterior al del 42 (si no, dos tramos seguidos repiten un cuadro).
        hasta = min(tl["duracion"] - 1, round(a.hasta * fps) - 1 if a.hasta is not None else tl["duracion"] - 1)
        rango = [f"--frames={desde}-{hasta}"]
        nombre += f"-{a.desde or 0:g}-{format(a.hasta, 'g') if a.hasta is not None else 'fin'}"
    else:
        rango = []
    destino = p.salida("render", f"{nombre}.mp4")
    # Con grano, cada cuadro es ruido nuevo y la calidad constante no tiene techo: 3 min a CRF 16
    # pesaron 1,9 GB (y 1,5 GB a CRF 21). Con grano, tasa fija: 12 Mb/s ≈ 270 MB por 3 min.
    grano = any(s.get("tipo") == "recuerdo" and s.get("grano", 0) > 0 for s in tl.get("sintesis", []))
    final = ["--video-bitrate=12M"] if grano else ["--crf=16"]
    # La tarjeta de video dibuja el preview en la mitad de tiempo (12 s contra 23 por cada 10 s de video, medido el
    # 2026-11-09). El final sigue en el procesador: el cielo cambia 3 de 255 y el grano cae distinto, y lo aprobado se vio así.
    calidad = ["--scale=0.5", "--crf=28", "--jpeg-quality=70", "--gl=angle"] if a.preview else [*final, "--jpeg-quality=95"]
    if a.preview and not rango and not por_tramos.tiene_sonido_propio(tl.get("capas")):
        publico = _publico(p, tl) if any("video" in c for c in tl.get("capas", [])) or tl.get("sintesis") else p.medios
        por_tramos.renderizar(p, tl, destino, publico, _remotion(), calidad)
        print(f"→ {destino}")
        return destino
    orden = [_remotion(), "render", "src/index.ts", "Montaje", str(destino), *_base_remotion(p), *calidad, *rango]
    print(" ".join(orden))
    subprocess.run(orden, cwd=RAIZ, check=True)
    print(f"→ {destino}")
    return destino


class _Variante(Proyecto):
    """Una versión que no está escrita en proyecto.json: la de base con una perilla cambiada.
    Su timeline vive en las salidas (`barridos/`), no en el repo: es de usar y tirar."""

    def __init__(self, nombre: str, base: str | None, clave: str, valor):
        super().__init__(nombre, base)
        self.cfg["montaje"] = {**self.cfg.get("montaje", {}), clave: valor}
        import re

        # El nombre va a un archivo: sin corchetes, comas ni dos puntos.
        self.version = re.sub(r"[^\w.-]+", "_", f"{base + '-' if base else ''}{clave}-{valor}").strip("_")
        self._timeline = self.salida("barridos", f"timeline-{self.version}.json")

    @property
    def timeline(self) -> Path:
        return self._timeline


def valores_del_barrido(texto: str) -> tuple[str, list]:
    """«fundido_golpes=0.5,1,2» → la perilla y sus valores (números, true/false o palabras).
    Si un valor lleva comas adentro (una lista), los valores se separan con punto y coma:
    «rejilla=[3,3,0.25];[2,2,0.5]»."""
    import json

    clave, _, lista = texto.partition("=")
    if not clave.strip() or not lista.strip():
        salir("`--barrer` va como perilla=valor,valor,…  (por ejemplo: fundido_golpes=0.5,1,2,4)")
    valores = []
    for crudo in lista.split(";" if ";" in lista else ","):
        try:
            valores.append(json.loads(crudo.strip()))
        except ValueError:
            valores.append(crudo.strip())
    return clave.strip(), valores


def cmd_barrer(a) -> None:
    """Una perilla, varios valores, una sola pantalla: cada valor se planifica y se renderiza sobre
    la misma base, y las variantes salen lado a lado, sincronizadas, cada una con su etiqueta.
    Es la forma de afinar mirando: «¿cuánto fundido?»."""
    import tempfile
    from argparse import Namespace

    from . import estilos, planificar, revisar

    clave, valores = valores_del_barrido(a.barrer)
    if a.version and len(a.version) != 1:
        salir("con `--barrer`, `--version` es una sola: la base sobre la que se cambia la perilla")
    base = a.version[0] if a.version else None
    if not 2 <= len(valores) <= 9:
        salir("un barrido compara de dos a nueve valores")
    renders = []
    for valor in valores:
        p = _Variante(a.proyecto, base, clave, valor)
        print(f"\n── {clave} = {valor} " + "─" * 40)
        planificar.planificar(p)
        desde, hasta = (a.desde, a.hasta) if a.desde is not None or a.hasta is not None else (p.prueba or (None, None))
        if hasta is None:
            salir("un barrido se mira en un tramo corto: di `--desde` y `--hasta` (o pon `prueba` en la versión de base)")
        pedido = Namespace(preview=not a.final, desde=desde, hasta=hasta, salida=None)
        try:
            render = cmd_render(p, pedido)
        except subprocess.CalledProcessError:
            render = cmd_render(p, pedido)
        medida = revisar.medir(render)
        print("  " + revisar.linea(medida))
        for alerta in revisar.avisos(medida):
            print(f"  ⚠ {alerta}")
        renders.append((valor, render))

    # Las variantes en una cuadrícula, cada una con su etiqueta; el sonido, el de la primera.
    n = len(renders)
    cols = 1 if n == 1 else 2 if n <= 4 else 3
    filas = -(-n // cols)
    sondeo = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", str(renders[0][1])],
                            capture_output=True, text=True, check=True).stdout.strip().split(",")
    w, h = int(sondeo[0]), int(sondeo[1])
    cw = (1920 // cols) // 2 * 2
    ch = round(cw * h / w / 2) * 2
    base_p = Proyecto(a.proyecto)
    destino = base_p.salida("render", f"barrido-{base + '-' if base else ''}{clave}.mp4")
    with tempfile.TemporaryDirectory() as tmp:
        entradas, filtros, celdas = [], [], []
        for i, (valor, render) in enumerate(renders):
            cartel = Path(tmp) / f"e{i}.png"
            estilos._rotulo(f"{clave} = {valor}", base or "base", cw, ch, cartel)
            entradas += ["-i", str(render)]
        for i in range(n):
            entradas += ["-loop", "1", "-i", str(Path(tmp) / f"e{i}.png")]
            filtros.append(f"[{i}:v]scale={cw}:{ch},setsar=1[v{i}];[v{i}][{n + i}:v]overlay=0:0:shortest=1[c{i}]")
            celdas.append(f"{(i % cols) * cw}_{(i // cols) * ch}")
        filtros.append("".join(f"[c{i}]" for i in range(n)) + f"xstack=inputs={n}:layout={'|'.join(celdas)}:fill=black,format=yuv420p[s]")
        subprocess.run(["ffmpeg", "-v", "error", "-y", *entradas, "-filter_complex", ";".join(filtros), "-map", "[s]", "-map", "0:a?",
                        "-c:v", "libx264", "-crf", "20", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(destino)], check=True)
    cmd_hoja(base_p, Namespace(video=destino.name, cada=a.cada, desde=None, hasta=None, ancho=640, columnas=3, filas=5))
    print(f"\n{n} valores de `{clave}` lado a lado ({cols}×{filas}) → {destino}")


def cmd_ejercicio(a) -> None:
    """Una vuelta de ejercicio: cada versión del proyecto se planifica, se renderiza su tramo
    de prueba y se saca su hoja de contacto; con `--muestra`, además corta la muestra del
    estilo que la versión nombra. Una versión que falla no detiene a las demás.

    En proyecto.json, cada versión dice cómo se prueba:

        "versiones": {"cortina": {"transicion": "cortina", "prueba": [30, 46], "estilo": "transicion-cortina"}}
    """
    import time
    from argparse import Namespace

    from . import estilos, planificar, revisar
    from .rutas import MEDIOS

    if a.barrer:
        cmd_barrer(a)
        return
    base = Proyecto(a.proyecto)
    versiones = a.version or list(base.cfg.get("versiones", {}))
    if not versiones:
        salir(f"«{a.proyecto}» no tiene `versiones` en proyecto.json: un ejercicio compara versiones")
    filas = []
    for v in versiones:
        t0 = time.time()
        try:
            p = Proyecto(a.proyecto, v)
            print(f"\n── {v} " + "─" * max(4, 60 - len(v)))
            planificar.planificar(p)
            desde, hasta = (a.desde, a.hasta) if a.desde is not None or a.hasta is not None else (p.prueba or (None, None))
            pedido = Namespace(preview=not a.final, desde=desde, hasta=hasta, salida=None)
            try:
                render = cmd_render(p, pedido)
            except subprocess.CalledProcessError:
                # Remotion a veces pierde un cuadro («Failed to fetch») y a la segunda sale.
                print("  el render falló; va de nuevo")
                render = cmd_render(p, pedido)
            cmd_hoja(p, Namespace(video=render.name, cada=a.cada, desde=None, hasta=None, ancho=384, columnas=5, filas=6))
            # Lo que la hoja no muestra: negro, cuadros repetidos, destellos, sonoridad.
            medida = revisar.medir(render)
            print("  " + revisar.linea(medida))
            alertas = revisar.avisos(medida)
            for alerta in alertas:
                print(f"  ⚠ {alerta}")
            nota = ""
            if a.muestra:
                if not p.estilo:
                    nota = "sin `estilo`: no se cortó muestra"
                elif not (estilos.ESTILOS / f"{p.estilo}.json").exists():
                    nota = f"falta estilos/{p.estilo}.json: no se cortó muestra"
                else:
                    largo = (hasta - (desde or 0)) if hasta is not None else leer_json(p.timeline)["duracion"] / leer_json(p.timeline)["fps"] - (desde or 0)
                    m0, m1 = p.muestra or (0.5, min(largo, 10.5))
                    estilos.muestra(p.estilo, render.relative_to(MEDIOS).as_posix(), m0, m1, 540)
                    nota = f"muestra → {p.estilo}"
            filas.append((v, f"{time.time() - t0:5.0f} s", render.name, " · ".join([nota, *(f"⚠ {x}" for x in alertas)]).strip(" ·")))
        except (SystemExit, Exception) as err:  # noqa: BLE001  una versión mal escrita no detiene a las demás
            filas.append((v, f"{time.time() - t0:5.0f} s", "FALLÓ", f"{type(err).__name__}: {err}"[:110]))
    print("\n" + "═" * 64)
    for v, tiempo, archivo, nota in filas:
        print(f"{v:<24} {tiempo}  {archivo}  {nota}")
    fallas = sum(f[2] == "FALLÓ" for f in filas)
    print(f"{len(filas) - fallas} de {len(filas)} versiones; renders y hojas en {base.salidas}")
    if fallas:
        raise SystemExit(1)


def cmd_studio(p: Proyecto, a) -> None:
    orden = [_remotion(), "studio", "src/index.ts", *_base_remotion(p), f"--port={a.puerto}"]
    if a.sin_abrir:
        orden.append("--no-open")
    print(" ".join(orden))
    subprocess.run(orden, cwd=RAIZ, check=True)


def cmd_panel(p: Proyecto, a) -> None:
    """El panel (Next): ver el video sin renderizar, editar proyecto.json y correr los comandos."""
    exe = RAIZ / "node_modules" / ".bin" / ("next.cmd" if sys.platform == "win32" else "next")
    if not exe.exists():
        salir("falta Next; corre `npm install` en la raíz del repo")
    print(f"panel: http://localhost:{a.puerto}/p/{p.nombre}")
    # Todo trabaja en local: Next no manda su telemetría anónima a Vercel, y el
    # panel escucha sólo en este computador (no en la red de la casa).
    entorno = {**os.environ, "NEXT_TELEMETRY_DISABLED": "1"}
    subprocess.run([str(exe), "dev", "-H", "127.0.0.1", "-p", str(a.puerto)], cwd=RAIZ, check=True, env=entorno)


def cmd_hoja(p: Proyecto, a) -> list[Path]:
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
    return salidas


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

    s = nuevo("planificar", "catálogo + partitura → proyectos/<p>/timeline.json")
    s.add_argument("--version", help="una de las `versiones` de proyecto.json → timeline-<version>.json")

    nuevo("clips", "copias de trabajo y curvas de los clips (movimiento, cámara, nitidez, cortes) → analisis/clips.json + hojas/clips.png")

    s = nuevo("transformar", "clips nuevos hechos de los clips: estela de luz, eco, barrido temporal o cámara lenta suave → transformados/")
    s.add_argument("--efecto", required=True, help="estela, eco, barrido o lento")
    s.add_argument("--clip", nargs="+", help="ids de los clips (por defecto, todos)")
    s.add_argument("--fuerza", type=float, help="estela, eco y barrido: segundos · lento: veces más lento")

    nuevo("ensamblar", "programa (render de otro experimento) + interludios con su audio → medios/<p>/render")

    nuevo("componer", "escribe una canción neutra en código (afinada, al tempo pedido) → medios/audio")

    nuevo("musicalizar", "le pone música a un video que ya existe (compone si hace falta) → medios/<p>/render")

    nuevo("senal", "fallas de transmisión (glitch) en las transiciones de un render ya hecho, con su sonido → medios/<p>/render")

    nuevo("sonorizar", "suma la capa de efectos (sintetizados, al pulso de los momentos) a un render ya hecho → medios/<p>/render")

    s = nuevo("proyector", "el sonido del proyector (traqueteo, pop del 2, clac de diapositiva) sobre un render con película o fotos que despiertan")
    s.add_argument("--version", help="usa timeline-<version>.json y <version>-final.mp4")
    s.add_argument("--render", help="el archivo en render/ (por defecto, el final de la versión)")
    s.add_argument("--nivel", type=float, default=16.0, help="dB por debajo de la canción")

    nuevo("sincronizar", "vuelve a poner al pulso una ráfaga dentro de un video que ya existe (sin tocar el audio) → medios/<p>/render")

    s = nuevo("paquete", "prepara video, portada y texto para cada red (no publica nada)")
    s.add_argument("--red", nargs="+", required=True, help="instagram-reel, instagram-feed, youtube-short, youtube")

    s = nuevo("render", "renderiza el timeline a medios/render/*.mp4")
    s.add_argument("--preview", action="store_true", help="mitad de resolución y compresión rápida")
    s.add_argument("--desde", type=float, help="segundo inicial")
    s.add_argument("--hasta", type=float, help="segundo final")
    s.add_argument("--salida", help="nombre del archivo, sin extensión")
    s.add_argument("--version", help="renderiza timeline-<version>.json; el archivo lleva el nombre de la versión")

    s = nuevo("studio", "abre Remotion Studio con el timeline del proyecto")
    s.add_argument("--puerto", type=int, default=3300)
    s.add_argument("--sin-abrir", action="store_true", help="no abrir el navegador del sistema")
    s.add_argument("--version", help="abre timeline-<version>.json")

    s = nuevo("panel", "abre el panel en el navegador: el video sin renderizar, proyecto.json y los comandos")
    s.add_argument("--puerto", type=int, default=3310)

    s = nuevo("hoja", "hojas de contacto de un render (medios/hojas/*.png)")
    s.add_argument("video", help="nombre del archivo dentro de medios/render")
    s.add_argument("--cada", type=float, default=2.0, help="segundos entre cuadros")
    s.add_argument("--desde", type=float)
    s.add_argument("--hasta", type=float)
    s.add_argument("--ancho", type=int, default=384)
    s.add_argument("--columnas", type=int, default=5)
    s.add_argument("--filas", type=int, default=6)

    nuevo("seleccion", "la mesa de selección: una muestra muda, un cuadro y las medidas de cada clip, para elegir a mano antes de editar → <biblioteca>/seleccion/")

    s = nuevo("revisar", "mide un render: negro, imagen quieta, cuadros repetidos, cortes, destellos por segundo y sonoridad")
    s.add_argument("video", help="nombre del archivo dentro de medios/render")

    nuevo("guion", "el esqueleto del guion: la canción en tramos con los estilos de la galería que sirven en cada uno → proyectos/<p>/GUION.md (si no existe)")

    s = nuevo("traer", "trae de Cantera las piezas de una serie, en su orden, a la biblioteca del proyecto → <biblioteca>/cantera-<serie>/")
    s.add_argument("--serie", required=True, help="el nombre de la serie en Cantera")
    s.add_argument("--carpeta", help="la carpeta de la biblioteca (por defecto, cantera-<serie>)")
    s.add_argument("--tipo", help="sólo video, imagen, audio o documento")

    s = nuevo("aplicar-guion", "lleva a los tramos de proyecto.json lo que Miguel cambió en la Mesa (orden de clips, estilo, lo que pasa)")
    s.add_argument("cambios", help="JSON con {\"T3\": {\"orden\": [...], \"estilo\": \"...\", \"pasa\": \"...\"}}")
    s.add_argument("--version", help="los tramos de una versión de proyecto.json")

    s = nuevo("tomas", "la lista de tomas que pide el guion, para producir el material antes de montar → proyectos/<p>/TOMAS.md")
    s.add_argument("--version", help="las tomas de una versión de proyecto.json")
    s.add_argument("--estado", action="store_true", help="qué tomas ya tienen su clip en las carpetas del proyecto")

    s = nuevo("ejercicio", "una vuelta de ejercicio: planifica cada versión, renderiza su tramo de prueba, saca su hoja y (con --muestra) la muestra de su estilo")
    s.add_argument("--version", nargs="+", help="sólo estas versiones (por defecto, todas las de proyecto.json)")
    s.add_argument("--desde", type=float, help="segundo inicial (por defecto, el `prueba` de cada versión)")
    s.add_argument("--hasta", type=float, help="segundo final")
    s.add_argument("--final", action="store_true", help="resolución completa (por defecto, preview a la mitad)")
    s.add_argument("--cada", type=float, default=1.0, help="segundos entre cuadros de la hoja")
    s.add_argument("--muestra", action="store_true", help="corta la muestra del `estilo` de cada versión (conviene con --final)")
    s.add_argument("--barrer", help="perilla=valor,valor,…: en vez de las versiones, la misma base con esa perilla en cada valor, lado a lado (fundido_golpes=0.5,1,2,4)")

    # El catálogo de estilos no es de un proyecto: no lleva <proyecto>.
    s = sub.add_parser("estilos", help="valida y lista el catálogo de estilos (estilos/*.json)", description="valida y lista el catálogo de estilos (estilos/*.json)")
    s.add_argument("--para", help="sólo los que sirven para esto (abrir, cerrar, subir la energía…)")
    s.add_argument("--material", help="fotos, clips, mixto o serie")
    s.add_argument("--estado", help="aprobado, a medias, pedido, propuesta o rechazado")

    s = sub.add_parser("muestra", help="corta unos segundos livianos de un render como muestra de un estilo → medios/estilos/<id>.mp4", description="corta unos segundos livianos de un render como muestra de un estilo → medios/estilos/<id>.mp4")
    s.add_argument("estilo", help="id del estilo (nombre del archivo en estilos/, sin .json)")
    s.add_argument("--de", required=True, help="el render, relativo a los medios (p. ej. 13-variaciones/render/final.mp4)")
    s.add_argument("--desde", type=float, required=True)
    s.add_argument("--hasta", type=float, required=True)
    s.add_argument("--alto", type=int, default=540, help="alto en píxeles (no agranda)")

    s = sub.add_parser("textos", help="valida y lista la galería de textos (textos/*.json)",
                       description="valida y lista la galería de textos: estilos de letra para títulos, frases, rótulos, subtítulos y créditos")
    s.add_argument("--familia", help="titulos, frases, rotulos, subtitulos o movimiento")
    s.add_argument("--estado", help="aprobado, a medias, propuesta…")

    s = sub.add_parser("tipografia", help="hace una tipografía propia desde una libre de fuentes/ (hoy: apretarla a lo ancho)",
                       description="hace una tipografía propia desde una libre de fuentes/: `apretar` multiplica todo lo horizontal (dibujo, anchos, kerning, acentos) por un factor")
    s.add_argument("accion", choices=["apretar"])
    s.add_argument("origen", help="el archivo dentro de fuentes/ (p. ej. archivo-black/ArchivoBlack-Regular.ttf)")
    s.add_argument("factor", type=float, help="0,82 = el «type 3c» del cartel de Curiana")
    s.add_argument("familia", help="el nombre de la nueva (p. ej. «Curiana Cartel»)")

    s = sub.add_parser("veredicto", help="anota el veredicto de Miguel sobre un estilo o un letrero (lo usa la galería del panel)",
                       description="anota el veredicto de Miguel sobre un estilo (estilos/) o un letrero (textos/): estado, fecha y, si las hay, sus palabras (también en direccion/REGISTRO.md)")
    s.add_argument("estilo", help="id del estilo o del letrero")
    s.add_argument("estado", help="aprobado, a medias, rechazado, o propuesta para deshacer")
    s.add_argument("--cita", default="", help="lo que dijo Miguel, con sus palabras")
    s.add_argument("--via", default="chat", help="por dónde lo dio: chat o galeria")

    s = sub.add_parser("transcribir", help="transcribe un audio o video en este computador: texto, subtítulos y cada palabra con su segundo → medios/transcripciones/",
                       description="transcribe un audio o video en este computador: texto, subtítulos y cada palabra con su segundo → medios/transcripciones/")
    s.add_argument("archivo", help="ruta al audio o video (absoluta o relativa a los medios)")
    s.add_argument("--idioma", default="es")
    s.add_argument("--pistas", help="nombres propios que conviene que reconozca («Paraguaná, Curiana»)")
    s.add_argument("--cancion", action="store_true", help="es una canción: sin el filtro de voz, que toma el canto con instrumentos por ruido")

    s = sub.add_parser("recorrido", help="la galería de corrido: unos segundos de cada muestra con su nombre, en un video liviano → medios/estilos/recorridos/",
                       description="la galería de corrido: unos segundos de cada muestra con su nombre, en un video liviano → medios/estilos/recorridos/")
    s.add_argument("--en", help="sólo los estilos vistos en este experimento (p. ej. 21-laboratorio-de-la-manana)")
    s.add_argument("--estado", help="aprobado, a medias, pedido, propuesta o rechazado")
    s.add_argument("--para", help="sólo los que sirven para esto")
    s.add_argument("--segundos", type=float, default=6.0, help="cuánto se ve cada estilo")
    s.add_argument("--salida", help="nombre del archivo, sin extensión")
    s.add_argument("--peso", type=float, default=28.0, help="MB como mucho (el chat acepta 30)")

    sub.add_parser("aprender", help="lo aprendido de las notas de Miguel: lecciones y veredictos como datos → direccion/APRENDIDO.md",
                   description="lo aprendido de las notas de Miguel: lecciones y veredictos como datos → direccion/APRENDIDO.md")

    s = sub.add_parser("limpiar-voz", help="la voz en off sin ruidos de boca entre palabras y con nivel parejo (usa la transcripción) → <archivo>-limpia.wav",
                       description="la voz en off sin ruidos de boca entre palabras y con nivel parejo: chasquidos fuera, lo que no es palabra más bajo, "
                                   "normalizada (ver py/montaje/voz.py). Antes: transcribir el mismo archivo")
    s.add_argument("archivo", help="la grabación (absoluta o relativa a los medios)")
    s.add_argument("--salida", help="dónde dejarla (por defecto, <archivo>-limpia.wav al lado)")
    s.add_argument("--transcripcion", help="el .json de transcribir (por defecto, transcripciones/<nombre>.json)")
    s.add_argument("--atenuar", type=float, default=30.0, help="dB que baja lo que no es palabra")
    s.add_argument("--hueco", type=float, default=0.09, help="segundos: huecos más cortos dentro de una frase no se tocan")

    s = sub.add_parser("comparar", help="anota cuál de dos estilos eligió Miguel al verlos lado a lado (lo usa la galería del panel)",
                       description="anota cuál de dos estilos eligió Miguel al verlos lado a lado en el probador → direccion/COMPARACIONES.json")
    s.add_argument("a", help="id de un estilo")
    s.add_argument("b", help="id del otro")
    s.add_argument("--gana", required=True, help="el id del que eligió, o igual")
    s.add_argument("--via", default="chat", help="por dónde lo dio: chat o galeria")

    s = sub.add_parser("analogo", help="la mesa analógica: un video o una foto pasado por aparatos simulados en su señal (cinta VHS, antena, TBC, televisor de tubo…) → <entrada>-<cadena>.mp4",
                       description="la mesa analógica: un video o una foto pasado por una cadena de aparatos simulados en su señal NTSC "
                                   "(cámara, cinta VHS, antena, TBC, colorizador, imán, relieve Rutt/Etra, realimentación, televisor de tubo). "
                                   "Ver py/montaje/analogo.py y direccion/ANALOGO.md")
    s.add_argument("entrada", nargs="?", help="el video o la foto (ruta absoluta o dentro de los medios)")
    s.add_argument("--cadena", help="un estilo de la galería con `comando: analogo`, o la cadena en JSON")
    s.add_argument("--salida", help="dónde dejarla (por defecto, <entrada>-<cadena>.mp4 al lado)")
    s.add_argument("--desde", type=float, help="segundo inicial")
    s.add_argument("--hasta", type=float, help="segundo final")
    s.add_argument("--segundos", type=float, default=6.0, help="una foto: cuánto dura el video")
    s.add_argument("--alto", type=int, help="alto de la salida (por defecto, el de la entrada)")
    s.add_argument("--ventana", nargs=2, type=float, action="append", metavar=("DESDE", "HASTA"),
                   help="la cadena sólo entra en esos segundos (se repite para varias)")
    s.add_argument("--fundido", type=float, default=0.5, help="segundos de entrada y salida de cada ventana")
    s.add_argument("--hilos", type=int, help="procesos a la vez (por defecto, los núcleos menos dos, hasta 12)")
    s.add_argument("--comparar", help="cadenas separadas por coma: una hoja con un cuadro de cada una, lado a lado")
    s.add_argument("--en", default="1,3,5", help="los segundos de la hoja de --comparar, separados por coma")
    s.add_argument("--recorrido", help="cadenas separadas por coma: un video con cada una sobre el mismo tramo "
                                       "(desde --desde, --segundos cada una), con su nombre; primero, tal cual")
    s.add_argument("--cadenas", action="store_true", help="lista las cadenas de la galería")
    s.add_argument("--golpes", default=None, metavar="PROYECTO",
                   help="los golpes de la canción de ese proyecto, para lo que va al pulso (la consola `al pulso`)")

    s = sub.add_parser("probar", help="el probador: cada estilo hace su muestra en el mismo banco (mismos clips, misma canción) → medios/estilos/probador/",
                       description="el probador: cada estilo hace su muestra en el mismo banco (mismos clips, misma canción), deja cuadros de "
                                   "referencia y mide lo que tarda → medios/estilos/probador/ (ver py/montaje/probador.py)")
    s.add_argument("estilos", nargs="*", help="ids de los estilos (sin ninguno, hace falta --todos o --armar)")
    s.add_argument("--todos", action="store_true", help="toda la galería; lo que no cambió no se vuelve a dibujar")
    s.add_argument("--armar", action="store_true", help="arma (o completa) el banco desde la biblioteca que dice proyectos/probador")
    s.add_argument("--fijar", action="store_true", help="los cuadros de ahora pasan a ser la referencia")
    s.add_argument("--rehacer", action="store_true", help="se vuelven a dibujar aunque estén guardados (para medir otra vez, o ver si sale igual)")

    a = ap.parse_args()
    if a.comando == "limpiar-voz":
        from . import voz

        voz.limpiar(a.archivo, a.salida, a.transcripcion, a.atenuar, a.hueco)
        return
    if a.comando == "analogo":
        from . import analogo

        analogo.cmd(a)
        return
    if a.comando == "probar":
        from . import probador

        if a.armar:
            probador.armar()
        if a.estilos or a.todos:
            if probador.probar(a.estilos or None, a.fijar, a.rehacer):
                raise SystemExit(1)
        elif not a.armar:
            salir("¿qué estilos? Dilos por su id, o --todos (o --armar para el banco)")
        return
    if a.comando == "aprender":
        from . import aprender

        aprender.escribir()
        return
    if a.comando == "transcribir":
        from . import transcribir

        transcribir.transcribir(a.archivo, a.idioma, a.pistas, a.cancion)
        return
    if a.comando == "textos":
        from . import textos

        textos.listar(a.familia, a.estado)
        return
    if a.comando == "tipografia":
        from . import tipografias

        tipografias.cmd_apretar(a.origen, a.factor, a.familia)
        return
    if a.comando in ("estilos", "muestra", "recorrido", "veredicto", "comparar"):
        from . import estilos

        if a.comando == "comparar":
            import json

            print(json.dumps(estilos.comparar(a.a, a.b, a.gana, a.via), ensure_ascii=False))
        elif a.comando == "veredicto":
            import json

            e = estilos.veredicto(a.estilo, a.estado, a.cita, a.via)
            print(json.dumps({"estado": e["estado"], "miguel": e["miguel"]}, ensure_ascii=False))
        elif a.comando == "estilos":
            estilos.listar(a.para, a.material, a.estado)
        elif a.comando == "recorrido":
            estilos.recorrido(a.en, a.estado, a.para, a.segundos, a.salida, a.peso)
        else:
            estilos.muestra(a.estilo, a.de, a.desde, a.hasta, a.alto)
        return
    if a.comando == "ejercicio":
        cmd_ejercicio(a)
        return
    p = Proyecto(a.proyecto, getattr(a, "version", None))
    if a.comando == "catalogo":
        catalogo.construir(p)
    elif a.comando == "clips":
        from . import clips

        clips.analizar(p)
    elif a.comando == "transformar":
        from . import transformar

        transformar.transformar(p, a.efecto, a.clip, a.fuerza)
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
    elif a.comando == "seleccion":
        from . import seleccion

        seleccion.preparar(p)
    elif a.comando == "revisar":
        from . import revisar

        revisar.revisar(p, a.video)
    elif a.comando == "guion":
        from . import guion

        guion.escribir(p)
    elif a.comando == "traer":
        from . import traer

        traer.traer(p, a.serie, a.carpeta, a.tipo)
    elif a.comando == "aplicar-guion":
        from . import guion

        guion.aplicar_desde_mesa(p, a.cambios)
    elif a.comando == "tomas":
        from . import tomas

        tomas.estado(p) if a.estado else tomas.escribir(p)
    elif a.comando == "planificar":
        planificar.planificar(p)
    elif a.comando == "ensamblar":
        from . import ensamblar

        ensamblar.ensamblar(p)
    elif a.comando == "componer":
        from . import componer

        componer.escribir(p)
    elif a.comando == "musicalizar":
        from . import musicalizar

        musicalizar.musicalizar(p)
    elif a.comando == "senal":
        from . import senal

        senal.senal(p)
    elif a.comando == "sonorizar":
        from . import sonido

        sonido.sonorizar(p)
    elif a.comando == "proyector":
        from . import proyector

        proyector.proyector(p, a.render, a.nivel)
    elif a.comando == "sincronizar":
        from . import sincronizar

        sincronizar.sincronizar(p)
    elif a.comando == "paquete":
        from . import publicar

        publicar.paquete(p, a.red)
    elif a.comando == "render":
        cmd_render(p, a)
    elif a.comando == "studio":
        cmd_studio(p, a)
    elif a.comando == "hoja":
        cmd_hoja(p, a)
    elif a.comando == "panel":
        cmd_panel(p, a)
