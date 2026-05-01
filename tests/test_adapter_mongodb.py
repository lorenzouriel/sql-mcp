"""
Integration tests for MongoDBAdapter.

Requires: pip install sql-mcp[mongodb]
Run with: $env:SQL_MCP_TEST_USE_COMPOSE="1"; pytest tests/test_adapter_mongodb.py -m integration -v
"""
import pytest
from sql_mcp.adapters.mongodb import MongoDBAdapter


pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
async def adapter(mongodb_dsn):
    a = MongoDBAdapter()
    await a.connect(mongodb_dsn)

    db_name = mongodb_dsn.rsplit("/", 1)[-1].split("?")[0] or "testdb"

    # Seed collections (idempotent — drop first)
    import asyncio
    def _seed():
        db = a._db
        for coll in ("order_items", "orders", "products", "customers"):
            db.drop_collection(coll)
        db["customers"].insert_many([
            {"name": "Alice Ferreira",  "email": "alice@example.com",  "country": "Brazil"},
            {"name": "Bob Smith",       "email": "bob@example.com",    "country": "USA"},
            {"name": "Carlos Ruiz",     "email": "carlos@example.com", "country": "Mexico"},
            {"name": "Diana Chen",      "email": "diana@example.com",  "country": "China"},
            {"name": "Eve Dupont",      "email": "eve@example.com",    "country": "France"},
        ])
        db["orders"].insert_many([
            {"customer_id": 1, "status": "completed", "total": 1329.98},
            {"customer_id": 2, "status": "pending",   "total":   49.90},
            {"customer_id": 3, "status": "completed", "total":  439.00},
            {"customer_id": 4, "status": "shipped",   "total": 1299.99},
            {"customer_id": 5, "status": "completed", "total":  119.98},
        ])
        db["products"].insert_many([
            {"name": "Laptop Pro 15",  "category": "Electronics", "price": 1299.99},
            {"name": "Wireless Mouse", "category": "Electronics", "price":   29.99},
            {"name": "Desk Chair",     "category": "Furniture",   "price":  349.00},
        ])
        db["order_items"].insert_many([
            {"order_id": 1, "product_id": 1, "quantity": 1, "unit_price": 1299.99},
            {"order_id": 1, "product_id": 2, "quantity": 1, "unit_price":   29.99},
            {"order_id": 2, "product_id": 4, "quantity": 1, "unit_price":   49.90},
        ])

    await asyncio.to_thread(_seed)
    yield a
    await a.disconnect()


# ---------------------------------------------------------------------------
# Basic connectivity
# ---------------------------------------------------------------------------

async def test_check_connection(adapter):
    assert await adapter.check_connection() is True


async def test_engine_name(adapter):
    assert adapter.engine_name == "mongodb"


async def test_query_language(adapter):
    assert adapter.query_language == "mql"


async def test_supports_sql(adapter):
    assert adapter.supports_sql is False


# ---------------------------------------------------------------------------
# list_schemas / list_tables
# ---------------------------------------------------------------------------

async def test_list_schemas(adapter):
    schemas = await adapter.list_schemas()
    assert isinstance(schemas, list)
    assert len(schemas) >= 1


async def test_list_tables(adapter):
    tables = await adapter.list_tables()
    assert isinstance(tables, list)
    assert len(tables) >= 4
    names = [t["table_name"] for t in tables]
    assert "customers" in names
    assert "orders" in names


async def test_list_tables_schema_filter(adapter, mongodb_dsn):
    db_name = mongodb_dsn.rsplit("/", 1)[-1].split("?")[0] or "testdb"
    tables = await adapter.list_tables(schema=db_name)
    assert all(t["schema_name"] == db_name for t in tables)


async def test_list_tables_shape(adapter):
    tables = await adapter.list_tables()
    for t in tables:
        assert "schema_name" in t
        assert "table_name" in t
        assert "row_count" in t


# ---------------------------------------------------------------------------
# execute_native_query — MQL filter
# ---------------------------------------------------------------------------

async def test_mql_filter_all(adapter):
    rows = await adapter.execute_native_query("{}", "customers")
    assert len(rows) == 5


async def test_mql_filter_condition(adapter):
    rows = await adapter.execute_native_query('{"status": "completed"}', "orders")
    assert len(rows) == 3
    assert all(r["status"] == "completed" for r in rows)


async def test_mql_filter_returns_dicts(adapter):
    rows = await adapter.execute_native_query("{}", "customers", max_rows=1)
    assert len(rows) == 1
    assert isinstance(rows[0], dict)
    assert "_id" not in rows[0]  # ObjectId stripped


async def test_mql_max_rows(adapter):
    rows = await adapter.execute_native_query("{}", "customers", max_rows=2)
    assert len(rows) == 2


# ---------------------------------------------------------------------------
# execute_native_query — aggregation pipeline
# ---------------------------------------------------------------------------

async def test_aggregation_group(adapter):
    pipeline = '[{"$group": {"_id": "$status", "count": {"$sum": 1}}}]'
    rows = await adapter.execute_native_query(pipeline, "orders")
    assert len(rows) >= 1
    assert all("_id" in r or "count" in r for r in rows)


async def test_aggregation_sort_limit(adapter):
    pipeline = '[{"$sort": {"total": -1}}, {"$limit": 2}]'
    rows = await adapter.execute_native_query(pipeline, "orders")
    assert len(rows) == 2


# ---------------------------------------------------------------------------
# execute_native_query — error handling
# ---------------------------------------------------------------------------

async def test_invalid_json_raises(adapter):
    with pytest.raises(Exception, match="Invalid MQL|JSON"):
        await adapter.execute_native_query("not json", "customers")


async def test_execute_query_raises_not_implemented(adapter):
    with pytest.raises(NotImplementedError):
        await adapter.execute_query("SELECT 1")


# ---------------------------------------------------------------------------
# schema_discovery
# ---------------------------------------------------------------------------

async def test_schema_discovery_returns_list(adapter):
    result = await adapter.schema_discovery()
    assert isinstance(result, list)
    assert len(result) > 0


async def test_schema_discovery_uppercase_keys(adapter):
    result = await adapter.schema_discovery()
    assert result[0].get("TABLE_NAME") is not None
    assert result[0].get("COLUMN_NAME") is not None
    assert result[0].get("DATA_TYPE") is not None


async def test_schema_discovery_covers_customers(adapter):
    result = await adapter.schema_discovery()
    table_names = {r["TABLE_NAME"] for r in result}
    assert "customers" in table_names
    customer_fields = {r["COLUMN_NAME"] for r in result if r["TABLE_NAME"] == "customers"}
    assert "name" in customer_fields
    assert "email" in customer_fields
    assert "country" in customer_fields


# ---------------------------------------------------------------------------
# get_database_info
# ---------------------------------------------------------------------------

async def test_get_database_info(adapter):
    info = await adapter.get_database_info()
    assert info["engine"] == "mongodb"
    assert info["query_language"] == "mql"
    assert "version" in info
