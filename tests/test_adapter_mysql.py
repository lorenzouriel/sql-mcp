import pytest

pytestmark = pytest.mark.integration


@pytest.fixture
async def adapter(mysql_dsn):
    pytest.importorskip("mysql.connector")
    from sql_mcp.adapters.mysql import MySQLAdapter

    a = MySQLAdapter()
    await a.connect(mysql_dsn)

    import mysql.connector
    # Parse DSN: mysql://user:pass@host:port/dbname
    from urllib.parse import urlparse
    parsed = urlparse(mysql_dsn)
    conn = mysql.connector.connect(
        host=parsed.hostname,
        port=parsed.port or 3306,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path.lstrip("/"),
    )
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS posts")
    cur.execute("DROP TABLE IF EXISTS users")
    cur.execute("CREATE TABLE users (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255) NOT NULL)")
    cur.execute("CREATE TABLE posts (id INT AUTO_INCREMENT PRIMARY KEY, title VARCHAR(255), user_id INT)")
    cur.execute("INSERT INTO users (name) VALUES ('Alice'), ('Bob')")
    conn.commit()
    cur.close()
    conn.close()

    yield a
    await a.disconnect()


class TestMySQLAdapter:

    def test_engine_name(self):
        from sql_mcp.adapters.mysql import MySQLAdapter
        assert MySQLAdapter().engine_name == "mysql"

    async def test_connect_and_disconnect(self, mysql_dsn):
        from sql_mcp.adapters.mysql import MySQLAdapter
        a = MySQLAdapter()
        await a.connect(mysql_dsn)
        assert a._conn is not None
        await a.disconnect()
        assert a._conn is None

    async def test_list_schemas(self, adapter):
        schemas = await adapter.list_schemas()
        assert isinstance(schemas, list)
        assert len(schemas) > 0
        # System schemas should be excluded
        for s in schemas:
            assert s not in ("information_schema", "performance_schema", "sys", "mysql")

    async def test_list_tables(self, adapter):
        tables = await adapter.list_tables()
        names = {t["table_name"] for t in tables}
        assert "users" in names
        assert "posts" in names

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
        assert info["engine"] == "mysql"
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
