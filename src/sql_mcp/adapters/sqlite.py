import asyncio
import sqlite3
import logging
from typing import Any

from .base import DatabaseAdapter

logger = logging.getLogger(__name__)


class SQLiteAdapter(DatabaseAdapter):

    def __init__(self) -> None:
        self._conn: sqlite3.Connection | None = None
        self._dsn: str = ""

    @property
    def engine_name(self) -> str:
        return "sqlite"

    async def connect(self, dsn: str) -> None:
        self._dsn = dsn

        def _connect() -> sqlite3.Connection:
            conn = sqlite3.connect(dsn, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn

        self._conn = await asyncio.to_thread(_connect)

    async def disconnect(self) -> None:
        if self._conn is not None:
            await asyncio.to_thread(self._conn.close)
            self._conn = None

    async def execute_query(
        self,
        sql: str,
        timeout: int = 30,
        max_rows: int = 50_000,
    ) -> list[dict[str, Any]]:
        def _execute() -> list[dict[str, Any]]:
            assert self._conn is not None
            self._conn.execute(f"PRAGMA busy_timeout = {timeout * 1000}")
            cursor = self._conn.cursor()
            try:
                cursor.execute(sql)
                if not cursor.description:
                    self._conn.commit()
                    return []
                cols = [d[0] for d in cursor.description]
                rows: list[dict[str, Any]] = []
                while True:
                    batch = cursor.fetchmany(1000)
                    if not batch:
                        break
                    rows.extend(dict(zip(cols, row)) for row in batch)
                    if len(rows) >= max_rows:
                        return rows[:max_rows]
                return rows
            except Exception as e:
                logger.exception("SQLite query error")
                raise RuntimeError(f"Query failed: {e}") from e
            finally:
                cursor.close()

        return await asyncio.to_thread(_execute)

    async def list_schemas(self) -> list[str]:
        return ["main"]

    async def list_tables(
        self,
        schema: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        return await self.execute_query(
            f"SELECT name AS table_name, 'main' AS schema_name, NULL AS row_count "
            f"FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' "
            f"ORDER BY name LIMIT {limit}",
            timeout=10,
            max_rows=limit,
        )

    async def schema_discovery(
        self,
        schema: str | None = None,
    ) -> list[dict[str, Any]]:
        tables = await self.list_tables(limit=500)
        result: list[dict[str, Any]] = []
        for t in tables:
            name = t["table_name"]
            cols = await self.execute_query(
                f"PRAGMA table_info('{name}')",
                timeout=10,
                max_rows=1000,
            )
            for c in cols:
                result.append({
                    "TABLE_SCHEMA": "main",
                    "TABLE_NAME": name,
                    "COLUMN_NAME": c.get("name"),
                    "DATA_TYPE": c.get("type"),
                    "CHARACTER_MAXIMUM_LENGTH": None,
                    "IS_NULLABLE": "NO" if c.get("notnull") else "YES",
                    "COLUMN_DEFAULT": c.get("dflt_value"),
                })
        return result

    async def get_database_info(self) -> dict[str, Any]:
        result = await self.execute_query(
            "SELECT sqlite_version() AS version",
            timeout=5,
            max_rows=1,
        )
        return {
            "engine": "sqlite",
            "database_name": self._dsn,
            "version": result[0]["version"] if result else "unknown",
        }

    async def check_connection(self) -> bool:
        try:
            result = await self.execute_query("SELECT 1 AS test", timeout=5, max_rows=1)
            return len(result) > 0
        except Exception:
            return False
