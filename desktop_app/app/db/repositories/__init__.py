"""Database repository helpers and implementations."""

from importlib import import_module
from typing import Any, Tuple

from .audit_repository import AuditRepository, audit_repository
from .base import BaseRepository, PaginatedResult

__all__ = [
    "AuditRepository",
    "BaseRepository",
    "PaginatedResult",
    "audit_repository",
    "CustomerRepository",
    "UserRepository",
    "customer_repository",
    "user_repository",
    "RoleRepository",
    "role_repository",
]

_LAZY_EXPORTS: dict[str, Tuple[str, str]] = {
    "CustomerRepository": (".customer_repository", "CustomerRepository"),
    "customer_repository": (".customer_repository", "customer_repository"),
    "UserRepository": (".user_repository", "UserRepository"),
    "user_repository": (".user_repository", "user_repository"),
    "RoleRepository": (".role_repository", "RoleRepository"),
    "role_repository": (".role_repository", "role_repository"),
}


def __getattr__(name: str) -> Any:
    """Lazily import repositories prone to circular imports."""

    try:
        module_name, attribute = _LAZY_EXPORTS[name]
    except KeyError as exc:  # pragma: no cover - guard clause
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc

    module = import_module(module_name, __name__)
    value = getattr(module, attribute)
    globals()[name] = value
    return value

