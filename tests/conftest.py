"""
Test fixtures for sql-mcp integration tests.

Two modes:
  - Docker Compose (fast): set SQL_MCP_TEST_USE_COMPOSE=1
    Expects containers from docker-compose.yml to already be running.
  - testcontainers (default): spins up ephemeral containers per session.
    Skipped if the testcontainers package is not installed.
"""
import os
import pytest


# ---------------------------------------------------------------------------
# DSN constants when using docker-compose.yml containers
# ---------------------------------------------------------------------------
_COMPOSE_POSTGRES_DSN = "postgresql://testuser:testpass@localhost:5432/testdb"
_COMPOSE_MYSQL_DSN    = "mysql://testuser:testpass@localhost:3306/testdb"
_COMPOSE_MSSQL_DSN    = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=localhost,1434;"
    "Database=master;"
    "UID=sa;"
    "PWD=TestPass123!;"
    "TrustServerCertificate=yes;"
    "Encrypt=no;"
)

_USE_COMPOSE = os.environ.get("SQL_MCP_TEST_USE_COMPOSE", "").lower() in ("1", "true", "yes")


# ---------------------------------------------------------------------------
# Postgres
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def postgres_dsn():
    if _USE_COMPOSE:
        yield _COMPOSE_POSTGRES_DSN
        return

    try:
        from testcontainers.postgres import PostgresContainer
    except ImportError:
        pytest.skip("testcontainers not installed — set SQL_MCP_TEST_USE_COMPOSE=1 to use docker-compose")

    with PostgresContainer("postgres:15") as pg:
        url = pg.get_connection_url()
        yield url.replace("postgresql+psycopg2://", "postgresql://")


# ---------------------------------------------------------------------------
# MySQL
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def mysql_dsn():
    if _USE_COMPOSE:
        yield _COMPOSE_MYSQL_DSN
        return

    try:
        from testcontainers.mysql import MySqlContainer
    except ImportError:
        pytest.skip("testcontainers not installed — set SQL_MCP_TEST_USE_COMPOSE=1 to use docker-compose")

    with MySqlContainer("mysql:8") as mysql:
        yield mysql.get_connection_url()


# ---------------------------------------------------------------------------
# MSSQL  (compose-only; testcontainers-mssql requires heavy setup)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def mssql_dsn():
    if not _USE_COMPOSE:
        pytest.skip("MSSQL integration tests require docker-compose — set SQL_MCP_TEST_USE_COMPOSE=1")
    yield _COMPOSE_MSSQL_DSN


# ---------------------------------------------------------------------------
# MongoDB
# ---------------------------------------------------------------------------

_COMPOSE_MONGODB_DSN = "mongodb://testuser:testpass@localhost:27017/testdb?authSource=admin"


@pytest.fixture(scope="session")
def mongodb_dsn():
    if _USE_COMPOSE:
        yield _COMPOSE_MONGODB_DSN
        return

    try:
        from testcontainers.mongodb import MongoDbContainer
    except ImportError:
        pytest.skip("testcontainers not installed — set SQL_MCP_TEST_USE_COMPOSE=1 to use docker-compose")

    with MongoDbContainer("mongo:7") as mongo:
        yield mongo.get_connection_url()


# ---------------------------------------------------------------------------
# Databricks  (cloud-only; requires env var)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def databricks_dsn():
    dsn = os.environ.get("DATABRICKS_TEST_DSN")
    if not dsn:
        pytest.skip("Set DATABRICKS_TEST_DSN env var to run Databricks integration tests")
    yield dsn


# ---------------------------------------------------------------------------
# Fabric Warehouse  (cloud-only; requires env var)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def fabric_warehouse_dsn():
    dsn = os.environ.get("FABRIC_WAREHOUSE_TEST_DSN")
    if not dsn:
        pytest.skip("Set FABRIC_WAREHOUSE_TEST_DSN env var to run Fabric Warehouse integration tests")
    yield dsn


# ---------------------------------------------------------------------------
# SQLite  (always available, no container needed)
# ---------------------------------------------------------------------------

@pytest.fixture
def sqlite_dsn(tmp_path):
    return str(tmp_path / "test.db")
