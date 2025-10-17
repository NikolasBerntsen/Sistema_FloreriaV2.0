"""Utility helpers for the desktop application."""
"""Utilidades compartidas de la aplicación de escritorio."""

from importlib import import_module
from typing import Any

from .config_loader import (
    ConfigError,
    DatabaseConfig,
    ValidationError,
    get_database_config,
    load_database_config,
)
from .csv_export import export_csv, generate_csv

__all__ = [
    "ConfigError",
    "DatabaseConfig",
    "ValidationError",
    "get_database_config",
    "load_database_config",
    "export_csv",
    "generate_csv",
    "AuthorizationError",
    "requires_role",
]

_SECURITY_EXPORTS = {"AuthorizationError", "requires_role"}


def __getattr__(name: str) -> Any:
    """Lazily import security helpers to avoid circular imports."""

    if name in _SECURITY_EXPORTS:
        module = import_module(".security", __name__)
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

