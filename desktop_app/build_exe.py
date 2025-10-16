"""Script auxiliar para generar el ejecutable de Florería Carlitos."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).resolve().parent
    main_script = project_root / "main.py"

    if not main_script.exists():
        raise FileNotFoundError(f"No se encontró el archivo principal: {main_script}")

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--name",
        "FloreriaCarlitos",
        str(main_script),
    ]

    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
