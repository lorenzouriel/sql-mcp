import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from sql_mcp.models import ConnectionConfig
from sql_mcp.registry import ConnectionRegistry, ConnectionEntry, set_registry
from sql_mcp.security import SecurityPolicy


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_entry(
    engine: str = "sqlite",
    read_only: bool = True,
    conn_id: str = "default",
    adapter: object = None,
) -> ConnectionEntry:
    if adapter is None:
        adapter = _mock_adapter(engine)
    policy = SecurityPolicy(read_only=read_only, engine=engine)
    config = ConnectionConfig(id=conn_id, engine=engine, dsn=":memory:", read_only=read_only)
    return ConnectionEntry(config=config, adapter=adapter, policy=policy)


def _mock_adapter(engine: str = "sqlite") -> MagicMock:
    a = MagicMock()
    a.engine_name = engine
    a.execute_query = AsyncMock(return_value=[{"id": 1, "name": "Alice"}])
    a.list_schemas = AsyncMock(return_value=["main"])
    a.list_tables = AsyncMock(return_value=[{"table_name": "users", "schema_name": "main"}])
    a.schema_discovery = AsyncMock(
        return_value=[{"TABLE_NAME": "users", "COLUMN_NAME": "id", "DATA_TYPE": "INTEGER"}]
    )
    a.get_database_info = AsyncMock(
        return_value={"engine": engine, "version": "3.x", "database_name": ":memory:"}
    )
    a.check_connection = AsyncMock(return_value=True)
    return a


def _single_registry(engine: str = "sqlite", read_only: bool = True) -> ConnectionRegistry:
    reg = ConnectionRegistry()
    entry = _make_entry(engine=engine, read_only=read_only)
    reg._entries["default"] = entry
    return reg


# ---------------------------------------------------------------------------
# execute_sql
# ---------------------------------------------------------------------------

class TestExecuteSql:

    async def test_returns_table_format_by_default(self):
        reg = _single_registry()
        with patch("sql_mcp.tools.get_registry", return_value=reg):
            from sql_mcp.tools import execute_sql
            result = await execute_sql("SELECT id, name FROM users")
        assert "Alice" in result

    async def test_json_format(self):
        reg = _single_registry()
        with patch("sql_mcp.tools.get_registry", return_value=reg):
            from sql_mcp.tools import execute_sql
            result = await execute_sql("SELECT id, name FROM users", format="json")
        parsed = json.loads(result.split("\n\n")[0])
        assert isinstance(parsed, list)
        assert parsed[0]["name"] == "Alice"

    async def test_csv_format(self):
        reg = _single_registry()
        with patch("sql_mcp.tools.get_registry", return_value=reg):
            from sql_mcp.tools import execute_sql
            result = await execute_sql("SELECT id, name FROM users", format="csv")
        assert "id,name" in result or "id" in result

    async def test_blocked_query_returns_error(self):
        reg = _single_registry(read_only=True)
        with patch("sql_mcp.tools.get_registry", return_value=reg):
            from sql_mcp.tools import execute_sql
            result = await execute_sql("INSERT INTO t VALUES (1)")
        assert result.startswith("ERROR:")

    async def test_adapter_exception_returns_error(self):
        adapter = _mock_adapter()
        adapter.execute_query = AsyncMock(side_effect=RuntimeError("boom"))
        reg = ConnectionRegistry()
        reg._entries["default"] = _make_entry(adapter=adapter)
        with patch("sql_mcp.tools.get_registry", return_value=reg):
            from sql_mcp.tools import execute_sql
            result = await execute_sql("SELECT 1")
        assert "ERROR:" in result

    async def test_no_result_shows_no_result(self):
        adapter = _mock_adapter()
        adapter.execute_query = AsyncMock(return_value=[])
        reg = ConnectionRegistry()
        reg._entries["default"] = _make_entry(adapter=adapter, read_only=False)
        with patch("sql_mcp.tools.get_registry", return_value=reg):
            from sql_mcp.tools import execute_sql
            result = await execute_sql("INSERT INTO t VALUES (1)", format="table")
        assert "(no result)" in result

    async def test_connection_id_routing(self):
        adapter_a = _mock_adapter()
        adapter_a.execute_query = AsyncMock(return_value=[{"db": "A"}])
        adapter_b = _mock_adapter()
        adapter_b.execute_query = AsyncMock(return_value=[{"db": "B"}])

        reg = ConnectionRegistry()
        reg._entries["db_a"] = _make_entry(conn_id="db_a", adapter=adapter_a)
        reg._entries["db_b"] = _make_entry(conn_id="db_b", adapter=adapter_b)

        with patch("sql_mcp.tools.get_registry", return_value=reg):
            from sql_mcp.tools import execute_sql
            result_a = await execute_sql("SELECT 1", connection_id="db_a")
            result_b = await execute_sql("SELECT 1", connection_id="db_b")

        assert "A" in result_a
        assert "B" in result_b

    async def test_unknown_connection_id_returns_error(self):
        reg = _single_registry()
        reg._entries["default"].policy = SecurityPolicy(engine="sqlite", read_only=True)
        # Override resolve to raise
        original_resolve = reg.resolve
        def bad_resolve(cid=None):
            if cid == "nope":
                raise ValueError("Unknown connection 'nope'")
            return original_resolve(cid)
        reg.resolve = bad_resolve

        with patch("sql_mcp.tools.get_registry", return_value=reg):
            from sql_mcp.tools import execute_sql
            result = await execute_sql("SELECT 1", connection_id="nope")
        assert "ERROR:" in result


