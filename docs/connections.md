# Connections

## connections.json

Register up to **20 named connections** across any combination of engines:

```json
{
  "connections": [
    {
      "id": "prod_mssql",
      "engine": "mssql",
      "dsn": "Driver={ODBC Driver 17 for SQL Server};Server=host,1433;Database=orders;UID=user;PWD=pass",
      "read_only": true,
      "description": "Production MSSQL",
      "query_timeout": 30,
      "max_rows": 10000
    },
    {
      "id": "analytics_pg",
      "engine": "postgres",
      "dsn": "postgresql://user:pass@host:5432/dw",
      "read_only": true,
      "description": "Analytics warehouse"
    }
  ]
}
```

| Field | Required | Default | Description |
|-------|:--------:|---------|-------------|
| `id` | yes | — | Unique ID. Lowercase letters, digits, underscores. 2-31 chars. |
| `engine` | yes | — | `mssql`, `postgres`, `mysql`, `mariadb`, `sqlite`, `mongodb`, `databricks`, or `fabric` |
| `dsn` | yes | — | Connection string (see DSN formats below) |
| `read_only` | | `true` | Only `SELECT` queries allowed when `true` |
| `query_timeout` | | `30` | Timeout in seconds (1-300) |
| `max_rows` | | `50000` | Max rows per query (1-500,000) |
| `description` | | `""` | Label shown in `list_connections` |

## DSN formats

### SQL Server (MSSQL)

```
Driver={ODBC Driver 17 for SQL Server};Server=host,port;Database=db;UID=user;PWD=pass;TrustServerCertificate=yes;Encrypt=no;
```

### PostgreSQL

```
postgresql://user:pass@host:5432/db
```

For SSL: append `?sslmode=require`

### MySQL / MariaDB

```
mysql://user:pass@host:3306/db
```

### SQLite

```
/absolute/path/to/file.db
```

Use `:memory:` for in-memory databases.

### MongoDB

```
mongodb://user:pass@host:27017/db?authSource=admin
```

!!! warning "authSource is almost always required"
    Users created via Docker's `MONGO_INITDB_ROOT_USERNAME` live in the `admin` database. Without `?authSource=admin` you'll get **Authentication failed (code 18)**.

### Databricks

```
databricks://token@<host>?http_path=<path>[&catalog=<catalog>][&schema=<schema>]
```

- **token**: Personal access token from workspace settings
- **host**: e.g. `dbc-xxxxxxx.cloud.databricks.com`
- **http_path**: e.g. `/sql/1.0/warehouses/abc123`

### Microsoft Fabric — Warehouse (T-SQL)

```
Driver={ODBC Driver 18 for SQL Server};Server=<workspace>.datawarehouse.fabric.microsoft.com;UID=user@org.com;PWD=pass;Authentication=ActiveDirectoryPassword;Encrypt=yes;
```

### Microsoft Fabric — Eventhouse (KQL)

```
kql://<cluster_hostname>/<database>
```

Requires `az login` before starting the server.

## Alternative connection sources

Instead of `--config`, you can use environment variables:

```bash
# JSON array
export SQL_MCP_CONNECTIONS='[{"id":"my_db","engine":"postgres","dsn":"postgresql://...","read_only":true}]'
sql-mcp

# Legacy single MSSQL connection
export MSSQL_CONNECTION_STRING="Driver={ODBC Driver 17 for SQL Server};Server=..."
sql-mcp
```

**Priority order:** `--config` > `SQL_MCP_CONNECTIONS` > `--engine`/`--dsn` > `MSSQL_CONNECTION_STRING`

## CLI flags

| Flag | Default | Description |
|------|---------|-------------|
| `--engine` | — | Engine type |
| `--dsn` | — | Connection string |
| `--config` | — | Path to `connections.json` |
| `--write` | `false` | Enable write operations |
| `--transport` | `stdio` | `stdio` or `http` |
| `--bind` | `127.0.0.1:8080` | Bind address for HTTP transport |
| `--log-level` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `--log-format` | `json` | `json` or `text` |

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Log verbosity |
| `LOG_FORMAT` | `json` | Log format |
| `ENABLE_METRICS` | `true` | Prometheus metrics |
| `MAX_QUERY_LENGTH` | `50000` | Max query length in characters |
