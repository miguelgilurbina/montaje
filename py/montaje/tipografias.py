"""Tipografías propias, hechas desde las libres del repo (fuentes/).

La primera, pedida por Miguel el 2026-11-18: **Curiana Cartel**, Archivo Black apretada a lo ancho al
0,82 (el «type 3c» del manual de marca: «la compresión es la identidad»). Hasta ahora la compresión era
un truco del motor (`compresion` en un letrero, un scaleX): hecha archivo, la letra apretada sirve en
cualquier lado (Canva, Figma, el sitio, un documento) y el motor mide sus anchos de verdad.

Una derivada de una tipografía OFL sigue siendo OFL: lleva la licencia y el aviso de la original, y no
puede usar su «Reserved Font Name» (Archivo Black no tiene; Lora y Plex sí). El dibujo se aprieta sin
hinting (las instrucciones de la original apuntan a puntos que ya no están donde estaban).

    python montaje.py tipografia apretar archivo-black/ArchivoBlack-Regular.ttf 0.82 "Curiana Cartel"
"""

from __future__ import annotations

from pathlib import Path

from .rutas import RAIZ, salir

FUENTES = RAIZ / "fuentes"
#: Los atributos de GPOS que son distancias horizontales (kerning, acentos sobre su letra, enlaces).
_HORIZONTALES = {"XAdvance", "XPlacement", "XCoordinate"}


def _carpeta(familia: str) -> str:
    return familia.lower().replace(" ", "-")


def _postscript(familia: str) -> str:
    return familia.replace(" ", "")


def _escalar_gpos(objeto, factor: float, vistos: set[int]) -> None:
    """Recorre GPOS entero y aprieta toda distancia horizontal (pares de kerning, anclas de los acentos)."""
    if id(objeto) in vistos:
        return
    vistos.add(id(objeto))
    if isinstance(objeto, list):
        for x in objeto:
            _escalar_gpos(x, factor, vistos)
        return
    atributos = getattr(objeto, "__dict__", None)
    if atributos is None:
        return
    for clave, valor in list(atributos.items()):
        if clave in _HORIZONTALES and isinstance(valor, (int, float)):
            setattr(objeto, clave, round(valor * factor))
        elif not isinstance(valor, (int, float, str, bytes)) and valor is not None:
            _escalar_gpos(valor, factor, vistos)


def apretar(origen: Path, destino: Path, factor: float, familia: str, nota: str) -> dict:
    """Una tipografía nueva: la de `origen` con todo lo horizontal multiplicado por `factor`, llamada `familia`."""
    from fontTools.pens.recordingPen import DecomposingRecordingPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.ttLib import TTFont

    if not 0.3 <= factor <= 1.5:
        salir(f"apretar a {factor}: el factor va de 0,3 a 1,5")
    f = TTFont(origen)
    if "glyf" not in f:
        salir(f"{origen.name}: sólo tipografías TrueType (glyf)")
    glifos = f.getGlyphSet()
    glyf, hmtx = f["glyf"], f["hmtx"]
    nuevos = {}
    for nombre in f.getGlyphOrder():
        # Descompuesto: un acento compuesto no se aprieta dos veces (la base y la copia).
        grabado = DecomposingRecordingPen(glifos)
        glifos[nombre].draw(grabado)
        pluma = TTGlyphPen(None)
        grabado.replay(TransformPen(pluma, (factor, 0, 0, 1, 0, 0)))
        nuevos[nombre] = pluma.glyph()
    for nombre, g in nuevos.items():
        glyf[nombre] = g
    for nombre in f.getGlyphOrder():
        avance, _ = hmtx[nombre]
        g = glyf[nombre]
        g.recalcBounds(glyf)
        hmtx[nombre] = (round(avance * factor), getattr(g, "xMin", 0) if g.numberOfContours else 0)
    if "GPOS" in f:
        _escalar_gpos(f["GPOS"].table, factor, set())
    if "kern" in f:
        for t in f["kern"].kernTables:
            t.kernTable = {par: round(v * factor) for par, v in t.kernTable.items()}
    # Sin hinting: sus instrucciones eran para el dibujo de antes.
    for tabla in ("fpgm", "prep", "cvt ", "hdmx", "LTSH", "VDMX", "DSIG"):
        if tabla in f:
            del f[tabla]
    os2 = f["OS/2"]
    os2.recalcAvgCharWidth(f)
    # 1 = ultra condensada … 5 = normal (87,5 % = 4; 75 % = 3).
    os2.usWidthClass = 5 if factor >= 0.94 else 4 if factor >= 0.81 else 3 if factor >= 0.69 else 2
    nombres = f["name"]
    original = nombres.getDebugName(1)
    copyright = (nombres.getDebugName(0) or "").strip()
    ps = _postscript(familia)
    for registro in list(nombres.names):
        if registro.nameID in (1, 2, 3, 4, 6, 16, 17, 21, 22, 25):
            nombres.removeNames(nameID=registro.nameID)
    for nid, texto in {
        0: f"{copyright}. {familia}: {nota}",
        1: familia,
        2: "Regular",
        3: f"{familia} · derivada de {original}",
        4: familia,
        6: f"{ps}-Regular",
    }.items():
        nombres.setName(texto, nid, 3, 1, 0x409)
        nombres.setName(texto, nid, 1, 0, 0)
    destino.parent.mkdir(parents=True, exist_ok=True)
    f.save(destino)
    return {"familia": familia, "archivo": destino, "glifos": len(nuevos), "original": original}


def licencia_derivada(origen_ofl: Path, destino: Path, familia: str, nota: str) -> None:
    """La licencia de la derivada: los avisos de la original, el de la derivada y el texto de la OFL sin tocar."""
    texto = origen_ofl.read_text(encoding="utf-8")
    destino.write_text(f"Copyright 2026 Curiana Radio ({familia}: {nota})\n{texto}", encoding="utf-8")


def cmd_apretar(origen: str, factor: float, familia: str) -> None:
    ruta = FUENTES / origen
    if not ruta.is_file():
        salir(f"no existe fuentes/{origen}")
    nota = f"derivada de {ruta.stem} apretada a lo ancho al {factor:g}, sin hinting (2026)"
    destino = FUENTES / _carpeta(familia) / f"{_postscript(familia)}-Regular.ttf"
    hecho = apretar(ruta, destino, factor, familia, nota)
    ofl = ruta.parent / "OFL.txt"
    if ofl.exists():
        licencia_derivada(ofl, destino.parent / "OFL.txt", familia, nota)
    print(f"{hecho['familia']} ← {hecho['original']} ×{factor:g}: {hecho['glifos']} glifos → fuentes/{destino.relative_to(FUENTES).as_posix()}")
    print("Falta registrarla en fuentes/fuentes.json (voz, licencia, archivo y peso).")
