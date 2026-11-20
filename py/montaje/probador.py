"""El probador: el mismo banco para todos los estilos.

Cada estilo de la galería hace aquí su muestra con el mismo material: los mismos clips, las mismas
fotos y el mismo trozo de canción (`proyectos/probador/proyecto.json`). Así las muestras se comparan
de verdad —lado a lado y sincronizadas, porque todas suenan igual y empiezan con el mismo clip—,
cada una deja unos cuadros de referencia para saber si un cambio al motor la tocó, y se mide cuánto
tarda cada estilo en dibujarse. Un estilo nuevo se prueba aquí sin armar un proyecto.

Se prueba **la receta del estilo tal como está escrita** (`tecnica` en `estilos/<id>.json`): la misma
que usa `guion` para armar un video. Si la muestra del probador no se parece a la de su video, a la
receta le falta algo, y eso también es un hallazgo. Lo que la receta no dice con valores (las capas
que acompañan, escritas en palabras en `con`) se toma de la versión del experimento que hizo su
muestra; los textos (título, rótulos, crédito) son los del banco (`textos`), nunca los de Miguel.

    python montaje.py probar --armar               # el banco: vínculos a los clips, las fotos y la canción
    python montaje.py probar toma-por-frase eco    # esos estilos
    python montaje.py probar --todos               # la galería entera; lo que no cambió no se vuelve a dibujar
    python montaje.py probar --todos --fijar       # además, los cuadros de ahora pasan a ser la referencia

Lo que deja, fuera del repo como las demás muestras (`~/Videos/montaje/estilos/probador/`):
`<id>.mp4` (la muestra), `ref/<id>-<n>.png` (los cuadros de referencia) y `registro.json` (cuánto
tardó, cuánto se parece a su referencia, por qué no se probó). El panel lo lee en `/estilos`.

El banco vive en su propia biblioteca (`~/Videos/montaje/probador`), hecha de vínculos duros a la de
práctica: no ocupa disco y sus clips transformados no se mezclan con los de los experimentos. El
análisis de la canción es el de la canción entera, cortado en el tramo del banco (mismos golpes y
misma energía que en un video de verdad): no correr `analizar` sobre el probador; `--armar` lo rehace.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from . import clips as catalogo_clips
from . import estilos as galeria
from . import musica, por_tramos, pulso, sintesis, transformar
from .rutas import MEDIOS, PROYECTOS, Proyecto, escribir_json, leer_json, salir

NOMBRE = "probador"
DESTINO = MEDIOS / "estilos" / "probador"
REGISTRO = DESTINO / "registro.json"
#: La receta del banco es la de este estilo: contra él se mide lo que tarda cada uno.
BASE = "toma-por-frase"
#: Dónde se toman los cuadros de referencia, en fracciones del video.
CUADROS = (0.2, 0.5, 0.85)
#: Desde cuánto parecido (SSIM: 1 es idéntico) un cuadro se considera el mismo.
IGUAL = 0.98
#: Capas cuyo texto pone el banco: el de un video es de Miguel y no viaja.
CON_TEXTO = {"titulo", "rotulos", "credito"}
#: Lo que el banco todavía no sabe probar, y por qué.
MODOS_DE_FOTOS = {"collage", "secuencia", "cinta", "actos", "superposicion"}
POR_QUE_NO = {
    "fotos": "modo de fotos: el banco todavía prueba sobre clips (le falta su catálogo de imágenes)",
    "momento": "un momento (ráfaga, destacado) va dentro de un modo de fotos: el banco todavía prueba sobre clips",
    "sincronizar": "rehace un video ya editado: necesita ese video, no un banco",
    "sobre-render": "va sobre un render terminado de un proyecto: todavía no se prueba aquí",
}


# ── El banco ───────────────────────────────────────────────────────────────

def _vincular(origen: Path, destino: Path) -> None:
    """Un vínculo duro (no ocupa disco); si ya está, no se toca. En otra unidad, una copia."""
    if not origen.exists():
        salir(f"no existe {origen}")
    if destino.exists():
        if destino.stat().st_size == origen.stat().st_size:
            return
        destino.unlink()
    destino.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(origen, destino)
    except OSError:
        shutil.copy2(origen, destino)


def cortar(m: dict, a: float, b: float) -> dict:
    """El análisis de la canción entera, en el tramo [a, b): los tiempos cuentan desde `a`.

    Analizar sólo el tramo daría otra energía (se normaliza contra sí mismo: la calma dejaría de
    ser calma), otras secciones (habría tres en quince segundos) y otro primer tiempo del compás.
    """
    eps = 1e-3
    # Los bordes van al primer tiempo del compás más cercano: escritos a mano, con dos decimales, caerían un poco antes o después.
    al_uno = lambda t: min(m["primeros_tiempos"], key=lambda u: abs(u - t))  # noqa: E731
    a = al_uno(a) if abs(al_uno(a) - a) < 0.1 else a
    b = al_uno(b) if abs(al_uno(b) - b) < 0.1 else b
    idx = [i for i, t in enumerate(m["beats"]) if a - eps <= t < b - eps]
    if len(idx) < 8:
        salir(f"el tramo {a}–{b} tiene {len(idx)} golpes: muy corto para un banco")
    beats = [round(m["beats"][i] - a, 3) for i in idx]
    unos = [round(t - a, 3) for t in m["primeros_tiempos"] if a - eps <= t < b - eps]
    fase = next((k for k, t in enumerate(beats) if unos and abs(t - unos[0]) < 0.02), 0) % 4
    secciones = []
    for s in m["secciones"]:
        ini, fin = max(s["ini"], a), min(s["fin"], b)
        if fin - ini < 0.5:
            continue
        dentro = [k for k, i in enumerate(idx) if ini - eps <= m["beats"][i] < fin - eps]
        if not dentro:
            continue
        energia = [m["energia"][idx[k]] for k in dentro]
        secciones.append({"beat_ini": dentro[0], "beat_fin": dentro[-1] + 1, "ini": round(ini - a, 3), "fin": round(fin - a, 3),
                          "energia": round(sum(energia) / len(energia), 3)})
    return {**m, "tramo": [a, b], "duracion": round(b - a, 3), "golpes_intro": 0, "beats": beats,
            "energia": [m["energia"][i] for i in idx], "fase_compas": fase, "primeros_tiempos": unos, "secciones": secciones}


def armar() -> Proyecto:
    """Arma (o completa) la biblioteca del banco desde la de práctica y analiza su canción."""
    p = Proyecto(NOMBRE)
    banco = p.cfg.get("banco") or salir("proyectos/probador/proyecto.json no tiene `banco`")
    de = MEDIOS / banco["de"]
    catalogo = leer_json(de / "analisis" / "clips.json")["clips"]
    por_id = {c["id"]: c for c in catalogo}
    pedidos = list(banco["clips"]) + list(banco.get("fotos", []))
    faltan = [i for i in pedidos if i not in por_id]
    if faltan:
        salir(f"no están en el catálogo de {banco['de']}: {', '.join(faltan)}")
    elegidos = [por_id[i] for i in pedidos]
    for c in elegidos:
        _vincular(de / c["src"], p.medios / c["src"])
        if not c.get("foto"):
            for carpeta in ("proxies", "borradores"):
                f = de / carpeta / Path(c["proxy"]).name
                if f.exists():
                    _vincular(f, p.medios / carpeta / f.name)
    for carpeta in p.cfg["clips"]:
        (p.medios / carpeta).mkdir(parents=True, exist_ok=True)
    _vincular(de / banco["musica"], p.medios / banco["musica"])
    # El catálogo: el de práctica para lo elegido (mismas medidas, mismas firmas) y los transformados que ya hubiera.
    destino = catalogo_clips.ruta_catalogo(p)
    previos = [c for c in leer_json(destino)["clips"] if c["src"].startswith("transformados/")] if destino.exists() else []
    escribir_json(destino, {"generado": dt.datetime.now().isoformat(timespec="seconds"), "clips": elegidos + previos})
    # La cámara lenta fluida: las copias interpoladas, si alguna falta (las de práctica ya vienen hechas).
    catalogo_clips.asegurar_copias(p, {c["proxy"] for c in elegidos if not c.get("foto")})
    # La canción: entera una vez, y cortada en el tramo.
    a, b = p.cfg["tramo"]
    entera = p.salida("analisis", "musica-entera.json")
    if not entera.exists():
        sin_tramo = Proyecto(NOMBRE)
        sin_tramo.cfg.pop("tramo", None)
        musica.analizar(sin_tramo)
        p.salida("analisis", "musica.json").replace(entera)
    m = cortar(leer_json(entera), a, b)
    escribir_json(p.salida("analisis", "musica.json"), m, compacto=True)
    n_clips = sum(not c.get("foto") for c in elegidos)
    print(f"banco: {n_clips} clips y {len(elegidos) - n_clips} fotos de {banco['de']}, {m['duracion']:.1f} s de "
          f"{Path(banco['musica']).stem} ({m['tramo'][0]:g}–{m['tramo'][1]:g} s, {m['bpm']:.0f} BPM, {len(m['primeros_tiempos'])} compases) → {p.medios}")
    return p


# ── La receta de cada estilo, sobre el banco ───────────────────────────────

_proyectos: dict[str, dict | None] = {}


def _su_video(e: dict) -> dict:
    """La versión del experimento que hizo la muestra del estilo (vacía si no se sabe)."""
    de = (e.get("muestra") or {}).get("de") or ""
    if not de:
        return {}
    nombre, archivo = de.split("/")[0], Path(de).stem
    if nombre not in _proyectos:
        ruta = PROYECTOS / nombre / "proyecto.json"
        _proyectos[nombre] = leer_json(ruta) if ruta.exists() else None
    versiones = (_proyectos[nombre] or {}).get("versiones", {})
    v = next((k for k in sorted(versiones, key=len, reverse=True) if archivo == k or archivo.startswith(k + "-")), None)
    return versiones[v] if v else {}


def _lienzo(texto: str, base: dict) -> dict:
    m = re.fullmatch(r"(\d+)x(\d+)", str(texto))
    if not m:
        salir(f"`salida` de la receta va como 1080x1920, no «{texto}»")
    return {**base, "ancho": int(m.group(1)), "alto": int(m.group(2))}


def _capa(tipo: str, propios: dict, fuente: dict, cfg: dict, m: dict) -> dict:
    """Una capa de síntesis para el banco: lo de su video, encima lo de la receta, y el texto del banco."""
    entrada = {k: v for k, v in fuente.items() if k != "tipo"}
    entrada.update(propios)
    dur = m["duracion"]
    # Los segundos de su video no son los del banco: entra desde el comienzo (o donde decía, si cabe) hasta el final.
    if not 0 <= float(entrada.get("desde", 0)) < dur / 2:
        entrada.pop("desde", None)
    entrada.pop("hasta", None)
    textos = cfg.get("textos", {})
    if tipo == "titulo":
        entrada["texto"] = textos.get("titulo", "")
    elif tipo == "credito":
        entrada["lineas"] = list(textos.get("credito", ["", "sonando ahora"]))
    elif tipo == "rotulos":
        entrada.pop("transcripcion", None)
        unos = m["primeros_tiempos"]
        # Una línea cada dos compases, desde el segundo: cae donde caen los cortes.
        entrada["lineas"] = [[round(t, 2), x] for t, x in zip(unos[1::2], textos.get("rotulos", []))]
    return {"tipo": tipo, **entrada}


def receta(e: dict, cfg: dict, m: dict) -> tuple[dict | None, str]:
    """Lo que el estilo le cambia al banco: `montaje` (perillas), `sintesis` (capas), `salida` (lienzo),
    `transformar` ([efecto, fuerza]) y `proyector` (nivel). None y el porqué si no se sabe probar."""
    t = e["tecnica"]
    # De cada tipo, la primera capa de su video (un título puede venir con su subtítulo detrás).
    fuentes: dict[str, dict] = {}
    for s in _su_video(e).get("sintesis", []):
        if isinstance(s, dict) and "tipo" in s:
            fuentes.setdefault(s["tipo"], s)

    def capa(tipo: str, propios: dict | None = None) -> dict:
        return _capa(tipo, propios or {}, fuentes.get(tipo, {}), cfg, m)

    def junto(lista) -> list[dict]:
        # «recuerdo» o, en palabras, «tinta rubrica/hueso 0.35»: la capa es la primera palabra; sus valores, los de su video.
        nombres = [str(x).split()[0] for x in ([lista] if isinstance(lista, str) else lista or [])]
        return [capa(n) for n in nombres if n in sintesis.POR_DEFECTO]

    modo = t.get("modo")
    if modo == "pulso":
        r = {"montaje": {k: v for k, v in t.items() if k in pulso.POR_DEFECTO}, "sintesis": junto(t.get("sintesis"))}
        if "salida" in t:
            r["salida"] = _lienzo(t["salida"], cfg["salida"])
        return r, ""
    if modo == "solo-sintesis":
        return {"montaje": {"modo": "solo-sintesis"}, "sintesis": junto(t.get("capas"))}, ""
    if modo in MODOS_DE_FOTOS:
        return None, POR_QUE_NO["fotos"]
    if "momento" in t:
        return None, POR_QUE_NO["momento"]
    if "capa" in t:
        tipo = t["capa"]
        if tipo not in sintesis.POR_DEFECTO:
            return None, f"la capa «{tipo}» no está en el motor"
        propios = {k: v for k, v in t.items() if k in sintesis.POR_DEFECTO[tipo]}
        return {"montaje": {}, "sintesis": [capa(tipo, propios)] + [c for c in junto(t.get("con")) if c["tipo"] != tipo]}, ""
    comando = t.get("comando")
    if comando == "transformar":
        efecto = t.get("efecto")
        if efecto not in transformar.EFECTOS:
            return None, f"efecto desconocido: {efecto}"
        return {"montaje": {"transformados": efecto}, "sintesis": [],
                "transformar": [efecto, float(t.get("fuerza", transformar.POR_DEFECTO[efecto]))]}, ""
    if comando == "proyector":
        # El proyector suena donde hay película: la de su video (la tira, la cuenta).
        cine = [capa(tipo) for tipo in ("pelicula", "cuenta") if tipo in fuentes] or [capa("pelicula")]
        return {"montaje": {}, "sintesis": cine, "proyector": float(t.get("nivel", 16))}, ""
    if comando == "analogo":
        # El banco tal cual, pasado después por la cadena de aparatos (como se usa: sobre un render).
        cadena = {"aparatos": t["cadena"], **{k: t[k] for k in ("captura", "semilla") if k in t}}
        return {"montaje": {}, "sintesis": [], "analogo": cadena}, ""
    if comando == "sincronizar":
        return None, POR_QUE_NO["sincronizar"]
    if comando:
        return None, POR_QUE_NO["sobre-render"]
    return None, "la receta no dice ni modo, ni capa, ni comando"


def huella_receta(r: dict) -> str:
    return hashlib.sha256(json.dumps(r, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]


class Probada(Proyecto):
    """El banco con la receta de un estilo encima. Su timeline vive en los medios: es de usar y tirar."""

    def __init__(self, id_: str, r: dict):
        super().__init__(NOMBRE)
        self.version = id_
        self.estilo = id_
        self.cfg["montaje"] = {**self.cfg.get("montaje", {}), **r.get("montaje", {})}
        self.cfg["sintesis"] = r.get("sintesis", [])
        if r.get("salida"):
            self.cfg["salida"] = r["salida"]
        self._timeline = self.salida("timelines", f"{id_}.json")

    @property
    def timeline(self) -> Path:
        return self._timeline


def _transformar(p: Proyecto, efecto: str, fuerza: float) -> None:
    """Las variantes con ese efecto y esa fuerza, para cada clip del banco (lo ya hecho igual no se rehace)."""
    hechos_f = p.medio("transformados", "hechos.json")
    hechos = leer_json(hechos_f) if hechos_f.exists() else {}
    originales = [c for c in catalogo_clips.cargar(p) if not c.get("foto") and not c["src"].startswith("transformados/")]
    faltan = [c["id"] for c in originales
              if hechos.get(f"{c['id']}-{efecto}") != fuerza or not (p.medios / "transformados" / f"{c['id']}-{efecto}.mp4").exists()]
    if not faltan:
        return
    transformar.transformar(p, efecto, faltan, fuerza)
    hechos.update({f"{i}-{efecto}": fuerza for i in faltan})
    escribir_json(hechos_f, hechos)
    catalogo_clips.analizar(p)


# ── Muestra, cuadros de referencia y registro ──────────────────────────────

def _duracion(video: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def _muestra(render: Path, destino: Path) -> None:
    """Como las demás muestras (`estilos.muestra`): alto 540, H.264 CRF 30, audio a 96 kb/s."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = destino.with_suffix(".tmp.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(render), "-vf", "scale=-2:'min(540,ih)':flags=lanczos",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "30", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k",
                    "-movflags", "+faststart", str(temporal)], check=True)
    temporal.replace(destino)


