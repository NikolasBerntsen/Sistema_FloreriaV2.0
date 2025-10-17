"""Helpers to initialise and verify the MySQL schema at runtime."""

from __future__ import annotations

import logging
import re
from contextlib import closing
from pathlib import Path
from typing import Iterable, List, Mapping, MutableMapping, Sequence, Set

from mysql.connector import Error as MySQLError
from mysql.connector.connection import MySQLConnection
from mysql.connector.cursor import MySQLCursor

__all__ = [
    "SCHEMA_TABLES",
    "EXTENSION_TABLES",
    "SCHEMA_FILE",
    "EXTENSION_FILE",
    "SEED_FILE",
    "database_exists",
    "missing_tables",
    "ensure_tables",
    "ensure_seed_data",
    "initialize_database",
]


ROOT_DIR = Path(__file__).resolve().parents[3]
SQL_DIR = ROOT_DIR / "db"
SCHEMA_FILE = SQL_DIR / "schema.sql"
EXTENSION_FILE = SQL_DIR / "extension.sql"
SEED_FILE = SQL_DIR / "seed.sql"

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


SeedRequirement = Mapping[str, Set[str]]

SEED_REQUIREMENTS: Mapping[str, SeedRequirement] = {
    "roles": {"name": {"ADMIN", "SALES", "LOGISTICS"}},
    "payment_methods": {
        "code": {"CASH", "CARD", "BANK_TRANSFER", "MOBILE_WALLET"}
    },
    "logistic_statuses": {
        "code": {
            "PENDING_PICKUP",
            "IN_TRANSIT",
            "DELIVERED",
            "RETURNED",
            "CANCELLED",
        }
    },
}


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


def _split_sql_statements(sql: str) -> List[str]:
    """Split ``sql`` into individual statements handling comments and quotes."""

    statements: List[str] = []
    statement: List[str] = []
    in_single_quote = False
    in_double_quote = False
    in_backtick = False
    in_line_comment = False
    in_block_comment = False

    i = 0
    length = len(sql)
    while i < length:
        char = sql[i]
        next_char = sql[i + 1] if i + 1 < length else ""

        if in_line_comment:
            if char == "\n":
                in_line_comment = False
            i += 1
            continue

        if in_block_comment:
            if char == "*" and next_char == "/":
                in_block_comment = False
                i += 2
            else:
                i += 1
            continue

        if not (in_single_quote or in_double_quote or in_backtick):
            if char == "-" and next_char == "-":
                in_line_comment = True
                i += 2
                continue
            if char == "#":
                in_line_comment = True
                i += 1
                continue
            if char == "/" and next_char == "*":
                in_block_comment = True
                i += 2
                continue

        if char == "'" and not (in_double_quote or in_backtick):
            in_single_quote = not in_single_quote
        elif char == '"' and not (in_single_quote or in_backtick):
            in_double_quote = not in_double_quote
        elif char == "`" and not (in_single_quote or in_double_quote):
            in_backtick = not in_backtick

        if char == ";" and not (
            in_single_quote or in_double_quote or in_backtick
        ):
            joined = "".join(statement).strip()
            if joined:
                statements.append(joined)
            statement = []
        else:
            statement.append(char)
        i += 1

    trailing = "".join(statement).strip()
    if trailing:
        statements.append(trailing)

    return statements


def _quote_identifier(identifier: str) -> str:
    """Return ``identifier`` quoted for MySQL statements."""

    escaped = identifier.replace("`", "``")
    return f"`{escaped}`"


def _ensure_database(connection: MySQLConnection, schema_name: str) -> None:
    """Create ``schema_name`` if it does not already exist."""

    schema_literal = _quote_identifier(schema_name)
    with closing(connection.cursor()) as cursor:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {schema_literal}")
    connection.commit()
    if connection.database != schema_name:
        connection.database = schema_name


def _execute_sql_file(
    connection: MySQLConnection,
    path: Path,
    logger: logging.Logger,
    *,
    schema_name: str,
) -> None:
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo SQL: {path}")

    sql = path.read_text(encoding="utf-8")
    statements = _split_sql_statements(sql)

    cursor: MySQLCursor = connection.cursor()
    schema_literal = _quote_identifier(schema_name)

    try:
        for statement in statements:
            normalized = statement.strip().lower()

            if normalized.startswith("use "):
                cursor.execute(f"USE {schema_literal}")
                continue

            if normalized.startswith("create database"):
                cursor.execute(
                    re.sub(
                        r"(?i)create\s+database\s+(if\s+not\s+exists\s+)?`?[^`\s]+`?",
                        f"CREATE DATABASE IF NOT EXISTS {schema_literal}",
                        statement,
                        count=1,
                    )
                )
                continue

            patched_statement = re.sub(
                r"`?floreriadb`?",
                schema_literal,
                statement,
                flags=re.IGNORECASE,
            )
            try:
                cursor.execute(patched_statement)
            except MySQLError as exc:
                if exc.errno == 1061:
                    logger.info(
                        "Índice duplicado detectado al ejecutar %s: %s. Se omite.",
                        path.name,
                        exc.msg,
                    )
                    continue
                raise
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

    _ensure_database(connection, schema_name)
    _execute_sql_file(connection, sql_file, logger, schema_name=schema_name)

    missing_after = missing_tables(connection, schema_name, tables)
    if missing_after:
        raise RuntimeError(
            "Las tablas siguen faltando luego de ejecutar "
            f"{sql_file.name}: {', '.join(missing_after)}"
        )

    return True


def _missing_seed_values(
    connection: MySQLConnection,
    requirements: Mapping[str, SeedRequirement],
) -> MutableMapping[str, Set[str]]:
    missing: MutableMapping[str, Set[str]] = {}
    for table, columns in requirements.items():
        for column, expected_values in columns.items():
            if not expected_values:
                continue
            placeholders = ", ".join(["%s"] * len(expected_values))
            column_literal = _quote_identifier(column)
            query = (
                f"SELECT {column_literal} FROM {_quote_identifier(table)} "
                f"WHERE {column_literal} IN ({placeholders})"
            )
            with closing(connection.cursor()) as cursor:
                cursor.execute(query, tuple(sorted(expected_values)))
                present = {row[0] for row in cursor.fetchall()}
            missing_values = set(expected_values) - present
            if missing_values:
                missing.setdefault(table, set()).update(missing_values)
    return missing


def ensure_seed_data(
    connection: MySQLConnection,
    schema_name: str,
    *,
    logger: logging.Logger | None = None,
) -> bool:
    """Ensure reference data exists by executing ``seed.sql`` when required."""

    logger = logger or logging.getLogger("app.db.bootstrap")
    _ensure_database(connection, schema_name)

    missing_values = _missing_seed_values(connection, SEED_REQUIREMENTS)
    if not missing_values:
        logger.info("Los datos de referencia ya existen. Se omite seed.sql")
        return False

    logger.info(
        "Datos de referencia faltantes: %s",
        ", ".join(
            f"{table}:{sorted(values)}" for table, values in sorted(missing_values.items())
        ),
    )

    _execute_sql_file(connection, SEED_FILE, logger, schema_name=schema_name)

    missing_after = _missing_seed_values(connection, SEED_REQUIREMENTS)
    if missing_after:
        raise RuntimeError(
            "Persisten datos de referencia faltantes luego de ejecutar seed.sql: "
            + ", ".join(
                f"{table}:{sorted(values)}"
                for table, values in sorted(missing_after.items())
            )
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

    seed_changed = ensure_seed_data(connection, schema_name, logger=logger)

    return changed or seed_changed

