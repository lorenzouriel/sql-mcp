<div align="center">
  <img src="docs/imgs/logo-only-nobg.png" alt="logo" width="200">
</div>

# sql-mcp
> One MCP to rule them all — connect Claude/Frameworks to MSSQL, PostgreSQL, MySQL, MariaDB, SQLite, MongoDB, Databricks, and Microsoft Fabric through a single interface.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![MCP](https://img.shields.io/badge/MCP-1.2%2B-purple)
![Version](https://img.shields.io/badge/version-3.0.0-blue)

## Overview
sql-mcp is a [Model Context Protocol](https://modelcontextprotocol.io/) server that gives Claude (and any other MCP-compatible client) direct, structured access to your databases. Instead of copy-pasting query results into a chat window, Claude can explore schemas, run queries, and reason over live data on your behalf.

The server supports **eight database engines** — Microsoft SQL Server, PostgreSQL, MySQL, MariaDB, SQLite, MongoDB, Databricks, and Microsoft Fabric — behind a single binary. You can connect to one database for a focused workflow, or register up to twenty connections simultaneously and let Claude query across all of them in a single conversation.

SQL engines use standard SQL. MongoDB uses MQL (JSON-based filter or aggregation pipeline). Databricks uses SparkSQL. Microsoft Fabric supports both T-SQL (Warehouse) and KQL (Eventhouse). The MCP surface is identical regardless of engine — Claude picks the right tool automatically.

Every connection defaults to read-only mode, and a layered security policy blocks destructive patterns before they ever reach the database.

## Features

- Single server for MSSQL, PostgreSQL, MySQL, MariaDB, SQLite, MongoDB, Databricks, and Microsoft Fabric
- Multi-connection registry — up to 20 named connections in one session
- Read-only by default with an explicit opt-in for writes
- `execute_native_query` for MongoDB MQL and other non-SQL engines
- Per-engine banned pattern lists block destructive DDL, system procedures, and file I/O commands
- MongoDB-specific security: `$where`, `$function`, `$accumulator`, `$out`, `$merge` blocked
- Multi-statement query blocking prevents semicolon-chained attacks
- Per-connection query timeout (1–300 seconds) and row cap (1–500,000)
- Three output formats: table, JSON, and CSV
- Optional adapters via Python extras — base install stays lean
- Structured JSON logging with configurable log level and sensitive data redaction
- Prometheus metrics endpoint (HTTP transport)
- HTTP transport with `/health`, `/ready`, `/info`, and `/metrics` endpoints
- Backward-compatible with `MSSQL_CONNECTION_STRING` environment variable from v1

## Quick Start

### Prerequisites

- Python 3.10 or later
- For MSSQL / Fabric Warehouse: [ODBC Driver 17 or 18 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
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

# MongoDB only
pip install "sql-mcp[mongodb]"

# Databricks only
pip install "sql-mcp[databricks]"

# Microsoft Fabric (Warehouse + Eventhouse)
pip install "sql-mcp[fabric]"

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

### Basic Usage

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

# MongoDB
sql-mcp --engine mongodb --dsn "mongodb://user:pass@localhost:27017/mydb?authSource=admin"

# Databricks
sql-mcp --engine databricks --dsn "databricks://token@<host>?http_path=/sql/1.0/warehouses/<id>&catalog=main&schema=default"

# Microsoft Fabric Warehouse
sql-mcp --engine fabric --dsn "Driver={ODBC Driver 18 for SQL Server};Server=<workspace>.datawarehouse.fabric.microsoft.com;UID=user@org.com;PWD=secret;Authentication=ActiveDirectoryPassword;Encrypt=yes;"

# Enable write operations (read-only is the default)
sql-mcp --engine postgres --dsn "postgresql://..." --write
```

## Multi-Connection Setup

Create a `connections.json` file to register multiple databases across any combination of engines:

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
      "id": "app_mongodb",
      "engine": "mongodb",
      "dsn": "mongodb://user:pass@mongo.internal:27017/appdb?authSource=admin",
      "read_only": true,
      "description": "Application MongoDB — document store",
      "query_timeout": 30,
      "max_rows": 5000
    },
    {
      "id": "datalake",
      "engine": "databricks",
      "dsn": "databricks://token@<host>?http_path=/sql/1.0/warehouses/<id>&catalog=main",
      "read_only": true,
      "description": "Databricks SQL Warehouse",
      "query_timeout": 60,
      "max_rows": 10000
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

Once connected, use `list_connections` in Claude to see all available databases, then pass `connection_id` to any tool to target a specific one.

A working six-engine reference configuration is available at [`examples/connections.json`](examples/connections.json).

## MCP Tools Reference

All nine tools are available to Claude once the server is running. Tools that accept a `connection_id` parameter use the default connection when the parameter is omitted.

| Tool | Description |
|------|-------------|
| `list_connections` | List all registered database connections with their IDs, engines, read-only status, and descriptions. **Use this first** when multiple connections are configured. |
| `execute_sql` | Execute a SQL (or SparkSQL / KQL) query. Supports `table`, `json`, and `csv` output formats. Enforces the connection's security policy before execution. |
| `execute_native_query` | Execute a native non-SQL query on a document store. Pass `query` as a JSON string — a `{}` dict for MongoDB MQL filter/find, or a `[]` list for an aggregation pipeline. Use `collection` to target a specific collection. For SQL/SparkSQL/KQL engines, use `execute_sql`. |
| `list_schemas` | List all schemas available in the connected database. |
| `list_tables` | List tables within a schema. Accepts an optional `schema` filter and a `limit` (max 1000). |
| `schema_discovery` | Return full column-level metadata for all tables in a schema, including data types and nullability. |
| `get_database_info` | Return server and database metadata: engine version, database name, query language, and connection details. |
| `get_policy_info` | Show the active security policy for a connection: read-only status, timeout, row cap, query length limit, and banned pattern count. |
| `check_db_connection` | Health check — verify that the connection to the database is alive. |

### Querying MongoDB

MongoDB uses MQL, not SQL. Use `execute_native_query` with a JSON string:

```
# Find all customers in Brazil
execute_native_query(
  query='{"country": "Brazil"}',
  collection="customers",
  connection_id="app_mongodb"
)

# Aggregation pipeline — total revenue by country
execute_native_query(
  query='[{"$group": {"_id": "$country", "total": {"$sum": "$total"}}}]',
  collection="orders",
  connection_id="app_mongodb"
)
```

## DSN Formats

| Engine | DSN Format |
|--------|-----------|
| MSSQL | `Driver={ODBC Driver 17 for SQL Server};Server=host,port;Database=db;UID=user;PWD=pass;TrustServerCertificate=yes;` |
| PostgreSQL | `postgresql://user:pass@host:5432/db` |
| MySQL / MariaDB | `mysql://user:pass@host:3306/db` |
| SQLite | `/path/to/file.db` or `:memory:` |
| MongoDB | `mongodb://user:pass@host:27017/db?authSource=admin` |
| Databricks | `databricks://token@<host>?http_path=<path>[&catalog=<c>][&schema=<s>]` |
| Fabric Warehouse | `Driver={ODBC Driver 18 for SQL Server};Server=<workspace>.datawarehouse.fabric.microsoft.com;UID=user@org;PWD=pass;Authentication=ActiveDirectoryPassword;Encrypt=yes;` |
| Fabric Eventhouse | `kql://<cluster_hostname>/<database>` |

> **MongoDB note:** Users created via `MONGO_INITDB_ROOT_*` live in the `admin` database. Always append `?authSource=admin` to the DSN if authentication fails.

> **Databricks note:** The DSN token is the personal access token (PAT). The `http_path` parameter is required; `catalog` and `schema` are optional and set the active context on connect.

> **Fabric Warehouse note:** Use `Authentication=ActiveDirectoryPassword` with explicit `UID` and `PWD` for non-interactive/background processes. `ActiveDirectoryInteractive` requires a browser popup.

## Security

sql-mcp treats security as a first-class concern, not an afterthought. Every query passes through a validation pipeline before it reaches the database.

**Read-only by default.** All connections start in read-only mode. Only `SELECT` statements are permitted — any query containing `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `CREATE`, `GRANT`, `DENY`, or `REVOKE` is rejected immediately. Write access requires an explicit `--write` flag or `"read_only": false` in the connection config.

**Engine-specific banned patterns.** Each engine has a curated list of patterns blocked regardless of read/write mode:

| Engine | Additional blocked patterns |
|--------|-----------------------------|
| MSSQL | `EXEC`, `EXECUTE`, `xp_*`, `sp_*`, `KILL`, `SHUTDOWN`, `OPENROWSET`, `OPENDATASOURCE`, `BULK INSERT` |
| PostgreSQL | `COPY`, `pg_read_file`, `pg_write_file`, `lo_import`, `lo_export` |
| MySQL / MariaDB | `LOAD DATA`, `INTO OUTFILE`, `INTO DUMPFILE`, `LOAD_FILE` |
| SQLite | `ATTACH`, `DETACH` |
| MongoDB (MQL) | `$where`, `$function`, `$accumulator`, `$out`, `$merge` |
| KQL (Fabric Eventhouse) | `externaldata`, `plugin` |
| All engines | `DROP`, `ALTER`, `TRUNCATE`, `CREATE`, `GRANT`, `REVOKE` |

**Multi-statement blocking.** Queries containing more than one statement (semicolons between statements, or `GO` separators in MSSQL) are rejected, preventing semicolon-chained injection attacks.

**Query length cap.** Queries longer than 50,000 characters are rejected before parsing.

**Per-connection row and timeout limits.** Each connection enforces an independent row cap (default 50,000, maximum 500,000) and query timeout (default 30 seconds, maximum 300 seconds).

**Audit logging.** Every allowed and denied query is logged with the tool name, mode (read-only or write), and a SHA-256 hash of the SQL text. Denied queries also log the specific reason. The active security policy for any connection can be inspected at runtime via the `get_policy_info` tool.

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MSSQL_CONNECTION_STRING` | — | ODBC connection string. Triggers legacy MSSQL mode (backward-compatible with v1). |
| `READ_ONLY` | `true` | Set to `false` to allow writes in legacy mode. |
| `ENABLE_WRITES` | `false` | Must be `true` AND `ADMIN_CONFIRM` must be non-empty to disable read-only in legacy mode. |
| `ADMIN_CONFIRM` | — | Confirmation token required alongside `ENABLE_WRITES=true`. |
| `SQL_MCP_CONNECTIONS` | — | JSON array of connection objects. Takes priority over `MSSQL_CONNECTION_STRING`. |
| `LOG_LEVEL` | `INFO` | Log verbosity: `DEBUG`, `INFO`, `WARNING`, or `ERROR`. |
| `LOG_FORMAT` | `json` | Log output format: `json` or `text`. |
| `ENABLE_METRICS` | `true` | Enable Prometheus metrics collection. |
| `MAX_QUERY_LENGTH` | `50000` | Maximum permitted query length in characters. |

### CLI Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--engine` | — | Database engine: `mssql`, `postgres`, `mysql`, `mariadb`, `sqlite`, `mongodb`, `databricks`, or `fabric`. |
| `--dsn` | — | Connection string or DSN for the database. |
| `--config` | — | Path to a `connections.json` file for multi-connection mode. |
| `--write` | `false` | Enable write operations. Read-only by default. |
| `--transport` | `stdio` | Transport protocol: `stdio` (Claude Desktop) or `http`. |
| `--bind` | `127.0.0.1:8080` | Bind address for HTTP transport. |
| `--log-level` | `INFO` | Log verbosity. |
| `--log-format` | `json` | Log format: `json` or `text`. |

### Multi-Connection JSON Config Fields

Each entry in the `connections` array accepts these fields:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | string | yes | — | Unique identifier. Lowercase letters, digits, and underscores. 2–31 characters. Must start with a letter. |
| `engine` | string | yes | — | One of: `mssql`, `postgres`, `mysql`, `mariadb`, `sqlite`, `mongodb`, `databricks`, `fabric`. |
| `dsn` | string | yes | — | Connection string for the database engine. See [DSN Formats](#dsn-formats). |
| `read_only` | boolean | no | `true` | When `true`, only `SELECT` (or read-equivalent) queries are permitted. |
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

# MongoDB
pip install "sql-mcp[mongodb]"

# Databricks
pip install "sql-mcp[databricks]"

# Microsoft Fabric (Warehouse T-SQL + Eventhouse KQL)
pip install "sql-mcp[fabric]"

# All database drivers
pip install "sql-mcp[all]"

# Development dependencies (testing, linting, type checking)
pip install "sql-mcp[dev]"
```

SQLite is supported without any additional extras because the `sqlite3` module is part of the Python standard library.

MongoDB, Databricks, and Fabric adapters are soft-loaded — if their driver packages are absent, the server still starts for the remaining engines.

## Docker

The provided Dockerfile builds an image with all database drivers pre-installed, including the Microsoft ODBC Driver 17 for SQL Server.

```bash
# Build the image
docker build -f scripts/Dockerfile -t sql-mcp .

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

### Spinning Up Local Databases

Use Docker Compose to start Postgres, MySQL, MongoDB, and MSSQL containers:

```bash
docker compose -f scripts/docker-compose.yml up -d
```

Then seed all local databases with the e-commerce sample dataset:

```bash
python scripts/seed_databases.py
```

### Running Tests

The test suite uses [testcontainers](https://testcontainers-python.readthedocs.io/) for PostgreSQL and MySQL integration tests by default. Docker must be running on the host. Alternatively, point tests at running Docker Compose containers:

```bash
# Run all tests (testcontainers mode — spins up ephemeral containers)
pytest

# Run against docker-compose containers (faster, no container spin-up)
SQL_MCP_TEST_USE_COMPOSE=1 pytest

# Run only SQLite tests (no Docker required)
pytest tests/test_adapter_sqlite.py

# Run security policy tests
pytest tests/test_security.py

# Run Databricks integration tests (requires live Databricks workspace)
DATABRICKS_TEST_DSN="databricks://token@host?http_path=..." pytest tests/test_adapter_databricks.py

# Run Fabric Warehouse integration tests (requires live Fabric workspace)
FABRIC_WAREHOUSE_TEST_DSN="Driver={ODBC Driver 18...}" pytest tests/test_adapter_fabric.py
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
