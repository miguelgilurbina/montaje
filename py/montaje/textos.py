"""La galería de textos: estilos de letra con nombre para títulos, frases, rótulos, subtítulos y créditos.

Pedida por Miguel el 2026-11-17, después del primer documental: «una galería de textos con fonts, con
estilos, de forma que tengamos algo base propio para la galería, para usar como de repente como
títulos». Cada estilo es un archivo en `textos/<id>.json` con su tipografía (de `fuentes/`, libres y
dentro del repo), su forma (tamaño, color, contorno, caja…), dónde va y cómo entra y sale. Se ven en
vivo en el panel (`/textos`), con el mismo componente que los dibuja en el video (src/Letrero.tsx), y
el veredicto se da ahí, como en los estilos.

En `planos`, un texto lo usa por su nombre:

    "textos": [{"texto": "Señales desde la radio", "letrero": "cartel-curiana", "desde": 0.1, "hasta": 0.95}]

    python montaje.py textos                      # valida y lista la galería
    python montaje.py textos --familia rotulos    # sólo una familia
"""

from __future__ import annotations

import json

from .rutas import RAIZ, salir

TEXTOS = RAIZ / "textos"
FUENTES = RAIZ / "fuentes"

# Vocabulario cerrado, como el de los estilos. Una palabra nueva se agrega aquí, en src/tipos.ts y en textos/README.md.
FAMILIAS = {
    "titulos": "títulos y portadas",
    "frases": "frases destacadas",
    "rotulos": "rótulos y citas",
    "subtitulos": "subtítulos y créditos",
    # Elegida por Miguel el 2026-11-19: la ventana, atravesar una letra, el karaoke, el latido, las letras que se arman.
    "movimiento": "texto en movimiento",
}
LUGARES = {"centro", "arriba", "abajo", "tercio-inferior", "arriba-izquierda", "abajo-izquierda", "abajo-derecha"}
ENTRADAS = {"fundido", "subir", "acercar", "desenfoque", "maquina", "palabras", "barrido", "armar", "ola", "ninguna"}
SALIDAS = {"fundido", "bajar", "atravesar", "ninguna"}
FONDOS = {"oscuro", "claro", "imagen", "mapa"}
ALINEADOS = {"izquierda", "centro", "derecha"}
#: Lo que va al timeline (la forma). El resto (nombre, frase, ejemplo, veredicto…) es de la galería.
DIBUJO = ["fuente", "peso", "cursiva", "variacion", "tamano", "mayusculas", "espaciado", "interlineado", "color", "compresion",
          "contorno", "sombra", "caja", "resaltado", "barra", "alineado", "lugar", "ancho", "giro", "entrada", "salida",
          "secundario", "rodillo", "ventana", "karaoke", "latido", "cursor"]
CAMPOS = ["nombre", "familia", "frase", "para", "fuente", "tamano", "color", "lugar", "ejemplo", "fondo", "estado", "miguel"]


def registro() -> dict:
    """Las tipografías del motor (fuentes/fuentes.json): familia → voz, licencia y archivos con su rango de pesos."""
    return json.loads((FUENTES / "fuentes.json").read_text(encoding="utf-8"))["familias"]


def leer() -> list[dict]:
    if not TEXTOS.exists():
        return []
    lista = []
    for ruta in sorted(TEXTOS.glob("*.json")):
        try:
            e = json.loads(ruta.read_text(encoding="utf-8"))
        except json.JSONDecodeError as err:
            salir(f"textos/{ruta.name}: no es JSON válido ({err})")
        e["id"] = ruta.stem
        lista.append(e)
    return lista


def _letra(e: dict, donde: str, familias: dict) -> list[str]:
    """Lo que está mal en una letra (la principal o la secundaria): tipografía, peso y cursiva que existan."""
    mal = []
    f = familias.get(e.get("fuente"))
    if not f:
        return [f"{donde}`fuente`: «{e.get('fuente')}» no está en fuentes/fuentes.json ({', '.join(familias)})"]
    peso = e.get("peso", 400)
    caras = [a for a in f["archivos"] if bool(a["cursiva"]) == bool(e.get("cursiva"))]
    if not caras:
        mal.append(f"{donde}{e['fuente']} no tiene cursiva" if e.get("cursiva") else f"{donde}{e['fuente']} sólo tiene cursiva")
    elif not any(a["peso"][0] <= peso <= a["peso"][1] for a in caras):
        mal.append(f"{donde}{e['fuente']} no tiene peso {peso} (tiene {', '.join(f'{a['peso'][0]}–{a['peso'][1]}' for a in caras)})")
    t = e.get("tamano")
    if not isinstance(t, (int, float)) or not 0.01 <= t <= 0.4:
        mal.append(f"{donde}`tamano` es el alto de la letra en fracción del cuadro (0,01 a 0,4), no {t}")
    if not str(e.get("color", "")).startswith("#"):
        mal.append(f"{donde}`color` va en #rrggbb (o #rrggbbaa)")
    return mal


