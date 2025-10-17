from __future__ import annotations

from contextlib import closing
from typing import Optional

from mysql.connector.connection import MySQLConnection

from .base import BaseRepository

__all__ = ["RoleRepository", "role_repository"]


class RoleRepository(BaseRepository):
    """Repository helpers for the ``roles`` table."""

    def __init__(self) -> None:
        super().__init__(
            table_name="roles",
            columns=("name", "description"),
            allowed_sort_fields=("id", "name"),
            default_sort=("name", "ASC"),
            filterable_fields=("name",),
            searchable_fields=("name", "description"),
        )

    def get_id_by_name(self, connection: MySQLConnection, name: str) -> Optional[int]:
        query = "SELECT id FROM roles WHERE name = %s LIMIT 1"
        with closing(connection.cursor()) as cursor:
            cursor.execute(query, (name,))
            row = cursor.fetchone()
            return int(row[0]) if row else None

    def upsert_role(
        self,
        connection: MySQLConnection,
        *,
        name: str,
        description: str,
    ) -> None:
        query = (
            "INSERT INTO roles (name, description) VALUES (%s, %s) "
            "ON DUPLICATE KEY UPDATE description = VALUES(description)"
        )
        with closing(connection.cursor()) as cursor:
            cursor.execute(query, (name, description))


role_repository = RoleRepository()

