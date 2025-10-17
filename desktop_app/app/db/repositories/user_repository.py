from __future__ import annotations

from contextlib import closing
from datetime import datetime
from typing import Any, MutableMapping, Optional, Sequence

from mysql.connector.connection import MySQLConnection

from .base import BaseRepository

__all__ = [
    "UserRepository",
    "user_repository",
]


class UserRepository(BaseRepository):
    """Repository helpers para la tabla ``users``."""

    def __init__(self) -> None:
        super().__init__(
            table_name="users",
            columns=(
                "role_id",
                "first_name",
                "last_name",
                "email",
                "password_hash",
                "is_active",
                "last_login_at",
                "must_reset_password",
                "password_reset_token",
                "password_reset_expires_at",
            ),
            primary_key="id",
            allowed_sort_fields=(
                "id",
                "email",
                "first_name",
                "last_name",
                "is_active",
                "last_login_at",
                "created_at",
                "updated_at",
            ),
            default_sort=("email", "ASC"),
            filterable_fields=("is_active", "role_id"),
            searchable_fields=("email", "first_name", "last_name"),
        )

    def get_active_by_email(
        self, connection: MySQLConnection, email: str
    ) -> Optional[MutableMapping[str, Any]]:
        """Recupera un usuario activo a partir del email."""

        query = (
            "SELECT u.*, r.name AS role_name "
            "FROM users u "
            "JOIN roles r ON r.id = u.role_id "
            "WHERE u.email = %s AND u.is_active = 1"
        )
        with closing(connection.cursor(dictionary=True)) as cursor:
            cursor.execute(query, (email,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_active_users(
        self, connection: MySQLConnection
    ) -> Sequence[MutableMapping[str, Any]]:
        """Devuelve todos los usuarios activos junto con su rol."""

        query = (
            "SELECT u.id, u.email, u.first_name, u.last_name, u.last_login_at, "
            "u.must_reset_password, r.name AS role_name "
            "FROM users u "
            "JOIN roles r ON r.id = u.role_id "
            "WHERE u.is_active = 1 "
            "ORDER BY u.email"
        )
        with closing(connection.cursor(dictionary=True)) as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def mark_successful_login(self, connection: MySQLConnection, user_id: int) -> None:
        """Actualiza la marca de último acceso de un usuario."""

        query = (
            "UPDATE users "
            "SET last_login_at = %s, must_reset_password = 0, "
            "password_reset_token = NULL, password_reset_expires_at = NULL "
            "WHERE id = %s"
        )
        now = datetime.utcnow()
        with closing(connection.cursor()) as cursor:
            cursor.execute(query, (now, user_id))

    def update_password_hash(
        self,
        connection: MySQLConnection,
        user_id: int,
        password_hash: str,
        *,
        must_reset: bool = False,
    ) -> None:
        """Actualiza el hash de contraseña de un usuario."""

        query = (
            "UPDATE users SET password_hash = %s, must_reset_password = %s, "
            "password_reset_token = NULL, password_reset_expires_at = NULL "
            "WHERE id = %s"
        )
        with closing(connection.cursor()) as cursor:
            cursor.execute(query, (password_hash, int(must_reset), user_id))

    def set_password_reset_token(
        self,
        connection: MySQLConnection,
        user_id: int,
        token: str,
        expires_at: datetime,
    ) -> None:
        """Registra un token temporal para restablecimiento de contraseña."""

        query = (
            "UPDATE users SET password_reset_token = %s, password_reset_expires_at = %s "
            "WHERE id = %s"
        )
        with closing(connection.cursor()) as cursor:
            cursor.execute(query, (token, expires_at, user_id))

    def clear_password_reset_token(self, connection: MySQLConnection, user_id: int) -> None:
        """Elimina el token de restablecimiento asociado al usuario."""

        query = (
            "UPDATE users SET password_reset_token = NULL, password_reset_expires_at = NULL "
            "WHERE id = %s"
        )
        with closing(connection.cursor()) as cursor:
            cursor.execute(query, (user_id,))


user_repository = UserRepository()
