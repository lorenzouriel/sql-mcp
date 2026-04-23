import asyncio
import logging
from typing import Any
from urllib.parse import urlparse, parse_qs

from .base import DatabaseAdapter

logger = logging.getLogger(__name__)

try:
    from databricks import sql as dbsql
except ImportError:
    dbsql = None  # type: ignore[assignment]


def _parse_databricks_dsn(dsn: str) -> dict[str, Any]:
    """Parse databricks://token@<host>?http_path=<path>[&catalog=<c>][&schema=<s>]"""
    u = urlparse(dsn)
    params = parse_qs(u.query)
    return {
        "server_hostname": u.hostname or "",
        "http_path": params.get("http_path", [""])[0],
        "access_token": u.password or u.username or "",
        "_catalog": params.get("catalog", [None])[0],
        "_schema": params.get("schema", [None])[0],
    }


class DatabricksAdapter(DatabaseAdapter):

    def __init__(self) -> None:
        self._conn: Any = None
        self._catalog: str | None = None

    @property
    def engine_name(self) -> str:
        return "databricks"

    @property
    def query_language(self) -> str:
        return "sparksql"

    async def connect(self, dsn: str) -> None:
        if dbsql is None:
            raise ImportError(
                "databricks-sql-connector is required for Databricks. "
                "Install with: pip install sql-mcp[databricks]"
            )

        parsed = _parse_databricks_dsn(dsn)
        catalog = parsed.pop("_catalog", None)
        schema = parsed.pop("_schema", None)
        self._catalog = catalog

        connect_kwargs = {k: v for k, v in parsed.items() if v}

        def _connect() -> Any:
            conn = dbsql.connect(**connect_kwargs)
            if catalog:
                cur = conn.cursor()
                cur.execute(f"USE CATALOG `{catalog}`")
                if schema:
                    cur.execute(f"USE `{schema}`")
                cur.close()
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
                logger.exception("Databricks query error")
                raise RuntimeError(f"Query failed: {e}") from e
            finally:
                cursor.close()

        return await asyncio.to_thread(_execute)

    async def list_schemas(self) -> list[str]:
        if self._catalog:
            result = await self.execute_query(
                f"SHOW SCHEMAS IN `{self._catalog}`", timeout=15, max_rows=500
            )
        else:
            result = await self.execute_query("SHOW SCHEMAS", timeout=15, max_rows=500)
        if not result:
            return []
        first = result[0]
        key = next(
            (k for k in first if "namespace" in k.lower() or "schema" in k.lower()), None
        )
        if not key:
            return []
        if self._catalog:
            return [f"{self._catalog}.{r[key]}" for r in result]
        return [r[key] for r in result]

    async def list_tables(
        self,
        schema: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        scope = f"IN `{schema}`" if schema else ""
        result = await self.execute_query(f"SHOW TABLES {scope}", timeout=30, max_rows=limit)
        return [
            {
                "schema_name": r.get("database") or r.get("namespace") or schema or "",
                "table_name": r.get("tableName") or r.get("table_name") or "",
                "row_count": None,
            }
            for r in result
        ]

    async def schema_discovery(
        self,
        schema: str | None = None,
    ) -> list[dict[str, Any]]:
        catalog_filter = f"AND table_catalog = '{self._catalog}'" if self._catalog else ""
        schema_filter = f"AND table_schema = '{schema}'" if schema else ""
        rows = await self.execute_query(
            f"SELECT table_schema, table_name, column_name, data_type, "
            f"character_maximum_length, is_nullable, column_default "
            f"FROM information_schema.columns "
            f"WHERE 1=1 {catalog_filter} {schema_filter} "
            f"ORDER BY table_name, ordinal_position",
            timeout=60,
            max_rows=10_000,
        )
        return [{k.upper(): v for k, v in row.items()} for row in rows]

    async def get_database_info(self) -> dict[str, Any]:
        result = await self.execute_query(
            "SELECT current_catalog(), current_database(), spark_version()",
            timeout=10,
            max_rows=1,
        )
        info = dict(result[0]) if result else {}
        info["engine"] = "databricks"
        info["query_language"] = "sparksql"
        return info

    async def check_connection(self) -> bool:
        try:
            result = await self.execute_query("SELECT 1 AS test", timeout=5, max_rows=1)
            return len(result) > 0
        except Exception:
            return False
