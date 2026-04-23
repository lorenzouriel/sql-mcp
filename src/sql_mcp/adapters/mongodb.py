import asyncio
import json
import logging
from typing import Any
from urllib.parse import urlparse

from .base import DatabaseAdapter

logger = logging.getLogger(__name__)

try:
    import pymongo
    from pymongo import MongoClient
except ImportError:
    pymongo = None  # type: ignore[assignment]

_TYPE_MAP: dict[type, str] = {
    str: "VARCHAR",
    int: "INTEGER",
    float: "FLOAT",
    bool: "BOOLEAN",
    dict: "OBJECT",
    list: "ARRAY",
    bytes: "BINARY",
}


def _infer_type(value: Any) -> str:
    return _TYPE_MAP.get(type(value), "VARCHAR")


class MongoDBAdapter(DatabaseAdapter):

    def __init__(self) -> None:
        self._client: Any = None
        self._db: Any = None
        self._db_name: str = ""

    @property
    def engine_name(self) -> str:
        return "mongodb"

    @property
    def query_language(self) -> str:
        return "mql"

    @property
    def supports_sql(self) -> bool:
        return False

    async def connect(self, dsn: str) -> None:
        if pymongo is None:
            raise ImportError(
                "pymongo is required for MongoDB. "
                "Install with: pip install sql-mcp[mongodb]"
            )

        def _connect() -> tuple[Any, Any, str]:
            client = MongoClient(dsn, serverSelectionTimeoutMS=5000)
            parsed = urlparse(dsn)
            db_name = parsed.path.lstrip("/") or "test"
            db = client[db_name]
            client.server_info()  # trigger connection to validate credentials early
            return client, db, db_name

        self._client, self._db, self._db_name = await asyncio.to_thread(_connect)

    async def disconnect(self) -> None:
        if self._client is not None:
            await asyncio.to_thread(self._client.close)
            self._client = None
            self._db = None

    async def execute_query(
        self,
        sql: str,
        timeout: int = 30,
        max_rows: int = 50_000,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError(
            "MongoDB does not support SQL. "
            "Use execute_native_query() with an MQL filter (dict) or aggregation pipeline (list)."
        )

    async def execute_native_query(
        self,
        query: str,
        collection: str,
        timeout: int = 30,
        max_rows: int = 50_000,
    ) -> list[dict[str, Any]]:
        def _execute() -> list[dict[str, Any]]:
            try:
                parsed = json.loads(query)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid MQL query (must be valid JSON): {e}") from e

            coll = self._db[collection]

            if isinstance(parsed, list):
                cursor = coll.aggregate(parsed, maxTimeMS=timeout * 1000)
            elif isinstance(parsed, dict):
                cursor = coll.find(parsed, limit=max_rows).max_time_ms(timeout * 1000)
            else:
                raise ValueError("MQL query must be a JSON object (filter) or array (pipeline)")

            rows: list[dict[str, Any]] = []
            for doc in cursor:
                doc.pop("_id", None)
                rows.append(doc)
                if len(rows) >= max_rows:
                    break
            return rows

        return await asyncio.to_thread(_execute)

    async def list_schemas(self) -> list[str]:
        def _list() -> list[str]:
            return sorted(
                db for db in self._client.list_database_names()
                if db not in ("admin", "local", "config")
            )
        return await asyncio.to_thread(_list)

    async def list_tables(
        self,
        schema: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        def _list() -> list[dict[str, Any]]:
            db = self._client[schema] if schema else self._db
            db_name = schema or self._db_name
            collections = sorted(db.list_collection_names())[:limit]
            return [
                {"schema_name": db_name, "table_name": c, "row_count": None}
                for c in collections
            ]
        return await asyncio.to_thread(_list)

    async def schema_discovery(
        self,
        schema: str | None = None,
    ) -> list[dict[str, Any]]:
        def _discover() -> list[dict[str, Any]]:
            db = self._client[schema] if schema else self._db
            db_name = schema or self._db_name
            results: list[dict[str, Any]] = []
            for coll_name in sorted(db.list_collection_names()):
                coll = db[coll_name]
                field_types: dict[str, str] = {}
                for doc in coll.find().limit(100):
                    doc.pop("_id", None)
                    for key, val in doc.items():
                        if key not in field_types:
                            field_types[key] = _infer_type(val)
                for field, dtype in sorted(field_types.items()):
                    results.append({
                        "TABLE_SCHEMA": db_name,
                        "TABLE_NAME": coll_name,
                        "COLUMN_NAME": field,
                        "DATA_TYPE": dtype,
                        "CHARACTER_MAXIMUM_LENGTH": None,
                        "IS_NULLABLE": None,
                        "COLUMN_DEFAULT": None,
                    })
            return results

        return await asyncio.to_thread(_discover)

    async def get_database_info(self) -> dict[str, Any]:
        def _info() -> dict[str, Any]:
            info = self._client.server_info()
            return {
                "engine": "mongodb",
                "database_name": self._db_name,
                "version": info.get("version", "unknown"),
                "query_language": "mql",
            }
        return await asyncio.to_thread(_info)

    async def check_connection(self) -> bool:
        try:
            await asyncio.to_thread(self._client.server_info)
            return True
        except Exception:
            return False
