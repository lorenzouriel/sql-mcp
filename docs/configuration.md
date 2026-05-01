# Configuration Reference

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SQL_MCP_CONNECTIONS` | — | JSON array of connection objects. Takes priority over all other connection sources. |
| `MSSQL_CONNECTION_STRING` | — | Legacy MSSQL ODBC string (v1 backward-compat). Lowest priority. |
| `READ_ONLY` | `true` | Used with `MSSQL_CONNECTION_STRING` mode. Set `false` to allow writes. |
| `ENABLE_WRITES` | `false` | Must be `true` AND `ADMIN_CONFIRM` non-empty to enable writes in legacy mode. |
| `ADMIN_CONFIRM` | — | Confirmation token required alongside `ENABLE_WRITES=true`. |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, or `ERROR`. |
| `LOG_FORMAT` | `json` | `json` for structured output, `text` for human-readable. |
| `ENABLE_METRICS` | `true` | Enable Prometheus metrics collection. |
| `MAX_QUERY_LENGTH` | `50000` | Maximum query length in characters. |

## CLI flags

| Flag | Default | Description |
|------|---------|-------------|
| `--engine` | — | Engine: `mssql`, `postgres`, `mysql`, `mariadb`, `sqlite`, `mongodb`, `databricks`, `fabric` |
| `--dsn` | — | Connection string or DSN |
| `--config` | — | Path to `connections.json` |
| `--write` | `false` | Enable write operations |
| `--transport` | `stdio` | `stdio` (Claude Desktop) or `http` |
| `--bind` | `127.0.0.1:8080` | Bind address for HTTP transport |
| `--log-level` | `INFO` | Log verbosity |
| `--log-format` | `json` | Log format |
| `--version` | — | Print version and exit |

## Connection source priority

When multiple connection sources are present, the server picks the first one found:

1. `--config` flag (highest priority)
2. `SQL_MCP_CONNECTIONS` environment variable
3. `--engine` + `--dsn` flags
4. `MSSQL_CONNECTION_STRING` environment variable (legacy)

## HTTP transport endpoints

When running with `--transport http`:

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Liveness — `{"status": "alive"}` |
| `GET /ready` | Readiness — checks all connections are reachable |
| `GET /info` | Server metadata and registered connections |
| `GET /metrics` | Prometheus metrics in text format |

## JSON config schema

```json
{
  "connections": [
    {
      "id": "my_db",
      "engine": "postgres",
      "dsn": "postgresql://user:pass@host:5432/db",
      "read_only": true,
      "query_timeout": 30,
      "max_rows": 50000,
      "description": "Optional label"
    }
  ]
}
```

- Minimum 1 connection, maximum **20** connections per instance
- `id` pattern: `^[a-z][a-z0-9_]{0,29}$`
