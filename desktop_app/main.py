"""Punto de entrada de la aplicación de escritorio basada en Electron."""

from __future__ import annotations

import configparser
import logging
import os
import shlex
import shutil
import signal
import subprocess
import sys
from contextlib import closing
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

import mysql.connector
from mysql.connector.connection import MySQLConnection

try:  # pragma: no cover - Dependencia opcional en tiempo de ejecución
    from dotenv import find_dotenv, load_dotenv
except ImportError:  # pragma: no cover - Dependencia opcional en tiempo de ejecución
    find_dotenv = None  # type: ignore[assignment]
    load_dotenv = None  # type: ignore[assignment]

from app.db.bootstrap import initialize_database


LOGGER = logging.getLogger(__name__)

DEFAULT_DESKTOP_MODE = "development"
BACKEND_SCRIPT_NAME = "dev_backend.py"


def load_local_config(path: Optional[str]) -> Dict[str, Any]:
    """Carga el archivo de configuración local si está disponible."""

    if not path:
        LOGGER.info("No se proporcionó ruta de configuración. Se usará una configuración vacía.")
        return {}

    config_path = Path(path).expanduser()
    if not config_path.exists():
        LOGGER.warning("El archivo de configuración %s no existe", config_path)
        return {}

    parser = configparser.ConfigParser()
    parser.read(config_path)

    config: Dict[str, Any] = {section: dict(parser[section]) for section in parser.sections()}
    LOGGER.info("Configuración local cargada desde %s", config_path)
    return config


def parse_mysql_dsn(dsn: str) -> Dict[str, Any]:
    """Convierte una cadena DSN en parámetros para mysql.connector."""

    if not dsn:
        raise ValueError("La variable de entorno FLORERIA_DB_DSN es obligatoria")

    parsed = urlparse(dsn)
    if parsed.scheme not in {"mysql", "mysql+mysqlconnector"}:
        raise ValueError("El DSN debe utilizar el esquema mysql")

    params: Dict[str, Any] = {
        "user": parsed.username,
        "password": parsed.password,
        "host": parsed.hostname,
        "port": parsed.port or 3306,
    }

    if parsed.path:
        params["database"] = parsed.path.lstrip("/")

    query = parse_qs(parsed.query)
    for key, value in query.items():
        if value:
            params[key] = value[-1]

    return params


def open_db_connection(dsn: str) -> MySQLConnection:
    """Abre una conexión MySQL usando un DSN, asegurando el esquema requerido."""

    params = parse_mysql_dsn(dsn)
    LOGGER.debug(
        "Conectando a MySQL con parámetros: %s",
        {k: v for k, v in params.items() if k != "password"},
    )

    schema = params.get("database") or "floreriadb"
    server_params = {k: v for k, v in params.items() if k != "database"}

    with closing(mysql.connector.connect(**server_params)) as server_connection:
        initialize_database(server_connection, schema, logger=LOGGER)

    params["database"] = schema
    connection = mysql.connector.connect(**params)
    return connection


def launch_backend_process(config: Dict[str, Any]) -> subprocess.Popen[bytes]:
    """Lanza el backend HTTP requerido para la aplicación."""

    custom_command = os.getenv("FLORERIA_BACKEND_CMD")
    backend_dir = Path(__file__).resolve().parent
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")

    if custom_command:
        command = shlex.split(custom_command)
        cwd = None
    else:
        script_path = backend_dir / BACKEND_SCRIPT_NAME
        if not script_path.exists():
            raise FileNotFoundError(
                f"No se encontró el backend de desarrollo en {script_path}. Configure FLORERIA_BACKEND_CMD."
            )
        command = [sys.executable, str(script_path)]
        cwd = backend_dir

    LOGGER.info("Iniciando backend HTTP con comando: %s", command)
    process = subprocess.Popen(command, cwd=cwd, env=env)
    return process


def _resolve_command(binary: str) -> str:
    """Resuelve la ruta absoluta de un ejecutable disponible en PATH."""

    resolved = shutil.which(binary)
    if resolved is None:
        raise FileNotFoundError(
            f"No se encontró el ejecutable '{binary}'. Añádelo al PATH o especifica "
            "FLORERIA_ELECTRON_BINARY."
        )

    return resolved


