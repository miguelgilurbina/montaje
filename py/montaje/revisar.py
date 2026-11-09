"""Medir un render en vez de mirarlo: lo que una hoja de contacto no muestra.

Una hoja saca un cuadro por segundo; entre dos cuadros caben un negro, un clip
congelado, una cámara lenta que repite cuadros o tres fogonazos seguidos. Esto lee
el render entero (chico y en gris) y cuenta:

- **negro**: segundos con el cuadro casi apagado, y el tramo más largo;
- **congelado**: el tramo más largo en que la imagen no cambia (una foto que
  despierta es eso a propósito; un clip trabado, no);
- **repetidos**: qué parte de los cuadros es igual al anterior (una cámara lenta
  sin interpolar repite uno de cada tantos);
- **cortes**: cambios bruscos por minuto;
- **destellos**: el máximo de fogonazos en un segundo. Un destello es una ida y
  vuelta de la luz del cuadro (sube y baja, o baja y sube) de más del 10 % del
  rango, sea de un cuadro al siguiente o en rampa. Más de tres por segundo es el
  límite que las pautas de accesibilidad (WCAG 2.3.1) ponen por la epilepsia
  fotosensible: eso no se publica. Es una aproximación prudente: mide la luz media
  del cuadro entero, no el área ni el rojo saturado que la pauta también mira;
- **sonido**: sonoridad integrada (LUFS) y pico real (dBTP).

    python montaje.py revisar <p> <archivo.mp4>

`ejercicio` lo corre sobre cada versión. No juzga si algo se ve bien: avisa lo que
conviene mirar. El oído y el ojo siguen siendo de Miguel.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import numpy as np

from .rutas import Proyecto, salir

ANCHO = 160
#: Bajo esta luz media (0..255) el cuadro cuenta como negro.
NEGRO = 8.0
#: Bajo esta diferencia media con el cuadro anterior (0..255), es el mismo cuadro.
QUIETO = 0.12
#: Un cambio de la luz media de más del 10 % del rango es medio destello; ida y vuelta, uno entero.
SALTO = 25.5


def _tramo_mas_largo(marca: np.ndarray) -> tuple[int, int]:
    """El tramo más largo de `True` seguidos: (largo, dónde empieza)."""
    mejor, donde, largo = 0, 0, 0
    for i, v in enumerate(marca):
        largo = largo + 1 if v else 0
        if largo > mejor:
            mejor, donde = largo, i - largo + 1
    return mejor, donde


def vaivenes(luz: np.ndarray) -> list[tuple[int, int]]:
    """Los cambios grandes de la luz: (cuadro en que termina, +1 si subió o -1 si bajó).

    Sigue la luz de extremo a extremo (un zigzag): un cambio cuenta cuando, desde el último
    extremo, la luz se fue `SALTO` o más para el otro lado, sin importar en cuántos cuadros.
    Así un fogonazo en rampa cuenta igual que uno de un cuadro, y dos cambios seguidos son
    siempre de sentido contrario.
    """
    if len(luz) < 2:
        return []
    cambios: list[tuple[int, int]] = []
    base = float(luz[0])         # el último extremo confirmado
    punta, donde, rumbo = base, 0, 0  # el extremo que se está formando y hacia dónde va
    for i in range(1, len(luz)):
        v = float(luz[i])
        if rumbo == 0:
            if abs(v - base) >= SALTO:
                rumbo, punta, donde = (1 if v > base else -1), v, i
        elif (v - punta) * rumbo > 0:
            punta, donde = v, i  # sigue en el mismo sentido: la punta se corre
        elif (punta - v) * rumbo >= SALTO:
            cambios.append((donde, rumbo))  # se dio vuelta: el extremo queda confirmado
            base, rumbo, punta, donde = punta, -rumbo, v, i
    if rumbo:
        cambios.append((donde, rumbo))
    return cambios


def destellos_por_segundo(luz: np.ndarray, fps: float) -> int:
    """El máximo de destellos (idas y vueltas de la luz) en un segundo cualquiera."""
    cuando = [i for i, _ in vaivenes(luz)]
    ventana = max(1, int(round(fps)))
    return max((sum(1 for c in cuando if t <= c < t + ventana) // 2 for t in cuando), default=0)


def medir_cuadros(luz: np.ndarray, dif: np.ndarray, fps: float) -> dict:
    """Las cuentas, a partir de la luz media de cada cuadro y su diferencia con el anterior.

    `dif[i]` compara el cuadro `i + 1` con el `i` (tiene un elemento menos que `luz`).
    """
    n = len(luz)
    negro = luz < NEGRO
    largo_negro, ini_negro = _tramo_mas_largo(negro)
    quieto = dif < QUIETO
    # Lo negro no cuenta como congelado: ahí no hay imagen que se trabe.
    largo_quieto, ini_quieto = _tramo_mas_largo(quieto & ~negro[1:])
    cortes = int(np.sum(dif > 28))
    por_segundo = destellos_por_segundo(luz, fps)
    return {
        "segundos": round(n / fps, 2),
        "negro_s": round(float(negro.sum()) / fps, 2),
        "negro_mas_largo_s": round(largo_negro / fps, 2),
        "negro_en_s": round(ini_negro / fps, 2),
        "congelado_s": round(largo_quieto / fps, 2),
        "congelado_en_s": round((ini_quieto + 1) / fps, 2),
        "repetidos": round(float(np.mean(quieto & ~negro[1:])) if n > 1 else 0.0, 3),
        "cortes_por_min": round(cortes / max(1e-9, n / fps) * 60, 1),
        "destellos_max_por_s": int(por_segundo),
    }


def avisos(m: dict) -> list[str]:
    """Lo que conviene mirar. Vacío no quiere decir que esté bien: quiere decir que esto no encontró nada."""
    a = []
    if m["destellos_max_por_s"] > 3:
        a.append(f"{m['destellos_max_por_s']} destellos en un segundo: pasa el límite de accesibilidad (3); no se publica así")
    borde = m["negro_en_s"] < 0.5 or m["negro_en_s"] + m["negro_mas_largo_s"] > m["segundos"] - 0.5
    if m["negro_mas_largo_s"] > 1.0 and not borde:
        a.append(f"{m['negro_mas_largo_s']:g} s de negro en el medio (desde {m['negro_en_s']:g} s)")
    if m["congelado_s"] > 1.5:
        a.append(f"imagen quieta {m['congelado_s']:g} s (desde {m['congelado_en_s']:g} s): ¿una foto a propósito o un clip trabado?")
    if m["repetidos"] > 0.08 and m["congelado_s"] <= 1.5:
        a.append(f"{m['repetidos'] * 100:.0f} % de cuadros repetidos: la cámara lenta tironea (¿`clips_interpolar`?)")
    # El pico de trabajo es el de la canción tal como vino; `paquete` lo deja en −1 dBTP al entregar.
    # Aquí sólo se avisa si ya satura.
    if m.get("pico_dbtp") is not None and m["pico_dbtp"] > -0.1:
        a.append(f"pico real {m['pico_dbtp']:+.1f} dBTP: el audio satura")
    return a


def _sonido(ruta: Path) -> tuple[float | None, float | None]:
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(ruta), "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    resumen = r.stderr[r.stderr.rfind("Summary:"):] if "Summary:" in r.stderr else ""
    i = re.search(r"I:\s+(-?[\d.]+) LUFS", resumen)
    pico = re.search(r"Peak:\s+(-?[\d.]+) dBFS", resumen)
    return (float(i.group(1)) if i else None), (float(pico.group(1)) if pico else None)


def medir(ruta: Path) -> dict:
    """Lee el render entero, chico y en gris, y lo mide."""
    sondeo = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate",
                             "-of", "csv=p=0", str(ruta)], capture_output=True, text=True, check=True).stdout.strip().split(",")
    w, h = int(sondeo[0]), int(sondeo[1])
    num, den = sondeo[2].split("/")
    fps = float(num) / float(den)
    alto = max(2, round(ANCHO * h / w / 2) * 2)
    crudo = subprocess.run(["ffmpeg", "-v", "error", "-i", str(ruta), "-an", "-vf", f"scale={ANCHO}:{alto},format=gray", "-f", "rawvideo", "-"],
                           capture_output=True, check=True).stdout
    # En bytes, como vienen, y las diferencias de a tandas: en coma flotante un vertical de tres minutos pedía gigas.
    cuadros = np.frombuffer(crudo, dtype=np.uint8).reshape(-1, alto, ANCHO)
    if len(cuadros) < 2:
        salir(f"{ruta.name}: no tiene cuadros que medir")
    luz = cuadros.reshape(len(cuadros), -1).mean(axis=1)
    dif = np.concatenate([
        np.abs(cuadros[a + 1 : b + 1].astype(np.int16) - cuadros[a:b].astype(np.int16)).reshape(b - a, -1).mean(axis=1)
        for a in range(0, len(cuadros) - 1, 256) for b in [min(a + 256, len(cuadros) - 1)]
    ])
    m = medir_cuadros(luz, dif, fps)
    m["lufs"], m["pico_dbtp"] = _sonido(ruta)
    return m


def linea(m: dict) -> str:
    """Las cuentas en un renglón."""
    sonido = f"{m['lufs']:.1f} LUFS, pico {m['pico_dbtp']:+.1f} dBTP" if m.get("lufs") is not None and m.get("pico_dbtp") is not None else "sin audio"
    return (f"negro {m['negro_s']:g} s · quieta a lo sumo {m['congelado_s']:g} s · repetidos {m['repetidos'] * 100:.0f} % · "
            f"{m['cortes_por_min']:g} cortes/min · destellos máx {m['destellos_max_por_s']}/s · {sonido}")


def revisar(p: Proyecto, video: str) -> dict:
    ruta = p.salidas / "render" / video
    if not ruta.exists():
        salir(f"no existe {ruta}")
    m = medir(ruta)
    print(f"{ruta.name} ({m['segundos']:g} s)\n  {linea(m)}")
    for a in avisos(m):
        print(f"  ⚠ {a}")
    if not avisos(m):
        print("  sin avisos (igual hay que mirar la hoja)")
    return m
