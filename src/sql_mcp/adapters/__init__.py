from .base import DatabaseAdapter
from .mssql import MSSQLAdapter
from .postgres import PostgresAdapter
from .mysql import MySQLAdapter
from .sqlite import SQLiteAdapter

try:
    from .mongodb import MongoDBAdapter
except ImportError:
    MongoDBAdapter = None  # type: ignore[assignment,misc]

try:
    from .databricks import DatabricksAdapter
except ImportError:
    DatabricksAdapter = None  # type: ignore[assignment,misc]

try:
    from .fabric import FabricAdapter
except ImportError:
    FabricAdapter = None  # type: ignore[assignment,misc]


ADAPTERS: dict[str, type[DatabaseAdapter]] = {
    "mssql":   MSSQLAdapter,
    "postgres": PostgresAdapter,
    "mysql":   MySQLAdapter,
    "mariadb": MySQLAdapter,
    "sqlite":  SQLiteAdapter,
}

if MongoDBAdapter is not None:
    ADAPTERS["mongodb"] = MongoDBAdapter

if DatabricksAdapter is not None:
    ADAPTERS["databricks"] = DatabricksAdapter

if FabricAdapter is not None:
    ADAPTERS["fabric"] = FabricAdapter


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