def errores(e: dict, familias: dict | None = None) -> list[str]:
    """Lo que le falta o le sobra a un estilo de texto. Vacío = está bien."""
    from .estilos import ESTADOS

    familias = familias or registro()
    mal = [f"falta `{c}`" for c in CAMPOS if c not in e]
    if mal:
        return mal
    if e["familia"] not in FAMILIAS:
        mal.append(f"`familia`: «{e['familia']}» no es {' / '.join(FAMILIAS)}")
    if e["lugar"] not in LUGARES:
        mal.append(f"`lugar`: «{e['lugar']}» no es {' / '.join(sorted(LUGARES))}")
    if e.get("alineado") and e["alineado"] not in ALINEADOS:
        mal.append(f"`alineado`: «{e['alineado']}» no es {' / '.join(ALINEADOS)}")
    if e["fondo"] not in FONDOS:
        mal.append(f"`fondo` (el de la muestra): «{e['fondo']}» no es {' / '.join(sorted(FONDOS))}")
    if e.get("entrada") and e["entrada"].get("tipo") not in ENTRADAS:
        mal.append(f"`entrada.tipo`: «{e['entrada'].get('tipo')}» no es {' / '.join(sorted(ENTRADAS))}")
    if e.get("salida") and e["salida"].get("tipo") not in SALIDAS:
        mal.append(f"`salida.tipo`: «{e['salida'].get('tipo')}» no es {' / '.join(sorted(SALIDAS))}")
    if e["estado"] not in ESTADOS:
        mal.append(f"`estado`: «{e['estado']}» no es {' / '.join(ESTADOS)}")
    if e["estado"] in ("aprobado", "a medias", "rechazado") and not e["miguel"] and not e.get("veredicto"):
        mal.append(f"`estado` {e['estado']} sin las palabras de Miguel en `miguel` ni su veredicto de la galería")
    if not isinstance(e["ejemplo"], dict) or not str(e["ejemplo"].get("texto", "")).strip():
        mal.append("`ejemplo` lleva al menos `texto` (lo que muestra la galería)")
    if not isinstance(e["para"], list) or not e["para"]:
        mal.append("`para`: una lista de usos, en palabras")
    mal += _letra(e, "", familias)
    if e.get("secundario"):
        mal += _letra(e["secundario"], "`secundario`: ", familias)
    if e.get("latido"):
        bpm = e["latido"].get("bpm")
        if bpm != "cancion" and not (isinstance(bpm, (int, float)) and 30 <= bpm <= 240):
            mal.append(f"`latido.bpm`: un tempo de 30 a 240, o «cancion» para el del proyecto (no {bpm})")
        if not isinstance(e["latido"].get("fuerza"), (int, float)) or not 0 < e["latido"]["fuerza"] <= 0.5:
            mal.append("`latido.fuerza`: cuánto crece en el golpe, de 0 a 0,5")
    if e.get("ventana") and not str(e["ventana"].get("fuera", "")).startswith("#"):
        mal.append("`ventana.fuera`: el color de afuera de las letras, en #rrggbb")
    if e.get("karaoke") and not str(e["karaoke"].get("activa", "")).startswith("#"):
        mal.append("`karaoke.activa`: el color de la palabra que suena, en #rrggbb")
    return mal


def estilo(id_: str, bpm: float | None = None) -> dict:
    """El estilo listo para el timeline: sólo su forma (lo que dibuja Letrero.tsx), con su id. Un `latido` con el
    tempo «cancion» toma `bpm`, el del proyecto."""
    ruta = TEXTOS / f"{id_}.json"
    if not ruta.exists():
        hay = ", ".join(e["id"] for e in leer())
        salir(f"no existe el letrero «{id_}» en textos/ (hay: {hay})")
    e = json.loads(ruta.read_text(encoding="utf-8"))
    mal = errores(e)
    if mal:
        salir(f"textos/{id_}.json: " + "; ".join(mal))
    forma = {"id": id_, **{k: e[k] for k in DIBUJO if k in e}}
    if forma.get("latido", {}).get("bpm") == "cancion":
        if not bpm:
            salir(f"el letrero «{id_}» late con la canción y el proyecto no tiene tempo (`componer.bpm` o `bpm` en proyecto.json)")
        forma["latido"] = {**forma["latido"], "bpm": float(bpm)}
    return forma


def archivos(estilos: list[dict]) -> list[str]:
    """Las tipografías que usan estos estilos, como rutas dentro de fuentes/ (normal y cursiva de cada familia)."""
    familias = registro()
    usadas = {x["fuente"] for e in estilos for x in (e, e.get("secundario") or {}) if x.get("fuente") in familias}
    return sorted(a["archivo"] for f in usadas for a in familias[f]["archivos"])


def listar(familia: str | None = None, estado: str | None = None) -> None:
    todos = leer()
    familias = registro()
    malos = {e["id"]: errores(e, familias) for e in todos}
    elegidos = [e for e in todos if (not familia or e.get("familia") == familia) and (not estado or e.get("estado") == estado)]
    for fam, nombre in FAMILIAS.items():
        grupo = [e for e in elegidos if e.get("familia") == fam]
        if not grupo:
            continue
        print(f"\n{nombre}")
        for e in grupo:
            sello = "✗ " + "; ".join(malos[e["id"]]) if malos[e["id"]] else e["estado"]
            print(f"  {e['id']:<28} {e.get('fuente', '?'):<28} {sello}")
    usadas = {e.get("fuente") for e in todos} | {(e.get("secundario") or {}).get("fuente") for e in todos}
    sin_usar = [f for f in familias if f not in usadas]
    print(f"\n{len(todos)} letreros · {len(familias)} tipografías" + (f" · sin usar: {', '.join(sin_usar)}" if sin_usar else ""))
    if any(malos.values()):
        salir(f"{sum(1 for m in malos.values() if m)} letreros con errores")
