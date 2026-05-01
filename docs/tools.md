# MCP Tools Reference

sql-mcp exposes **nine tools** to Claude. Tools that accept `connection_id` use the default (single) connection when the parameter is omitted.

---

## list_connections

List all registered database connections.

```
list_connections()
```

Returns each connection's `id`, `engine`, `read_only` status, and `description`.

!!! tip "Always start here"
    In multi-connection sessions, call `list_connections` first so Claude knows what's available before routing queries.

---

## execute_sql

Execute a SQL, SparkSQL, or KQL query.

```
execute_sql(sql, format="table", connection_id=None)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sql` | string | — | Query to execute |
| `format` | string | `"table"` | Output format: `table`, `json`, or `csv` |
| `connection_id` | string | `None` | Target connection (required when multiple are registered) |

The query passes through the connection's [security policy](security.md) before reaching the database.

**Examples:**

```sql
-- PostgreSQL / MSSQL / MySQL / SQLite
SELECT name, country FROM customers WHERE country = 'Brazil'

-- Databricks SparkSQL
SELECT * FROM main.ecommerce.orders WHERE status = 'completed'

-- Fabric KQL (Eventhouse)
customers | where country == 'Brazil' | project name, email
```

---

## execute_native_query

Execute a native non-SQL query on a document store (MongoDB MQL).

```
execute_native_query(query, collection, format="table", connection_id=None)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | — | JSON string: `{}` dict for MQL filter, `[]` list for aggregation pipeline |
| `collection` | string | — | Target collection name |
| `format` | string | `"table"` | Output format: `table`, `json`, or `csv` |
| `connection_id` | string | `None` | Target connection |

!!! info "SQL engines: use execute_sql instead"
    `execute_native_query` is for MongoDB. For SQL/SparkSQL/KQL engines, use `execute_sql`.

**MQL filter (find):**

```json
{"country": "Brazil"}
```

Returns all documents where `country` equals `"Brazil"`.

**MQL filter with projection:**

```json
{"status": "completed", "total": {"$gt": 100}}
```

**Aggregation pipeline:**

```json
[
  {"$match": {"status": "completed"}},
  {"$group": {"_id": "$country", "revenue": {"$sum": "$total"}}},
  {"$sort": {"revenue": -1}}
]
```

---

## list_schemas

List all schemas in the connected database.

```
list_schemas(connection_id=None)
```

Returns schema names as a list. For MongoDB, returns the database name. For Databricks, returns catalog-qualified schema names when a catalog is set.

---

## list_tables

List tables within a schema.

```
list_tables(schema=None, limit=200, connection_id=None)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `schema` | string | `None` | Filter by schema name |
| `limit` | integer | `200` | Max tables to return (capped at 1000) |
| `connection_id` | string | `None` | Target connection |

Returns `schema_name`, `table_name`, and `row_count` (where available) for each table.

---

## schema_discovery

Get full column-level metadata for a schema.

```
schema_discovery(schema=None, connection_id=None)
```

Returns `TABLE_NAME`, `COLUMN_NAME`, `DATA_TYPE`, `IS_NULLABLE`, `COLUMN_DEFAULT`, and `CHARACTER_MAXIMUM_LENGTH` for every column. Output is always JSON.

For MongoDB, field types are inferred by sampling up to 100 documents per collection.

---

## get_database_info

Get server and database metadata.

```
get_database_info(connection_id=None)
```

Returns engine version, database name, query language, and connection details. Useful for confirming which database is active.

---

## get_policy_info

Inspect the active security policy for a connection.

```
get_policy_info(connection_id=None)
```

Returns:

- `read_only` — whether write operations are blocked
- `query_timeout` — timeout in seconds
- `max_rows` — row cap per query
- `max_query_length` — character limit
- `banned_pattern_count` — number of patterns checked per query

---

## check_db_connection

Verify that a database connection is alive.

```
check_db_connection(connection_id=None)
```

Returns `true` if the connection responds, `false` otherwise. Useful for diagnosing connectivity issues before running queries.
