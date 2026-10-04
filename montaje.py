#!/usr/bin/env python
"""Punto de entrada único: `python montaje.py <comando> <proyecto> [opciones]`.

Corre `python montaje.py --help` para ver los comandos. El código vive en py/montaje/.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "py"))

from montaje.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
