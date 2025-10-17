from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass
from typing import Optional

import bcrypt
from mysql.connector.connection import MySQLConnection

from app.db.connection import connection_scope
from app.db.repositories.user_repository import user_repository
from app.services.audit_service import log_audit

__all__ = [
    "AuthenticationError",
    "Session",
    "authenticate",
    "get_current_session",
    "hash_password",
    "is_authenticated",
    "logout",
    "verify_password",
]

LOGGER = logging.getLogger(__name__)


class AuthenticationError(RuntimeError):
    """Se lanza cuando las credenciales proporcionadas no son válidas."""


@dataclass(frozen=True)
class Session:
    """Información básica de la sesión autenticada."""

    token: str
    user_id: int
    email: str
    role: str
    full_name: str

    @property
    def actor(self) -> str:
        """Nombre descriptivo del actor para auditoría."""

        return self.full_name or self.email


class _SessionStore:
    """Almacén simple en memoria para la sesión autenticada."""

    def __init__(self) -> None:
        self._current: Optional[Session] = None

    def store(self, session: Session) -> None:
        self._current = session

    def get(self) -> Optional[Session]:
        return self._current

    def clear(self) -> None:
        self._current = None


_session_store = _SessionStore()


def hash_password(password: str) -> str:
    """Genera un hash bcrypt para la contraseña indicada."""

    if not password:
        raise ValueError("La contraseña no puede estar vacía")
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verifica que la contraseña en texto plano coincida con el hash almacenado."""

    if not password or not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:  # pragma: no cover - hash inválido en base
        LOGGER.warning("Hash de contraseña inválido detectado durante la autenticación")
        return False


def authenticate(
    email: str,
    password: str,
    *,
    connection: Optional[MySQLConnection] = None,
) -> Session:
    """Autentica al usuario y registra la sesión activa."""

    normalized_email = (email or "").strip().lower()
    if not normalized_email or not password:
        raise AuthenticationError("Debe ingresar email y contraseña")

    if connection is None:
        with connection_scope() as scoped_connection:
            return _authenticate_with_connection(scoped_connection, normalized_email, password)
    return _authenticate_with_connection(connection, normalized_email, password)


def _authenticate_with_connection(
    connection: MySQLConnection, email: str, password: str
) -> Session:
    user = user_repository.get_active_by_email(connection, email)
    if not user:
        log_audit(
            actor=email,
            actor_id=None,
            entity="auth",
            action="login_failed",
            after={"reason": "usuario no encontrado"},
            connection=connection,
        )
        raise AuthenticationError("Usuario o contraseña inválidos")

    if not verify_password(password, user["password_hash"]):
        log_audit(
            actor=email,
            actor_id=int(user["id"]),
            entity="auth",
            action="login_failed",
            after={"reason": "credenciales inválidas"},
            connection=connection,
        )
        raise AuthenticationError("Usuario o contraseña inválidos")

    token = secrets.token_urlsafe(32)
    full_name = f"{user['first_name']} {user.get('last_name', '')}".strip()
    session = Session(
        token=token,
        user_id=int(user["id"]),
        email=user["email"],
        role=user.get("role_name", ""),
        full_name=full_name,
    )

    _session_store.store(session)
    user_repository.mark_successful_login(connection, session.user_id)

    log_audit(
        actor=session.email,
        actor_id=session.user_id,
        entity="auth",
        action="login",
        after={"status": "success", "role": session.role},
        connection=connection,
    )

    return session


def get_current_session() -> Optional[Session]:
    """Devuelve la sesión autenticada actual, si existe."""

    return _session_store.get()


def is_authenticated() -> bool:
    """Indica si existe una sesión autenticada activa."""

    return _session_store.get() is not None


def logout() -> None:
    """Cierra la sesión actual y registra el evento."""

    session = _session_store.get()
    if session is None:
        return

    _session_store.clear()

    try:
        log_audit(
            actor=session.email,
            actor_id=session.user_id,
            entity="auth",
            action="logout",
            after={"status": "success"},
        )
    except Exception:  # pragma: no cover - logging defensivo
        LOGGER.debug("Error al registrar auditoría de cierre de sesión", exc_info=True)
