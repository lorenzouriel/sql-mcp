import pytest
from unittest.mock import MagicMock, patch, AsyncMock


@pytest.fixture
def mock_conn():
    conn = MagicMock()
    cursor = MagicMock()
    cursor.description = [("id",), ("name",)]
    cursor.fetchmany.side_effect = [
        [(1, "Alice"), (2, "Bob")],
        [],
    ]
    conn.cursor.return_value = cursor
    return conn


@pytest.fixture
async def adapter(mock_conn):
    with patch("sql_mcp.adapters.mssql.pyodbc") as mock_pyodbc:
        mock_pyodbc.connect.return_value = mock_conn
        mock_pyodbc.pooling = True

        from sql_mcp.adapters.mssql import MSSQLAdapter
        a = MSSQLAdapter()
        a._conn = mock_conn
        return a


class TestMSSQLAdapter:

    async def test_engine_name(self, adapter):
        assert adapter.engine_name == "mssql"

    async def test_execute_query_returns_list_of_dicts(self, adapter, mock_conn):
        cursor = MagicMock()
        cursor.description = [("col1",), ("col2",)]
        cursor.fetchmany.side_effect = [[(1, "a")], []]
        mock_conn.cursor.return_value = cursor

        result = await adapter.execute_query("SELECT col1, col2 FROM t")
        assert isinstance(result, list)
        assert result[0] == {"col1": 1, "col2": "a"}

    async def test_execute_query_no_resultset(self, adapter, mock_conn):
        cursor = MagicMock()
        cursor.description = None
        mock_conn.cursor.return_value = cursor

        result = await adapter.execute_query("USE mydb")
        assert result == []
        mock_conn.commit.assert_called_once()

    async def test_execute_query_respects_max_rows(self, adapter, mock_conn):
        cursor = MagicMock()
        cursor.description = [("n",)]
        cursor.fetchmany.side_effect = [[(i,) for i in range(1000)], []]
        mock_conn.cursor.return_value = cursor

        result = await adapter.execute_query("SELECT n FROM t", max_rows=3)
        assert len(result) == 3

    async def test_check_connection_true(self, adapter, mock_conn):
        cursor = MagicMock()
        cursor.description = [("test",)]
        cursor.fetchmany.side_effect = [[(1,)], []]
        mock_conn.cursor.return_value = cursor

        assert await adapter.check_connection() is True

    async def test_check_connection_false_on_error(self, adapter, mock_conn):
        mock_conn.cursor.side_effect = Exception("connection lost")
        assert await adapter.check_connection() is False

    async def test_disconnect_closes_conn(self, adapter, mock_conn):
        await adapter.disconnect()
        mock_conn.close.assert_called_once()
        assert adapter._conn is None
