"""El borrador del teaser de la alfa, con montaje mismo y con el material de prueba (`python montaje.py demo`).

    python proyectos/37-el-teaser-de-la-alfa/armar.py            # → <medios>/37-el-teaser-de-la-alfa/borrador.mp4

Cuatro partes, cada una hecha por el motor (`analogo`), y ffmpeg las junta:

1. **Sintonía** (3,5 s): el dial se mueve hasta 88.8 y la imagen sale de la nieve. Es una interpretación grabada como
   la grabaría la consola (`sintonia.json`: la nieve, el rodar y el desenganche bajan a mano).
2. **Los aparatos** (`--recorrido`): el mismo plano por varias cadenas de la galería, dos segundos cada una, con su
   nombre.
3. **La marca** (5 s): el haz del osciloscopio dibuja MONTAJE con las letras de la marca; el sonido es el dibujo.
4. **El cartón** (3,5 s): el nombre, qué es y dónde está, por el tubo.

Es un borrador para mirar y decidir (direccion/TEASER.md): el material, el orden y la música los decide Miguel.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
MEDIOS = Path(os.environ.get("MONTAJE_MEDIOS", Path.home() / "Videos" / "montaje"))
SALIDA = MEDIOS / AQUI.name
CLIPS = MEDIOS / "demo" / "clips"
PYTHON = sys.executable
ANCHO, ALTO, FPS = 1280, 720, 30
CADENAS = ["cinta-gastada", "super-8-de-la-familia", "pelicula-tintada", "risografia", "moire", "destello-de-sol",
           "iman-en-el-televisor"]
# Las letras: la de la marca para el nombre (está en el repo) y una de máquina para lo demás.
LETRA = RAIZ / "fuentes" / "curiana-cartel" / "CurianaCartel-Regular.ttf"
MONO = Path("C:/Windows/Fonts/consola.ttf") if os.name == "nt" else Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")


def correr(*args: str) -> None:
    print("·", " ".join(str(a) for a in args[:6]), "…" if len(args) > 6 else "")
    subprocess.run([*args], check=True, cwd=RAIZ, env={**os.environ, "PYTHONIOENCODING": "utf-8"})


def analogo(entrada: Path, cadena, salida: Path, *extra: str) -> Path:
    texto = cadena if isinstance(cadena, str) else json.dumps(cadena)
    correr(PYTHON, "montaje.py", "analogo", str(entrada), "--cadena", texto, "--salida", str(salida), "--alto", str(ALTO), *extra)
    return salida


def ruta_ff(p: Path) -> str:
    """Una ruta dentro de un filtro de ffmpeg (los dos puntos de Windows van escapados)."""
    return str(p).replace("\\", "/").replace(":", "\\:")


def negro_con_pulso(segundos: float, destino: Path) -> Path:
    from montaje.demo import PULSO   # el mismo pulso del material de prueba

    correr("ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=black:s={ANCHO}x{ALTO}:r={FPS}:d={segundos}",
           "-f", "lavfi", "-i", f"aevalsrc='{PULSO}':s=48000:d={segundos}", "-shortest",
           "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-c:a", "aac", str(destino))
    return destino


def carton(segundos: float, destino: Path) -> Path:
    lineas = [
        (LETRA, 120, "montaje", "(h/2)-150", "0xe6b43c"),
        (MONO, 34, "editar video con un agente, en español", "(h/2)+10", "0xeee6d4"),
        (MONO, 34, "una mesa de aparatos analógicos · alfa · MIT", "(h/2)+60", "0xeee6d4"),
        (MONO, 30, "github.com/miguelgilurbina/montaje", "(h/2)+140", "0x7e93aa"),
    ]
    filtros = ",".join(
        f"drawtext=fontfile='{ruta_ff(letra)}':text='{texto}':fontsize={tam}:fontcolor={col}:x=(w-text_w)/2:y={y}"
        for letra, tam, texto, y, col in lineas)
    fondo = negro_con_pulso(segundos, SALIDA / "partes" / "carton-fondo.mp4")
    correr("ffmpeg", "-v", "error", "-y", "-i", str(fondo), "-vf", f"format=yuv420p,{filtros}", "-c:v", "libx264", "-crf", "16",
           "-c:a", "copy", str(destino))
    return destino


def main() -> None:
    if not (CLIPS / "cielo-con-sol.mp4").exists():
        correr(PYTHON, "montaje.py", "demo")
    partes = SALIDA / "partes"
    partes.mkdir(parents=True, exist_ok=True)
    cielo = CLIPS / "cielo-con-sol.mp4"

    # 1. Sintonía: el dial y la imagen que sale de la nieve, tocada a mano (lo grabado, en sintonia.json).
    # El dial va entre la antena y el tubo: antes de la antena, la nieve lo tapaba; el tubo va siempre al final.
    sintonia = analogo(cielo, [{"aparato": "antena", "nieve": 1.0, "sonido": "aire"},
                               {"aparato": "dial", "inicio": True, "frecuencia": 88.8, "dura": 2.2, "sonido": "sintonia"},
                               {"aparato": "pantalla", "sonido": "parlante"}],
                       partes / "1-sintonia.mp4", "--hasta", "3.5", "--automatizacion", str(AQUI / "sintonia.json"))

    # 2. Los aparatos, uno tras otro sobre el mismo plano.
    aparatos = partes / "2-aparatos.mp4"
    correr(PYTHON, "montaje.py", "analogo", str(cielo), "--recorrido", ",".join(CADENAS), "--desde", "3.5", "--segundos", "2",
           "--alto", str(ALTO), "--salida", str(aparatos))

    # 3. La marca: el haz dibuja el nombre; el audio es el dibujo.
    marca = analogo(negro_con_pulso(5.0, partes / "negro.mp4"),
                    [{"aparato": "osciloscopio", "mezcla": 0.0, "dibujo": "nombre", "texto": "MONTAJE", "cada": 0.0,
                      "tinta": "oro", "sonido": "marca"}],
                    partes / "3-marca.mp4")

    # 4. El cartón, por el tubo.
    final = analogo(carton(3.5, partes / "carton.mp4"), [{"aparato": "pantalla", "curva": 0.06, "persistencia": 0.3}],
                    partes / "4-carton.mp4")

    # Juntar: las cuatro partes ya salen a 1280×720, 30 cuadros y estéreo a 48 kHz. Con el filtro `concat`, el
    # recorrido (cosido de pedazos, con cuadros B) perdía cuadros al juntarse, aun renumerándolos (480 → 423); el
    # «demuxer» de concat corre cada archivo por su duración y no pierde ninguno.
    lista = [sintonia, aparatos, marca, final]
    indice = partes / "lista.txt"
    indice.write_text("".join(f"file '{p.as_posix()}'\n" for p in lista), encoding="utf-8")
    destino = SALIDA / "borrador.mp4"
    correr("ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(indice),
           "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
           "-movflags", "+faststart", str(destino))
    print(f"→ {destino}")


if __name__ == "__main__":
    sys.path.insert(0, str(RAIZ / "py"))
    main()
