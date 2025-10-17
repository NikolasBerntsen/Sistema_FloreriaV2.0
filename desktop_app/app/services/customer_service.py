from __future__ import annotations

import logging
from contextlib import closing
from datetime import date
from decimal import Decimal
from typing import Any, Mapping, MutableMapping, Optional, Sequence

from mysql.connector.connection import MySQLConnection

from app.db.connection import connection_scope
from app.db.repositories.customer_repository import (
    PaginatedResult,
    customer_repository,
)
from app.services.auth_service import get_current_session

__all__ = [
    "ACTIVE_STATUS",
    "INACTIVE_STATUS",
    "create_customer",
    "deactivate_customer",
    "get_customer",
    "get_financial_summary",
    "list_customers",
    "update_customer",
]

LOGGER = logging.getLogger(__name__)

ACTIVE_STATUS = "active"
INACTIVE_STATUS = "inactive"


def list_customers(
    *,
    page: int = 1,
    size: int = 20,
    sort: str | None = None,
    filters: Mapping[str, Any] | None = None,
    search: str | None = None,
) -> PaginatedResult:
    """Return a paginated list of customers using repository defaults."""

    return customer_repository.list_customers(
        page=page,
        size=size,
        sort=sort,
        filters=filters,
        search=search,
    )


def create_customer(data: Mapping[str, Any]) -> MutableMapping[str, Any]:
    """Create a new customer record and return the persisted row."""

    actor, actor_id = _get_actor_context()
    payload = dict(data)
    payload.setdefault("status", ACTIVE_STATUS)
    return customer_repository.create_customer(
        payload,
        actor=actor,
        actor_id=actor_id,
    )


def get_customer(customer_id: int) -> MutableMapping[str, Any] | None:
    """Retrieve a customer by its identifier if it exists."""

    return customer_repository.get_customer(customer_id)


def update_customer(customer_id: int, data: Mapping[str, Any]) -> MutableMapping[str, Any]:
    """Update an existing customer identified by ``customer_id``."""

    if not data:
        raise ValueError("No se proporcionaron datos para actualizar")

    actor, actor_id = _get_actor_context()
    return customer_repository.update_customer(
        customer_id,
        data,
        actor=actor,
        actor_id=actor_id,
    )


def deactivate_customer(customer_id: int) -> MutableMapping[str, Any]:
    """Mark a customer as inactive."""

    actor, actor_id = _get_actor_context()
    return customer_repository.update_customer(
        customer_id,
        {"status": INACTIVE_STATUS},
        actor=actor,
        actor_id=actor_id,
    )


