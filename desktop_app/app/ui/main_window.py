"""Componentes de interfaz de alto nivel para la ventana principal."""
from __future__ import annotations

import logging
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional, Sequence

from app.services.branding_service import BrandingInfo

from .navigation import NavigationController, ViewDefinition
from . import theme

__all__ = ["MenuItem", "MainWindow"]

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class MenuItem:
    """Representa una acción del menú lateral."""

    text: str
    command: Callable[[], None]
    tooltip: Optional[str] = None
    shortcut: Optional[str] = None


class MainWindow:
    """Crea la estructura base con cabecera, breadcrumbs y menú lateral."""

    def __init__(
        self,
        root: tk.Tk,
        branding: BrandingInfo,
        *,
        side_menu_items: Sequence[MenuItem] | None = None,
    ) -> None:
        self.root = root
        self.branding = branding
        self.navigation = NavigationController(self._display_view)
        self._current_view: Optional[tk.Widget] = None
        self._logo_image: Optional[tk.PhotoImage] = None
        self._menu_buttons: List[tk.Button] = []
        self._menu_tooltips: List[theme.Tooltip] = []

        theme.apply_base_theme(root)

        self._container = tk.Frame(root, bg=theme.BACKGROUND_COLOR)
        self._container.pack_forget()

        self._build_header()
        self._build_body()
        self.set_side_menu_items(side_menu_items or [])

        self._register_navigation_shortcuts()

    # ------------------------------------------------------------------
    # Construcción de interfaz
    # ------------------------------------------------------------------
    def _build_header(self) -> None:
        if hasattr(self, "_header") and self._header.winfo_exists():
            header = self._header
            for child in header.winfo_children():
                child.destroy()
        else:
            self._header = tk.Frame(self._container, bg=theme.SURFACE_COLOR, padx=18, pady=14)
            self._header.pack(fill=tk.X)
            header = self._header

        branding_frame = tk.Frame(header, bg=theme.SURFACE_COLOR)
        branding_frame.pack(side=tk.LEFT, anchor=tk.NW)

        if self.branding.logo_path:
            self._logo_image = self._load_logo(self.branding.logo_path)
            if self._logo_image is not None:
                logo_label = tk.Label(branding_frame, image=self._logo_image, bg=theme.SURFACE_COLOR)
                logo_label.pack(side=tk.LEFT, padx=(0, 10))

        text_frame = tk.Frame(branding_frame, bg=theme.SURFACE_COLOR)
        text_frame.pack(side=tk.LEFT)

        name_label = tk.Label(
            text_frame,
            text=self.branding.name,
            font=(theme.FONT_FAMILY, theme.FONT_SIZE_TITLE, "bold"),
            bg=theme.SURFACE_COLOR,
            fg=theme.TEXT_PRIMARY,
        )
        name_label.pack(anchor=tk.W)

        if self.branding.tagline:
            tagline_label = tk.Label(
                text_frame,
                text=self.branding.tagline,
                font=(theme.FONT_FAMILY, theme.FONT_SIZE_SUBTITLE),
                bg=theme.SURFACE_COLOR,
                fg=theme.TEXT_SECONDARY,
            )
            tagline_label.pack(anchor=tk.W)

        nav_frame = tk.Frame(header, bg=theme.SURFACE_COLOR)
        nav_frame.pack(side=tk.RIGHT, anchor=tk.NE)

        self._breadcrumb_var = tk.StringVar(value="Inicio")
        breadcrumb_label = tk.Label(
            nav_frame,
            textvariable=self._breadcrumb_var,
            font=(theme.FONT_FAMILY, theme.FONT_SIZE_BODY),
            bg=theme.SURFACE_COLOR,
            fg=theme.TEXT_SECONDARY,
        )
        breadcrumb_label.pack(side=tk.BOTTOM, anchor=tk.E)

        controls_frame = tk.Frame(nav_frame, bg=theme.SURFACE_COLOR)
        controls_frame.pack(side=tk.TOP, anchor=tk.E, pady=(0, 6))

        self._back_button = tk.Button(controls_frame, text="◀", command=self.navigation.go_back)
        theme.style_secondary_button(self._back_button)
        self._back_button.pack(side=tk.LEFT, padx=4)
        self._home_button = tk.Button(controls_frame, text="⌂", command=self.navigation.go_home)
        theme.style_secondary_button(self._home_button)
        self._home_button.pack(side=tk.LEFT, padx=4)
        self._forward_button = tk.Button(controls_frame, text="▶", command=self.navigation.go_forward)
        theme.style_secondary_button(self._forward_button)
        self._forward_button.pack(side=tk.LEFT, padx=4)

        self._tooltips = [
            theme.Tooltip(self._back_button, "Atrás (Alt+Izquierda)"),
            theme.Tooltip(self._home_button, "Inicio (Alt+Inicio)"),
            theme.Tooltip(self._forward_button, "Adelante (Alt+Derecha)"),
        ]

    def _build_body(self) -> None:
        body = tk.Frame(self._container, bg=theme.BACKGROUND_COLOR)
        body.pack(fill=tk.BOTH, expand=True)

        self._side_menu = tk.Frame(body, bg=theme.SURFACE_COLOR, width=220, padx=12, pady=18)
        self._side_menu.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12), pady=(4, 16))
        self._side_menu.pack_propagate(False)

        self._content = tk.Frame(body, bg=theme.SURFACE_COLOR, padx=30, pady=24)
        self._content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=(4, 16))

    def _load_logo(self, path: Path) -> Optional[tk.PhotoImage]:
        try:
            return tk.PhotoImage(file=str(path))
        except Exception:  # pragma: no cover - depende de archivo externo
            LOGGER.warning("No fue posible cargar el logotipo desde %s", path)
            return None

    def _register_navigation_shortcuts(self) -> None:
        theme.register_shortcut(self.root, "<Alt-Left>", self.navigation.go_back)
        theme.register_shortcut(self.root, "<Alt-Right>", self.navigation.go_forward)
        theme.register_shortcut(self.root, "<Alt-Home>", self.navigation.go_home)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def show(self) -> None:
        self._container.pack(fill=tk.BOTH, expand=True)
        self._container.tkraise()
        self._update_navigation_controls()

    def hide(self) -> None:
        self._container.pack_forget()

    def set_side_menu_items(self, items: Sequence[MenuItem]) -> None:
        """Reemplaza el contenido del menú lateral."""

        for button in self._menu_buttons:
            button.destroy()
        self._menu_buttons.clear()
        self._menu_tooltips.clear()

        for index, item in enumerate(items):
            button = tk.Button(self._side_menu, text=item.text, command=item.command)
            if index == 0:
                theme.style_primary_button(button)
            else:
                theme.style_secondary_button(button)
            button.pack(fill=tk.X, pady=6)
            self._menu_buttons.append(button)

            if item.tooltip:
                self._menu_tooltips.append(theme.Tooltip(button, item.tooltip))
            if item.shortcut:
                theme.register_shortcut(self.root, item.shortcut, item.command)

    def update_branding(self, branding: BrandingInfo) -> None:
        """Permite refrescar la identidad visual sin reconstruir la ventana."""

        self.branding = branding
        for child in self._header.winfo_children():
            child.destroy()
        self._build_header()

    def set_menu_enabled(self, index: int, enabled: bool) -> None:
        """Actualiza el estado de un botón del menú lateral."""

        if 0 <= index < len(self._menu_buttons):
            state = tk.NORMAL if enabled else tk.DISABLED
            self._menu_buttons[index].config(state=state)

    # ------------------------------------------------------------------
    # Renderizado de vistas
    # ------------------------------------------------------------------
    def _display_view(self, view: ViewDefinition) -> None:
        if self._current_view is not None:
            self._current_view.destroy()
            self._current_view = None

        widget = view.factory(self._content)
        if isinstance(widget, tk.Widget):
            self._current_view = widget
            if widget.winfo_manager() == "":
                widget.pack(fill=tk.BOTH, expand=True)

        crumbs = " / ".join(view.breadcrumbs) if view.breadcrumbs else view.title
        self._breadcrumb_var.set(crumbs)
        self._update_navigation_controls()

    def _update_navigation_controls(self) -> None:
        state_back = tk.NORMAL if self.navigation.can_go_back() else tk.DISABLED
        state_forward = tk.NORMAL if self.navigation.can_go_forward() else tk.DISABLED
        state_home = tk.NORMAL if self.navigation.current is not None else tk.DISABLED

        self._back_button.config(state=state_back)
        self._forward_button.config(state=state_forward)
        self._home_button.config(state=state_home)

