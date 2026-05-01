"""
Integration tests for DatabricksAdapter.

Requires: pip install sql-mcp[databricks]
Run with: $env:DATABRICKS_TEST_DSN="databricks://token@host?http_path=..."; pytest tests/test_adapter_databricks.py -m integration -v
"""
import pytest
from sql_mcp.adapters.databricks import DatabricksAdapter


pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
async def adapter(databricks_dsn):
    a = DatabricksAdapter()
    await a.connect(databricks_dsn)
    yield a
    await a.disconnect()


# ---------------------------------------------------------------------------
# Basic connectivity
# ---------------------------------------------------------------------------

async def test_check_connection(adapter):
    assert await adapter.check_connection() is True


async def test_engine_name(adapter):
    assert adapter.engine_name == "databricks"


async def test_query_language(adapter):
    assert adapter.query_language == "sparksql"


async def test_supports_sql(adapter):
    assert adapter.supports_sql is True


# ---------------------------------------------------------------------------
# execute_query — SparkSQL
# ---------------------------------------------------------------------------

async def test_select_one(adapter):
    result = await adapter.execute_query("SELECT 1 AS test")
    assert len(result) == 1
    assert list(result[0].values())[0] == 1


async def test_select_returns_list_of_dicts(adapter):
    result = await adapter.execute_query("SELECT 1 AS a, 2 AS b")
    assert isinstance(result, list)
    assert isinstance(result[0], dict)


async def test_max_rows_respected(adapter):
    result = await adapter.execute_query(
        "SELECT explode(sequence(1, 100)) AS n", max_rows=10
    )
    assert len(result) <= 10


async def test_empty_result_on_ddl(adapter):
    result = await adapter.execute_query("SHOW DATABASES")
    assert isinstance(result, list)


# ---------------------------------------------------------------------------
# list_schemas
# ---------------------------------------------------------------------------

async def test_list_schemas_returns_list(adapter):
    schemas = await adapter.list_schemas()
    assert isinstance(schemas, list)
    assert len(schemas) >= 1


async def test_list_schemas_strings(adapter):
    schemas = await adapter.list_schemas()
    assert all(isinstance(s, str) for s in schemas)


# ---------------------------------------------------------------------------
# list_tables
# ---------------------------------------------------------------------------

async def test_list_tables_returns_list(adapter):
    tables = await adapter.list_tables()
    assert isinstance(tables, list)


async def test_list_tables_shape(adapter):
    tables = await adapter.list_tables()
    if tables:
        for t in tables:
            assert "schema_name" in t
            assert "table_name" in t
            assert "row_count" in t


# ---------------------------------------------------------------------------
# schema_discovery
# ---------------------------------------------------------------------------

async def test_schema_discovery_returns_list(adapter):
    result = await adapter.schema_discovery()
    assert isinstance(result, list)


async def test_schema_discovery_uppercase_keys(adapter):
    result = await adapter.schema_discovery()
    if result:
        assert "TABLE_NAME" in result[0]
        assert "COLUMN_NAME" in result[0]
        assert "DATA_TYPE" in result[0]


# ---------------------------------------------------------------------------
# get_database_info
# ---------------------------------------------------------------------------

async def test_get_database_info(adapter):
    info = await adapter.get_database_info()
    assert info["engine"] == "databricks"
    assert info["query_language"] == "sparksql"


# ---------------------------------------------------------------------------
# execute_native_query raises
# ---------------------------------------------------------------------------

async def test_execute_native_query_raises(adapter):
    with pytest.raises(NotImplementedError):
        await adapter.execute_native_query("{}", "some_table")
