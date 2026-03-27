import pytest

pytestmark = pytest.mark.integration


@pytest.fixture
async def adapter(postgres_dsn):
    psycopg2 = pytest.importorskip("psycopg2")  # noqa: F841
    from sql_mcp.adapters.postgres import PostgresAdapter

    a = PostgresAdapter()
    await a.connect(postgres_dsn)

    import psycopg2 as pg
    conn = pg.connect(postgres_dsn)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS posts")
    cur.execute("DROP TABLE IF EXISTS users")
    cur.execute("CREATE TABLE users (id SERIAL PRIMARY KEY, name TEXT NOT NULL)")
    cur.execute("CREATE TABLE posts (id SERIAL PRIMARY KEY, title TEXT, user_id INTEGER)")
    cur.execute("INSERT INTO users (name) VALUES ('Alice'), ('Bob')")
    conn.commit()
    cur.close()
    conn.close()

    yield a
    await a.disconnect()


class TestPostgresAdapter:

    def test_engine_name(self):
        from sql_mcp.adapters.postgres import PostgresAdapter
        assert PostgresAdapter().engine_name == "postgres"

    async def test_connect_and_disconnect(self, postgres_dsn):
        from sql_mcp.adapters.postgres import PostgresAdapter
        a = PostgresAdapter()
        await a.connect(postgres_dsn)
        assert a._conn is not None
        await a.disconnect()
        assert a._conn is None

    async def test_list_schemas(self, adapter):
        schemas = await adapter.list_schemas()
        assert "public" in schemas
        # Should not include pg_catalog or pg_toast
        for s in schemas:
            assert not s.startswith("pg_")
            assert s != "information_schema"

    async def test_list_tables(self, adapter):
        tables = await adapter.list_tables()
        names = {t["table_name"] for t in tables}
        assert "users" in names
        assert "posts" in names

    async def test_list_tables_has_schema(self, adapter):
        tables = await adapter.list_tables()
        for t in tables:
            assert "schema_name" in t
            assert "table_name" in t

    async def test_execute_query_returns_list_of_dicts(self, adapter):
        result = await adapter.execute_query("SELECT id, name FROM users ORDER BY id")
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[1]["name"] == "Bob"

    async def test_execute_query_max_rows(self, adapter):
        result = await adapter.execute_query(
            "SELECT id, name FROM users ORDER BY id",
            max_rows=1,
        )
        assert len(result) == 1

    async def test_execute_query_no_resultset(self, adapter):
        result = await adapter.execute_query(
            "INSERT INTO users (name) VALUES ('Charlie')"
        )
        assert result == []

    async def test_check_connection(self, adapter):
        assert await adapter.check_connection() is True

    async def test_get_database_info(self, adapter):
        info = await adapter.get_database_info()
        assert info["engine"] == "postgres"
        assert "version" in info
        assert "database_name" in info

    async def test_schema_discovery(self, adapter):
        cols = await adapter.schema_discovery()
        table_names = {c["TABLE_NAME"] for c in cols}
        assert "users" in table_names
        col_names = {c["COLUMN_NAME"] for c in cols if c["TABLE_NAME"] == "users"}
        assert "id" in col_names
        assert "name" in col_names

    async def test_schema_discovery_has_data_type(self, adapter):
        cols = await adapter.schema_discovery()
        user_cols = [c for c in cols if c["TABLE_NAME"] == "users"]
        for col in user_cols:
            assert "DATA_TYPE" in col
            assert col["DATA_TYPE"] is not None

    async def test_timeout_parameter(self, adapter):
        # Should not raise for a fast query even with tight timeout
        result = await adapter.execute_query("SELECT 1 AS n", timeout=5)
        assert result[0]["n"] == 1
