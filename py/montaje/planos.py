"""Planos: el video contado plano a plano, como en un guion de documental.

Los demás modos cortan al pulso de una canción. Éste sigue un guion escrito por planos (el de un
trabajo, un informe, un documental): cada plano dice qué imagen se ve, cuánto dura, por dónde la
recorre la cámara, qué texto aparece y qué se dibuja encima. La música va debajo, más baja donde
habla la voz y callada donde suena una cuña.

En proyecto.json, `"montaje": {"modo": "planos"}` y una lista `planos`:

    {"n": 4, "dura": 5, "img": "fotos/1.png",
     "camara": [[0, null], [0.7, [0.5, 0.5, 0.2]]],      # [momento, encuadre]; null = la imagen entera
     "efectos": [{"tipo": "gris_fuera", "zona": [0.43, 0.43, 0.58, 0.58], "ini": 0.2, "dura": 0.3}],
     "textos": [{"texto": "Autora (2024, p. 12)", "estilo": "cita", "desde": 0.1, "hasta": 1}],
     "difuminar": [[0.1, 0.4, 0.9, 0.95]],               # zonas que se borronean en la imagen (datos personales)
     "entrada": 0.5,                                      # segundos de fundido (0 = corte)
     "musica_db": -14,                                    # la cama en este plano (null = callada)
     "falta": "la portada de la propuesta 2026"}          # lo que todavía no llegó: un aviso en el borrador

Una **serie** («tres fotos, corte cada 2,5 s»): `"imgs"` en vez de `"img"`, cada una un nombre o
`{"img", "camara", "difuminar"}`. Se cortan parejo dentro del plano, cada una con un acercamiento
lento (o su `camara`), y los textos del plano siguen encima sin cortarse.

Los momentos (`camara`, `desde`/`hasta` de los textos, `ini`/`dura` de los efectos) van en
fracciones del plano, de 0 a 1: cuando la voz llegue y los planos cambien de largo, todo se
reacomoda solo. Las zonas y los encuadres, en fracciones de la imagen ([centro x, centro y, ancho]).

Las imágenes no se tocan: se dibuja desde copias livianas en `derivados/` (a lo sumo 3200 px de
lado, con las zonas de `difuminar` ya borroneadas). El sonido se mezcla aquí en una sola pista
(`derivados/mezcla-….wav`): la música compuesta (`componer`, que se rehace si cambia el largo) y,
cuando estén, la voz y las cuñas. La voz va por tramos: `"voz": {"archivo": "voz/vo1-limpia.wav", "desde": 2.95}`
en el plano donde entra (sigue sonando por los planos siguientes hasta que se acaba); las cuñas, con
`"video": {"desde": s, "volumen": 1}` en su plano.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path

import numpy as np

from . import textos as galeria_textos
from .rutas import Proyecto, salir

FPS = 30
MAXIMO = 3200
FUNDIDO = 0.5
#: dB de la música donde no se dice otra cosa (sin voz todavía; con voz, la regla del guion: 20 dB bajo ella).
MUSICA_DB = -14.0
RAMPA = 0.6
ESTILOS = {"portada", "titulo", "rotulo", "cita", "frase", "aviso"}
#: Las transiciones de la galería que aprobó Miguel (la persiana, no). Con transición, la entrada por defecto es de 0,7 s.
TRANSICIONES = ("cortina", "iris", "empuje", "destello", "zoom")
ENTRADA_TRANSICION = 0.7
EFECTOS = {"gris", "gris_fuera", "resaltar", "tachar", "islas_fantasma", "silueta", "isla_nueva"}


def _huella(*partes) -> str:
    return hashlib.sha256(json.dumps(partes, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()[:10]


def derivado(p: Proyecto, rel: str, difuminar: list | None = None, maximo: int = MAXIMO) -> tuple[str, list[int]]:
    """Una copia liviana de la imagen, con las zonas de `difuminar` borroneadas. El original no se toca."""
    from PIL import Image, ImageFilter, ImageOps

    origen = p.medios / rel
    if not origen.is_file():
        salir(f"no existe {origen}")
    st = origen.stat()
    png = origen.suffix.lower() == ".png"
    destino = p.medio("derivados", f"{origen.stem}-{_huella(rel, st.st_size, int(st.st_mtime), difuminar, maximo)}.{'png' if png else 'jpg'}")
    if destino.exists():
        with Image.open(destino) as im:
            return destino.relative_to(p.medios).as_posix(), list(im.size)
    with Image.open(origen) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        w, h = im.size
        for x0, y0, x1, y1 in difuminar or []:
            caja = (int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h))
            radio = max(6, round(0.018 * max(w, h)))
            # Dos pasadas: que no se lea ni de cerca.
            borron = im.crop(caja).filter(ImageFilter.GaussianBlur(radio)).filter(ImageFilter.GaussianBlur(radio))
            im.paste(borron, caja)
        k = min(1.0, maximo / max(w, h))
        if k < 1:
            im = im.resize((round(w * k), round(h * k)), Image.LANCZOS)
        im.save(destino, **({"optimize": True} if png else {"quality": 92}))
        return destino.relative_to(p.medios).as_posix(), list(im.size)


def _tamano_video(ruta: Path) -> list[int]:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", str(ruta)],
                       capture_output=True, text=True, check=True)
    w, h = r.stdout.strip().split(",")[:2]
    return [int(w), int(h)]


def derivado_video(p: Proyecto, rel: str, desde: float, dura: float, ancho_min: float) -> tuple[str, list[int]]:
    """El tramo que el plano usa de un video, sin audio (la voz y las cuñas van en la mezcla) y del tamaño que pide su
    encuadre más cerrado. Un 4K de cámara entero (35-120 Mb/s) hace que el compositor de Remotion se pase de su espera
    cuando dos planos del mismo video se cruzan (2026-11-17, cuadro 6575 del 23): con el tramo a ~1080p, no."""
    origen = p.medios / rel
    if not origen.is_file():
        salir(f"no existe {origen}")
    w, h = _tamano_video(origen)
    # Que el encuadre más cerrado (`ancho_min` de la imagen) siga llenando 1920 px sin agrandar.
    ancho = min(w, 2 * math.ceil(1920 / max(0.1, ancho_min) / 2))
    alto = 2 * round(h * ancho / w / 2)
    st = origen.stat()
    destino = p.medio("derivados", f"{origen.stem}-{_huella(rel, st.st_size, int(st.st_mtime), round(desde, 3), round(dura, 3), ancho)}.mp4")
    if not destino.exists():
        print(f"  derivado de video: {rel} {desde:.2f}+{dura:.2f} s a {ancho}×{alto}", flush=True)
        tmp = destino.with_suffix(".tmp.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{desde:.3f}", "-i", str(origen), "-t", f"{dura:.3f}", "-an",
                        "-vf", f"scale={ancho}:{alto}:flags=lanczos", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                        "-pix_fmt", "yuv420p", "-g", "15", "-movflags", "+faststart", str(tmp)], check=True)
        tmp.replace(destino)
    return destino.relative_to(p.medios).as_posix(), [ancho, alto]


def texto_a_timeline(n, t: dict, ini: int, fin: int) -> dict:
    """Un texto en cuadros. Con `letrero`, un estilo de la galería de textos (textos/<id>.json, se dibuja con
    Letrero.tsx); si no, uno de los estilos propios del modo (`estilo`, con su `tono` y su `lugar`)."""
    if t.get("letrero"):
        return {"texto": t["texto"], "estilo": t.get("estilo", "titulo"), "ini": ini, "fin": fin,
                "letrero": galeria_textos.estilo(t["letrero"]), **({"secundario": t["secundario"]} if t.get("secundario") else {})}
    if t.get("estilo") not in ESTILOS:
        salir(f"plano {n}: estilo de texto desconocido «{t.get('estilo')}» (hay: {', '.join(sorted(ESTILOS))}; "
              "o un `letrero` de la galería de textos)")
    return {"texto": t["texto"], "estilo": t["estilo"], "ini": ini, "fin": fin,
            **({"tono": t["tono"]} if t.get("tono") else {}), **({"lugar": t["lugar"]} if t.get("lugar") else {})}


def _encuadre(e):
    if e is None:
        return None
    if not (isinstance(e, list) and len(e) == 3):
        salir(f"un encuadre es [centro x, centro y, ancho] en fracciones de la imagen, o null; no {e}")
    return [round(float(v), 4) for v in e]


def plano_a_timeline(p: Proyecto, pl: dict, n_cuadros: int, ini: int, entrada: int) -> dict:
    """Un plano de proyecto.json, en cuadros y con sus imágenes livianas."""
    a = lambda u: round(float(u) * n_cuadros)  # noqa: E731  fracción del plano → cuadros
    salida: dict = {"id": f"plano-{pl['n']}", "n": pl["n"], "ini": ini, "fin": ini + n_cuadros, "entrada": entrada}
    if pl.get("img"):
        if pl.get("video"):
            # Sólo su tramo, con 2 s de más: el plano sigue debajo mientras entra el siguiente (hasta ~1 s).
            anchos = [e[1][2] for e in pl.get("camara") or [] if isinstance(e, list) and len(e) == 2 and e[1]]
            salida["img"], salida["fuente"] = derivado_video(p, pl["img"], float(pl["video"].get("desde", 0)),
                                                             n_cuadros / FPS + 2.0, min(anchos, default=1.0))
            salida["video"] = {"desde": 0.0}
        else:
            salida["img"], salida["fuente"] = derivado(p, pl["img"], pl.get("difuminar"))
    if pl.get("color"):
        salida["color"] = pl["color"]
    if pl.get("velo"):
        salida["velo"] = float(pl["velo"])
    if pl.get("transicion"):
        tr = pl["transicion"] if isinstance(pl["transicion"], dict) else {"tipo": pl["transicion"]}
        if tr["tipo"] not in TRANSICIONES:
            salir(f"plano {pl['n']}: transición desconocida «{tr['tipo']}» (hay: {', '.join(TRANSICIONES)})")
        salida["transicion"] = {"tipo": tr["tipo"], "dir": list(tr.get("dir", [1, 0])), **({"centro": list(tr["centro"])} if tr.get("centro") else {})}
    salida["camara"] = [{"t": a(t), "e": _encuadre(e)} for t, e in (pl.get("camara") or [[0, None]])]
    efectos = []
    for e in pl.get("efectos") or []:
        if e.get("tipo") not in EFECTOS:
            salir(f"plano {pl['n']}: efecto desconocido «{e.get('tipo')}» (hay: {', '.join(sorted(EFECTOS))})")
        x = dict(e)
        for k in ("ini", "dura", "cada"):
            if k in x:
                x[k] = a(x[k])
        efectos.append(x)
    if efectos:
        salida["efectos"] = efectos
    textos = [texto_a_timeline(pl["n"], t, a(t.get("desde", 0)), a(t.get("hasta", 1))) for t in pl.get("textos") or []]
    if pl.get("falta"):
        textos.append({"texto": f"FALTA · {pl['falta']}", "estilo": "aviso", "ini": 0, "fin": n_cuadros})
    if textos:
        salida["textos"] = textos
    if pl.get("rodillo"):
        salida["rodillo"] = list(pl["rodillo"])
    return salida


#: El acercamiento lento de una foto de una serie, una vez hacia un lado y otra hacia el otro.
KEN_BURNS = ([[0, [0.5, 0.5, 1.0]], [1, [0.53, 0.47, 0.84]]], [[0, [0.52, 0.48, 0.86]], [1, [0.48, 0.52, 1.0]]])


def serie(pl: dict) -> list[dict]:
    """Las fotos de una serie como planos sin texto (los textos van aparte, encima de todas)."""
    piezas = []
    for k, x in enumerate(pl["imgs"]):
        x = {"img": x} if isinstance(x, str) else dict(x)
        color = x.get("color", pl.get("color"))
        # La primera foto entra con la transición del plano; las demás, con la suya si la dicen.
        tr = x.get("transicion", pl.get("transicion") if k == 0 else None)
        piezas.append({"n": f"{pl['n']}.{k + 1}", "img": x["img"], "camara": x.get("camara", KEN_BURNS[k % 2]),
                       **({"transicion": tr} if tr else {}),
                       **({"difuminar": x["difuminar"]} if x.get("difuminar") else {}), **({"color": color} if color else {}),
                       **({"dura": float(x["dura"])} if x.get("dura") else {}), **({"entrada": float(x["entrada"])} if x.get("entrada") else {})})
    return piezas


#: Largo de una fila de subtítulo y de un subtítulo entero (dos filas), en caracteres.
FILA = 42
CUADRO = 80


def _filas(texto: str) -> str:
    """Una o dos filas: si no cabe en una, se corta en el espacio más cerca de la mitad."""
    if len(texto) <= FILA:
        return texto
    mitad = len(texto) // 2
    espacios = [i for i, c in enumerate(texto) if c == " "]
    if not espacios:
        return texto
    k = min(espacios, key=lambda i: abs(i - mitad))
    return texto[:k] + "\n" + texto[k + 1:]


def subtitulos(p: Proyecto, planos: list[dict], marcas: list[tuple[float, float]]) -> list[dict]:
    """Los subtítulos de la voz, en segundos del video: las palabras de cada transcripción (`transcribir` de la voz
    original; la limpia tiene los mismos tiempos), agrupadas en subtítulos de una o dos filas que cortan en las pausas
    y en los puntos. `subtitulos.correcciones` de proyecto.json arregla lo que la transcripción entendió mal."""
    from .rutas import MEDIOS

    correcciones = (p.cfg.get("subtitulos") or {}).get("correcciones", {})
    salida = []
    for pl, (a, _) in zip(planos, marcas):
        v = pl.get("voz")
        if not v:
            continue
        nombre = Path(v["archivo"]).stem.removesuffix("-limpia")
        ruta = MEDIOS / "transcripciones" / f"{nombre}.json"
        if not ruta.exists():
            continue
        corrimiento = a - float(v.get("desde", 0))
        palabras = [w for s in json.loads(ruta.read_text(encoding="utf-8"))["segmentos"] for w in s["palabras"]]
        grupo: list[dict] = []

        def cerrar():
            if not grupo:
                return
            texto = " ".join(w["p"].strip() for w in grupo)
            for mal, bien in correcciones.items():
                texto = texto.replace(mal, bien)
            salida.append({"t": round(grupo[0]["ini"] + corrimiento, 3), "fin": round(grupo[-1]["fin"] + corrimiento + 0.3, 3), "texto": texto})
            grupo.clear()

        for w in palabras:
            if grupo:
                largo = len(" ".join(x["p"] for x in grupo)) + 1 + len(w["p"])
                pausa = w["ini"] - grupo[-1]["fin"]
                punto = grupo[-1]["p"].rstrip().endswith((".", "?", "!", ":"))
                coma = grupo[-1]["p"].rstrip().endswith((",", ";"))
                if pausa > 0.6 or largo > CUADRO or (punto and largo > 24) or (coma and largo > 55):
                    cerrar()
            grupo.append(w)
        cerrar()
    salida.sort(key=lambda s: s["t"])
    for s, sig in zip(salida, salida[1:]):
        s["fin"] = min(s["fin"], sig["t"] - 0.05)
        s["fin"] = max(s["fin"], min(s["t"] + 1.0, sig["t"] - 0.05))
    for s in salida:
        s["texto"] = _filas(s["texto"])
    return salida


def escribir_srt(destino: Path, subs: list[dict]) -> None:
    def hms(t: float) -> str:
        ms = round(t * 1000)
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"

    destino.write_text("".join(f"{i}\n{hms(s['t'])} --> {hms(s['fin'])}\n{s['texto']}\n\n" for i, s in enumerate(subs, 1)), encoding="utf-8")


def tiempos(planos: list[dict]) -> list[tuple[float, float]]:
    """Dónde empieza y termina cada plano, en segundos del video (uno detrás de otro)."""
    t, salida = 0.0, []
    for pl in planos:
        dura = float(pl.get("dura", 0))
        if dura <= 0:
            salir(f"plano {pl.get('n')}: falta `dura` (segundos)")
        salida.append((t, t + dura))
        t += dura
    return salida


def envolvente(planos: list[dict], marcas: list[tuple[float, float]], total: float, defecto: float, rampa: float, sr: int) -> np.ndarray:
    """La ganancia de la música, muestra a muestra: el nivel de cada plano, con rampas suaves entre uno y otro."""
    n = int(round(total * sr))
    g = np.zeros(n)
    for pl, (a, b) in zip(planos, marcas):
        db = pl.get("musica_db", defecto)
        g[int(a * sr): int(b * sr)] = 0.0 if db is None else 10 ** (float(db) / 20)
    # Rampas: media móvil por suma acumulada (una convolución directa de un segundo a 48 kHz sobre
    # cinco minutos son cientos de miles de millones de cuentas; ésta es lineal).
    k = max(1, int(rampa * sr))
    c = np.concatenate([[0.0], np.cumsum(np.pad(g, (k // 2, k - 1 - k // 2), mode="edge"))])
    return ((c[k:] - c[:-k]) / k)[:n]


def _leer_audio(ruta: Path, sr: int, desde: float = 0.0, dura: float | None = None) -> np.ndarray:
    """Un audio (o el sonido de un video) en estéreo, a `sr`, por ffmpeg."""
    orden = ["ffmpeg", "-v", "error", "-ss", f"{desde:.3f}", "-i", str(ruta)]
    if dura is not None:
        orden += ["-t", f"{dura:.3f}"]
    orden += ["-ac", "2", "-ar", str(sr), "-f", "f32le", "-"]
    datos = subprocess.run(orden, capture_output=True, check=True).stdout
    return np.frombuffer(datos, dtype=np.float32).reshape(-1, 2).astype(np.float64)


def mezclar(p: Proyecto, planos: list[dict], marcas: list[tuple[float, float]], total: float) -> str | None:
    """La pista entera: música con su envolvente, la voz si está y las cuñas de los clips. → derivados/mezcla-….wav"""
    import soundfile as sf

    from .sonido import SR

    mezcla_cfg = p.cfg.get("mezcla", {})
    fuentes = []
    if p.cfg.get("musica"):
        ruta = p.medios / p.cfg["musica"]
        fuentes.append(("musica", ruta))
    cunas = [(pl, m) for pl, m in zip(planos, marcas) if pl.get("video") and pl["video"].get("volumen")]
    # La voz va por tramos (vo1, vo2…): cada una entra donde empieza el plano que la nombra y sigue hasta su final.
    voces = [(pl["voz"], a) for pl, (a, _) in zip(planos, marcas) if pl.get("voz")]
    if not fuentes and not cunas and not voces:
        return None
    firmas = [(k, str(r), r.stat().st_size, int(r.stat().st_mtime)) for k, r in fuentes if r.exists()]
    for v, _ in voces:
        r = p.medios / v["archivo"]
        if not r.exists():
            salir(f"no existe la voz {r}")
        firmas.append(("voz", v["archivo"], r.stat().st_size, int(r.stat().st_mtime)))
    destino = p.medio("derivados", f"mezcla-{_huella(firmas, [(pl, m) for pl, m in zip(planos, marcas)], mezcla_cfg, total)}.wav")
    if destino.exists():
        return destino.relative_to(p.medios).as_posix()
    n = int(round(total * SR))
    pista = np.zeros((n, 2))
    for clave, ruta in fuentes:
        if not ruta.exists():
            salir(f"no existe {ruta}")
        y = _leer_audio(ruta, SR)[:n]
        y = y * envolvente(planos, marcas, total, mezcla_cfg.get("musica_db", MUSICA_DB), mezcla_cfg.get("rampa", RAMPA), SR)[: len(y), None]
        pista[: len(y)] += y
    for v, a in voces:
        desde = float(v.get("desde", 0))
        y = _leer_audio(p.medios / v["archivo"], SR, desde, float(v["hasta"]) - desde if v.get("hasta") else None)
        y = y * 10 ** (float(mezcla_cfg.get("voz_db", 0)) / 20)
        i = int(a * SR)
        pista[i: i + len(y)] += y[: max(0, n - i)]
    for pl, (a, b) in cunas:
        y = _leer_audio(p.medios / pl["img"], SR, float(pl["video"].get("desde", 0)), b - a) * float(pl["video"]["volumen"])
        i = int(a * SR)
        pista[i: i + len(y)] += y[: n - i]
    pico = np.max(np.abs(pista)) or 1.0
    if pico > 0.89:  # -1 dBFS
        pista *= 0.89 / pico
    sf.write(str(destino), pista.astype(np.float32), SR, subtype="PCM_24")
    return destino.relative_to(p.medios).as_posix()


def planificar(p: Proyecto) -> None:
    from . import componer
    from .planificar import escribir

    planos = p.cfg.get("planos") or salir("modo planos sin `planos` en proyecto.json")
    out = {"ancho": 1920, "alto": 1080, "fps": FPS, "fondo": "#07090d", **p.cfg.get("salida", {})}
    fps = int(out["fps"])
    marcas = tiempos(planos)
    total = marcas[-1][1]
    fundido = float(p.cfg.get("montaje", {}).get("fundido", FUNDIDO))
    entradas = [round(float(pl.get("entrada", (ENTRADA_TRANSICION if pl.get("transicion") else fundido) if i else 0)) * fps)
                for i, pl in enumerate(planos)]
    lista, textos = [], []
    for i, (pl, (a, b)) in enumerate(zip(planos, marcas)):
        ini = round(a * fps)
        n_cuadros = round(b * fps) - ini
        piezas = serie(pl) if pl.get("imgs") else [pl]
        # Cada foto de la serie dura lo que dice (en proporción, para que sumen el plano) o todas igual.
        pesos = [x.get("dura", 1.0) for x in piezas] if len(piezas) > 1 and all(x.get("dura") for x in piezas) else [1.0] * len(piezas)
        acum = np.cumsum([0.0, *pesos]) / sum(pesos)
        cortes = [ini + round(n_cuadros * u) for u in acum]
        for k, pieza in enumerate(piezas):
            entra = entradas[i] if k == 0 else round(float(pieza.get("entrada", 0)) * fps)
            if k > 0 and entra:
                piezas_previa = lista[-1]
                piezas_previa["fin"] += entra  # la anterior sigue debajo mientras ésta entra
            tl_pl = plano_a_timeline(p, pieza, cortes[k + 1] - cortes[k], cortes[k], entra)
            if k + 1 == len(piezas) and i + 1 < len(planos):
                # El que se va sigue debajo hasta que el que llega termina de entrar.
                tl_pl["fin"] += entradas[i + 1]
                # Y si el que llega empuja, éste sale por el otro lado en esos mismos cuadros.
                sig = planos[i + 1].get("transicion")
                sig = sig if isinstance(sig, dict) else {"tipo": sig} if sig else None
                if sig and sig["tipo"] == "empuje" and entradas[i + 1]:
                    tl_pl["empujada"] = {"cuadros": entradas[i + 1], "dir": list(sig.get("dir", [1, 0]))}
            lista.append(tl_pl)
        if len(piezas) > 1:
            # Los textos de la serie, en cuadros del video: siguen encima mientras las fotos se cortan.
            for t in pl.get("textos") or []:
                textos.append(texto_a_timeline(pl["n"], t, ini + round(float(t.get("desde", 0)) * n_cuadros),
                                               ini + round(float(t.get("hasta", 1)) * n_cuadros)))
    # La música compuesta dura lo que el video: si el largo cambió, se compone de nuevo.
    if p.cfg.get("componer"):
        ruta = p.medios / p.cfg["musica"]
        dura_actual = None
        if ruta.exists():
            import soundfile as sf

            dura_actual = sf.info(str(ruta)).duration
        if dura_actual is None or abs(dura_actual - total) > 0.25:
            p.cfg["componer"] = {**p.cfg["componer"], "archivo": p.cfg["musica"]}
            componer.escribir(p, total)
    audio = mezclar(p, planos, marcas, total)
    subs = subtitulos(p, planos, marcas)
    if subs:
        # Para revisar el texto: lo que la transcripción entendió mal se corrige en `subtitulos.correcciones`.
        escribir_srt(p.dir / "subtitulos.srt", subs)
    tl = {
        "version": 1,
        "modo": "planos",
        "proyecto": p.nombre,
        "ancho": int(out["ancho"]),
        "alto": int(out["alto"]),
        "fps": fps,
        "fondo": out["fondo"],
        "duracion": round(total * fps),
        "audio": {"src": audio, "desde": 0, "hasta": round(total, 3)} if audio else None,
        "meta": {"planos": len(planos), "segundos": round(total, 2)},
        "planos": lista,
        **({"textos": textos} if textos else {}),
        **({"subtitulos": [{"ini": round(s["t"] * fps), "fin": round(s["fin"] * fps), "texto": s["texto"]} for s in subs]} if subs else {}),
        "capas": [],
    }
    # Las tipografías de los letreros: el render las pone en su carpeta pública (cli._publico).
    fuentes = galeria_textos.archivos([t["letrero"] for t in [*textos, *(t for x in lista for t in x.get("textos", []))] if t.get("letrero")])
    if fuentes:
        tl["fuentes"] = fuentes
    escribir(p.timeline, tl)
    print(f"{len(planos)} planos, {total // 60:.0f}:{total % 60:04.1f} a {fps} cps → {p.timeline}")
    for pl, (a, b) in zip(planos, marcas):
        aviso = f"  · FALTA: {pl['falta']}" if pl.get("falta") else ""
        print(f"  {str(pl['n']):>4}  {a // 60:.0f}:{a % 60:04.1f}–{b // 60:.0f}:{b % 60:04.1f}  {Path(pl.get('img') or '(fondo)').name}{aviso}")
