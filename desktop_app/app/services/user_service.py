from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from mysql.connector import errors as mysql_errors
from mysql.connector.connection import MySQLConnection

from app.db.repositories.role_repository import role_repository
from app.db.repositories.user_repository import user_repository
from app.services.audit_service import log_audit
from app.services.auth_service import hash_password

__all__ = ["InitialAdmin", "UserService", "user_service"]

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class InitialAdmin:
    """Data required to create the first administrator."""

    first_name: str
    last_name: str
    email: str
    password: str


class UserService:
    """High level helpers to manage user accounts."""

    _ADMIN_ROLE_NAME = "ADMIN"
    _ADMIN_DESCRIPTION = "Acceso completo al sistema"

    def has_active_users(self, connection: MySQLConnection) -> bool:
        query = "SELECT 1 FROM users WHERE is_active = 1 LIMIT 1"
        with connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchone() is not None

    def ensure_admin_role(self, connection: MySQLConnection) -> int:
        role_repository.upsert_role(
            connection,
            name=self._ADMIN_ROLE_NAME,
            description=self._ADMIN_DESCRIPTION,
        )
        role_id = role_repository.get_id_by_name(connection, self._ADMIN_ROLE_NAME)
        if role_id is None:
            raise RuntimeError("No se pudo obtener el rol ADMIN luego de insertarlo")
        return role_id

    def create_initial_admin(
        self, connection: MySQLConnection, data: InitialAdmin
    ) -> dict[str, Optional[str]]:
        """Create the first administrator user ensuring proper auditing."""

        normalized_email = data.email.strip().lower()
        if not normalized_email:
            raise ValueError("El email es obligatorio")
        if not data.first_name.strip():
            raise ValueError("El nombre es obligatorio")
        if not data.password:
            raise ValueError("La contraseña es obligatoria")

        password_hash = hash_password(data.password)

        if getattr(connection, "in_transaction", False):
            LOGGER.debug(
                "Reutilizando transacción abierta para crear el administrador inicial"
            )
        else:
            connection.start_transaction()

        try:
            role_id = self.ensure_admin_role(connection)
            user_id = user_repository.create(
                connection,
                {
                    "role_id": role_id,
                    "first_name": data.first_name.strip(),
                    "last_name": data.last_name.strip(),
                    "email": normalized_email,
                    "password_hash": password_hash,
                    "is_active": 1,
                    "must_reset_password": 0,
                },
            )

            log_audit(
                actor=normalized_email,
                actor_id=user_id,
                entity="users",
                entity_id=str(user_id),
                action="create_admin",
                after={
                    "role": self._ADMIN_ROLE_NAME,
                    "first_name": data.first_name.strip(),
                    "last_name": data.last_name.strip(),
                },
                connection=connection,
            )

            connection.commit()
            return {"id": user_id, "email": normalized_email}
        except mysql_errors.IntegrityError as exc:
            connection.rollback()
            LOGGER.warning("No se pudo crear el administrador inicial: %s", exc)
            raise ValueError("El email ya está registrado en el sistema") from exc
        except Exception:
            connection.rollback()
            raise


user_service = UserService()

