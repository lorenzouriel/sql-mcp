# MCP Tools

sql-mcp exposes **nine tools** to Claude. All tools accept an optional `connection_id` — required when multiple connections are registered.

## list_connections

List all registered database connections with their `id`, `engine`, `read_only` status, and `description`.

!!! tip
    Start every multi-connection session with `list_connections` so Claude knows what's available.

## execute_sql

Execute a SQL, SparkSQL, or KQL query.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sql` | string | — | Query to execute |
| `format` | string | `"table"` | `table`, `json`, or `csv` |
| `connection_id` | string | `None` | Target connection |

Queries pass through the [security](security.md) validation pipeline before reaching the database.

## execute_native_query

Execute a native MongoDB MQL query.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | — | JSON string: `{}` for filter, `[]` for aggregation pipeline |
| `collection` | string | — | Target collection |
| `format` | string | `"table"` | `table`, `json`, or `csv` |
| `connection_id` | string | `None` | Target connection |

**Filter example:**
```json
{"country": "Brazil"}
```

**Aggregation example:**
```json
[
  {"$match": {"status": "completed"}},
  {"$group": {"_id": "$country", "revenue": {"$sum": "$total"}}}
]
```

## list_schemas

List all schemas in the database.

## list_tables

List tables within a schema.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `schema` | string | `None` | Filter by schema |
| `limit` | integer | `200` | Max tables (capped at 1000) |
| `connection_id` | string | `None` | Target connection |

## schema_discovery

Get column-level metadata (name, type, nullable, default) for all tables in a schema. Output is JSON.

## get_database_info

Get server version, database name, query language, and connection details.

## get_policy_info

Inspect the active security policy: `read_only`, `query_timeout`, `max_rows`, `max_query_length`, and banned pattern count.

## check_db_connection

Health check — returns whether the connection is alive.
