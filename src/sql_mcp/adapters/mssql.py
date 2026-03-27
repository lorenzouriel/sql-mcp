import asyncio
import logging
from typing import Any

from .base import DatabaseAdapter

logger = logging.getLogger(__name__)

try:
    import pyodbc
    pyodbc.pooling = True
except ImportError:
    pyodbc = None  # type: ignore[assignment]


class DatabaseError(Exception):
    pass


class QueryTimeoutError(DatabaseError):
    pass


class MSSQLAdapter(DatabaseAdapter):

    def __init__(self) -> None:
        self._conn: Any = None

    @property
    def engine_name(self) -> str:
        return "mssql"

    async def connect(self, dsn: str) -> None:
        if pyodbc is None:
            raise ImportError("pyodbc is required for MSSQL. Install with: pip install sql-mcp[mssql]")

        def _connect() -> Any:
            conn = pyodbc.connect(dsn, autocommit=False, timeout=30)
            conn.setencoding(encoding="utf-8")
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
                logger.exception("MSSQL query error")
                raise DatabaseError(f"Query failed: {e}") from e
            finally:
                cursor.close()

        try:
            return await asyncio.wait_for(asyncio.to_thread(_execute), timeout=timeout)
        except asyncio.TimeoutError:
            raise QueryTimeoutError(f"Query exceeded {timeout}s timeout") from None

    async def list_schemas(self) -> list[str]:
        result = await self.execute_query(
            "SELECT s.name FROM sys.schemas s "
            "INNER JOIN sys.sysusers u ON s.principal_id = u.uid "
            "WHERE u.issqluser = 1 "
            "AND s.name NOT IN ('sys', 'guest', 'INFORMATION_SCHEMA') "
            "ORDER BY s.name",
            timeout=30,
            max_rows=1000,
        )
        return [r["name"] for r in result]

    async def list_tables(
        self,
        schema: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        schema_filter = (
            f"AND s.name = '{schema.replace(chr(39), chr(39) * 2)}'"
            if schema
            else ""
        )
        sql = f"""
            SELECT TOP {limit}
                s.name AS schema_name,
                t.name AS table_name,
                p.rows AS row_count
            FROM sys.tables t
            INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
            INNER JOIN sys.partitions p
                ON t.object_id = p.object_id AND p.index_id IN (0, 1)
            WHERE t.type = 'U'
            {schema_filter}
            ORDER BY s.name, t.name
        """
        return await self.execute_query(sql, timeout=30, max_rows=limit)

    async def schema_discovery(
        self,
        schema: str | None = None,
    ) -> list[dict[str, Any]]:
        schema_filter = (
            f"WHERE c.TABLE_SCHEMA = '{schema.replace(chr(39), chr(39) * 2)}'"
            if schema
            else ""
        )
        sql = f"""
            SELECT
                c.TABLE_SCHEMA, c.TABLE_NAME, c.COLUMN_NAME,
                c.DATA_TYPE, c.CHARACTER_MAXIMUM_LENGTH,
                c.IS_NULLABLE, c.COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS c
            {schema_filter}
            ORDER BY c.TABLE_NAME, c.ORDINAL_POSITION
        """
        return await self.execute_query(sql, timeout=60, max_rows=10_000)

    async def get_database_info(self) -> dict[str, Any]:
        result = await self.execute_query(
            "SELECT DB_NAME() AS database_name, @@VERSION AS version, "
            "CAST(SERVERPROPERTY('MachineName') AS NVARCHAR(128)) AS machine_name, "
            "CAST(SERVERPROPERTY('Edition') AS NVARCHAR(128)) AS edition",
            timeout=10,
            max_rows=1,
        )
        info = dict(result[0]) if result else {}
        info["engine"] = "mssql"
        return info

    async def check_connection(self) -> bool:
        try:
            result = await self.execute_query("SELECT 1 AS test", timeout=5, max_rows=1)
            return len(result) > 0
        except Exception:
            return False
