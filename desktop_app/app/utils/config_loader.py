from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Mapping, Optional

__all__ = [
    "DatabaseConfig",
    "ConfigError",
    "ValidationError",
    "load_database_config",
    "get_database_config",
]


class ConfigError(RuntimeError):
    """Base exception for configuration related errors."""


class ValidationError(ConfigError):
    """Raised when the configuration file does not match the expected schema."""

    def __init__(self, errors: Mapping[str, str]) -> None:
        message = "Configuración de base de datos inválida"
        if errors:
            details = ", ".join(f"{field}: {reason}" for field, reason in errors.items())
            message = f"{message}: {details}"
        super().__init__(message)
        self.errors = dict(errors)


@dataclass(frozen=True)
class DatabaseConfig:
    """Normalized database configuration."""

    host: str
    port: int
    username: str
    password: str
    schema: str

    def as_dict(self) -> Dict[str, Any]:
        """Return the configuration as a dictionary compatible with mysql.connector."""

        return {
            "host": self.host,
            "port": self.port,
            "user": self.username,
            "password": self.password,
            "database": self.schema,
        }


_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "database.json"
_REQUIRED_FIELDS: Dict[str, type] = {
    "host": str,
    "port": int,
    "username": str,
    "password": str,
    "schema": str,
}

_config_cache: Optional[DatabaseConfig] = None
_cache_lock = Lock()


def _validate_schema(payload: Mapping[str, Any]) -> DatabaseConfig:
    errors: Dict[str, str] = {}
    normalized: Dict[str, Any] = {}

    for field, expected_type in _REQUIRED_FIELDS.items():
        if field not in payload:
            errors[field] = "campo requerido ausente"
            continue

        value = payload[field]
        if expected_type is str:
            if not isinstance(value, str) or not value.strip():
                errors[field] = "debe ser una cadena no vacía"
                continue
            normalized[field] = value.strip()
        elif expected_type is int:
            if isinstance(value, bool):
                errors[field] = "debe ser un número entero"
                continue
            if isinstance(value, str):
                if not value.strip():
                    errors[field] = "debe ser un número entero"
                    continue
                try:
                    number = int(value)
                except ValueError as exc:  # pragma: no cover - defensive
                    errors[field] = "debe ser un número entero"
                    continue
                normalized[field] = number
            elif isinstance(value, (int,)):
                normalized[field] = int(value)
            else:
                errors[field] = "debe ser un número entero"
        else:  # pragma: no cover - no other types expected
            errors[field] = "tipo de dato inesperado"

    if errors:
        raise ValidationError(errors)

    port = normalized["port"]
    if not 0 < port < 65536:
        raise ValidationError({"port": "debe estar en el rango 1-65535"})

    return DatabaseConfig(
        host=normalized["host"],
        port=port,
        username=normalized["username"],
        password=normalized["password"],
        schema=normalized["schema"],
    )


def load_database_config(path: Optional[Path] = None, *, reload: bool = False) -> DatabaseConfig:
    """Load and validate the database configuration from ``config/database.json``.

    Parameters
    ----------
    path:
        Optional explicit path to the configuration file. When omitted, the
        default ``config/database.json`` relative to the project root is used.
    reload:
        If ``True`` the configuration is re-read from disk even when it was
        previously cached.
    """

    global _config_cache

    if path is None:
        path = _DEFAULT_CONFIG_PATH

    if not isinstance(path, Path):
        path = Path(path)

    with _cache_lock:
        if not reload and _config_cache is not None and path == _DEFAULT_CONFIG_PATH:
            return _config_cache

        if not path.exists():
            raise ConfigError(f"No se encontró el archivo de configuración: {path}")

        try:
            raw_data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover - depends on external file
            raise ConfigError(f"El archivo de configuración contiene JSON inválido: {exc}") from exc

        if not isinstance(raw_data, Mapping):
            raise ValidationError({"root": "el contenido debe ser un objeto JSON"})

        config = _validate_schema(raw_data)

        if path == _DEFAULT_CONFIG_PATH:
            _config_cache = config

        return config


def get_database_config() -> DatabaseConfig:
    """Return the cached database configuration, loading it if necessary."""

    return load_database_config()
