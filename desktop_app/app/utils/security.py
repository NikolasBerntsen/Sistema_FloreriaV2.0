from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Iterable, TypeVar

from app.services.auth_service import get_current_session

__all__ = ["AuthorizationError", "requires_role"]

T = TypeVar("T")


class AuthorizationError(RuntimeError):
    """Se lanza cuando el usuario no posee privilegios suficientes."""


def _normalize_roles(roles: Iterable[str]) -> set[str]:
    return {role.upper() for role in roles if role}


def requires_role(*roles: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorador que valida la sesión activa y el rol antes de ejecutar una acción."""

    normalized = _normalize_roles(roles)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            session = get_current_session()
            if session is None:
                raise AuthorizationError("Debe iniciar sesión para continuar")

            if normalized and session.role.upper() not in normalized:
                raise AuthorizationError("No cuenta con permisos para realizar esta acción")

            return func(*args, **kwargs)

        return wrapper

    return decorator