def _cuadro(video: Path, t: float, destino: Path) -> None:
    """Un cuadro a 270 de alto: la mitad de la muestra alcanza para ver si algo cambió y pesa la cuarta parte."""
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(video), "-frames:v", "1",
                    "-vf", "scale=-2:270:flags=area", str(destino)], check=True)


def parecido(a: Path, b: Path) -> float:
    """SSIM entre dos cuadros (1 = idéntico), con el filtro de ffmpeg."""
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(a), "-i", str(b), "-lavfi", "[0:v][1:v]scale2ref[x][y];[x][y]ssim", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"All:([0-9.]+)", r.stderr)
    if not m:
        salir(f"ffmpeg no comparó {a.name} con {b.name}")
    return float(m.group(1))


def referencia(id_: str, render: Path, fijar: bool) -> list[float] | None:
    """Los cuadros de ahora contra los de referencia. Sin referencia (o con `fijar`), los de ahora la pasan a ser: None."""
    dur = _duracion(render)
    carpeta = DESTINO / "ref"
    carpeta.mkdir(parents=True, exist_ok=True)
    refs = [carpeta / f"{id_}-{k}.png" for k in range(len(CUADROS))]
    if fijar or not all(r.exists() for r in refs):
        for f, r in zip(CUADROS, refs):
            _cuadro(render, f * dur, r)
        return None
    valores = []
    for f, r in zip(CUADROS, refs):
        ahora = r.with_name(r.stem + "-ahora.png")
        _cuadro(render, f * dur, ahora)
        valores.append(round(parecido(r, ahora), 4))
        ahora.unlink()
    return valores