def launch_electron_frontend(config: Dict[str, Any]) -> int:
    """Ejecuta el proceso principal de Electron y espera a que finalice."""

    frontend_dir = Path(__file__).resolve().parent / "frontend_electron"
    if not frontend_dir.exists():
        raise FileNotFoundError(f"No se encontró el frontend de Electron en {frontend_dir}")

    mode = os.getenv("FLORERIA_DESKTOP_MODE", DEFAULT_DESKTOP_MODE).lower()
    binary_override = os.getenv("FLORERIA_ELECTRON_BINARY")

    if mode == "development":
        npm_binary = _resolve_command("npm")
        command = [npm_binary, "run", "dev:electron"]
        node_env = "development"
    elif mode in {"production", "npx", "packaged"}:
        node_env = "production"
        if binary_override:
            command = [binary_override]
        else:
            npx_binary = _resolve_command("npx")
            command = [npx_binary, "electron", "."]
    else:
        raise ValueError(
            "FLORERIA_DESKTOP_MODE debe ser 'development', 'production' o 'packaged'."
        )

    env = os.environ.copy()
    env.setdefault("NODE_ENV", node_env)

    backend_section = config.get("backend") if isinstance(config.get("backend"), dict) else {}
    backend_url = backend_section.get("url") if isinstance(backend_section, dict) else None
    if backend_url:
        env.setdefault("FLORERIA_BACKEND_URL", backend_url)

    LOGGER.info("Lanzando frontend Electron con comando: %s", command)
    process = subprocess.Popen(command, cwd=frontend_dir, env=env)

    try:
        return process.wait()
    except KeyboardInterrupt:
        LOGGER.info("Interrupción recibida. Solicitando cierre de Electron…")
        if process.poll() is None:
            process.send_signal(signal.SIGINT)
        raise
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                LOGGER.warning("Electron no respondió al cierre. Forzando terminación…")
                process.kill()


def bootstrap() -> None:
    """Carga configuración, gestiona la conexión a MySQL y lanza los procesos necesarios."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if load_dotenv is not None and find_dotenv is not None:
        dotenv_path = find_dotenv()
        if dotenv_path:
            load_dotenv(dotenv_path=dotenv_path, override=False)
            LOGGER.info("Variables de entorno cargadas desde %s", dotenv_path)
    elif Path(".env").exists():  # pragma: no cover - Ruta de respaldo sin python-dotenv
        LOGGER.warning(
            "El archivo .env está presente pero python-dotenv no está instalado. "
            "Instálalo para cargar variables automáticamente."
        )

    config_path = os.getenv("FLORERIA_CONFIG_PATH")
    config = load_local_config(config_path)

    dsn = os.getenv("FLORERIA_DB_DSN")
    connection: Optional[MySQLConnection] = None
    backend_process: Optional[subprocess.Popen[bytes]] = None

    try:
        if dsn:
            connection = open_db_connection(dsn)
            LOGGER.info("Conexión MySQL inicializada correctamente.")
        else:
            LOGGER.info("No se definió FLORERIA_DB_DSN. Se omite la conexión a MySQL.")

        backend_process = launch_backend_process(config)
        LOGGER.info("Backend HTTP iniciado con PID %s", backend_process.pid)

        exit_code = launch_electron_frontend(config)
        if exit_code != 0:
            raise SystemExit(exit_code)
    except KeyboardInterrupt:
        LOGGER.info("Ejecución interrumpida por el usuario.")
    except FileNotFoundError as exc:
        LOGGER.error("No se pudo iniciar uno de los procesos requeridos: %s", exc)
        raise SystemExit(1) from exc
    finally:
        if backend_process is not None and backend_process.poll() is None:
            LOGGER.info("Deteniendo backend HTTP…")
            backend_process.terminate()
            try:
                backend_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                LOGGER.warning("Forzando detención del backend HTTP…")
                backend_process.kill()

        if connection is not None:
            connection.close()
            LOGGER.info("Conexión MySQL cerrada.")


if __name__ == "__main__":
    bootstrap()

