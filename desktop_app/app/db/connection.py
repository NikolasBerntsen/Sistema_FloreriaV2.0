from __future__ import annotations

import contextlib
from functools import wraps
from threading import Lock
from typing import Any, Callable, Generator, Optional, TypeVar

from mysql.connector.connection import MySQLConnection
from mysql.connector.pooling import MySQLConnectionPool

from app.utils.config_loader import DatabaseConfig, get_database_config, load_database_config

__all__ = [
    "get_pool",
    "init_pool",
    "connection_scope",
    "with_connection",
    "with_transaction",
]


_POOL: Optional[MySQLConnectionPool] = None
_POOL_LOCK = Lock()
_DEFAULT_POOL_NAME = "sistema_floreria_pool"
_DEFAULT_POOL_SIZE = 5

T = TypeVar("T")


def init_pool(
    *,
    config: Optional[DatabaseConfig] = None,
    pool_name: str = _DEFAULT_POOL_NAME,
    pool_size: int = _DEFAULT_POOL_SIZE,
    reset: bool = False,
) -> MySQLConnectionPool:
    """Initialise the global connection pool."""

    global _POOL

    with _POOL_LOCK:
        if _POOL is not None and not reset:
            return _POOL

        if config is None:
            config = load_database_config()

        pool_config: dict[str, Any] = {
            "pool_name": pool_name,
            "pool_size": pool_size,
            "pool_reset_session": True,
            "autocommit": False,
        }
        pool_config.update(config.as_dict())

        _POOL = MySQLConnectionPool(**pool_config)
        return _POOL


def get_pool() -> MySQLConnectionPool:
    """Return the global connection pool, creating it on demand."""

    if _POOL is None:
        init_pool(config=get_database_config())
    assert _POOL is not None  # for type-checkers
    return _POOL


@contextlib.contextmanager
def connection_scope() -> Generator[MySQLConnection, None, None]:
    """Context manager yielding a pooled MySQL connection."""

    connection = get_pool().get_connection()
    try:
        yield connection
    finally:
        connection.close()


def with_connection(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator that injects a pooled connection as ``connection`` kwarg."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        with connection_scope() as connection:
            kwargs["connection"] = connection
            return func(*args, **kwargs)

    return wrapper


def with_transaction(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator providing a connection and wrapping the call in a transaction."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        with connection_scope() as connection:
            kwargs["connection"] = connection
            try:
                result = func(*args, **kwargs)
                connection.commit()
                return result
            except Exception:
                connection.rollback()
                raise

    return wrapper
