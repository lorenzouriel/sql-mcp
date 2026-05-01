# Setup & Testing

## Clone and install

```bash
git clone https://github.com/lorenzouriel/universal-db-mcp.git
cd universal-db-mcp

# With uv (recommended)
uv sync --extra all --extra dev

# Or with pip
pip install -e ".[all,dev]"
```

## Start local databases

Use Docker Compose to spin up Postgres 15, MySQL 8, MongoDB 7, and MSSQL 2022:

```bash
docker compose -f scripts/docker-compose.yml up -d
```

Services and credentials:

| Service | Port | User | Password | Database |
|---------|------|------|----------|----------|
| PostgreSQL | 5432 | testuser | testpass | testdb |
| MySQL | 3306 | testuser | testpass | testdb |
| MongoDB | 27017 | testuser | testpass | testdb |
| MSSQL | 1434 | sa | TestPass123! | master |

## Seed sample data

Load the e-commerce dataset (customers, products, orders, order_items) into all running local databases:

```bash
python scripts/seed_databases.py
```

The script skips any engine whose driver is not installed.

## Run tests

The test suite has two modes:

=== "testcontainers (default)"

    Spins up ephemeral containers per session. Docker must be running.

    ```bash
    pytest
    ```

=== "Docker Compose (faster)"

    Uses already-running containers from `docker-compose.yml`.

    ```bash
    SQL_MCP_TEST_USE_COMPOSE=1 pytest
    ```

### Run specific test targets

```bash
# SQLite only (no Docker required)
pytest tests/test_adapter_sqlite.py

# Security policy
pytest tests/test_security.py

# Tools layer (uses mock adapters)
pytest tests/test_tools.py

# MongoDB integration
SQL_MCP_TEST_USE_COMPOSE=1 pytest tests/test_adapter_mongodb.py

# MSSQL integration (compose-only)
SQL_MCP_TEST_USE_COMPOSE=1 pytest tests/test_adapter_mssql.py

# Databricks (requires live workspace)
DATABRICKS_TEST_DSN="databricks://token@host?http_path=..." pytest tests/test_adapter_databricks.py

# Fabric Warehouse (requires live workspace)
FABRIC_WAREHOUSE_TEST_DSN="Driver={ODBC Driver 18...}" pytest tests/test_adapter_fabric.py
```

### Coverage report

```bash
pytest --cov=src/sql_mcp --cov-report=term-missing
```

## Linting and type checking

```bash
black src/ tests/
ruff check src/ tests/
mypy src/
```

## Project structure

```
src/sql_mcp/
├── cli.py            # Argument parsing + server startup
├── server.py         # FastMCP transport dispatch + HTTP routes
├── tools.py          # All 9 MCP tool definitions
├── models.py         # Pydantic connection config validation
├── registry.py       # Connection registry + adapter lifecycle
├── security.py       # Query validation pipeline
├── metrics.py        # Prometheus metrics
├── health.py         # /health, /ready, /info handlers
├── logging_config.py # JSON logging + sensitive data redaction
├── utils.py          # Output formatters (table, json, csv)
└── adapters/
    ├── base.py        # DatabaseAdapter abstract base class
    ├── mssql.py
    ├── postgres.py
    ├── mysql.py
    ├── sqlite.py
    ├── mongodb.py     # MQL adapter (soft-loaded)
    ├── databricks.py  # SparkSQL adapter (soft-loaded)
    └── fabric.py      # T-SQL + KQL adapter (soft-loaded)
```

## Adding a new adapter

1. Create `src/sql_mcp/adapters/<engine>.py` implementing `DatabaseAdapter`
2. Add a soft-import block in `src/sql_mcp/adapters/__init__.py`
3. Register the adapter in the `ADAPTERS` dict
4. Add an optional extra in `pyproject.toml`
5. Add fixtures in `tests/conftest.py` and a test file `tests/test_adapter_<engine>.py`

The `validate_engine` validator in `models.py` automatically accepts any key added to `ADAPTERS` — no change needed there.
