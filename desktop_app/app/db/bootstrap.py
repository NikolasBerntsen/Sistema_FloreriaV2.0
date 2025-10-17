"""Helpers to initialise and verify the MySQL schema at runtime."""

from __future__ import annotations

import logging
from contextlib import closing
from pathlib import Path
from typing import Iterable, List, Sequence

from mysql.connector.connection import MySQLConnection
from mysql.connector.cursor import MySQLCursor

__all__ = [
    "SCHEMA_TABLES",
    "EXTENSION_TABLES",
    "SCHEMA_FILE",
    "EXTENSION_FILE",
    "database_exists",
    "missing_tables",
    "ensure_tables",
    "initialize_database",
]


ROOT_DIR = Path(__file__).resolve().parents[3]
SQL_DIR = ROOT_DIR / "db"
SCHEMA_FILE = SQL_DIR / "schema.sql"
EXTENSION_FILE = SQL_DIR / "extension.sql"

SCHEMA_TABLES: Sequence[str] = (
    "roles",
    "users",
    "payment_methods",
    "logistic_statuses",
    "product_categories",
    "products",
    "customers",
    "customer_addresses",
    "orders",
    "order_items",
    "payments",
    "shipments",
    "shipment_status_history",
    "audit_log",
)

EXTENSION_TABLES: Sequence[str] = (
    "inventory_movements",
    "inventory_levels",
    "product_price_history",
    "lost_orders",
)


def database_exists(connection: MySQLConnection, schema_name: str) -> bool:
    """Return ``True`` when the provided schema exists."""

    query = "SELECT 1 FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s"
    with closing(connection.cursor()) as cursor:
        cursor.execute(query, (schema_name,))
        return cursor.fetchone() is not None


def missing_tables(
    connection: MySQLConnection, schema_name: str, tables: Iterable[str]
) -> List[str]:
    """Return the subset of ``tables`` that are missing in ``schema_name``."""

    if not database_exists(connection, schema_name):
        return list(tables)

    missing: List[str] = []
    query = (
        "SELECT 1 FROM INFORMATION_SCHEMA.TABLES "
        "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s LIMIT 1"
    )
    for table in tables:
        with closing(connection.cursor()) as cursor:
            cursor.execute(query, (schema_name, table))
            if cursor.fetchone() is None:
                missing.append(table)
    return missing


def _execute_sql_file(
    connection: MySQLConnection, path: Path, logger: logging.Logger
) -> None:
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo SQL: {path}")

    sql = path.read_text(encoding="utf-8")
    cursor: MySQLCursor = connection.cursor()
    try:
        for _ in cursor.execute(sql, multi=True):
            pass
        connection.commit()
    except Exception:
        connection.rollback()
        logger.exception("Error al ejecutar %s", path)
        raise
    finally:
        cursor.close()


def ensure_tables(
    connection: MySQLConnection,
    schema_name: str,
    tables: Sequence[str],
    sql_file: Path,
    *,
    logger: logging.Logger | None = None,
    dry_run: bool = False,
) -> bool:
    """Ensure the tables listed in ``tables`` exist in ``schema_name``.

    Returns ``True`` when the SQL file had to be executed.
    """

    logger = logger or logging.getLogger("app.db.bootstrap")

    missing = missing_tables(connection, schema_name, tables)
    if not missing:
        logger.info("Las tablas %s ya existen", sql_file.name)
        return False

    logger.info("Tablas faltantes (%s): %s", sql_file.name, ", ".join(missing))
    if dry_run:
        logger.info("Ejecución en modo dry-run, se omite la carga de %s", sql_file)
        return False

    _execute_sql_file(connection, sql_file, logger)

    missing_after = missing_tables(connection, schema_name, tables)
    if missing_after:
        raise RuntimeError(
            "Las tablas siguen faltando luego de ejecutar "
            f"{sql_file.name}: {', '.join(missing_after)}"
        )

    return True


def initialize_database(
    connection: MySQLConnection,
    schema_name: str,
    *,
    include_extension: bool = True,
    logger: logging.Logger | None = None,
) -> bool:
    """Ensure that the base schema (and optional extension) exist."""

    logger = logger or logging.getLogger("app.db.bootstrap")
    changed = ensure_tables(
        connection,
        schema_name,
        SCHEMA_TABLES,
        SCHEMA_FILE,
        logger=logger,
    )

    if include_extension:
        changed = (
            ensure_tables(
                connection,
                schema_name,
                EXTENSION_TABLES,
                EXTENSION_FILE,
                logger=logger,
            )
            or changed
        )

    return changed

