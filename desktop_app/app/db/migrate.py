"""Utility to ensure database schema is up to date.

The script verifies the presence of the core tables defined in
``db/schema.sql`` and the inventory/lost-orders extension in
``db/extension.sql``. Missing tables trigger the execution of the
corresponding SQL file, using MySQL multi-statements so the `CREATE
DATABASE` and `USE` commands are honoured.

Usage example::

    python -m app.db.migrate --user root --password secret \\
        --host 127.0.0.1 --database floreriadb
"""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path
from typing import Iterable, List

import mysql.connector
from mysql.connector.connection import MySQLConnection
from mysql.connector.cursor import MySQLCursor

ROOT_DIR = Path(__file__).resolve().parents[3]
SQL_DIR = ROOT_DIR / "db"
SCHEMA_FILE = SQL_DIR / "schema.sql"
EXTENSION_FILE = SQL_DIR / "extension.sql"

SCHEMA_TABLES: List[str] = [
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
]

EXTENSION_TABLES: List[str] = [
    "inventory_movements",
    "inventory_levels",
    "product_price_history",
    "lost_orders",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Execute pending database migrations")
    parser.add_argument("--host", default=os.getenv("DB_HOST", "127.0.0.1"), help="MySQL host")
    parser.add_argument("--port", type=int, default=int(os.getenv("DB_PORT", "3306")), help="MySQL port")
    parser.add_argument("--user", default=os.getenv("DB_USER", "root"), help="MySQL user")
    parser.add_argument("--password", default=os.getenv("DB_PASSWORD"), help="MySQL password")
    parser.add_argument(
        "--database",
        default=os.getenv("DB_NAME", "floreriadb"),
        help="Database/schema name to inspect",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not execute SQL files, only report missing tables",
    )
    return parser.parse_args()


def connect_mysql(args: argparse.Namespace) -> MySQLConnection:
    return mysql.connector.connect(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        autocommit=False,
        use_pure=True,
    )


def database_exists(connection: MySQLConnection, schema_name: str) -> bool:
    query = "SELECT 1 FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s"
    with connection.cursor() as cursor:
        cursor.execute(query, (schema_name,))
        return cursor.fetchone() is not None


def table_exists(connection: MySQLConnection, schema_name: str, table_name: str) -> bool:
    query = (
        "SELECT 1 FROM INFORMATION_SCHEMA.TABLES "
        "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s LIMIT 1"
    )
    with connection.cursor() as cursor:
        cursor.execute(query, (schema_name, table_name))
        return cursor.fetchone() is not None


def missing_tables(connection: MySQLConnection, schema_name: str, tables: Iterable[str]) -> List[str]:
    if not database_exists(connection, schema_name):
        return list(tables)
    return [table for table in tables if not table_exists(connection, schema_name, table)]


def execute_sql_file(connection: MySQLConnection, path: Path, logger: logging.Logger) -> None:
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo SQL: {path}")

    sql = path.read_text(encoding="utf-8")
    logger.info("Ejecutando %s", path)
    cursor: MySQLCursor = connection.cursor()
    try:
        for _ in cursor.execute(sql, multi=True):
            pass
        connection.commit()
    except mysql.connector.Error:
        connection.rollback()
        logger.exception("Error al ejecutar %s", path)
        raise
    finally:
        cursor.close()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logger = logging.getLogger("migrate")

    if not SCHEMA_FILE.exists() or not EXTENSION_FILE.exists():
        raise FileNotFoundError("Los archivos schema.sql y extension.sql deben existir en el directorio db/")

    connection = connect_mysql(args)
    schema_name = args.database

    try:
        missing_core = missing_tables(connection, schema_name, SCHEMA_TABLES)
        if missing_core:
            logger.info("Tablas base faltantes: %s", ", ".join(missing_core))
            if args.dry_run:
                logger.info("Ejecución en modo dry-run, se omite la carga de %s", SCHEMA_FILE)
            else:
                execute_sql_file(connection, SCHEMA_FILE, logger)
                missing_core = missing_tables(connection, schema_name, SCHEMA_TABLES)
                if missing_core:
                    raise RuntimeError(
                        "Las tablas base siguen faltando luego de ejecutar schema.sql: "
                        + ", ".join(missing_core)
                    )
        else:
            logger.info("Las tablas base ya existen, no se ejecuta schema.sql")

        missing_ext = missing_tables(connection, schema_name, EXTENSION_TABLES)
        if missing_ext:
            logger.info("Tablas de extensión faltantes: %s", ", ".join(missing_ext))
            if args.dry_run:
                logger.info("Ejecución en modo dry-run, se omite la carga de %s", EXTENSION_FILE)
            else:
                execute_sql_file(connection, EXTENSION_FILE, logger)
                missing_ext = missing_tables(connection, schema_name, EXTENSION_TABLES)
                if missing_ext:
                    raise RuntimeError(
                        "Las tablas de extensión siguen faltando luego de ejecutar extension.sql: "
                        + ", ".join(missing_ext)
                    )
        else:
            logger.info("Las tablas de extensión ya existen, no se ejecuta extension.sql")

        if not missing_core and not missing_ext:
            logger.info("La base de datos ya estaba actualizada. No se realizaron cambios.")
        else:
            logger.info("Migración completada correctamente.")
    finally:
        connection.close()


if __name__ == "__main__":
    main()

