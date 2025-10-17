from __future__ import annotations

import logging
from typing import Any, Mapping, Optional

from mysql.connector.connection import MySQLConnection

from app.db.connection import connection_scope
from app.db.repositories.audit_repository import audit_repository

__all__ = ["log_audit"]

LOGGER = logging.getLogger(__name__)


def log_audit(
    actor: str,
    entity: str,
    action: str,
    before: Optional[Mapping[str, Any]] = None,
    after: Optional[Mapping[str, Any]] = None,
    *,
    actor_id: Optional[int] = None,
    entity_id: Optional[str] = None,
    connection: Optional[MySQLConnection] = None,
) -> None:
    """Registra un evento de auditoría, ignorando errores de manera segura."""

    try:
        if connection is None:
            with connection_scope() as scoped_connection:
                audit_repository.log_event(
                    scoped_connection,
                    actor=actor,
                    actor_id=actor_id,
                    entity=entity,
                    entity_id=entity_id,
                    action=action,
                    before=before,
                    after=after,
                )
        else:
            audit_repository.log_event(
                connection,
                actor=actor,
                actor_id=actor_id,
                entity=entity,
                entity_id=entity_id,
                action=action,
                before=before,
                after=after,
            )
    except Exception:  # pragma: no cover - registro de auditoría no crítico
        LOGGER.exception(
            "No se pudo registrar el evento de auditoría", extra={"entity": entity, "action": action}
        )
