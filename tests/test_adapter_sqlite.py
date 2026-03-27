import pytest
from sql_mcp.adapters.sqlite import SQLiteAdapter


@pytest.fixture
async def adapter(sqlite_dsn):
    a = SQLiteAdapter()
    await a.connect(sqlite_dsn)

    # Seed some test data
    import sqlite3
    conn = sqlite3.connect(sqlite_dsn)
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
    conn.execute("CREATE TABLE posts (id INTEGER PRIMARY KEY, title TEXT, user_id INTEGER)")
    conn.execute("INSERT INTO users VALUES (1, 'Alice'), (2, 'Bob')")
    conn.commit()
    conn.close()

    yield a
    await a.disconnect()


class TestSQLiteAdapter:

    def test_engine_name(self):
        assert SQLiteAdapter().engine_name == "sqlite"

    async def test_connect_memory(self):
        a = SQLiteAdapter()
        await a.connect(":memory:")
        assert a._conn is not None
        await a.disconnect()

    async def test_list_schemas_returns_main(self, adapter):
        schemas = await adapter.list_schemas()
        assert schemas == ["main"]

    async def test_list_tables(self, adapter):
        tables = await adapter.list_tables()
        names = {t["table_name"] for t in tables}
        assert "users" in names
        assert "posts" in names

    async def test_list_tables_excludes_sqlite_internal(self, adapter):
        tables = await adapter.list_tables()
        for t in tables:
            assert not t["table_name"].startswith("sqlite_")

    async def test_execute_query_returns_list_of_dicts(self, adapter):
        result = await adapter.execute_query("SELECT id, name FROM users ORDER BY id")
        assert len(result) == 2
        assert result[0] == {"id": 1, "name": "Alice"}
        assert result[1] == {"id": 2, "name": "Bob"}

    async def test_execute_query_max_rows(self, adapter):
        result = await adapter.execute_query(
            "SELECT id, name FROM users ORDER BY id",
            max_rows=1,
        )
        assert len(result) == 1

    async def test_execute_query_no_resultset(self, adapter):
        result = await adapter.execute_query(
            "INSERT INTO users VALUES (99, 'Test')"
        )
        assert result == []

    async def test_check_connection(self, adapter):
        assert await adapter.check_connection() is True

    async def test_get_database_info(self, adapter, sqlite_dsn):
        info = await adapter.get_database_info()
        assert info["engine"] == "sqlite"
        assert info["database_name"] == sqlite_dsn
        assert "version" in info

    async def test_schema_discovery(self, adapter):
        cols = await adapter.schema_discovery()
        table_names = {c["TABLE_NAME"] for c in cols}
        assert "users" in table_names
        col_names = {c["COLUMN_NAME"] for c in cols if c["TABLE_NAME"] == "users"}
        assert "id" in col_names
        assert "name" in col_names

    async def test_disconnect(self, sqlite_dsn):
        a = SQLiteAdapter()
        await a.connect(sqlite_dsn)
        await a.disconnect()
        assert a._conn is None
