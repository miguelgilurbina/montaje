#!/usr/bin/env python
"""Punto de entrada único: `python montaje.py <comando> <proyecto> [opciones]`.

Corre `python montaje.py --help` para ver los comandos. El código vive en py/montaje/.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "py"))

# En Windows, con la salida redirigida, Python escribe en cp1252 y se cae con «→».
for flujo in (sys.stdout, sys.stderr):
    if hasattr(flujo, "reconfigure"):
        flujo.reconfigure(encoding="utf-8")

from montaje.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
