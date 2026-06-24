# Getting Started

## Prerequisites

- Python 3.10+
- Claude Desktop or any MCP-compatible client
- For MSSQL / Fabric: [ODBC Driver 17 or 18 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)

## Install

Install with the extras for the engines you need:

```bash
pip install "sql-mcp[all]"          # every engine
pip install "sql-mcp[postgres]"     # just PostgreSQL
pip install "sql-mcp[mssql]"        # just SQL Server
pip install "sql-mcp[mongodb]"      # just MongoDB
pip install "sql-mcp[databricks]"   # just Databricks
pip install "sql-mcp[fabric]"       # just Fabric
```

SQLite needs no extra — `sqlite3` ships with Python.

| Extra | Packages installed |
|-------|--------------------|
| `mssql` | `pyodbc` |
| `postgres` | `psycopg2-binary` |
| `mysql` | `mysql-connector-python` |
| `mongodb` | `pymongo` |
| `databricks` | `databricks-sql-connector` |
| `fabric` | `pyodbc`, `azure-kusto-data` |
| `all` | All of the above |
| `dev` | pytest, black, ruff, mypy, testcontainers |

Adapters for MongoDB, Databricks, and Fabric are **soft-loaded** — if their driver isn't installed, the server skips them and keeps running.

## Create a connections file

```json
{
  "connections": [
    {
      "id": "my_postgres",
      "engine": "postgres",
      "dsn": "postgresql://user:pass@localhost:5432/mydb",
      "read_only": true,
      "description": "My PostgreSQL database"
    }
  ]
}
```

See [Connections](connections.md) for the full field reference and DSN formats for every engine.

## Add to Claude Desktop

Open your Claude Desktop config:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Windows (MS Store):** `%LOCALAPPDATA%\Packages\Claude_<id>\LocalCache\Roaming\Claude\claude_desktop_config.json`

Add the `sql-mcp` entry:

```json
{
  "mcpServers": {
    "sql-mcp": {
      "command": "sql-mcp",
      "args": ["--config", "/path/to/connections.json"]
    }
  }
}
```

!!! warning "Windows: use full path"
    Claude Desktop does not inherit your shell's PATH. Use the absolute path to `sql-mcp.exe` inside your virtual environment:
    `"command": "C:/Users/you/.venv/Scripts/sql-mcp.exe"`

**Restart Claude Desktop** after saving.

## Single-connection shorthand

No config file needed for a single database:

```bash
sql-mcp --engine postgres --dsn "postgresql://user:pass@localhost:5432/mydb"
sql-mcp --engine sqlite --dsn "/path/to/app.db"
sql-mcp --engine mongodb --dsn "mongodb://user:pass@localhost:27017/mydb?authSource=admin"
```

## Use it

In Claude, start with:

```
List my database connections.
```

Then:

```
Show me all tables in my_postgres.
Run this query on my_postgres: SELECT * FROM customers LIMIT 10
```
