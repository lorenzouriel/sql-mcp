import asyncio
import logging
from typing import Any

from .base import DatabaseAdapter

logger = logging.getLogger(__name__)

try:
    import pyodbc
except ImportError:
    pyodbc = None  # type: ignore[assignment]

try:
    from azure.kusto.data import KustoClient, KustoConnectionStringBuilder
except ImportError:
    KustoClient = None  # type: ignore[assignment]
    KustoConnectionStringBuilder = None  # type: ignore[assignment]


class FabricAdapter(DatabaseAdapter):
    """Microsoft Fabric adapter supporting Fabric Warehouse (T-SQL) and Eventhouse (KQL).

    DSN format:
      Warehouse:  standard ODBC connection string
      Eventhouse: kql://<cluster_hostname>/<database>
    """

    def __init__(self) -> None:
        self._conn: Any = None
        self._kusto_client: Any = None
        self._kusto_database: str = ""
        self._mode: str = "sql"

    @property
    def engine_name(self) -> str:
        return "fabric"

    @property
    def query_language(self) -> str:
        return self._mode

    async def connect(self, dsn: str) -> None:
        if dsn.startswith("kql://"):
            await self._connect_kql(dsn)
        else:
            await self._connect_sql(dsn)

    async def _connect_sql(self, dsn: str) -> None:
        if pyodbc is None:
            raise ImportError(
                "pyodbc is required for Fabric Warehouse. "
                "Install with: pip install sql-mcp[fabric]"
            )
        self._mode = "sql"
        self._conn = await asyncio.to_thread(
            lambda: pyodbc.connect(dsn, autocommit=True)
        )

    async def _connect_kql(self, dsn: str) -> None:
        if KustoClient is None:
            raise ImportError(
                "azure-kusto-data is required for Fabric Eventhouse. "
                "Install with: pip install sql-mcp[fabric]"
            )
        self._mode = "kql"
        parts = dsn[len("kql://"):].split("/", 1)
        cluster_uri = f"https://{parts[0]}"
        self._kusto_database = parts[1] if len(parts) > 1 else ""

        def _connect() -> Any:
            kcsb = KustoConnectionStringBuilder.with_az_cli_authentication(cluster_uri)
            return KustoClient(kcsb)

        self._kusto_client = await asyncio.to_thread(_connect)

    async def disconnect(self) -> None:
        if self._conn is not None:
            await asyncio.to_thread(self._conn.close)
            self._conn = None
        self._kusto_client = None

    async def execute_query(
        self,
        sql: str,
        timeout: int = 30,
        max_rows: int = 50_000,
    ) -> list[dict[str, Any]]:
        if self._mode == "kql":
            return await self._execute_kql(sql, timeout, max_rows)
        return await self._execute_sql(sql, timeout, max_rows)

    async def _execute_sql(
        self, sql: str, timeout: int, max_rows: int
    ) -> list[dict[str, Any]]:
        def _run() -> list[dict[str, Any]]:
            cursor = self._conn.cursor()
            try:
                cursor.execute(sql)
                if not cursor.description:
                    return []
                cols = [col[0] for col in cursor.description]
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
                raise RuntimeError(f"Fabric SQL query failed: {e}") from e
            finally:
                cursor.close()

        return await asyncio.to_thread(_run)

    async def _execute_kql(
        self, kql: str, timeout: int, max_rows: int
    ) -> list[dict[str, Any]]:
        def _run() -> list[dict[str, Any]]:
            response = self._kusto_client.execute(self._kusto_database, kql)
            result_table = response.primary_results[0]
            cols = [col.column_name for col in result_table.columns]
            rows: list[dict[str, Any]] = []
            for row in result_table.rows:
                rows.append(dict(zip(cols, row)))
                if len(rows) >= max_rows:
                    break
            return rows

        return await asyncio.to_thread(_run)

    async def list_schemas(self) -> list[str]:
        if self._mode == "kql":
            result = await self.execute_query(".show databases", timeout=10, max_rows=200)
            return [
                r.get("DatabaseName") or r.get("database_name") or ""
                for r in result
                if r.get("DatabaseName") or r.get("database_name")
            ]
        result = await self.execute_query(
            "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA ORDER BY SCHEMA_NAME",
            timeout=10,
            max_rows=500,
        )
        return [
            r.get("SCHEMA_NAME") or r.get("schema_name") or ""
            for r in result
            if r.get("SCHEMA_NAME") or r.get("schema_name")
        ]

    async def list_tables(
        self,
        schema: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        if self._mode == "kql":
            result = await self.execute_query(".show tables", timeout=15, max_rows=limit)
            return [
                {
                    "schema_name": self._kusto_database,
                    "table_name": r.get("TableName") or r.get("table_name") or "",
                    "row_count": None,
                }
                for r in result
            ]
        where = "WHERE TABLE_TYPE = 'BASE TABLE'"
        if schema:
            where += f" AND TABLE_SCHEMA = '{schema.replace(chr(39), chr(39) * 2)}'"
        rows = await self.execute_query(
            f"SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES {where} "
            f"ORDER BY TABLE_SCHEMA, TABLE_NAME",
            timeout=30,
            max_rows=limit,
        )
        return [
            {
                "schema_name": r.get("TABLE_SCHEMA") or r.get("table_schema") or "",
                "table_name": r.get("TABLE_NAME") or r.get("table_name") or "",
                "row_count": None,
            }
            for r in rows
        ]

    async def schema_discovery(
        self,
        schema: str | None = None,
    ) -> list[dict[str, Any]]:
        if self._mode == "kql":
            result = await self.execute_query(
                ".show databases schema", timeout=30, max_rows=10_000
            )
            return [{k.upper(): v for k, v in r.items()} for r in result]
        where = f"WHERE c.TABLE_SCHEMA = '{schema}'" if schema else ""
        rows = await self.execute_query(
            f"SELECT c.TABLE_SCHEMA, c.TABLE_NAME, c.COLUMN_NAME, c.DATA_TYPE, "
            f"c.CHARACTER_MAXIMUM_LENGTH, c.IS_NULLABLE, c.COLUMN_DEFAULT "
            f"FROM INFORMATION_SCHEMA.COLUMNS c {where} "
            f"ORDER BY c.TABLE_NAME, c.ORDINAL_POSITION",
            timeout=60,
            max_rows=10_000,
        )
        return [{k.upper(): v for k, v in row.items()} for row in rows]

    async def get_database_info(self) -> dict[str, Any]:
        if self._mode == "kql":
            return {
                "engine": "fabric",
                "schema_type": "eventhouse",
                "query_language": "kql",
                "database": self._kusto_database,
            }
        result = await self.execute_query(
            "SELECT @@VERSION AS version", timeout=10, max_rows=1
        )
        info = dict(result[0]) if result else {}
        info["engine"] = "fabric"
        info["schema_type"] = "warehouse"
        info["query_language"] = "sql"
        return info

    async def check_connection(self) -> bool:
        try:
            if self._mode == "kql":
                result = await self.execute_query("print 'ok'", timeout=5, max_rows=1)
            else:
                result = await self.execute_query("SELECT 1 AS test", timeout=5, max_rows=1)
            return len(result) > 0
        except Exception:
            return False
