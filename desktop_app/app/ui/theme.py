"""Definiciones de colores, tipografías y utilidades de estilo."""
from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from typing import Callable, Optional

__all__ = [
    "BACKGROUND_COLOR",
    "SURFACE_COLOR",
    "PRIMARY_COLOR",
    "ACCENT_COLOR",
    "TEXT_PRIMARY",
    "TEXT_SECONDARY",
    "FONT_FAMILY",
    "FONT_SIZE_BODY",
    "FONT_SIZE_SUBTITLE",
    "FONT_SIZE_TITLE",
    "Tooltip",
    "style_primary_button",
    "style_secondary_button",
    "register_shortcut",
    "apply_base_theme",
]

BACKGROUND_COLOR = "#F5F7FA"
SURFACE_COLOR = "#FFFFFF"
PRIMARY_COLOR = "#2E86C1"
ACCENT_COLOR = "#1ABC9C"
TEXT_PRIMARY = "#1C2833"
TEXT_SECONDARY = "#5D6D7E"
FONT_FAMILY = "Segoe UI"
FONT_SIZE_TITLE = 16
FONT_SIZE_SUBTITLE = 12
FONT_SIZE_BODY = 10


def apply_base_theme(root: tk.Misc) -> None:
    """Configura colores y tipografías base para la ventana principal."""

    root.configure(bg=BACKGROUND_COLOR)
    root.option_add("*Font", f"{FONT_FAMILY} {FONT_SIZE_BODY}")
    root.option_add("*Label.background", SURFACE_COLOR)
    root.option_add("*Label.foreground", TEXT_PRIMARY)
    root.option_add("*Button.font", f"{FONT_FAMILY} {FONT_SIZE_BODY}")


def style_primary_button(button: tk.Button) -> None:
    """Aplica colores y relieve al botón principal."""

    button.configure(
        bg=PRIMARY_COLOR,
        fg="white",
        activebackground="#1F618D",
        activeforeground="white",
        relief=tk.FLAT,
        bd=0,
        padx=14,
        pady=8,
        cursor="hand2",
    )


def style_secondary_button(button: tk.Button) -> None:
    """Estilo alternativo para botones secundarios."""

    button.configure(
        bg=SURFACE_COLOR,
        fg=PRIMARY_COLOR,
        activebackground="#EAF2F8",
        activeforeground=PRIMARY_COLOR,
        relief=tk.GROOVE,
        bd=1,
        padx=12,
        pady=6,
        cursor="hand2",
        highlightthickness=0,
    )


@dataclass
class Tooltip:
    """Tooltip ligero basado en Toplevel."""

    widget: tk.Widget
    text: str
    delay: int = 500

    def __post_init__(self) -> None:
        self._after_id: Optional[str] = None
        self._window: Optional[tk.Toplevel] = None
        self.widget.bind("<Enter>", self._schedule)
        self.widget.bind("<Leave>", self._hide)
        self.widget.bind("<ButtonPress>", self._hide)

    def _schedule(self, _event: tk.Event) -> None:
        self._cancel()
        self._after_id = self.widget.after(self.delay, self._show)

    def _cancel(self) -> None:
        if self._after_id is not None:
            self.widget.after_cancel(self._after_id)
            self._after_id = None

    def _show(self) -> None:
        self._cancel()
        if self._window is not None:
            return

        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

        self._window = tk.Toplevel(self.widget)
        self._window.wm_overrideredirect(True)
        self._window.configure(bg=TEXT_PRIMARY)
        label = tk.Label(
            self._window,
            text=self.text,
            bg=TEXT_PRIMARY,
            fg="white",
            font=(FONT_FAMILY, FONT_SIZE_BODY),
            padx=8,
            pady=4,
        )
        label.pack()
        self._window.wm_geometry(f"+{x}+{y}")

    def _hide(self, _event: tk.Event) -> None:
        self._cancel()
        if self._window is not None:
            self._window.destroy()
            self._window = None


def register_shortcut(root: tk.Misc, sequence: str, command: Callable[[], None]) -> None:
    """Asocia un atajo de teclado global a la ventana raíz."""

    def _callback(event: tk.Event) -> str:
        command()
        return "break"

    root.bind(sequence, _callback)