def leer_registro() -> dict:
    return leer_json(REGISTRO) if REGISTRO.exists() else {}


def costo(registro: dict, id_: str) -> float | None:
    """Lo que tarda en dibujarse, en veces lo que tarda el banco solo."""
    a, b = (registro.get(id_) or {}).get("dibujo_s"), (registro.get(BASE) or {}).get("dibujo_s")
    return round(a / b, 2) if a and b else None


# ── Probar ─────────────────────────────────────────────────────────────────

def probar(ids: list[str] | None, fijar: bool = False, rehacer: bool = False) -> int:
    """Prueba esos estilos (o todos) sobre el banco. Devuelve cuántos fallaron.

    `rehacer`: se vuelven a dibujar aunque estén guardados (para medir otra vez lo que tardan, o para ver
    si el dibujo sale igual dos veces). El primer dibujo de cada vuelta se hace dos veces y vale el
    segundo: el primero paga el arranque (los clips que todavía no están en la memoria del disco)."""
    from argparse import Namespace

    from . import planificar, proyector
    from .cli import cmd_render

    base = Proyecto(NOMBRE)
    if not catalogo_clips.ruta_catalogo(base).exists() or not (base.salidas / "analisis" / "musica.json").exists():
        salir("el banco no está armado: corre `python montaje.py probar --armar`")
    m = musica.cargar(base)
    todos = {e["id"]: e for e in galeria.leer()}
    desconocidos = [i for i in ids or [] if i not in todos]
    if desconocidos:
        salir(f"no hay estilos {', '.join(desconocidos)} (están en estilos/)")
    # El banco solo primero: contra él se mide lo que tarda cada uno.
    pedidos = sorted(ids or todos, key=lambda i: (i != BASE, i))
    registro = leer_registro()
    tramos_dir = base.salida("render", ".tramos", "x").parent
    filas, fallas, calentado = [], 0, False

    def dibujar(p: Proyecto) -> tuple[Path, float, list[str]]:
        antes = set(tramos_dir.glob("*.mp4"))
        por_tramos.medidas.clear()
        render = cmd_render(p, Namespace(preview=True, desde=None, hasta=None, salida=None))
        # Sólo el dibujo: preparar el paquete tarda lo mismo para todos y no dice nada del estilo.
        return render, por_tramos.medidas.get("dibujo_s", 0.0), sorted(f.name for f in set(tramos_dir.glob("*.mp4")) - antes)

    for id_ in pedidos:
        e = todos[id_]
        r, motivo = receta(e, base.cfg, m)
        ahora = dt.datetime.now().isoformat(timespec="seconds")
        if r is None:
            registro[id_] = {"fecha": ahora, "motivo": motivo}
            filas.append((id_, e["estado"], "", "", "", f"no se prueba: {motivo}"))
            continue
        print(f"\n── {id_} " + "─" * max(4, 60 - len(id_)), flush=True)
        anterior = registro.get(id_, {})
        try:
            if r.get("transformar"):
                _transformar(base, *r["transformar"])
            p = Probada(id_, r)
            planificar.planificar(p)
            if rehacer:
                for nombre in anterior.get("piezas", []):
                    (tramos_dir / nombre).unlink(missing_ok=True)
            render, dibujo, nuevas = dibujar(p)
            if nuevas and not calentado:
                print("  (el primer dibujo de la vuelta paga el arranque: va de nuevo para medirlo)", flush=True)
                for nombre in nuevas:
                    (tramos_dir / nombre).unlink(missing_ok=True)
                render, dibujo, nuevas = dibujar(p)
            calentado = calentado or bool(nuevas)
            dibujado = bool(nuevas)
            dibujo_del_banco = render
            if r.get("proyector") is not None:
                proyector.proyector(p, render.name, r["proyector"])
                render = render.with_name(render.stem + "-proyector.mp4")
            if r.get("analogo") is not None:
                from . import analogo

                t0 = time.time()
                sale = render.with_name(render.stem + "-analogo.mp4")
                analogo.procesar(render, sale, r["analogo"], callado=True)
                render = sale
                # Lo que cuesta un estilo analógico es su cadena, no el banco (que sale guardado).
                dibujo, dibujado = time.time() - t0, True
            muestra = DESTINO / f"{id_}.mp4"
            _muestra(render, muestra)
            intermedios = {render, dibujo_del_banco}
            # Si cambió la receta, la referencia vieja no sirve para juzgar al motor: se renueva.
            receta_nueva = bool(anterior.get("receta")) and anterior["receta"] != huella_receta(r)
            valores = referencia(id_, render, fijar or receta_nueva)
            # El render se cose de nuevo en un segundo desde los pedazos guardados: lo que queda es la muestra.
            for f in intermedios:
                f.unlink(missing_ok=True)
            tl = leer_json(p.timeline)
            codigo = por_tramos.huella_codigo()[:12]
            # Una misma medida varía hasta un tercio de una vez a otra: vale la menor con el mismo código
            # (lo que el estilo cuesta de verdad, sin lo que el computador estaba haciendo al lado).
            # (No para las cadenas analógicas: su código no entra en la huella, y un motor más lento quedaría escondido.)
            if (dibujado and not r.get("analogo") and anterior.get("dibujo_s") and anterior.get("codigo") == codigo
                    and anterior.get("receta") == huella_receta(r)):
                dibujo = min(dibujo, anterior["dibujo_s"])
            entrada = {"fecha": ahora, "receta": huella_receta(r), "lienzo": f"{tl['ancho']}x{tl['alto']}",
                       "segundos": round(tl["duracion"] / tl["fps"], 2), "mb": round(muestra.stat().st_size / 1e6, 2),
                       # Lo que tardó sólo vale si de verdad se dibujó: un pedazo guardado sale en un segundo.
                       "dibujo_s": round(dibujo, 1) if dibujado else anterior.get("dibujo_s"),
                       "parecido": valores, "referencia": "nueva" if valores is None else "comparada",
                       "codigo": codigo, "piezas": nuevas or anterior.get("piezas", [])}
            registro[id_] = entrada
            cambio = valores is not None and min(valores) < IGUAL
            nota = ("receta nueva: referencia nueva" if receta_nueva else "referencia nueva" if valores is None
                    else "CAMBIÓ contra su referencia" if cambio else "igual a su referencia")
            filas.append((id_, e["estado"], f"{entrada['dibujo_s'] or 0:.0f} s" + ("" if dibujado else " (guardado)"),
                          "", " ".join(f"{v:.3f}" for v in valores or []), nota))
        except (SystemExit, Exception) as err:  # noqa: BLE001  un estilo que falla no detiene a los demás
            fallas += 1
            registro[id_] = {**anterior, "fecha": ahora, "falla": f"{type(err).__name__}: {err}"[:300]}
            filas.append((id_, e["estado"], "", "", "", f"FALLÓ: {err}"[:120]))
        escribir_json(REGISTRO, registro)
    print("\n" + "═" * 72)
    for id_, estado, tardo, _, valores, nota in filas:
        x = costo(registro, id_)
        print(f"{id_:<28} {estado:<10} {tardo:>14} {f'×{x:.1f}' if x else '':>6}  {valores:<20} {nota}")
    probados = sum(1 for f in filas if not f[5].startswith(("no se prueba", "FALLÓ")))
    print(f"{probados} probados, {len(filas) - probados - fallas} sin probar, {fallas} fallaron · muestras y registro en {DESTINO}")
    return fallas
