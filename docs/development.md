# Development

## Setup

```bash
git clone https://github.com/lorenzouriel/sql-mcp.git
cd sql-mcp

# With uv (recommended)
uv sync --extra all --extra dev

# Or with pip
pip install -e ".[all,dev]"
```

## Local databases (Docker)

```bash
docker compose -f scripts/docker-compose.yml up -d
```

| Service | Port | User | Password | Database |
|---------|------|------|----------|----------|
| PostgreSQL | 5432 | testuser | testpass | testdb |
| MySQL | 3306 | testuser | testpass | testdb |
| MongoDB | 27017 | testuser | testpass | testdb |
| MSSQL | 1434 | sa | TestPass123! | master |

Seed sample data (customers, products, orders, order_items):

```bash
python scripts/seed_databases.py
```

## Tests

```bash
pytest                                    # all tests (uses testcontainers)
pytest tests/test_adapter_sqlite.py       # SQLite only (no Docker)
pytest tests/test_security.py             # security policy
pytest tests/test_tools.py                # tools layer (mock adapters)
```

For tests against Docker Compose containers:

```bash
SQL_MCP_TEST_USE_COMPOSE=1 pytest
```

Coverage: `pytest --cov=src/sql_mcp --cov-report=term-missing`

## Linting

```bash
black src/ tests/
ruff check src/ tests/
mypy src/
```

## Docker production image

```bash
docker build -f scripts/Dockerfile -t sql-mcp .

# Single connection
docker run --rm -i sql-mcp --engine postgres --dsn "postgresql://user:pass@host:5432/db"

# Multi-connection
docker run --rm -i -v /path/to/connections.json:/app/connections.json sql-mcp --config /app/connections.json

# HTTP transport
docker run --rm -p 8080:8080 sql-mcp --engine postgres --dsn "postgresql://..." --transport http --bind 0.0.0.0:8080
```

HTTP endpoints: `GET /health`, `GET /ready`, `GET /info`, `GET /metrics`

## Project structure

```
src/sql_mcp/
├── cli.py            # Argument parsing + startup
├── server.py         # FastMCP transport + HTTP routes
├── tools.py          # 9 MCP tool definitions
├── models.py         # Pydantic config validation
├── registry.py       # Connection registry + lifecycle
├── security.py       # Query validation pipeline
├── metrics.py        # Prometheus metrics
├── health.py         # Health endpoints
├── logging_config.py # JSON logging + redaction
├── utils.py          # Output formatters
└── adapters/
    ├── base.py        # DatabaseAdapter ABC
    ├── mssql.py
    ├── postgres.py
    ├── mysql.py
    ├── sqlite.py
    ├── mongodb.py     # soft-loaded
    ├── databricks.py  # soft-loaded
    └── fabric.py      # soft-loaded
```

## Adding a new adapter

1. Create `src/sql_mcp/adapters/<engine>.py` implementing `DatabaseAdapter`
2. Add a soft-import block in `src/sql_mcp/adapters/__init__.py`
3. Register in the `ADAPTERS` dict
4. Add an optional extra in `pyproject.toml`
5. Add test file `tests/test_adapter_<engine>.py`
