"""Que el motor aprenda de las notas de Miguel.

Dos fuentes, y ninguna adivina:

- **Las lecciones** (`direccion/LECCIONES.json`): lo que Miguel dijo que cambia cómo se arma, con su cita,
  su fecha y su regla. Una lección con `perillas` o `capa` la aplica sola el primer armado de `guion`
  en los tramos donde vale (`cuando`: energía, modo, tono del proyecto, si la canción tiene letra); una con
  `consejo`, la dice. Se escriben a mano: el motor no saca reglas de una sola frase sin que alguien la lea.
- **Los veredictos de la galería** (`estilos/*.json`): `aprender` compara, perilla por perilla, las recetas
  aprobadas contra las que quedaron «a medias» o «no», y dice qué estilos rechazados no tienen todavía su
  porqué (sin porqué no se puede escribir su `evitar`). Con pocos veredictos es una pista, no una regla.

    python montaje.py aprender        → direccion/APRENDIDO.md

El `tono` de un proyecto (`"tono": "recuerdo"` en proyecto.json) dice a qué canciones se parece: una
lección aprendida con una canción de recuerdo no se impone sola a una de fiesta.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

from . import estilos as catalogo
from .rutas import MEDIOS, RAIZ

LECCIONES = RAIZ / "direccion" / "LECCIONES.json"
APRENDIDO = RAIZ / "direccion" / "APRENDIDO.md"


def leer() -> list[dict]:
    return json.loads(LECCIONES.read_text(encoding="utf-8"))["lecciones"] if LECCIONES.exists() else []


def nombre_de_audio(ruta: str) -> str:
    """El nombre con que `transcribir` guarda lo de un audio (el mismo cálculo que `transcribir._nombre`)."""
    a = unicodedata.normalize("NFKD", Path(ruta).stem).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", a).strip("-") or "audio"


def transcripcion_de(cfg: dict) -> str | None:
    """La transcripción de la canción del proyecto, si ya se hizo (relativa a los medios)."""
    musica = cfg.get("musica")
    if not musica:
        return None
    rel = f"transcripciones/{nombre_de_audio(musica)}.srt"
    return rel if (MEDIOS / rel).exists() else None


def vale(leccion: dict, energia: str | None = None, modo: str | None = None, tono: str | None = None, letra: bool = False) -> bool:
    """¿La lección vale aquí? Cada condición de `cuando` que la lección pone tiene que cumplirse."""
    c = leccion.get("cuando") or {}
    if "energia" in c and energia not in c["energia"]:
        return False
    if "modo" in c and modo != c["modo"]:
        return False
    if "tono" in c and tono not in c["tono"]:
        return False
    if c.get("letra") and not letra:
        return False
    return True


def sobre_tramo(tramo: dict, energia: str, modo: str, tono: str | None, lecciones: list[dict] | None = None) -> list[str]:
    """Le pone a un tramo del armado las perillas de las lecciones que valen ahí; devuelve sus ids."""
    usadas = []
    for lc in lecciones if lecciones is not None else leer():
        if lc.get("perillas") and vale(lc, energia, modo, tono):
            tramo.update(lc["perillas"])
            usadas.append(lc["id"])
    return usadas


def faltan_por_tono(energia: str, modo: str, tono: str | None, lecciones: list[dict] | None = None) -> list[dict]:
    """Las lecciones que valdrían si el proyecto dijera su tono: para avisar, no para imponer."""
    return [lc for lc in (lecciones if lecciones is not None else leer())
            if lc.get("perillas") and "tono" in (lc.get("cuando") or {}) and tono is None
            and vale({**lc, "cuando": {k: v for k, v in lc["cuando"].items() if k != "tono"}}, energia, modo)]


def capas(cfg: dict, lecciones: list[dict] | None = None) -> list[tuple[str, dict]]:
    """Las capas que las lecciones suman al armado entero (la letra al centro, si la canción la tiene)."""
    transcrita = transcripcion_de(cfg)
    salida = []
    for lc in lecciones if lecciones is not None else leer():
        if lc.get("capa") and vale(lc, tono=cfg.get("tono"), letra=bool(transcrita)):
            capa = dict(lc["capa"])
            if capa.get("tipo") == "rotulos" and transcrita:
                capa["transcripcion"] = transcrita
            salida.append((lc["id"], capa))
    return salida


def consejos(lecciones: list[dict] | None = None) -> list[dict]:
    return [lc for lc in (lecciones if lecciones is not None else leer()) if lc.get("consejo")]


# ── Los veredictos como datos ──────────────────────────────────────────────

def comparar(estilos: list[dict]) -> list[dict]:
    """Por cada perilla con número que aparece en tres recetas o más: sus valores en lo aprobado y en lo demás."""
    valores: dict[str, dict[str, list[float]]] = defaultdict(lambda: {"aprobado": [], "otro": []})
    for e in estilos:
        grupo = "aprobado" if e["estado"] == "aprobado" else "otro" if e["estado"] in ("a medias", "rechazado") else None
        if not grupo:
            continue
        t = e.get("tecnica") or {}
        # La misma palabra es otra perilla en otra técnica: la `fuerza` del golpe no es la de la tinta.
        donde = t.get("capa") or t.get("comando") or t.get("modo") or "?"
        for k, v in t.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                valores[f"{donde} · {k}"][grupo].append(float(v))
            elif isinstance(v, list) and len(v) == 2 and all(isinstance(x, (int, float)) for x in v):
                valores[f"{donde} · {k}"][grupo].append(float(sum(v)) / 2)  # un rango [calma, pico]: su punto medio
    filas = []
    for k, g in sorted(valores.items()):
        if len(g["aprobado"]) + len(g["otro"]) >= 3:
            filas.append({"perilla": k, **g})
    return filas


def sin_porque(estilos: list[dict]) -> list[dict]:
    """Los estilos con «no» o «a medias» sin una palabra de Miguel. El `evitar` que se escribió al proponerlos no cuenta:
    es lo que se sospechaba antes, no por qué no le gustó."""
    return [e for e in estilos if e["estado"] in ("rechazado", "a medias") and not e.get("miguel") and not (e.get("veredicto") or {}).get("cita")]


def _rango(xs: list[float]) -> str:
    if not xs:
        return "—"
    a, b = min(xs), max(xs)
    f = lambda x: f"{x:g}".replace(".", ",")  # noqa: E731
    return f"{f(a)}" if a == b else f"{f(a)}–{f(b)}"


def escribir() -> Path:
    lecciones = leer()
    estilos = catalogo.leer()
    cuenta = {s: sum(e["estado"] == s for e in estilos) for s in catalogo.ESTADOS}
    filas = [
        "# Lo aprendido",
        "",
        "> **Lo escribe `python montaje.py aprender`** desde `direccion/LECCIONES.json` y los veredictos de `estilos/`.",
        "> No se corrige aquí: una lección nueva va a LECCIONES.json, con la cita de Miguel.",
        "",
        "## Las lecciones",
        "",
    ]
    for lc in lecciones:
        como = ("el primer armado de `guion` le pone " + ", ".join(f"`{k}` {json.dumps(v)}" for k, v in lc["perillas"].items())
                if lc.get("perillas") else f"el primer armado suma la capa `{lc['capa']['tipo']}`" if lc.get("capa") else "`guion` lo dice como consejo")
        cuando = ", ".join(f"{k}: {v if not isinstance(v, list) else ' o '.join(v)}" for k, v in (lc.get("cuando") or {}).items()) or "siempre"
        filas += [f"### {lc['id']} · {lc['fecha']}", "", f"«{lc['cita']}»", "", f"**Regla:** {lc['regla']}", "",
                  f"**Cuándo:** {cuando}. **Qué hace:** {como}."]
        if lc.get("medido"):
            filas += ["", f"**Medido:** {lc['medido']}"]
        filas.append("")
    filas += ["## Los veredictos como datos", "",
              f"La galería tiene {len(estilos)} estilos: " + ", ".join(f"{n} {s}" for s, n in cuenta.items() if n) + ".",
              "Por perilla, los valores de lo aprobado y de lo que quedó a medias o en «no» (un rango es su punto medio).",
              "Con tan pocos «no», es una pista: dice dónde mirar, no qué hacer.", "",
              "| Perilla | Aprobado | A medias o no |", "|---|---|---|"]
    for f in comparar(estilos):
        filas.append(f"| `{f['perilla']}` | {_rango(f['aprobado'])} ({len(f['aprobado'])}) | {_rango(f['otro'])} ({len(f['otro'])}) |")
    falta = sin_porque(estilos)
    filas += ["", "## Lo que falta saber", ""]
    if falta:
        filas += ["Estos estilos tienen «no» o «a medias» sin porqué: hasta saberlo, su `evitar` queda vacío y el motor sólo",
                  "puede no elegirlos, no aprender de ellos.", ""]
        filas += [f"- `{e['id']}` ({e['estado']}): {e.get('frase') or e.get('nombre', '')}" for e in falta]
    else:
        filas.append("Todo «no» y «a medias» dice por qué.")
    filas.append("")
    APRENDIDO.write_text("\n".join(filas), encoding="utf-8")
    print(f"{len(lecciones)} lecciones; {len(comparar(estilos))} perillas comparadas; {len(falta)} estilos sin porqué → {APRENDIDO}")
    return APRENDIDO
