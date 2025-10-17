"""Controlador de navegación basado en pila para la interfaz."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, List, Sequence

__all__ = ["ViewDefinition", "NavigationController"]


@dataclass(frozen=True)
class ViewDefinition:
    """Describe una vista renderizable dentro de la ventana principal."""

    identifier: str
    title: str
    breadcrumbs: Sequence[str]
    factory: Callable[[Any], Any]

    def with_breadcrumbs(self, breadcrumbs: Iterable[str]) -> "ViewDefinition":
        return ViewDefinition(
            identifier=self.identifier,
            title=self.title,
            breadcrumbs=tuple(breadcrumbs),
            factory=self.factory,
        )


class NavigationController:
    """Gestiona la navegación entre vistas manteniendo historial y futuro."""

    def __init__(self, on_view_change: Callable[[ViewDefinition], None]) -> None:
        self._on_view_change = on_view_change
        self._history: List[ViewDefinition] = []
        self._future: List[ViewDefinition] = []
        self._current: ViewDefinition | None = None
        self._home: ViewDefinition | None = None

    @property
    def current(self) -> ViewDefinition | None:
        return self._current

    def set_home(self, view: ViewDefinition, *, navigate: bool = True) -> None:
        """Define la vista de inicio y navega hacia ella si se indica."""

        self._home = view
        if navigate:
            self.go_home()

    def navigate_to(self, view: ViewDefinition) -> None:
        """Navega hacia una vista, almacenando la actual en el historial."""

        if self._current is not None:
            self._history.append(self._current)
        self._current = view
        self._future.clear()
        self._notify()

    def go_back(self) -> None:
        """Regresa a la vista anterior si existe."""

        if not self._history:
            return
        if self._current is not None:
            self._future.append(self._current)
        self._current = self._history.pop()
        self._notify()

    def go_forward(self) -> None:
        """Avanza a la siguiente vista si existe."""

        if not self._future:
            return
        if self._current is not None:
            self._history.append(self._current)
        self._current = self._future.pop()
        self._notify()

    def go_home(self) -> None:
        """Limpia el historial y lleva a la vista inicial."""

        if self._home is None:
            return
        self._history.clear()
        self._future.clear()
        self._current = self._home
        self._notify()

    def can_go_back(self) -> bool:
        return bool(self._history)

    def can_go_forward(self) -> bool:
        return bool(self._future)

    def reset(self) -> None:
        """Borra el estado actual sin disparar renderizados."""

        self._history.clear()
        self._future.clear()
        self._current = None

    def _notify(self) -> None:
        if self._current is not None:
            self._on_view_change(self._current)
