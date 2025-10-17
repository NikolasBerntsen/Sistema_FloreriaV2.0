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
from app.services.branding_service import BrandingInfo, get_branding
from app.ui import theme as ui_theme
from app.ui.main_window import MainWindow, MenuItem
from app.ui.navigation import ViewDefinition
from app.utils.security import AuthorizationError, requires_role


LOGGER = logging.getLogger(__name__)


class FloreriaApp:
    """Aplicación principal basada en Tkinter con autenticación y control de roles."""

    def __init__(self, connection: MySQLConnection, config: Dict[str, Any]) -> None:
        self._connection = connection
        self._config = config
        self._branding: BrandingInfo = get_branding(config)
        self._root: Optional[tk.Tk] = None if tk is not None else None
        self._login_frame: Optional[tk.Frame] = None
        self._main_window: Optional[MainWindow] = None
        self._home_view: Optional[ViewDefinition] = None
        self._window_logo: Optional[object] = None
        self._email_var = tk.StringVar(value="") if tk is not None else None
        self._password_var = tk.StringVar(value="") if tk is not None else None
        self._status_var = tk.StringVar(value="") if tk is not None else None
        self._user_info_var = tk.StringVar(value="") if tk is not None else None

    def run(self) -> None:
        if tk is None:
            raise RuntimeError(
                "Tkinter no está disponible en este entorno. La interfaz gráfica no puede iniciarse."
            )

        self._root = tk.Tk()
        self._root.title(self._branding.name)
        self._root.geometry("960x620")
        self._root.minsize(820, 520)
        self._root.configure(bg=ui_theme.BACKGROUND_COLOR)
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)

        if self._branding.logo_path:
            try:
                self._window_logo = tk.PhotoImage(file=str(self._branding.logo_path))
                self._root.iconphoto(True, self._window_logo)
            except Exception:  # pragma: no cover - depende de archivos externos
                LOGGER.warning("No se pudo establecer el icono de la ventana", exc_info=True)

        self._build_login_view()
        self._build_status_bar()
        self._show_login_view()

        self._root.mainloop()

    # ------------------------------------------------------------------
    # Construcción de vistas
    # ------------------------------------------------------------------
    def _build_login_view(self) -> None:
        assert tk is not None and self._root is not None

        self._login_frame = tk.Frame(self._root, padx=40, pady=40, bg=ui_theme.SURFACE_COLOR)

        title = tk.Label(
            self._login_frame,
            text=f"Iniciar sesión en {self._branding.name}",
            font=(ui_theme.FONT_FAMILY, 20, "bold"),
            bg=ui_theme.SURFACE_COLOR,
            fg=ui_theme.TEXT_PRIMARY,
        )
        title.grid(row=0, column=0, columnspan=2, pady=(0, 12))

        row_offset = 0
        if self._branding.tagline:
            tagline = tk.Label(
                self._login_frame,
                text=self._branding.tagline,
                font=(ui_theme.FONT_FAMILY, ui_theme.FONT_SIZE_SUBTITLE),
                bg=ui_theme.SURFACE_COLOR,
                fg=ui_theme.TEXT_SECONDARY,
            )
            tagline.grid(row=1, column=0, columnspan=2, pady=(0, 18))
            row_offset = 1

        email_label = tk.Label(
            self._login_frame,
            text="Correo electrónico",
            bg=ui_theme.SURFACE_COLOR,
            fg=ui_theme.TEXT_PRIMARY,
        )
        email_entry = tk.Entry(self._login_frame, textvariable=self._email_var, width=38)
        email_label.grid(row=1 + row_offset, column=0, sticky=tk.W, pady=5)
        email_entry.grid(row=1 + row_offset, column=1, pady=5)

        password_label = tk.Label(
            self._login_frame,
            text="Contraseña",
            bg=ui_theme.SURFACE_COLOR,
            fg=ui_theme.TEXT_PRIMARY,
        )
        password_entry = tk.Entry(
            self._login_frame, textvariable=self._password_var, width=38, show="*"
        )
        password_label.grid(row=2 + row_offset, column=0, sticky=tk.W, pady=5)
        password_entry.grid(row=2 + row_offset, column=1, pady=5)

        login_button = tk.Button(
            self._login_frame,
            text="Ingresar",
            command=self._handle_login,
        )
        ui_theme.style_primary_button(login_button)
        login_button.grid(row=3 + row_offset, column=0, columnspan=2, pady=(18, 12))

        status_message = tk.Label(
            self._login_frame,
            textvariable=self._status_var,
            bg=ui_theme.SURFACE_COLOR,
            fg="#C0392B",
        )
        status_message.grid(row=4 + row_offset, column=0, columnspan=2)

        password_entry.bind("<Return>", lambda event: self._handle_login())

    def _build_status_bar(self) -> None:
        assert tk is not None and self._root is not None

        status_text = "Conexión a base de datos establecida"
        if self._config:
            status_text += " • Configuración local cargada"

        status_bar = tk.Label(
            self._root,
            text=status_text,
            font=(ui_theme.FONT_FAMILY, ui_theme.FONT_SIZE_BODY),
            anchor=tk.W,
            bd=1,
            relief=tk.SUNKEN,
            padx=12,
            bg=ui_theme.SURFACE_COLOR,
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _ensure_dashboard(self) -> None:
        assert tk is not None and self._root is not None

        if self._main_window is not None:
            return

        menu_items = [
            MenuItem(
                text="Panel administrativo",
                command=self._handle_admin_panel,
                tooltip="Acceder al panel administrativo",
                shortcut="<Control-Shift-A>",
            ),
            MenuItem(
                text="Cerrar sesión",
                command=self._handle_logout,
                tooltip="Cerrar la sesión actual",
                shortcut="<Control-L>",
            ),
        ]

        self._main_window = MainWindow(
            self._root,
            self._branding,
            side_menu_items=menu_items,
        )

        self._home_view = ViewDefinition(
            identifier="dashboard.home",
            title="Inicio",
            breadcrumbs=("Inicio",),
            factory=self._build_home_view,
        )
        self._main_window.navigation.set_home(self._home_view)

    def _build_home_view(self, parent: tk.Widget) -> tk.Widget:
        frame = tk.Frame(parent, bg=ui_theme.SURFACE_COLOR)

        welcome = tk.Label(
            frame,
            text=f"Bienvenido a {self._branding.name}",
            font=(ui_theme.FONT_FAMILY, ui_theme.FONT_SIZE_TITLE, "bold"),
            bg=ui_theme.SURFACE_COLOR,
            fg=ui_theme.TEXT_PRIMARY,
            pady=10,
        )
        welcome.pack(anchor=tk.W)

        info = tk.Label(
            frame,
            textvariable=self._user_info_var,
            font=(ui_theme.FONT_FAMILY, ui_theme.FONT_SIZE_SUBTITLE),
            bg=ui_theme.SURFACE_COLOR,
            fg=ui_theme.TEXT_SECONDARY,
            pady=4,
        )
        info.pack(anchor=tk.W)

        return frame

    # ------------------------------------------------------------------
    # Gestión de eventos
    # ------------------------------------------------------------------
    def _show_login_view(self) -> None:
        assert tk is not None
        if self._main_window is not None:
            self._main_window.hide()

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
            if self._main_window is not None:
                self._main_window.set_menu_enabled(0, session.role.upper() == "ADMIN")
        else:
            self._user_info_var.set("")

        if self._main_window is not None:
            self._main_window.show()
            self._main_window.navigation.go_home()

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
        if self._main_window is not None:
            self._main_window.navigation.reset()
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

    config_path = os.getenv("FLORERIA_CONFIG_PATH")
    config = load_local_config(config_path)
    branding = get_branding(config)
    LOGGER.info("Iniciando aplicación de escritorio %s", branding.name)

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