def get_financial_summary(
    customer_id: int,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
) -> Mapping[str, Any]:
    """Return aggregate financial information for the provided customer."""

    with connection_scope() as connection:
        orders_summary = _fetch_orders_summary(
            connection,
            customer_id,
            date_from=date_from,
            date_to=date_to,
        )
        payments_summary = _fetch_payments_summary(
            connection,
            customer_id,
            date_from=date_from,
            date_to=date_to,
        )

    outstanding = max(
        Decimal("0"),
        orders_summary["total_amount"] - payments_summary["total_paid"],
        orders_summary["balance_due"],
    )

    return {
        "orders": {
            "count": orders_summary["count"],
            "totalAmount": float(orders_summary["total_amount"]),
            "balanceDue": float(orders_summary["balance_due"]),
        },
        "payments": {
            "count": payments_summary["count"],
            "totalPaid": float(payments_summary["total_paid"]),
        },
        "outstandingBalance": float(outstanding),
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_actor_context() -> tuple[str, Optional[int]]:
    session = get_current_session()
    if session:
        return session.actor, session.user_id
    return "sistema", None


def _fetch_orders_summary(
    connection: MySQLConnection,
    customer_id: int,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
) -> Mapping[str, Decimal | int]:
    if not _table_exists(connection, "orders"):
        return {
            "count": 0,
            "total_amount": Decimal("0"),
            "balance_due": Decimal("0"),
        }

    amount_column = _first_existing_column(
        connection,
        "orders",
        ("total_amount", "grand_total", "total", "amount"),
    )
    balance_column = _first_existing_column(
        connection,
        "orders",
        ("balance_due", "outstanding_balance", "pending_amount"),
    )
    date_column = _first_existing_column(
        connection,
        "orders",
        ("created_at", "ordered_at", "date"),
    )

    select_parts: list[str] = ["COUNT(*) AS count"]
    if amount_column:
        select_parts.append(f"COALESCE(SUM({amount_column}), 0) AS total_amount")
    else:
        select_parts.append("0 AS total_amount")
    if balance_column:
        select_parts.append(f"COALESCE(SUM({balance_column}), 0) AS balance_due")
    else:
        select_parts.append("0 AS balance_due")

    where_clauses = ["customer_id = %s"]
    params: list[Any] = [customer_id]
    if date_column:
        if date_from:
            where_clauses.append(f"{date_column} >= %s")
            params.append(date_from)
        if date_to:
            where_clauses.append(f"{date_column} <= %s")
            params.append(date_to)

    query = (
        f"SELECT {', '.join(select_parts)} FROM orders WHERE {' AND '.join(where_clauses)}"
    )

    with closing(connection.cursor(dictionary=True)) as cursor:
        cursor.execute(query, tuple(params))
        row = cursor.fetchone() or {}

    return {
        "count": int(row.get("count", 0)),
        "total_amount": _as_decimal(row.get("total_amount")),
        "balance_due": _as_decimal(row.get("balance_due")),
    }


def _fetch_payments_summary(
    connection: MySQLConnection,
    customer_id: int,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
) -> Mapping[str, Decimal | int]:
    if not _table_exists(connection, "payments"):
        return {"count": 0, "total_paid": Decimal("0")}

    date_column = _first_existing_column(
        connection,
        "payments",
        ("paid_at", "payment_date", "created_at", "date"),
    )
    amount_column = _first_existing_column(
        connection,
        "payments",
        ("amount", "total", "value"),
    )

    where_clauses: list[str] = []
    params: list[Any] = []
    join_clause = ""

    if _column_exists(connection, "payments", "customer_id"):
        where_clauses.append("p.customer_id = %s")
        params.append(customer_id)
    elif _column_exists(connection, "payments", "order_id") and _table_exists(
        connection, "orders"
    ):
        join_clause = "JOIN orders o ON o.id = p.order_id"
        where_clauses.append("o.customer_id = %s")
        params.append(customer_id)
    else:
        return {"count": 0, "total_paid": Decimal("0")}

    if date_column:
        if date_from:
            where_clauses.append(f"p.{date_column} >= %s")
            params.append(date_from)
        if date_to:
            where_clauses.append(f"p.{date_column} <= %s")
            params.append(date_to)

    amount_expr = f"p.{amount_column}" if amount_column else "0"
    query = (
        "SELECT COUNT(*) AS count, "
        f"COALESCE(SUM({amount_expr}), 0) AS total_paid "
        "FROM payments p "
        f"{join_clause} "
        f"WHERE {' AND '.join(where_clauses)}"
    )

    with closing(connection.cursor(dictionary=True)) as cursor:
        cursor.execute(query, tuple(params))
        row = cursor.fetchone() or {}

    return {
        "count": int(row.get("count", 0)),
        "total_paid": _as_decimal(row.get("total_paid")),
    }


def _table_exists(connection: MySQLConnection, table_name: str) -> bool:
    query = (
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema = DATABASE() AND table_name = %s"
    )
    with closing(connection.cursor()) as cursor:
        cursor.execute(query, (table_name,))
        count = cursor.fetchone()
        return bool(count and count[0])


def _column_exists(
    connection: MySQLConnection, table_name: str, column_name: str
) -> bool:
    query = (
        "SELECT COUNT(*) FROM information_schema.columns "
        "WHERE table_schema = DATABASE() AND table_name = %s AND column_name = %s"
    )
    with closing(connection.cursor()) as cursor:
        cursor.execute(query, (table_name, column_name))
        count = cursor.fetchone()
        return bool(count and count[0])


def _first_existing_column(
    connection: MySQLConnection,
    table_name: str,
    candidates: Sequence[str],
) -> str | None:
    for column in candidates:
        if _column_exists(connection, table_name, column):
            return column
    return None


def _as_decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if value is None:
        return Decimal("0")
    try:
        return Decimal(str(value))
    except Exception:  # pragma: no cover - conversión defensiva
        LOGGER.debug("No se pudo convertir %s a Decimal", value, exc_info=True)
        return Decimal("0")
