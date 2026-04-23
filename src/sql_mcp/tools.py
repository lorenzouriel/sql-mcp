import json
import logging
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from .registry import get_registry
from .metrics import MetricsContext, record_query_blocked
from .utils import format_table, format_json, format_csv, result_summary

logger = logging.getLogger(__name__)

mcp = FastMCP("sql-mcp")


def _to_cols_rows(
    result: list[dict[str, Any]],
) -> tuple[list[str], list[tuple[Any, ...]]]:
    if not result:
        return [], []
    cols = list(result[0].keys())
    rows = [tuple(r.values()) for r in result]
    return cols, rows


@mcp.tool()
async def execute_sql(
    sql: str,
    format: str = "table",
    connection_id: Optional[str] = None,
) -> str:
    """Execute a SQL query. Specify connection_id when multiple databases are connected."""
    try:
        entry = get_registry().resolve(connection_id)
    except (ValueError, RuntimeError) as e:
        return f"ERROR: {e}"
    conn_label = connection_id or "default"

    is_allowed, reason = entry.policy.validate_query(sql, tool_name="execute_sql")
    if not is_allowed:
        record_query_blocked(reason or "unknown", entry.adapter.engine_name, conn_label)
        return f"ERROR: Query not allowed - {reason}"

    with MetricsContext("execute_sql", entry.adapter.engine_name, conn_label) as m:
        try:
            result = await entry.adapter.execute_query(
                sql,
                timeout=entry.policy.query_timeout,
                max_rows=entry.policy.max_rows,
            )
            m.set_rows(len(result))
            cols, rows = _to_cols_rows(result)
            if format.lower() == "json":
                out = format_json(cols, rows)
            elif format.lower() == "csv":
                out = format_csv(cols, rows)
            else:
                out = format_table(cols, rows) if cols else "(no result)"
            return f"{out}\n\n[{result_summary(cols, rows)}]"
        except Exception as e:
            logger.exception("execute_sql failed")
            return f"ERROR: {type(e).__name__}: {e}"


@mcp.tool()
async def execute_native_query(
    query: str,
    collection: str,
    format: str = "table",
    connection_id: Optional[str] = None,
) -> str:
    """Execute a native query on a document store (e.g. MongoDB MQL).
    Use when query_language is 'mql'. For SQL/SparkSQL/KQL engines use execute_sql.

    query: JSON string — dict for MQL filter, list for aggregation pipeline.
    collection: collection name to query against.
    """
    try:
        entry = get_registry().resolve(connection_id)
    except (ValueError, RuntimeError) as e:
        return f"ERROR: {e}"
    conn_label = connection_id or "default"

    is_allowed, reason = entry.policy.validate_query(query, tool_name="execute_native_query")
    if not is_allowed:
        record_query_blocked(reason or "unknown", entry.adapter.engine_name, conn_label)
        return f"ERROR: Query not allowed - {reason}"

    with MetricsContext("execute_native_query", entry.adapter.engine_name, conn_label) as m:
        try:
            result = await entry.adapter.execute_native_query(
                query,
                collection=collection,
                timeout=entry.policy.query_timeout,
                max_rows=entry.policy.max_rows,
            )
            m.set_rows(len(result))
            cols, rows = _to_cols_rows(result)
            if format.lower() == "json":
                out = format_json(cols, rows)
            elif format.lower() == "csv":
                out = format_csv(cols, rows)
            else:
                out = format_table(cols, rows) if cols else "(no result)"
            return f"{out}\n\n[{result_summary(cols, rows)}]"
        except Exception as e:
            logger.exception("execute_native_query failed")
            return f"ERROR: {type(e).__name__}: {e}"


@mcp.tool()
async def list_schemas(connection_id: Optional[str] = None) -> str:
    """List all schemas. Specify connection_id when multiple databases are connected."""
    entry = get_registry().resolve(connection_id)
    with MetricsContext("list_schemas", entry.adapter.engine_name, connection_id or "default") as m:
        try:
            schemas = await entry.adapter.list_schemas()
            m.set_rows(len(schemas))
            return "\n".join(f"  - {s}" for s in schemas) if schemas else "No schemas found."
        except Exception as e:
            logger.exception("list_schemas failed")
            return f"ERROR: {type(e).__name__}: {e}"


@mcp.tool()
async def list_tables(
    schema: Optional[str] = None,
    limit: int = 200,
    connection_id: Optional[str] = None,
) -> str:
    """List tables. Specify connection_id when multiple databases are connected."""
    if limit < 1:
        return "ERROR: limit must be >= 1"
    limit = min(limit, 1000)
    entry = get_registry().resolve(connection_id)
    with MetricsContext("list_tables", entry.adapter.engine_name, connection_id or "default") as m:
        try:
            result = await entry.adapter.list_tables(schema=schema, limit=limit)
            m.set_rows(len(result))
            if not result:
                return "No tables found."
            cols, rows = _to_cols_rows(result)
            return f"{format_table(cols, rows)}\n\n[{len(result)} table(s)]"
        except Exception as e:
            logger.exception("list_tables failed")
            return f"ERROR: {type(e).__name__}: {e}"


@mcp.tool()
async def schema_discovery(
    schema: Optional[str] = None,
    connection_id: Optional[str] = None,
) -> str:
    """Get full schema metadata. Specify connection_id when multiple databases are connected."""
    entry = get_registry().resolve(connection_id)
    with MetricsContext("schema_discovery", entry.adapter.engine_name, connection_id or "default") as m:
        try:
            result = await entry.adapter.schema_discovery(schema=schema)
            m.set_rows(len(result))
            if not result:
                return "No schema information found."
            cols, rows = _to_cols_rows(result)
            return format_json(cols, rows)
        except Exception as e:
            logger.exception("schema_discovery failed")
            return f"ERROR: {type(e).__name__}: {e}"


@mcp.tool()
async def get_database_info(connection_id: Optional[str] = None) -> str:
    """Get server/database metadata. Specify connection_id when multiple databases are connected."""
    entry = get_registry().resolve(connection_id)
    with MetricsContext("get_database_info", entry.adapter.engine_name, connection_id or "default") as m:
        try:
            info = await entry.adapter.get_database_info()
            info["connection_id"] = connection_id or "default"
            m.set_rows(1)
            return json.dumps(info, indent=2, default=str)
        except Exception as e:
            logger.exception("get_database_info failed")
            return f"ERROR: {type(e).__name__}: {e}"


@mcp.tool()
async def get_policy_info(connection_id: Optional[str] = None) -> str:
    """Get security policy for a connection."""
    entry = get_registry().resolve(connection_id)
    policy = entry.policy.explain()
    policy["connection_id"] = connection_id or "default"
    return json.dumps(policy, indent=2)


@mcp.tool()
async def check_db_connection(connection_id: Optional[str] = None) -> str:
    """Health check. Specify connection_id when multiple databases are connected."""
    entry = get_registry().resolve(connection_id)
    healthy = await entry.adapter.check_connection()
    mark = "✓" if healthy else "✗"
    status = "healthy" if healthy else "unhealthy"
    return f"{mark} Connection '{connection_id or 'default'}' ({entry.adapter.engine_name}): {status}"


@mcp.tool()
async def list_connections() -> str:
    """List all registered database connections. Use this to discover available connections before querying."""
    connections = get_registry().list_connections()
    return json.dumps(connections, indent=2)
