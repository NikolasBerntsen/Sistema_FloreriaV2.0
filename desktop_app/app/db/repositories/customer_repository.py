from __future__ import annotations

from typing import Any, Mapping, MutableMapping, Optional

from mysql.connector.connection import MySQLConnection

from app.db.connection import with_connection, with_transaction

from .base import BaseRepository, PaginatedResult

__all__ = [
    "CustomerRepository",
    "customer_repository",
]


class CustomerRepository(BaseRepository):
    """CRUD operations for the ``customers`` table."""

    def __init__(self) -> None:
        super().__init__(
            table_name="customers",
            columns=(
                "first_name",
                "last_name",
                "email",
                "phone",
                "tax_id",
                "status",
            ),
            primary_key="id",
            allowed_sort_fields=(
                "id",
                "first_name",
                "last_name",
                "email",
                "phone",
                "status",
                "created_at",
                "updated_at",
            ),
            default_sort=("created_at", "DESC"),
            filterable_fields=("status",),
            searchable_fields=(
                "first_name",
                "last_name",
                "email",
                "phone",
                "tax_id",
            ),
        )

    @with_connection
    def list_customers(
        self,
        *,
        page: int = 1,
        size: int = 20,
        sort: Optional[str] = None,
        filters: Optional[Mapping[str, Any]] = None,
        search: Optional[str] = None,
        connection: MySQLConnection,
    ) -> PaginatedResult:
        """Return a paginated list of customers."""

        return self.list_paginated(
            connection,
            page=page,
            size=size,
            sort=sort,
            filters=filters,
            search=search,
        )

    @with_connection
    def get_customer(
        self,
        customer_id: int,
        *,
        for_update: bool = False,
        connection: MySQLConnection,
    ) -> Optional[MutableMapping[str, Any]]:
        """Fetch a single customer by its identifier."""

        return self.get_by_id(connection, customer_id, for_update=for_update)

    @with_transaction
    def create_customer(
        self,
        data: Mapping[str, Any],
        *,
        connection: MySQLConnection,
    ) -> MutableMapping[str, Any]:
        """Insert a new customer and return the persisted record."""

        customer_id = self.create(connection, data)
        customer = self.get_by_id(connection, customer_id)
        if customer is None:  # pragma: no cover - defensive
            raise RuntimeError("No se pudo recuperar el cliente recién creado")
        return customer

    @with_transaction
    def update_customer(
        self,
        customer_id: int,
        data: Mapping[str, Any],
        *,
        connection: MySQLConnection,
    ) -> MutableMapping[str, Any]:
        """Update an existing customer and return the updated record."""

        updated = self.update(connection, customer_id, data)
        if not updated:
            raise RuntimeError(f"Cliente {customer_id} no encontrado")
        customer = self.get_by_id(connection, customer_id)
        if customer is None:  # pragma: no cover - defensive
            raise RuntimeError("No se pudo recuperar el cliente actualizado")
        return customer

    @with_transaction
    def delete_customer(
        self,
        customer_id: int,
        *,
        connection: MySQLConnection,
    ) -> bool:
        """Delete a customer. Returns ``True`` if a row was removed."""

        deleted = self.delete(connection, customer_id)
        return bool(deleted)


customer_repository = CustomerRepository()
