# Quick Start

Get sql-mcp running with Claude Desktop in under five minutes.

## Prerequisites

- Python 3.10 or later
- Claude Desktop (or any MCP-compatible client)
- For MSSQL / Fabric Warehouse: [ODBC Driver 17 or 18 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)

## Step 1 — Install

Install the package with the extras for the engines you need:

=== "All engines"

    ```bash
    pip install "sql-mcp[all]"
    ```

=== "PostgreSQL"

    ```bash
    pip install "sql-mcp[postgres]"
    ```

=== "SQL Server"

    ```bash
    pip install "sql-mcp[mssql]"
    ```

=== "MongoDB"

    ```bash
    pip install "sql-mcp[mongodb]"
    ```

=== "Databricks"

    ```bash
    pip install "sql-mcp[databricks]"
    ```

=== "Fabric"

    ```bash
    pip install "sql-mcp[fabric]"
    ```

SQLite needs no extra — `sqlite3` is part of the Python standard library.

## Step 2 — Create a connections file

Create a `connections.json` file with your databases:

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

See [DSN Formats](dsn-formats.md) for connection string syntax for every engine.

## Step 3 — Add to Claude Desktop

Open your Claude Desktop configuration file:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

Add the `sql-mcp` entry:

=== "Windows"

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

    !!! warning "Full path required on Windows"
        Claude Desktop does not inherit your shell's PATH. Use the absolute path to the `sql-mcp.exe` inside your virtual environment.

=== "macOS / Linux"

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

    This assumes a global install via `pipx install "sql-mcp[all]"`.

**Restart Claude Desktop** after saving the config.

## Step 4 — Use it

In Claude, start with:

```
List my database connections.
```

Claude will call `list_connections` and show all registered databases. Then:

```
Show me all tables in my_postgres.
```

```
Run this query on my_postgres: SELECT * FROM customers LIMIT 10
```

## Single-connection shorthand

No config file needed for a single database — pass the engine and DSN directly:

```bash
sql-mcp --engine postgres --dsn "postgresql://user:pass@localhost:5432/mydb"
sql-mcp --engine sqlite --dsn "/path/to/app.db"
sql-mcp --engine mongodb --dsn "mongodb://user:pass@localhost:27017/mydb?authSource=admin"
```

## Next steps

- [Multi-Connection Setup](connections.md) — register multiple databases
- [MCP Tools Reference](tools.md) — all nine tools explained
- [Security](security.md) — understand the query validation pipeline
