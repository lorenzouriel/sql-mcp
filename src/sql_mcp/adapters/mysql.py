import asyncio
import logging
from typing import Any
from urllib.parse import urlparse

from .base import DatabaseAdapter

logger = logging.getLogger(__name__)

try:
    import mysql.connector
except ImportError:
    mysql = None  # type: ignore[assignment]


def _parse_mysql_dsn(dsn: str) -> dict[str, Any]:
    u = urlparse(dsn)
    kwargs: dict[str, Any] = {}
    if u.hostname:
        kwargs["host"] = u.hostname
    if u.port:
        kwargs["port"] = u.port
    if u.username:
        kwargs["user"] = u.username
    if u.password:
        kwargs["password"] = u.password
    if u.path and u.path.lstrip("/"):
        kwargs["database"] = u.path.lstrip("/")
    return kwargs


class MySQLAdapter(DatabaseAdapter):

    def __init__(self) -> None:
        self._conn: Any = None

    @property
    def engine_name(self) -> str:
        return "mysql"

    async def connect(self, dsn: str) -> None:
        if mysql is None:
            raise ImportError(
                "mysql-connector-python is required for MySQL. "
                "Install with: pip install sql-mcp[mysql]"
            )

        def _connect() -> Any:
            return mysql.connector.connect(
                **_parse_mysql_dsn(dsn),
                autocommit=True,
                connection_timeout=30,
            )

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
            cursor = self._conn.cursor(dictionary=True)
            try:
                cursor.execute(f"SET SESSION MAX_EXECUTION_TIME={timeout * 1000}")
                cursor.execute(sql)
                if not cursor.description:
                    return []
                rows: list[dict[str, Any]] = []
                while True:
                    batch = cursor.fetchmany(1000)
                    if not batch:
                        break
                    rows.extend(batch)
                    if len(rows) >= max_rows:
                        return rows[:max_rows]
                return rows
            except Exception as e:
                logger.exception("MySQL query error")
                raise RuntimeError(f"Query failed: {e}") from e
            finally:
                cursor.close()

        return await asyncio.to_thread(_execute)

    async def list_schemas(self) -> list[str]:
        result = await self.execute_query(
            "SELECT schema_name FROM information_schema.schemata "
            "WHERE schema_name NOT IN "
            "('mysql', 'information_schema', 'performance_schema', 'sys') "
            "ORDER BY schema_name",
            timeout=10,
            max_rows=1000,
        )
        # MySQL returns information_schema column names in uppercase
        return [r.get("SCHEMA_NAME") or r.get("schema_name") for r in result]

    async def list_tables(
        self,
        schema: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        where = "WHERE table_type = 'BASE TABLE'"
        if schema:
            where += f" AND table_schema = '{schema.replace(chr(39), chr(39) * 2)}'"
        rows = await self.execute_query(
            f"SELECT table_schema AS schema_name, table_name, table_rows AS row_count "
            f"FROM information_schema.tables {where} "
            f"ORDER BY table_schema, table_name LIMIT {limit}",
            timeout=30,
            max_rows=limit,
        )
        # MySQL returns information_schema aliases in uppercase; normalize to lowercase
        return [{k.lower(): v for k, v in row.items()} for row in rows]

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
        # MySQL returns aliases in uppercase; normalize to uppercase for consistency
        return [{k.upper(): v for k, v in row.items()} for row in rows]

    async def get_database_info(self) -> dict[str, Any]:
        result = await self.execute_query(
            "SELECT DATABASE() AS database_name, VERSION() AS version",
            timeout=10,
            max_rows=1,
        )
        info = dict(result[0]) if result else {}
        info["engine"] = "mysql"
        return info

    async def check_connection(self) -> bool:
        try:
            result = await self.execute_query("SELECT 1 AS test", timeout=5, max_rows=1)
            return len(result) > 0
        except Exception:
            return False
