# Multi-Connection Setup

Register up to **20 named connections** across any combination of engines in a single `connections.json` file.

## connections.json format

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

## Field reference

| Field | Type | Required | Default | Description |
|-------|------|:--------:|---------|-------------|
| `id` | string | ✅ | — | Unique identifier. Lowercase letters, digits, underscores. 2–31 chars. Must start with a letter. |
| `engine` | string | ✅ | — | `mssql`, `postgres`, `mysql`, `mariadb`, `sqlite`, `mongodb`, `databricks`, or `fabric` |
| `dsn` | string | ✅ | — | Connection string. See [DSN Formats](dsn-formats.md). |
| `read_only` | boolean | | `true` | When `true`, only `SELECT` (or read-equivalent) queries are permitted. |
| `query_timeout` | integer | | `30` | Timeout in seconds. Range: 1–300. |
| `max_rows` | integer | | `50000` | Max rows per query. Range: 1–500,000. |
| `description` | string | | `""` | Human-readable label shown in `list_connections`. |

## Starting the server

```bash
sql-mcp --config connections.json
```

Or via environment variable (useful for containers):

```bash
export SQL_MCP_CONNECTIONS='[
  {"id":"prod_sql","engine":"mssql","dsn":"Driver=...","read_only":true},
  {"id":"analytics","engine":"postgres","dsn":"postgresql://...","read_only":true}
]'
sql-mcp
```

## Targeting connections in Claude

When multiple connections are registered, pass `connection_id` to any tool:

```
List all tables on analytics_pg.
```

```
Run this query on prod_mssql: SELECT TOP 10 * FROM orders
```

```
List collections in app_mongodb.
```

If you omit `connection_id` with a single-connection setup, it uses the default. With multiple connections, Claude will ask which one you mean.

!!! tip
    Start every multi-connection session with `list_connections` so Claude knows what's available.

## A working 6-engine example

See [`examples/connections.json`](https://github.com/lorenzouriel/sql-mcp/blob/main/examples/connections.json) in the repository for a ready-to-use reference covering MSSQL, PostgreSQL, MySQL, MongoDB, Databricks, and Fabric.
