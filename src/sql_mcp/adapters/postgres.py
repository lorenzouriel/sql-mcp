import asyncio
import logging
from typing import Any

from .base import DatabaseAdapter

logger = logging.getLogger(__name__)

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    psycopg2 = None  # type: ignore[assignment]


class PostgresAdapter(DatabaseAdapter):

    def __init__(self) -> None:
        self._conn: Any = None

    @property
    def engine_name(self) -> str:
        return "postgres"

    async def connect(self, dsn: str) -> None:
        if psycopg2 is None:
            raise ImportError(
                "psycopg2 is required for PostgreSQL. "
                "Install with: pip install sql-mcp[postgres]"
            )

        def _connect() -> Any:
            conn = psycopg2.connect(dsn)
            conn.autocommit = True
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
            cursor = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            try:
                cursor.execute(f"SET statement_timeout = {timeout * 1000}")
                cursor.execute(sql)
                if not cursor.description:
                    return []
                rows: list[dict[str, Any]] = []
                while True:
                    batch = cursor.fetchmany(1000)
                    if not batch:
                        break
                    rows.extend(dict(r) for r in batch)
                    if len(rows) >= max_rows:
                        return rows[:max_rows]
                return rows
            except Exception as e:
                logger.exception("Postgres query error")
                raise RuntimeError(f"Query failed: {e}") from e
            finally:
                cursor.close()

        return await asyncio.to_thread(_execute)

    async def list_schemas(self) -> list[str]:
        result = await self.execute_query(
            "SELECT schema_name FROM information_schema.schemata "
            "WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast') "
            "ORDER BY schema_name",
            timeout=10,
            max_rows=1000,
        )
        return [r["schema_name"] for r in result]

    async def list_tables(
        self,
        schema: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        where = "WHERE table_type = 'BASE TABLE'"
        if schema:
            where += f" AND table_schema = '{schema.replace(chr(39), chr(39) * 2)}'"
        return await self.execute_query(
            f"SELECT table_schema AS schema_name, table_name, NULL AS row_count "
            f"FROM information_schema.tables {where} "
            f"ORDER BY table_schema, table_name LIMIT {limit}",
            timeout=30,
            max_rows=limit,
        )

    async def schema_discovery(
        self,
        schema: str | None = None,
    ) -> list[dict[str, Any]]:
        where = ""
        if schema:
            where = f"WHERE c.table_schema = '{schema.replace(chr(39), chr(39) * 2)}'"
        rows = await self.execute_query(
            f"SELECT c.table_schema AS TABLE_SCHEMA, c.table_name AS TABLE_NAME, "
            f"c.column_name AS COLUMN_NAME, c.data_type AS DATA_TYPE, "
            f"c.character_maximum_length AS CHARACTER_MAXIMUM_LENGTH, "
            f"c.is_nullable AS IS_NULLABLE, c.column_default AS COLUMN_DEFAULT "
            f"FROM information_schema.columns c {where} "
            f"ORDER BY c.table_name, c.ordinal_position",
            timeout=60,
            max_rows=10_000,
        )
        # psycopg2 RealDictCursor lowercases all aliases; normalize to uppercase
        return [{k.upper(): v for k, v in row.items()} for row in rows]

    async def get_database_info(self) -> dict[str, Any]:
        result = await self.execute_query(
            "SELECT current_database() AS database_name, version() AS version",
            timeout=10,
            max_rows=1,
        )
        info = dict(result[0]) if result else {}
        info["engine"] = "postgres"
        return info

    async def check_connection(self) -> bool:
        try:
            result = await self.execute_query("SELECT 1 AS test", timeout=5, max_rows=1)
            return len(result) > 0
        except Exception:
            return False
