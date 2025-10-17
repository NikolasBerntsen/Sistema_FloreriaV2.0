from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Optional

try:
    import tkinter as tk
    from tkinter import messagebox
except Exception:  # pragma: no cover - environments without Tk support
    tk = None  # type: ignore[assignment]
    messagebox = None  # type: ignore[assignment]

from app.services.user_service import InitialAdmin, UserService

from .. import theme

__all__ = ["InitialAdminDialog"]


_EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class _DialogCallbacks:
    on_success: Callable[[str], None]
    on_close: Callable[[], None]


class InitialAdminDialog:
    """Modal dialog that assists in creating the first administrator user."""

    def __init__(
        self,
        parent: tk.Tk,
        *,
        user_service: UserService,
        on_success: Callable[[str], None],
        on_close: Callable[[], None],
        connection,
    ) -> None:
        if tk is None:
            raise RuntimeError("Tkinter no está disponible en este entorno")

        self._parent = parent
        self._user_service = user_service
        self._connection = connection
        self._callbacks = _DialogCallbacks(on_success=on_success, on_close=on_close)
        self._created_email: Optional[str] = None

        self._window = tk.Toplevel(parent)
        self._window.title("Crear usuario administrador")
        self._window.configure(bg=theme.SURFACE_COLOR, padx=24, pady=20)
        self._window.transient(parent)
        self._window.grab_set()
        self._window.resizable(False, False)
        self._window.protocol("WM_DELETE_WINDOW", self._handle_close)

        self._first_name_var = tk.StringVar()
        self._last_name_var = tk.StringVar()
        self._email_var = tk.StringVar()
        self._password_var = tk.StringVar()
        self._confirm_var = tk.StringVar()
        self._status_var = tk.StringVar()

        self._build_form()

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------
    def _build_form(self) -> None:
        assert tk is not None

        header = tk.Label(
            self._window,
            text="No se encontraron usuarios. Configure el administrador inicial.",
            bg=theme.SURFACE_COLOR,
            fg=theme.TEXT_PRIMARY,
            font=(theme.FONT_FAMILY, theme.FONT_SIZE_SUBTITLE, "bold"),
            wraplength=420,
            justify=tk.LEFT,
        )
        header.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 14))

        self._add_entry("Nombre", self._first_name_var, 1)
        self._add_entry("Apellido", self._last_name_var, 2)
        self._add_entry("Correo electrónico", self._email_var, 3)
        self._add_entry("Contraseña", self._password_var, 4, show="*")
        self._add_entry("Confirmar contraseña", self._confirm_var, 5, show="*")

        self._status_label = tk.Label(
            self._window,
            textvariable=self._status_var,
            fg="#C0392B",
            bg=theme.SURFACE_COLOR,
            wraplength=420,
            justify=tk.LEFT,
        )
        self._status_label.grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=(8, 0))

        self._create_button = tk.Button(
            self._window,
            text="Crear administrador",
            command=self._handle_submit,
        )
        theme.style_primary_button(self._create_button)
        self._create_button.grid(row=7, column=0, columnspan=2, pady=(16, 0), sticky=tk.E)

        self._first_name_var.set("")
        self._window.after(50, lambda: self._entries[0].focus_set())

    def _add_entry(
        self,
        label_text: str,
        variable: tk.StringVar,
        row: int,
        *,
        show: Optional[str] = None,
    ) -> None:
        assert tk is not None

        label = tk.Label(
            self._window,
            text=label_text,
            bg=theme.SURFACE_COLOR,
            fg=theme.TEXT_SECONDARY,
        )
        entry = tk.Entry(self._window, textvariable=variable, width=38, show=show)
        label.grid(row=row, column=0, sticky=tk.W, pady=4)
        entry.grid(row=row, column=1, sticky=tk.W, pady=4)

        if not hasattr(self, "_entries"):
            self._entries: list[tk.Entry] = []
        self._entries.append(entry)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------
    def _handle_close(self) -> None:
        self._window.grab_release()
        self._window.destroy()
        self._callbacks.on_close()

    def _handle_submit(self) -> None:
        if tk is None:
            return

        error = self._validate()
        if error:
            self._status_var.set(error)
            return

        admin_data = InitialAdmin(
            first_name=self._first_name_var.get().strip(),
            last_name=self._last_name_var.get().strip(),
            email=self._email_var.get().strip(),
            password=self._password_var.get(),
        )

        try:
            result = self._user_service.create_initial_admin(self._connection, admin_data)
        except ValueError as exc:
            self._status_var.set(str(exc))
            return
        except Exception as exc:  # pragma: no cover - defensive UI feedback
            self._status_var.set("Ocurrió un error al crear el usuario. Consulte los registros.")
            if messagebox is not None:
                messagebox.showerror("Error", f"No se pudo crear el administrador: {exc}")
            return

        self._created_email = result.get("email")
        if messagebox is not None:
            messagebox.showinfo(
                "Administrador creado",
                "Se creó el usuario administrador. Ya puede iniciar sesión.",
            )
        self._window.grab_release()
        self._window.destroy()
        if self._created_email:
            self._callbacks.on_success(self._created_email)
        else:  # pragma: no cover - guard clause
            self._callbacks.on_close()

    def _validate(self) -> Optional[str]:
        first_name = self._first_name_var.get().strip()
        email = self._email_var.get().strip()
        password = self._password_var.get()
        confirm = self._confirm_var.get()

        if not first_name:
            return "El nombre es obligatorio"
        if not email:
            return "El correo electrónico es obligatorio"
        if not _EMAIL_REGEX.match(email):
            return "Ingrese un correo electrónico válido"
        if not password or len(password) < 6:
            return "La contraseña debe tener al menos 6 caracteres"
        if password != confirm:
            return "Las contraseñas no coinciden"
        return None

