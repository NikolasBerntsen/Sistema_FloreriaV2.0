from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
from math import ceil
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Optional, Sequence, Tuple

from mysql.connector.connection import MySQLConnection

__all__ = [
    "BaseRepository",
    "PaginatedResult",
]


@dataclass(frozen=True)
class PaginatedResult:
    """Container for paginated data and metadata."""

    data: Sequence[Mapping[str, Any]]
    meta: Mapping[str, int]


class BaseRepository:
    """Base CRUD repository with pagination support."""

    table_name: str
    columns: Tuple[str, ...]
    primary_key: str
    allowed_sort_fields: Tuple[str, ...]
    default_sort: Tuple[str, str]
    filterable_fields: Tuple[str, ...]
    searchable_fields: Tuple[str, ...]
    max_page_size: int

    def __init__(
        self,
        *,
        table_name: str,
        columns: Iterable[str],
        primary_key: str = "id",
        allowed_sort_fields: Optional[Iterable[str]] = None,
        default_sort: Tuple[str, str] = ("id", "ASC"),
        filterable_fields: Optional[Iterable[str]] = None,
        searchable_fields: Optional[Iterable[str]] = None,
        max_page_size: int = 100,
    ) -> None:
        self.table_name = table_name
        self.columns = tuple(columns)
        self.primary_key = primary_key
        allowed = set(allowed_sort_fields or [])
        if not allowed:
            allowed.update(self.columns)
            allowed.add(self.primary_key)
        allowed.add(default_sort[0])
        self.allowed_sort_fields = tuple(sorted(allowed))
        direction = default_sort[1].upper()
        if direction not in {"ASC", "DESC"}:
            raise ValueError("default_sort direction must be 'ASC' or 'DESC'")
        self.default_sort = (default_sort[0], direction)
        self.filterable_fields = tuple(sorted(set(filterable_fields or self.columns)))
        self.searchable_fields = tuple(sorted(set(searchable_fields or [])))
        self.max_page_size = max(1, max_page_size)

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------
    def create(self, connection: MySQLConnection, data: Mapping[str, Any]) -> int:
        allowed_data = self._prepare_data(data)
        if not allowed_data:
            raise ValueError("No hay campos válidos para insertar")

        columns = ", ".join(allowed_data.keys())
        placeholders = ", ".join(["%s"] * len(allowed_data))
        query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        values = list(allowed_data.values())

        with closing(connection.cursor()) as cursor:
            cursor.execute(query, values)
            return int(cursor.lastrowid)

    def get_by_id(
        self, connection: MySQLConnection, record_id: Any, *, for_update: bool = False
    ) -> Optional[Dict[str, Any]]:
        clause = "FOR UPDATE" if for_update else ""
        query = (
            f"SELECT * FROM {self.table_name} WHERE {self.primary_key} = %s {clause}".strip()
        )
        with closing(connection.cursor(dictionary=True)) as cursor:
            cursor.execute(query, (record_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update(
        self,
        connection: MySQLConnection,
        record_id: Any,
        data: Mapping[str, Any],
    ) -> int:
        allowed_data = self._prepare_data(data)
        if not allowed_data:
            raise ValueError("No hay campos válidos para actualizar")

        assignments = ", ".join(f"{column} = %s" for column in allowed_data)
        values = list(allowed_data.values()) + [record_id]
        query = f"UPDATE {self.table_name} SET {assignments} WHERE {self.primary_key} = %s"

        with closing(connection.cursor()) as cursor:
            cursor.execute(query, values)
            return cursor.rowcount

    def delete(self, connection: MySQLConnection, record_id: Any) -> int:
        query = f"DELETE FROM {self.table_name} WHERE {self.primary_key} = %s"
        with closing(connection.cursor()) as cursor:
            cursor.execute(query, (record_id,))
            return cursor.rowcount

    # ------------------------------------------------------------------
    # Listing helpers
    # ------------------------------------------------------------------
    def list_paginated(
        self,
        connection: MySQLConnection,
        *,
        page: int = 1,
        size: int = 20,
        sort: Optional[str] = None,
        filters: Optional[Mapping[str, Any]] = None,
        search: Optional[str] = None,
    ) -> PaginatedResult:
        page = max(1, page)
        size = max(1, min(size, self.max_page_size))
        sort_field, sort_direction = self._parse_sort(sort)

        where_clauses: list[str] = []
        params: list[Any] = []

        if filters:
            for field, value in filters.items():
                if field not in self.filterable_fields:
                    raise ValueError(f"Filtro no permitido: {field}")
                where_clauses.append(f"{field} = %s")
                params.append(value)

        if search and self.searchable_fields:
            like_pattern = f"%{search.strip()}%"
            search_clause = " OR ".join(f"{field} LIKE %s" for field in self.searchable_fields)
            where_clauses.append(f"({search_clause})")
            params.extend([like_pattern] * len(self.searchable_fields))

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        offset = (page - 1) * size
        order_clause = f"ORDER BY {sort_field} {sort_direction}"
        limit_clause = "LIMIT %s OFFSET %s"

        rows = self._fetch_rows(
            connection,
            query=(
                f"SELECT * FROM {self.table_name} "
                f"{where_sql} {order_clause} {limit_clause}".strip()
            ),
            params=(*params, size, offset),
        )

        total = self._count_rows(
            connection,
            query=f"SELECT COUNT(*) AS total FROM {self.table_name} {where_sql}".strip(),
            params=tuple(params),
        )

        meta = {
            "page": page,
            "size": size,
            "total": total,
            "totalPages": ceil(total / size) if total else 0,
        }
        return PaginatedResult(data=rows, meta=meta)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _prepare_data(self, data: Mapping[str, Any]) -> MutableMapping[str, Any]:
        allowed: MutableMapping[str, Any] = {}
        for key in self.columns:
            if key in data:
                allowed[key] = data[key]
        return allowed

    def _parse_sort(self, sort: Optional[str]) -> Tuple[str, str]:
        if sort:
            field_part, _, direction_part = sort.partition(",")
            field = field_part.strip()
            direction = direction_part.strip().upper() if direction_part else "ASC"
            if field not in self.allowed_sort_fields:
                raise ValueError(f"Ordenamiento no permitido: {field}")
            if direction not in {"ASC", "DESC"}:
                raise ValueError("La dirección de ordenamiento debe ser ASC o DESC")
            return field, direction
        return self.default_sort

    def _fetch_rows(
        self,
        connection: MySQLConnection,
        *,
        query: str,
        params: Sequence[Any],
    ) -> list[Dict[str, Any]]:
        with closing(connection.cursor(dictionary=True)) as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def _count_rows(
        self,
        connection: MySQLConnection,
        *,
        query: str,
        params: Sequence[Any],
    ) -> int:
        with closing(connection.cursor()) as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()
            if row is None:
                return 0
            if isinstance(row, Mapping):
                return int(row.get("total", 0))
            return int(row[0])
