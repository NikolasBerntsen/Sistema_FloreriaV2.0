"""Punto de entrada de la aplicación de escritorio Florería Carlitos."""

from __future__ import annotations

import configparser
import logging
import os
from contextlib import closing
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

import mysql.connector
from mysql.connector.connection import MySQLConnection

try:
    import tkinter as tk
    from tkinter import messagebox
except Exception:  # pragma: no cover - Tk puede no estar disponible en entornos headless
    tk = None
    messagebox = None


LOGGER = logging.getLogger(__name__)


class FloreriaApp:
    """Aplicación principal basada en Tkinter."""

    def __init__(self, connection: MySQLConnection, config: Dict[str, Any]) -> None:
        self._connection = connection
        self._config = config
        self._root: Optional[tk.Tk] = None if tk is not None else None

    def run(self) -> None:
        if tk is None:
            raise RuntimeError(
                "Tkinter no está disponible en este entorno. La interfaz gráfica no puede iniciarse."
            )

        self._root = tk.Tk()
        self._root.title("Florería Carlitos")
        self._root.geometry("600x400")

        label = tk.Label(
            self._root,
            text="Bienvenido a Florería Carlitos",
            font=("Helvetica", 16, "bold"),
            pady=20,
        )
        label.pack()

        status = tk.Label(
            self._root,
            text="Conexión a base de datos establecida",
            font=("Helvetica", 10),
        )
        status.pack(side=tk.BOTTOM, pady=10)

        self._root.mainloop()


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
    """Abre una conexión MySQL usando un DSN."""

    params = parse_mysql_dsn(dsn)
    LOGGER.debug("Conectando a MySQL con parámetros: %s", {k: v for k, v in params.items() if k != "password"})
    connection = mysql.connector.connect(**params)
    return connection


def launch_main_window(connection: MySQLConnection, config: Dict[str, Any]) -> None:
    """Inicializa y lanza la ventana principal."""

    app = FloreriaApp(connection=connection, config=config)
    app.run()


def bootstrap() -> None:
    """Carga configuración, abre la conexión a MySQL y lanza la interfaz de usuario."""

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    LOGGER.info("Iniciando aplicación de escritorio Florería Carlitos")
    config_path = os.getenv("FLORERIA_CONFIG_PATH")
    config = load_local_config(config_path)

    dsn = os.getenv("FLORERIA_DB_DSN")

    try:
        with closing(open_db_connection(dsn)) as connection:
            launch_main_window(connection, config)
    except Exception as exc:  # pragma: no cover - Gestión de errores de arranque
        LOGGER.exception("Error al inicializar la aplicación: %s", exc)
        if messagebox is not None:
            messagebox.showerror("Florería Carlitos", f"Ocurrió un error al iniciar la aplicación:\n{exc}")
        raise


if __name__ == "__main__":
    bootstrap()
