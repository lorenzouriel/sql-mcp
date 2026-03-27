# sql-mcp

> Universal SQL MCP server — connect Claude to MSSQL, PostgreSQL, MySQL, MariaDB, and SQLite through a single interface.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![MCP](https://img.shields.io/badge/MCP-1.2%2B-purple)
![Version](https://img.shields.io/badge/version-2.0.0-blue)

## Overview

sql-mcp is a [Model Context Protocol](https://modelcontextprotocol.io/) server that gives Claude (and any other MCP-compatible client) direct, structured access to your databases. Instead of copy-pasting query results into a chat window, Claude can explore schemas, run queries, and reason over live data on your behalf.

The server supports five database engines — Microsoft SQL Server, PostgreSQL, MySQL, MariaDB, and SQLite — behind a single binary. You can connect to one database for a focused workflow, or register up to twenty connections simultaneously and let Claude query across all of them in a single conversation.

sql-mcp evolved from `mssql-mcp-python` and is designed for developers and data teams who want to bring AI-assisted SQL into their existing infrastructure without giving up control. Every connection defaults to read-only mode, and a layered security policy blocks destructive SQL patterns before they ever reach the database.

## Features

- Single server for MSSQL, PostgreSQL, MySQL, MariaDB, and SQLite
- Multi-connection registry — up to 20 named connections in one session
- Read-only by default with an explicit opt-in for writes
- Per-engine banned pattern lists block destructive DDL, system procedures, and file I/O commands
- Multi-statement query blocking prevents semicolon-chained attacks
- Per-connection query timeout (1–300 seconds) and row cap (1–500,000)
- Three output formats: table, JSON, and CSV
- Structured JSON logging with configurable log level
- Prometheus metrics endpoint (HTTP transport)
- HTTP transport with `/health`, `/ready`, `/info`, and `/metrics` endpoints
- Backward-compatible with `MSSQL_CONNECTION_STRING` environment variable from v1

## Quick Start

### Prerequisites

- Python 3.10 or later
- For MSSQL: [ODBC Driver 17 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
- Claude Desktop (or any MCP client)

### Installation

Install the package with the extras for the database engines you need:

```bash
# SQL Server only
pip install "sql-mcp[mssql]"

# PostgreSQL only
pip install "sql-mcp[postgres]"

# MySQL / MariaDB only
pip install "sql-mcp[mysql]"

# All engines
pip install "sql-mcp[all]"

# SQLite ships with Python — no extra required
pip install sql-mcp
```

### Connect to Claude Desktop

Open your Claude Desktop configuration file and add an entry under `mcpServers`.

> **Windows note:** Claude Desktop does not inherit your shell's PATH, so you must use the **full absolute path** to the `sql-mcp` executable inside your virtual environment (e.g. `C:/Users/you/project/.venv/Scripts/sql-mcp.exe`). On macOS/Linux the short name `sql-mcp` works if you install globally (`pipx install sql-mcp`).

**Single connection — PostgreSQL example:**

```json
{
  "mcpServers": {
    "sql-mcp": {
      "command": "C:/Users/you/project/.venv/Scripts/sql-mcp.exe",
      "args": ["--transport", "stdio", "--engine", "postgres", "--dsn", "postgresql://user:pass@localhost:5432/mydb"]
    }
  }
}
```

**Multi-connection — config file:**

```json
{
  "mcpServers": {
    "sql-mcp": {
      "command": "C:/Users/you/project/.venv/Scripts/sql-mcp.exe",
      "args": ["--transport", "stdio", "--config", "C:/path/to/connections.json"]
    }
  }
}
```

**macOS / Linux (global install via pipx):**

```json
{
  "mcpServers": {
    "sql-mcp": {
      "command": "sql-mcp",
      "args": ["--transport", "stdio", "--config", "/path/to/connections.json"]
    }
  }
}
```

The Claude Desktop configuration file is located at:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

After editing the file, **restart Claude Desktop** for the changes to take effect.

### Basic Usage (single-connection)

Start the server from the command line for any supported engine:

```bash
# SQL Server
sql-mcp --engine mssql --dsn "Driver={ODBC Driver 17 for SQL Server};Server=localhost;Database=mydb;UID=sa;PWD=secret"

# PostgreSQL
sql-mcp --engine postgres --dsn "postgresql://user:pass@localhost:5432/mydb"

# MySQL
sql-mcp --engine mysql --dsn "mysql://user:pass@localhost:3306/mydb"

# SQLite
sql-mcp --engine sqlite --dsn "/path/to/app.db"

# Enable write operations (read-only is the default)
sql-mcp --engine postgres --dsn "postgresql://..." --write
```

## Multi-Connection Setup

Create a `connections.json` file to register multiple databases:

```json
{
  "connections": [
    {
      "id": "prod_mssql",
      "engine": "mssql",
      "dsn": "Driver={ODBC Driver 17 for SQL Server};Server=prod-sql.internal,1433;Database=orders;UID=ro_user;PWD=secret",
      "read_only": true,
      "description": "Production MSSQL — orders database",
      "query_timeout": 30,
      "max_rows": 10000
    },
    {
      "id": "analytics_pg",
      "engine": "postgres",
      "dsn": "postgresql://analyst:secret@analytics.internal:5432/dw",
      "read_only": true,
      "description": "Analytics Postgres data warehouse",
      "query_timeout": 60,
      "max_rows": 50000
    },
    {
      "id": "app_mysql",
      "engine": "mysql",
      "dsn": "mysql://app_user:secret@app-db.internal:3306/appdb",
      "read_only": false,
      "description": "Application MySQL — read/write access",
      "query_timeout": 10,
      "max_rows": 5000
    }
  ]
}
```

Start the server with the config file:

```bash
sql-mcp --config connections.json
```

You can also pass the connection list as an environment variable:

```bash
export SQL_MCP_CONNECTIONS='[
  {"id":"prod_sql","engine":"mssql","dsn":"Driver=...","read_only":true},
  {"id":"analytics","engine":"postgres","dsn":"postgresql://...","read_only":true}
]'
sql-mcp
```

Once connected, use `list_connections` in Claude to see available databases, then pass `connection_id` to any tool to target a specific one.

## MCP Tools Reference

All eight tools are available to Claude once the server is running. Tools that accept a `connection_id` parameter use the default connection when the parameter is omitted.

| Tool | Description |
|------|-------------|
| `execute_sql` | Execute a SQL query. Supports `table`, `json`, and `csv` output formats. Enforces the connection's security policy before execution. |
| `list_schemas` | List all schemas available in the connected database. |
| `list_tables` | List tables within a schema. Accepts an optional `schema` filter and a `limit` (max 1000). |
| `schema_discovery` | Return full column-level metadata for all tables in a schema, including data types and nullability. |
| `get_database_info` | Return server and database metadata: engine version, database name, and connection details. |
| `get_policy_info` | Show the active security policy for a connection: read-only status, timeout, row cap, query length limit, and banned pattern count. |
| `check_db_connection` | Health check — verify that the connection to the database is alive. |
| `list_connections` | List all registered database connections with their IDs, engines, and descriptions. Use this first when multiple connections are configured. |

## Security

sql-mcp treats security as a first-class concern, not an afterthought. Every query passes through a validation pipeline before it reaches the database.

**Read-only by default.** All connections start in read-only mode. In this mode, only `SELECT` statements are permitted — any query containing `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `CREATE`, `GRANT`, `DENY`, or `REVOKE` is rejected immediately. Write access requires an explicit `--write` flag or `"read_only": false` in the connection config.

**Engine-specific banned patterns.** Beyond the write-operation check, each engine has a curated list of banned patterns that are blocked regardless of read/write mode:

| Engine | Additional blocked patterns |
|--------|-----------------------------|
| MSSQL | `EXEC`, `EXECUTE`, `xp_*`, `sp_*`, `KILL`, `SHUTDOWN`, `OPENROWSET`, `OPENDATASOURCE`, `BULK INSERT` |
| PostgreSQL | `COPY`, `pg_read_file`, `pg_write_file`, `lo_import`, `lo_export` |
| MySQL / MariaDB | `LOAD DATA`, `INTO OUTFILE`, `INTO DUMPFILE`, `LOAD_FILE` |
| SQLite | `ATTACH`, `DETACH` |
| All engines | `DROP`, `ALTER`, `TRUNCATE`, `CREATE`, `GRANT`, `REVOKE` |

**Multi-statement blocking.** Queries containing more than one statement (semicolons between statements, or `GO` separators in MSSQL) are rejected, preventing semicolon-chained injection attacks.

**Query length cap.** Queries longer than 50,000 characters are rejected before parsing.

**Per-connection row and timeout limits.** Each connection enforces an independent row cap (default 50,000, maximum 500,000) and query timeout (default 30 seconds, maximum 300 seconds). Long-running or large-result queries are terminated at the database level.

**Audit logging.** Every allowed and denied query is logged with the tool name, mode (read-only or write), and a SHA-256 hash of the SQL text. Denied queries also log the specific reason. The active security policy for any connection can be inspected at runtime via the `get_policy_info` tool.

## Configuration Reference

### Single Connection (Environment Variables)

| Variable | Default | Description |
|----------|---------|-------------|
| `MSSQL_CONNECTION_STRING` | — | ODBC connection string. Triggers legacy MSSQL mode (backward-compatible with v1). |
| `READ_ONLY` | `true` | Set to `false` to allow writes in legacy mode. |
| `ENABLE_WRITES` | `false` | Must be `true` AND `ADMIN_CONFIRM` must be non-empty to disable read-only in legacy mode. |
| `ADMIN_CONFIRM` | — | Confirmation token required alongside `ENABLE_WRITES=true`. |
| `SQL_MCP_CONNECTIONS` | — | JSON array of connection objects. Takes priority over `MSSQL_CONNECTION_STRING`. |
| `LOG_LEVEL` | `INFO` | Log verbosity: `DEBUG`, `INFO`, `WARNING`, or `ERROR`. |
| `LOG_FORMAT` | `json` | Log output format: `json` or `text`. |
| `MAX_QUERY_LENGTH` | `50000` | Maximum permitted query length in characters. |

### CLI Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--engine` | — | Database engine: `mssql`, `postgres`, `mysql`, `mariadb`, or `sqlite`. |
| `--dsn` | — | Connection string or DSN for the database. |
| `--config` | — | Path to a `connections.json` file for multi-connection mode. |
| `--write` | `false` | Enable write operations. Read-only by default. |
| `--transport` | `stdio` | Transport protocol: `stdio` (Claude Desktop) or `http`. |
| `--bind` | `127.0.0.1:8080` | Bind address for HTTP transport. |
| `--log-level` | `INFO` | Log verbosity. |
| `--log-format` | `json` | Log format: `json` or `text`. |

### Multi-Connection (JSON Config)

Each entry in the `connections` array accepts these fields:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | string | yes | — | Unique identifier. Lowercase letters, digits, and underscores. 2–31 characters. Must start with a letter. |
| `engine` | string | yes | — | One of: `mssql`, `postgres`, `mysql`, `mariadb`, `sqlite`. |
| `dsn` | string | yes | — | Connection string for the database engine. |
| `read_only` | boolean | no | `true` | When `true`, only `SELECT` queries are permitted. |
| `query_timeout` | integer | no | `30` | Query timeout in seconds. Range: 1–300. |
| `max_rows` | integer | no | `50000` | Maximum rows returned per query. Range: 1–500,000. |
| `description` | string | no | `""` | Human-readable label shown in `list_connections`. |

A maximum of 20 connections can be registered per server instance.

## Installation Options

Install only the drivers you need to keep the dependency footprint small:

```bash
# MSSQL (requires ODBC Driver 17 on the host)
pip install "sql-mcp[mssql]"

# PostgreSQL
pip install "sql-mcp[postgres]"

# MySQL and MariaDB
pip install "sql-mcp[mysql]"

# All database drivers
pip install "sql-mcp[all]"

# Development dependencies (testing, linting, type checking)
pip install "sql-mcp[dev]"
```

SQLite is supported without any additional extras because the `sqlite3` module is part of the Python standard library.

## Docker

The provided Dockerfile builds an image with all database drivers pre-installed, including the Microsoft ODBC Driver 17 for SQL Server.

```bash
# Build the image
docker build -t sql-mcp .

# Run with a PostgreSQL connection
docker run --rm -i \
  sql-mcp \
  --engine postgres \
  --dsn "postgresql://user:pass@host.docker.internal:5432/mydb"

# Run with HTTP transport for use in a service mesh
docker run --rm -p 8080:8080 \
  sql-mcp \
  --engine postgres \
  --dsn "postgresql://user:pass@db:5432/mydb" \
  --transport http \
  --bind 0.0.0.0:8080
```

When using HTTP transport, the following endpoints are available:

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Liveness check — returns `{"status": "alive"}` |
| `GET /ready` | Readiness check — verifies all connections are reachable |
| `GET /info` | Server metadata and registered connection list |
| `GET /metrics` | Prometheus metrics in text format |

## Development

### Setup

```bash
git clone https://github.com/lorenzouriel/universal-db-mcp.git
cd universal-db-mcp

# Install all drivers and development dependencies
pip install -e ".[all,dev]"
```

### Running Tests

The test suite uses [testcontainers](https://testcontainers-python.readthedocs.io/) for PostgreSQL and MySQL integration tests. Docker must be running on the host for those tests to execute.

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=term-missing

# Run only SQLite tests (no Docker required)
pytest tests/test_adapter_sqlite.py

# Run security policy tests
pytest tests/test_security.py

# Run a specific test file
pytest tests/test_tools.py -v
```

## Contributing

Contributions are welcome. Please open an issue to discuss significant changes before submitting a pull request.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Run tests and linting before committing

```bash
pytest
black src/ tests/
ruff check src/ tests/
mypy src/
```

4. Open a pull request against `main`

Bug reports and feature requests can be filed on the [issue tracker](https://github.com/lorenzouriel/universal-db-mcp/issues).

## License

MIT License. See [LICENSE](LICENSE) for details.
