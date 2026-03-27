import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from sql_mcp.models import ConnectionConfig
from sql_mcp.registry import ConnectionRegistry


def _sqlite_config(conn_id: str = "default", read_only: bool = True) -> ConnectionConfig:
    return ConnectionConfig(
        id=conn_id,
        engine="sqlite",
        dsn=":memory:",
        read_only=read_only,
    )


@pytest.fixture
async def registry_with_sqlite():
    registry = ConnectionRegistry()
    await registry.register(_sqlite_config("db1"))
    return registry


class TestSingleConnection:

    async def test_resolve_without_id_returns_only_connection(self):
        registry = ConnectionRegistry()
        await registry.register(_sqlite_config("default"))
        entry = registry.resolve()
        assert entry.config.id == "default"

    async def test_resolve_with_matching_id(self):
        registry = ConnectionRegistry()
        await registry.register(_sqlite_config("mydb"))
        entry = registry.resolve("mydb")
        assert entry.config.id == "mydb"

    async def test_resolve_unknown_id_raises(self):
        registry = ConnectionRegistry()
        await registry.register(_sqlite_config("default"))
        with pytest.raises(ValueError, match="Unknown connection"):
            registry.resolve("does_not_exist")

    async def test_resolve_no_connections_raises(self):
        registry = ConnectionRegistry()
        with pytest.raises(ValueError, match="No connections registered"):
            registry.resolve()

    async def test_count(self):
        registry = ConnectionRegistry()
        assert registry.count == 0
        await registry.register(_sqlite_config())
        assert registry.count == 1


class TestMultiConnection:

    async def test_resolve_requires_id_with_multiple_connections(self):
        registry = ConnectionRegistry()
        await registry.register(_sqlite_config("db1"))
        await registry.register(_sqlite_config("db2"))
        with pytest.raises(ValueError, match="Specify connection_id"):
            registry.resolve()

    async def test_resolve_routes_to_correct_connection(self):
        registry = ConnectionRegistry()
        await registry.register(_sqlite_config("db1"))
        await registry.register(_sqlite_config("db2"))
        entry = registry.resolve("db2")
        assert entry.config.id == "db2"

    async def test_error_message_lists_available_ids(self):
        registry = ConnectionRegistry()
        await registry.register(_sqlite_config("alpha"))
        await registry.register(_sqlite_config("beta"))
        with pytest.raises(ValueError) as exc_info:
            registry.resolve("gamma")
        assert "alpha" in str(exc_info.value)
        assert "beta" in str(exc_info.value)

    async def test_list_connections_returns_all(self):
        registry = ConnectionRegistry()
        await registry.register(_sqlite_config("db1"))
        await registry.register(_sqlite_config("db2"))
        connections = registry.list_connections()
        assert len(connections) == 2
        ids = {c["id"] for c in connections}
        assert ids == {"db1", "db2"}

    async def test_list_connections_metadata(self):
        registry = ConnectionRegistry()
        await registry.register(
            ConnectionConfig(
                id="mydb",
                engine="sqlite",
                dsn=":memory:",
                read_only=True,
                description="Test DB",
            )
        )
        conn = registry.list_connections()[0]
        assert conn["engine"] == "sqlite"
        assert conn["read_only"] is True
        assert conn["description"] == "Test DB"
        assert conn["status"] == "connected"


class TestRegisterAll:

    async def test_register_all_returns_results(self):
        registry = ConnectionRegistry()
        configs = [_sqlite_config("a"), _sqlite_config("b")]
        results = await registry.register_all(configs)
        assert results["a"] is None
        assert results["b"] is None

    async def test_duplicate_id_raises(self):
        registry = ConnectionRegistry()
        await registry.register(_sqlite_config("dup"))
        with pytest.raises(ValueError, match="already registered"):
            await registry.register(_sqlite_config("dup"))

    async def test_register_all_partial_failure_continues(self):
        registry = ConnectionRegistry()
        configs = [
            _sqlite_config("ok"),
            ConnectionConfig(id="bad", engine="sqlite", dsn="/nonexistent/path/db.sqlite"),
        ]
        results = await registry.register_all(configs)
        assert results["ok"] is None
        assert results["bad"] is not None  # error message


class TestPolicyIsolation:

    async def test_per_connection_read_only(self):
        registry = ConnectionRegistry()
        await registry.register(_sqlite_config("ro", read_only=True))
        await registry.register(_sqlite_config("rw", read_only=False))

        ro = registry.resolve("ro")
        rw = registry.resolve("rw")

        assert ro.policy.read_only is True
        assert rw.policy.read_only is False
