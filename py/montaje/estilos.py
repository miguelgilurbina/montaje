"""El catálogo de estilos: recetas con nombre para elegir según el guion.

Una **técnica** es lo que el motor sabe hacer (un modo, un momento o un comando).
Un **estilo** es una técnica con sus valores, un nombre, para qué sirve, con qué
material funciona y lo que Miguel dijo de ella. Cada estilo es un archivo en
`estilos/<id>.json` (el repo guarda sólo texto) y su **muestra**, unos segundos
livianos para verlo, vive en `<medios>/estilos/<id>.mp4`: los renders de los
ejercicios se pueden borrar después del veredicto, la receta y la muestra quedan.

    python montaje.py estilos                  # valida y lista el catálogo
    python montaje.py estilos --para abrir     # sólo los que sirven para abrir
    python montaje.py muestra <id> --de 13-variaciones/render/x.mp4 --desde 23.6 --hasta 31.6
    python montaje.py recorrido --en 21-laboratorio-de-la-manana   # la galería de corrido, en un video
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from .rutas import MEDIOS, PROYECTOS, RAIZ, escribir_json, salir

ESTILOS = RAIZ / "estilos"
MUESTRAS = MEDIOS / "estilos"

# Vocabulario cerrado: el guion habla con estas palabras y el catálogo también.
# Una palabra nueva se agrega aquí (y en estilos/README.md) a propósito.
PARA = {
    "abrir": "el comienzo del video: presentar el canal o el tema",
    "cerrar": "el final: la firma, lo que se queda",
    "transición": "pasar de una parte a otra",
    "presentar la marca": "que se vea Curiana Radio",
    "mostrar el archivo": "que se vea mucho material, el archivo como algo vivo",
    "destacar": "una sola imagen o un solo clip al frente",
    "subir la energía": "acelerar, el pico",
    "respirar": "bajar, dejar mirar",
    "loop": "que el final empalme con el comienzo",
}
MATERIAL = {
    "fotos": "imágenes fijas",
    "clips": "videos que se mueven",
    "mixto": "fotos y clips juntos",
    "serie": "variaciones de una misma imagen",
    "cualquiera": "va encima de cualquier material (una capa)",
    "ninguno": "sale entero del código, sin material",
}
ENERGIA = {
    "calma": "lento, se deja mirar",
    "media": "pulso parejo",
    "alta": "rápido, el pico",
    "sube": "va de lento a rápido",
    "sigue": "acelera y frena con la canción",
}
ESTADOS = {
    "aprobado": "Miguel lo dijo",
    "a medias": "Miguel aprobó una parte y otra no (ver `miguel` y `evitar`)",
    "pedido": "Miguel lo pidió y está hecho, falta su veredicto",
    "propuesta": "de Claude, sin probar con Miguel",
    "rechazado": "Miguel dijo que no; queda para no repetirlo",
}
MODOS = {"collage", "secuencia", "cinta", "actos", "superposicion", "pulso", "solo-sintesis"}
MOMENTOS = {"destacado", "rafaga", "barrido", "video"}
COMANDOS = {"sincronizar", "senal", "sonorizar", "ensamblar", "musicalizar", "transformar", "proyector"}
#: Capas hechas en código que van encima de un montaje (`sintesis` en el timeline).
CAPAS = {"recuerdo", "fugas", "polvo", "partitura", "campo", "tinta", "calima", "tv", "titulo", "credito", "cuenta", "pelicula", "onda", "foco", "golpe", "rotulos", "luz", "barras", "rayas"}
CAMPOS = ["nombre", "frase", "para", "material", "energia", "dura", "tecnica", "estado", "miguel", "visto_en", "evitar"]


def leer() -> list[dict]:
    if not ESTILOS.exists():
        return []
    estilos = []
    for ruta in sorted(ESTILOS.glob("*.json")):
        try:
            e = json.loads(ruta.read_text(encoding="utf-8"))
        except json.JSONDecodeError as err:
            salir(f"{ruta.name}: no es JSON válido ({err})")
        e["id"] = ruta.stem
        estilos.append(e)
    return estilos


def errores(e: dict) -> list[str]:
    """Lo que le falta o le sobra a un estilo. Vacío = está bien."""
    mal = [f"falta `{c}`" for c in CAMPOS if c not in e]
    if mal:
        return mal
    for c in ("nombre", "frase", "dura"):
        if not isinstance(e[c], str) or not e[c].strip():
            mal.append(f"`{c}` tiene que ser un texto")
    for c in ("para", "miguel", "visto_en", "evitar"):
        if not isinstance(e[c], list) or not all(isinstance(x, str) for x in e[c]):
            mal.append(f"`{c}` tiene que ser una lista de textos")
    if mal:
        return mal
    mal += [f"`para`: «{x}» no está en el vocabulario ({', '.join(PARA)})" for x in e["para"] if x not in PARA]
    if not e["para"]:
        mal.append("`para` vacío: ¿para qué sirve?")
    if e["material"] not in MATERIAL:
        mal.append(f"`material`: «{e['material']}» no es {' / '.join(MATERIAL)}")
    if e["energia"] not in ENERGIA:
        mal.append(f"`energia`: «{e['energia']}» no es {' / '.join(ENERGIA)}")
    if e["estado"] not in ESTADOS:
        mal.append(f"`estado`: «{e['estado']}» no es {' / '.join(ESTADOS)}")
    # Un veredicto lleva las palabras de Miguel o, si lo dio con un clic en la galería, la marca de ese clic.
    if e["estado"] in ("aprobado", "a medias", "rechazado") and not e["miguel"] and not e.get("veredicto"):
        mal.append(f"`estado` {e['estado']} sin las palabras de Miguel en `miguel` ni su veredicto de la galería")
    t = e["tecnica"]
    claves = [k for k in ("modo", "momento", "comando", "capa") if isinstance(t, dict) and k in t]
    if len(claves) != 1:
        mal.append("`tecnica` lleva exactamente uno de `modo`, `momento`, `comando` o `capa`")
    else:
        k = claves[0]
        validos = {"modo": MODOS, "momento": MOMENTOS, "comando": COMANDOS, "capa": CAPAS}[k]
        if t[k] not in validos:
            mal.append(f"`tecnica.{k}`: «{t[k]}» no es {' / '.join(sorted(validos))}")
    mal += [f"`visto_en`: no existe el experimento «{p}»" for p in e["visto_en"] if not (PROYECTOS / p / "proyecto.json").exists()]
    return mal


def muestra_de(e: dict) -> Path:
    return MUESTRAS / f"{e['id']}.mp4"


def listar(para: str | None = None, material: str | None = None, estado: str | None = None) -> None:
    estilos = leer()
    if not estilos:
        salir(f"no hay estilos en {ESTILOS}")
    con_error = {e["id"]: errores(e) for e in estilos}
    con_error = {k: v for k, v in con_error.items() if v}
    for k, v in con_error.items():
        print(f"✗ {k}")
        for m in v:
            print(f"    {m}")
    if con_error:
        salir(f"{len(con_error)} de {len(estilos)} estilos con errores")

    elegidos = [
        e
        for e in estilos
        if (para is None or para in e["para"]) and (material is None or e["material"] == material) and (estado is None or e["estado"] == estado)
    ]
    for e in elegidos:
        m = muestra_de(e)
        peso = f"muestra {m.stat().st_size / 1e6:.1f} MB" if m.exists() else "sin muestra"
        print(f"{e['estado']:<10} {e['id']:<26} {e['material']:<6} {e['energia']:<6} {', '.join(e['para'])}  · {peso}")
    total = sum(muestra_de(e).stat().st_size for e in estilos if muestra_de(e).exists())
    print(f"\n{len(elegidos)} de {len(estilos)} estilos · muestras: {total / 1e6:.1f} MB en {MUESTRAS}")


def muestra(id_: str, de: str, desde: float, hasta: float, alto: int) -> None:
    """Corta unos segundos de un render y los deja livianos como muestra del estilo.

    Una sola recodificación, alto `alto` (sin agrandar), H.264 CRF 30 y audio a
    96 kb/s: pocos cientos de KB por segundo, lo justo para reconocer el estilo.
    """
    ruta = ESTILOS / f"{id_}.json"
    if not ruta.exists():
        salir(f"no existe el estilo «{id_}» (hay: {', '.join(e['id'] for e in leer())})")
    fuente = (MEDIOS / de).resolve()
    if not fuente.is_file():
        salir(f"no existe {fuente}")
    if hasta <= desde:
        salir("`--hasta` tiene que ser mayor que `--desde`")
    if not shutil.which("ffmpeg"):
        salir("falta ffmpeg en el PATH")
    destino = MUESTRAS / f"{id_}.mp4"
    destino.parent.mkdir(parents=True, exist_ok=True)
    orden = [
        "ffmpeg", "-v", "error", "-y", "-ss", str(desde), "-i", str(fuente), "-t", str(hasta - desde),
        "-vf", f"scale=-2:'min({alto},ih)':flags=lanczos", "-c:v", "libx264", "-preset", "slow", "-crf", "30",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(destino),
    ]
    subprocess.run(orden, check=True)
    e = json.loads(ruta.read_text(encoding="utf-8"))
    # De dónde salió, por si el render ya no está cuando alguien la mire.
    e["muestra"] = {"de": de.replace("\\", "/"), "desde": desde, "hasta": hasta}
    escribir_json(ruta, e)
    print(f"→ {destino} ({destino.stat().st_size / 1e6:.2f} MB)")


# ── El veredicto ───────────────────────────────────────────────────────────

def limpiar_cita(cita: str) -> str:
    """Las palabras de Miguel en una sola línea, sin las comillas que las envuelven enteras
    (las de adentro se quedan: «me gusta el "empuje"» sigue siendo eso)."""
    t = " ".join(str(cita).split())
    for abre, cierra in (("«", "»"), ("“", "”"), ('"', '"')):
        if len(t) >= 2 and t[0] == abre and t[-1] == cierra and abre not in t[1:-1] and cierra not in t[1:-1]:
            t = t[1:-1].strip()
    return t[:600]


def veredicto(id_: str, estado: str, cita: str = "", via: str = "chat") -> dict:
    """Anota el veredicto de Miguel sobre un estilo: `estado`, cuándo y por dónde lo dio y, si dijo
    algo, sus palabras (en `miguel` del estilo y al final de direccion/REGISTRO.md, que las guarda
    todas en orden). Lo llama la galería del panel (`via="galeria"`: el clic vale como veredicto
    aunque no escriba nada) y sirve igual para lo que diga en el chat.

        python montaje.py veredicto transicion-iris aprobado --cita "ese sí"
    """
    import datetime as dt
    import re

    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", id_) or not (ESTILOS / f"{id_}.json").exists():
        salir(f"no existe el estilo «{id_}»")
    if estado not in ESTADOS:
        salir(f"estado desconocido: {estado} (hay: {', '.join(ESTADOS)})")
    ruta = ESTILOS / f"{id_}.json"
    e = json.loads(ruta.read_text(encoding="utf-8"))
    palabras = limpiar_cita(cita)
    fecha = dt.date.today().isoformat()
    e["estado"] = estado
    if palabras and palabras not in e["miguel"]:
        e["miguel"].append(palabras)
    if estado in ("propuesta", "pedido"):
        e.pop("veredicto", None)  # deshacer: vuelve a esperar; las palabras ya anotadas quedan
    else:
        e["veredicto"] = {"estado": estado, "fecha": fecha, "via": via}
    escribir_json(ruta, e)
    registro = RAIZ / "direccion" / "REGISTRO.md"
    if palabras and registro.exists():
        crudo = registro.read_bytes().decode("utf-8")
        texto = crudo.replace("\r\n", "\n").rstrip()
        titulo = f"## {fecha} · Veredictos desde la galería" if via == "galeria" else f"## {fecha} · Veredictos"
        if titulo not in texto:
            texto += f"\n\n{titulo}\n"
        texto += f"\n- {e['nombre']} (`{id_}`), {estado}: «{palabras}»\n"
        # Los saltos de línea, como estaban.
        registro.write_bytes((texto.replace("\n", "\r\n") if "\r\n" in crudo else texto).encode("utf-8"))
    return e


# ── El recorrido: la galería de corrido ────────────────────────────────────

#: En qué orden pasan: primero lo que Miguel ya eligió.
_ORDEN_ESTADO = ["aprobado", "a medias", "pedido", "propuesta", "rechazado"]


def _letra(nombres: list[str], tam: int):
    """La primera tipografía que haya en el sistema; si ninguna, la de PIL."""
    from PIL import ImageFont

    for n in nombres:
        try:
            return ImageFont.truetype(n, tam)
        except OSError:
            continue
    return ImageFont.load_default()


def _rotulo(nombre: str, dato: str, W: int, H: int, destino: Path) -> None:
    """El cartel de un tramo del recorrido: una banda oscura abajo, el dato y el nombre."""
    from PIL import Image, ImageDraw

    alto = round(H * 0.135)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    banda = Image.new("RGBA", (W, alto), (7, 9, 13, 0))
    d = ImageDraw.Draw(banda)
    for y in range(alto):
        d.line([(0, y), (W, y)], fill=(7, 9, 13, int(205 * y / alto)))
    im.alpha_composite(banda, (0, H - alto))
    d = ImageDraw.Draw(im)
    margen = round(W * 0.026)
    d.rectangle([margen, H - round(alto * 0.77), margen + 3, H - round(alto * 0.27)], fill=(230, 180, 60))
    d.text((margen + 16, H - round(alto * 0.81)), dato, font=_letra(["consola.ttf", "DejaVuSansMono.ttf"], round(H * 0.024)), fill=(198, 207, 217))
    d.text((margen + 16, H - round(alto * 0.6)), nombre.upper(), font=_letra(["bahnschrift.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"], round(H * 0.046)),
           fill=(230, 180, 60))
    im.save(destino)


def elegir_para_recorrido(estilos: list[dict], en: str | None, estado: str | None, para: str | None) -> list[dict]:
    """Los estilos que entran al recorrido (con muestra o sin ella), en el orden en que pasan."""
    elegidos = [e for e in estilos
                if (en is None or en in e["visto_en"]) and (estado is None or e["estado"] == estado) and (para is None or para in e["para"])]
    return sorted(elegidos, key=lambda e: (_ORDEN_ESTADO.index(e["estado"]) if e["estado"] in _ORDEN_ESTADO else 99, e["id"]))


def recorrido(en: str | None = None, estado: str | None = None, para: str | None = None, segundos: float = 6.0,
              nombre: str | None = None, peso: float = 28.0, lienzo: tuple[int, int] = (1080, 720)) -> Path:
    """Unos segundos de cada muestra, con su nombre y su estado, en un solo video liviano.

    Para ver de corrido lo que dejó un ejercicio (`--en`) o toda la galería, y para
    mandarlo por chat: si pasa de `peso` MB se recodifica en dos pasadas hasta caber.
    Sale de las muestras, no de los renders: sirve aunque los renders ya se hayan borrado.
    """
    import os
    import tempfile

    if not shutil.which("ffmpeg"):
        salir("falta ffmpeg en el PATH")
    elegidos = elegir_para_recorrido(leer(), en, estado, para)
    con_muestra = [e for e in elegidos if muestra_de(e).exists()]
    if not con_muestra:
        salir("ningún estilo con muestra cumple el filtro")
    sin = [e["id"] for e in elegidos if not muestra_de(e).exists()]
    if sin:
        print(f"sin muestra (no entran): {', '.join(sin)}")
    W, H = lienzo
    destino = MUESTRAS / "recorridos" / f"{nombre or 'recorrido' + ('-' + en if en else '') + ('-' + estado.replace(' ', '-') if estado else '')}.mp4"
    destino.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        partes = []
        for i, e in enumerate(con_muestra):
            fuente = muestra_de(e)
            sondeo = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type", "-of", "json", str(fuente)],
                                    capture_output=True, text=True, check=True)
            datos = json.loads(sondeo.stdout)
            dura = min(segundos, float(datos["format"]["duration"]))
            con_audio = any(st.get("codec_type") == "audio" for st in datos.get("streams", []))
            cartel = tmp / f"r{i:03d}.png"
            _rotulo(e["nombre"], f"{e['estado']} · {e['id']}", W, H, cartel)
            entradas = ["-t", f"{dura:.3f}", "-i", str(fuente), "-loop", "1", "-t", f"{dura:.3f}", "-i", str(cartel)]
            if not con_audio:
                entradas += ["-f", "lavfi", "-t", f"{dura:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
            filtro = (f"[0:v]fps=24,scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x07090d,setsar=1[v];"
                      f"[v][1:v]overlay=0:0:format=auto,format=yuv420p,fade=in:0:8,fade=out:st={max(0.0, dura - 0.35):.3f}:d=0.35[s];"
                      f"[{'0' if con_audio else '2'}:a]aresample=48000,afade=in:st=0:d=0.25,afade=out:st={max(0.0, dura - 0.4):.3f}:d=0.4[a]")
            parte = tmp / f"p{i:03d}.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-y", *entradas, "-filter_complex", filtro, "-map", "[s]", "-map", "[a]",
                            "-c:v", "libx264", "-crf", "18", "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2", str(parte)], check=True)
            partes.append(parte)
        lista = tmp / "lista.txt"
        lista.write_text("".join(f"file '{p.as_posix()}'\n" for p in partes), encoding="utf-8")
        crudo = tmp / "crudo.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy", "-movflags", "+faststart", str(crudo)],
                       check=True)
        total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(crudo)],
                                     capture_output=True, text=True, check=True).stdout)
        if crudo.stat().st_size <= peso * 1024 * 1024:
            shutil.copy2(crudo, destino)
        else:
            tasa = max(200_000, int(peso * 0.97 * 8 * 1024 * 1024 / total - 128_000))
            for pasada in (1, 2):
                orden = ["ffmpeg", "-v", "error", "-y", "-i", str(crudo), "-c:v", "libx264", "-preset", "slow", "-b:v", str(tasa),
                         "-pass", str(pasada), "-passlogfile", str(tmp / "pasada")]
                orden += ["-an", "-f", "mp4", os.devnull] if pasada == 1 else ["-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(destino)]
                subprocess.run(orden, check=True)
    print(f"{len(con_muestra)} estilos, {total:.0f} s, {destino.stat().st_size / 1e6:.1f} MB")
    print(f"→ {destino}")
    return destino
