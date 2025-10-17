from __future__ import annotations

import json
from contextlib import closing
from typing import Any, Mapping, Optional

from mysql.connector.connection import MySQLConnection

__all__ = [
    "AuditRepository",
    "audit_repository",
]


class AuditRepository:
    """Repositorio auxiliar para registrar eventos de auditoría."""

    def log_event(
        self,
        connection: MySQLConnection,
        *,
        actor: str,
        action: str,
        entity: str,
        before: Optional[Mapping[str, Any]] = None,
        after: Optional[Mapping[str, Any]] = None,
        actor_id: Optional[int] = None,
        entity_id: Optional[str] = None,
    ) -> None:
        """Inserta un evento en la tabla ``audit_log``."""

        query = (
            "INSERT INTO audit_log (actor, actor_user_id, entity, entity_id, action, before_state, after_state) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        )
        params = (
            actor,
            actor_id,
            entity,
            entity_id,
            action,
            json.dumps(before, ensure_ascii=False) if before is not None else None,
            json.dumps(after, ensure_ascii=False) if after is not None else None,
        )
        with closing(connection.cursor()) as cursor:
            cursor.execute(query, params)


audit_repository = AuditRepository()
