from .base import DatabaseAdapter
from .mssql import MSSQLAdapter
from .postgres import PostgresAdapter
from .mysql import MySQLAdapter
from .sqlite import SQLiteAdapter

ADAPTERS: dict[str, type[DatabaseAdapter]] = {
    "mssql": MSSQLAdapter,
    "postgres": PostgresAdapter,
    "mysql": MySQLAdapter,
    "mariadb": MySQLAdapter,
    "sqlite": SQLiteAdapter,
}


def create_adapter(engine: str) -> DatabaseAdapter:
    cls = ADAPTERS.get(engine)
    if cls is None:
        supported = ", ".join(sorted(ADAPTERS.keys()))
        raise ValueError(f"Unsupported engine '{engine}'. Supported: {supported}")
    return cls()


__all__ = [
    "DatabaseAdapter",
    "MSSQLAdapter",
    "PostgresAdapter",
    "MySQLAdapter",
    "SQLiteAdapter",
    "ADAPTERS",
    "create_adapter",
]
