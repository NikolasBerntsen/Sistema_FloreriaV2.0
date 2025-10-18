"""Lanzador de la experiencia de escritorio basada en Electron/React.

Este módulo reemplaza la interfaz Tkinter original y delega la visualización
al nuevo proyecto web ubicado en ``web_app/``. Puede ejecutarse en modo
*desarrollo* (levantando los procesos de Vite + Electron) o localizar el
paquete generado por ``electron-builder`` para ejecutarlo como una aplicación
convencional en Windows.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import textwrap
import webbrowser
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
WEB_APP_DIR = REPO_ROOT / "web_app"
DIST_DIR = WEB_APP_DIR / "dist"
ELECTRON_DIST_DIR = WEB_APP_DIR / "dist-electron"


class LaunchError(RuntimeError):
    """Error controlado al intentar iniciar la nueva interfaz."""


def _ensure_web_app() -> None:
    if not WEB_APP_DIR.exists():
        raise LaunchError(
            textwrap.dedent(
                """
                No se encontró el directorio `web_app/`. Ejecute el script desde la raíz del
                repositorio y verifique que el nuevo proyecto haya sido inicializado.
                """
            ).strip()
        )


def _ensure_node() -> None:
    if shutil.which("npm") is None:
        raise LaunchError(
            "Se requiere Node.js + npm para ejecutar la nueva interfaz."
            " Instale Node 18+ antes de continuar."
        )


def _run_command(command: list[str], *, cwd: Path) -> subprocess.Popen:
    try:
        return subprocess.Popen(command, cwd=str(cwd))
    except FileNotFoundError as exc:  # pragma: no cover - entorno sin ejecutable
        raise LaunchError(f"No fue posible ejecutar {' '.join(command)}: {exc}") from exc


def _launch_dev() -> int:
    _ensure_node()
    print("Iniciando modo desarrollo (Vite + Electron)...")
    process = _run_command(["npm", "run", "dev"], cwd=WEB_APP_DIR)
    try:
        return process.wait()
    except KeyboardInterrupt:  # pragma: no cover - interacción manual
        process.terminate()
        return 130


def _find_packaged_executable() -> Optional[Path]:
    if not ELECTRON_DIST_DIR.exists():
        return None

    # electron-builder puede generar instaladores (.exe) o carpetas portables
    for candidate in sorted(ELECTRON_DIST_DIR.glob("*.exe")):
        if candidate.is_file():
            return candidate

    for directory in ELECTRON_DIST_DIR.iterdir():
        if directory.is_dir() and "win" in directory.name.lower():
            executables = list(directory.glob("*.exe"))
            if executables:
                return executables[0]
    return None


def _open_executable(path: Path) -> None:
    if sys.platform.startswith("win"):
        os.startfile(str(path))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen([str(path)], cwd=str(path.parent))


def _launch_packaged() -> int:
    packaged = _find_packaged_executable()
    if packaged is not None:
        print(f"Abriendo paquete generado: {packaged}")
        _open_executable(packaged)
        return 0

    if DIST_DIR.exists():
        index = DIST_DIR / "index.html"
        print(
            "No se halló un ejecutable empaquetado."
            " Se abrirá la versión estática en el navegador predeterminado."
        )
        webbrowser.open(index.as_uri())
        return 0

    raise LaunchError(
        textwrap.dedent(
            """
            No se encontró un paquete generado. Ejecute `npm install` y luego
            `npm run build:electron` dentro de `web_app/` para producir el instalador.
            """
        ).strip()
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lanzador del nuevo front-end")
    parser.add_argument(
        "mode",
        choices={"auto", "dev", "packaged"},
        default="auto",
        nargs="?",
        help="Modo de ejecución: 'dev' utiliza npm run dev, 'packaged' busca el .exe generado",
    )
    args = parser.parse_args(argv)

    try:
        _ensure_web_app()
        if args.mode == "dev":
            return _launch_dev()
        if args.mode == "packaged":
            return _launch_packaged()

        # modo auto: si existe un ejecutable usarlo, de lo contrario abrir la versión estática
        executable = _find_packaged_executable()
        if executable:
            print("Se encontró un ejecutable empaquetado. Ejecutándolo...")
            _open_executable(executable)
            return 0
        if DIST_DIR.exists():
            index = DIST_DIR / "index.html"
            print("Iniciando la versión estática desde dist/")
            webbrowser.open(index.as_uri())
            return 0
        print("No hay paquete disponible. Cambiando al modo desarrollo.")
        return _launch_dev()
    except LaunchError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover - entrada CLI
    sys.exit(main())
