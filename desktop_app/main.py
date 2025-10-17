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

from app.services.auth_service import (
    AuthenticationError,
    authenticate,
    get_current_session,
    logout as logout_user,
)
from app.services.audit_service import log_audit
from app.utils.security import AuthorizationError, requires_role


LOGGER = logging.getLogger(__name__)


class FloreriaApp:
    """Aplicación principal basada en Tkinter con autenticación y control de roles."""

    def __init__(self, connection: MySQLConnection, config: Dict[str, Any]) -> None:
        self._connection = connection
        self._config = config
        self._root: Optional[tk.Tk] = None if tk is not None else None
        self._login_frame: Optional[tk.Frame] = None
        self._dashboard_frame: Optional[tk.Frame] = None
        self._email_var = tk.StringVar(value="") if tk is not None else None
        self._password_var = tk.StringVar(value="") if tk is not None else None
        self._status_var = tk.StringVar(value="") if tk is not None else None
        self._user_info_var = tk.StringVar(value="") if tk is not None else None
        self._admin_button: Optional[tk.Button] = None

    def run(self) -> None:
        if tk is None:
            raise RuntimeError(
                "Tkinter no está disponible en este entorno. La interfaz gráfica no puede iniciarse."
            )

        self._root = tk.Tk()
        self._root.title("Florería Carlitos")
        self._root.geometry("640x420")
        self._root.minsize(520, 360)
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_login_view()
        self._build_status_bar()
        self._show_login_view()

        self._root.mainloop()

    # ------------------------------------------------------------------
    # Construcción de vistas
    # ------------------------------------------------------------------
    def _build_login_view(self) -> None:
        assert tk is not None and self._root is not None

        self._login_frame = tk.Frame(self._root, padx=40, pady=40)

        title = tk.Label(
            self._login_frame,
            text="Iniciar sesión",
            font=("Helvetica", 18, "bold"),
        )
        title.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        email_label = tk.Label(self._login_frame, text="Correo electrónico")
        email_entry = tk.Entry(self._login_frame, textvariable=self._email_var, width=35)
        email_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        email_entry.grid(row=1, column=1, pady=5)

        password_label = tk.Label(self._login_frame, text="Contraseña")
        password_entry = tk.Entry(
            self._login_frame, textvariable=self._password_var, width=35, show="*"
        )
        password_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        password_entry.grid(row=2, column=1, pady=5)

        login_button = tk.Button(
            self._login_frame,
            text="Ingresar",
            width=20,
            command=self._handle_login,
        )
        login_button.grid(row=3, column=0, columnspan=2, pady=(15, 10))

        status_message = tk.Label(
            self._login_frame,
            textvariable=self._status_var,
            fg="red",
        )
        status_message.grid(row=4, column=0, columnspan=2)

        password_entry.bind("<Return>", lambda event: self._handle_login())

    def _build_status_bar(self) -> None:
        assert tk is not None and self._root is not None

        status_text = "Conexión a base de datos establecida"
        if self._config:
            status_text += " • Configuración local cargada"

        status_bar = tk.Label(
            self._root,
            text=status_text,
            font=("Helvetica", 9),
            anchor=tk.W,
            bd=1,
            relief=tk.SUNKEN,
            padx=10,
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _ensure_dashboard(self) -> None:
        assert tk is not None and self._root is not None

        if self._dashboard_frame is not None:
            return

        self._dashboard_frame = tk.Frame(self._root, padx=30, pady=30)

        welcome = tk.Label(
            self._dashboard_frame,
            text="Bienvenido a Florería Carlitos",
            font=("Helvetica", 16, "bold"),
            pady=10,
        )
        welcome.pack()

        user_info = tk.Label(
            self._dashboard_frame,
            textvariable=self._user_info_var,
            font=("Helvetica", 11),
            pady=5,
        )
        user_info.pack()

        button_bar = tk.Frame(self._dashboard_frame, pady=20)
        button_bar.pack()

        admin_button = tk.Button(
            button_bar,
            text="Panel administrativo",
            width=22,
            command=self._handle_admin_panel,
        )
        admin_button.grid(row=0, column=0, padx=10)
        self._admin_button = admin_button

        logout_button = tk.Button(
            button_bar,
            text="Cerrar sesión",
            width=18,
            command=self._handle_logout,
        )
        logout_button.grid(row=0, column=1, padx=10)

    # ------------------------------------------------------------------
    # Gestión de eventos
    # ------------------------------------------------------------------
    def _show_login_view(self) -> None:
        assert tk is not None
        if self._dashboard_frame is not None:
            self._dashboard_frame.pack_forget()

        if self._login_frame is not None:
            self._status_var.set("")
            self._password_var.set("")
            self._login_frame.pack(expand=True)
            self._login_frame.focus_set()

    def _show_dashboard(self) -> None:
        assert tk is not None

        if self._login_frame is not None:
            self._login_frame.pack_forget()

        self._ensure_dashboard()

        session = get_current_session()
        if session is not None:
            display_name = session.full_name or session.email
            self._user_info_var.set(f"Usuario: {display_name} • Rol: {session.role}")
            if self._admin_button is not None:
                state = tk.NORMAL if session.role.upper() == "ADMIN" else tk.DISABLED
                self._admin_button.config(state=state)

        if self._dashboard_frame is not None:
            self._dashboard_frame.pack(expand=True, fill=tk.BOTH)

    def _handle_login(self) -> None:
        assert tk is not None
        email = self._email_var.get().strip() if self._email_var is not None else ""
        password = self._password_var.get() if self._password_var is not None else ""

        try:
            authenticate(email, password, connection=self._connection)
        except AuthenticationError as exc:
            LOGGER.warning("Intento de autenticación fallido para %s", email)
            self._status_var.set(str(exc))
            if messagebox is not None:
                messagebox.showerror("Acceso denegado", str(exc))
            return

        self._status_var.set("")
        self._password_var.set("")
        self._show_dashboard()

    def _handle_logout(self) -> None:
        logout_user()
        self._show_login_view()

    @requires_role("ADMIN")
    def _open_admin_panel(self) -> None:
        session = get_current_session()
        if session is None:  # pragma: no cover - defensa adicional
            raise AuthorizationError("Debe iniciar sesión para continuar")

        log_audit(
            actor=session.email,
            actor_id=session.user_id,
            entity="ui",
            action="open_admin_panel",
        )

        if messagebox is not None:
            messagebox.showinfo(
                "Panel administrativo",
                "Accedió correctamente al panel administrativo protegido.",
            )

    def _handle_admin_panel(self) -> None:
        try:
            self._open_admin_panel()
        except AuthorizationError as exc:
            LOGGER.info("Intento de acceso a panel sin permisos: %s", exc)
            if messagebox is not None:
                messagebox.showwarning("Permiso insuficiente", str(exc))

    def _on_close(self) -> None:
        try:
            logout_user()
        finally:
            if self._root is not None:
                self._root.destroy()


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