# ---------------------------------------------------------------------------
# list_schemas
# ---------------------------------------------------------------------------

class TestListSchemas:

    async def test_returns_schema_list(self):
        reg = _single_registry()
        with patch("sql_mcp.tools.get_registry", return_value=reg):
            from sql_mcp.tools import list_schemas
            result = await list_schemas()
        assert "main" in result

    async def test_empty_returns_no_schemas(self):
        adapter = _mock_adapter()
        adapter.list_schemas = AsyncMock(return_value=[])
        reg = ConnectionRegistry()
        reg._entries["default"] = _make_entry(adapter=adapter)
        with patch("sql_mcp.tools.get_registry", return_value=reg):
            from sql_mcp.tools import list_schemas
            result = await list_schemas()
        assert "No schemas" in result


# ---------------------------------------------------------------------------
# list_tables
# ---------------------------------------------------------------------------

class TestListTables:

    async def test_returns_table_list(self):
        reg = _single_registry()
        with patch("sql_mcp.tools.get_registry", return_value=reg):
            from sql_mcp.tools import list_tables
            result = await list_tables()
        assert "users" in result

    async def test_limit_zero_returns_error(self):
        reg = _single_registry()
        with patch("sql_mcp.tools.get_registry", return_value=reg):
            from sql_mcp.tools import list_tables
            result = await list_tables(limit=0)
        assert "ERROR:" in result

    async def test_empty_returns_no_tables(self):
        adapter = _mock_adapter()
        adapter.list_tables = AsyncMock(return_value=[])
        reg = ConnectionRegistry()
        reg._entries["default"] = _make_entry(adapter=adapter)
        with patch("sql_mcp.tools.get_registry", return_value=reg):
            from sql_mcp.tools import list_tables
            result = await list_tables()
        assert "No tables" in result


# ---------------------------------------------------------------------------
# schema_discovery
# ---------------------------------------------------------------------------

class TestSchemaDiscovery:

    async def test_returns_json(self):
        reg = _single_registry()
        with patch("sql_mcp.tools.get_registry", return_value=reg):
            from sql_mcp.tools import schema_discovery
            result = await schema_discovery()
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert parsed[0]["TABLE_NAME"] == "users"

    async def test_empty_returns_no_info(self):
        adapter = _mock_adapter()
        adapter.schema_discovery = AsyncMock(return_value=[])
        reg = ConnectionRegistry()
        reg._entries["default"] = _make_entry(adapter=adapter)
        with patch("sql_mcp.tools.get_registry", return_value=reg):
            from sql_mcp.tools import schema_discovery
            result = await schema_discovery()
        assert "No schema" in result


# ---------------------------------------------------------------------------
# get_database_info
# ---------------------------------------------------------------------------

class TestGetDatabaseInfo:

    async def test_returns_json_with_engine(self):
        reg = _single_registry()
        with patch("sql_mcp.tools.get_registry", return_value=reg):
            from sql_mcp.tools import get_database_info
            result = await get_database_info()
        parsed = json.loads(result)
        assert parsed["engine"] == "sqlite"
        assert parsed["connection_id"] == "default"


# ---------------------------------------------------------------------------
# get_policy_info
# ---------------------------------------------------------------------------

class TestGetPolicyInfo:

    async def test_returns_policy_json(self):
        reg = _single_registry(read_only=True)
        with patch("sql_mcp.tools.get_registry", return_value=reg):
            from sql_mcp.tools import get_policy_info
            result = await get_policy_info()
        parsed = json.loads(result)
        assert parsed["read_only"] is True
        assert "banned_pattern_count" in parsed
        assert parsed["connection_id"] == "default"


# ---------------------------------------------------------------------------
# check_db_connection
# ---------------------------------------------------------------------------

class TestCheckDbConnection:

    async def test_healthy_connection(self):
        reg = _single_registry()
        with patch("sql_mcp.tools.get_registry", return_value=reg):
            from sql_mcp.tools import check_db_connection
            result = await check_db_connection()
        assert "healthy" in result

    async def test_unhealthy_connection(self):
        adapter = _mock_adapter()
        adapter.check_connection = AsyncMock(return_value=False)
        reg = ConnectionRegistry()
        reg._entries["default"] = _make_entry(adapter=adapter)
        with patch("sql_mcp.tools.get_registry", return_value=reg):
            from sql_mcp.tools import check_db_connection
            result = await check_db_connection()
        assert "unhealthy" in result


# ---------------------------------------------------------------------------
# list_connections
# ---------------------------------------------------------------------------

class TestListConnections:

    async def test_returns_all_connections(self):
        reg = ConnectionRegistry()
        reg._entries["db1"] = _make_entry(conn_id="db1", engine="sqlite")
        reg._entries["db2"] = _make_entry(conn_id="db2", engine="postgres")
        with patch("sql_mcp.tools.get_registry", return_value=reg):
            from sql_mcp.tools import list_connections
            result = await list_connections()
        parsed = json.loads(result)
        ids = {c["id"] for c in parsed}
        assert ids == {"db1", "db2"}

    async def test_connection_metadata_present(self):
        reg = _single_registry()
        with patch("sql_mcp.tools.get_registry", return_value=reg):
            from sql_mcp.tools import list_connections
            result = await list_connections()
        parsed = json.loads(result)
        conn = parsed[0]
        assert "engine" in conn
        assert "read_only" in conn
        assert "status" in conn
