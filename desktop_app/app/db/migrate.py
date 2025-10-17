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
from typing import List

import mysql.connector
from mysql.connector.connection import MySQLConnection

from .bootstrap import (
    EXTENSION_FILE,
    EXTENSION_TABLES,
    SCHEMA_FILE,
    SCHEMA_TABLES,
    ensure_tables,
    missing_tables,
)


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


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logger = logging.getLogger("migrate")

    if not SCHEMA_FILE.exists() or not EXTENSION_FILE.exists():
        raise FileNotFoundError("Los archivos schema.sql y extension.sql deben existir en el directorio db/")

    connection = connect_mysql(args)
    schema_name = args.database

    try:
        missing_core: List[str] = missing_tables(connection, schema_name, SCHEMA_TABLES)
        if missing_core:
            logger.info("Tablas base faltantes: %s", ", ".join(missing_core))
        core_applied = ensure_tables(
            connection,
            schema_name,
            SCHEMA_TABLES,
            SCHEMA_FILE,
            logger=logger,
            dry_run=args.dry_run,
        )
        if core_applied:
            logger.info("Se ejecutó %s para crear tablas base", SCHEMA_FILE)

        missing_ext: List[str] = missing_tables(connection, schema_name, EXTENSION_TABLES)
        if missing_ext:
            logger.info("Tablas de extensión faltantes: %s", ", ".join(missing_ext))
        ext_applied = ensure_tables(
            connection,
            schema_name,
            EXTENSION_TABLES,
            EXTENSION_FILE,
            logger=logger,
            dry_run=args.dry_run,
        )
        if ext_applied:
            logger.info("Se ejecutó %s para crear tablas de extensión", EXTENSION_FILE)

        remaining = missing_tables(connection, schema_name, SCHEMA_TABLES + EXTENSION_TABLES)
        if remaining:
            raise RuntimeError(
                "Persisten tablas faltantes luego de la migración: " + ", ".join(remaining)
            )

        if missing_core or missing_ext:
            if args.dry_run:
                logger.info("Ejecución en modo dry-run completada. No se aplicaron cambios.")
            else:
                logger.info("Migración completada correctamente.")
        else:
            logger.info("La base de datos ya estaba actualizada. No se realizaron cambios.")
    finally:
        connection.close()


if __name__ == "__main__":
    main()

