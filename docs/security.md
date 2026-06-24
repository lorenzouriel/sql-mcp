# Security

Every query passes through a validation pipeline before reaching the database.

## Validation pipeline

```
Query → Length check → Normalize → Multi-statement block → Write check → Banned patterns → Audit log → Database
```

1. **Length check** — reject if > `MAX_QUERY_LENGTH` (default 50,000 chars)
2. **Normalization** — uppercase + strip comments (SQL engines only)
3. **Multi-statement block** — reject queries with multiple statements (prevents injection)
4. **Write check** — reject DML/DDL if `read_only = true`
5. **Banned patterns** — reject per-engine dangerous patterns
6. **Audit log** — SHA-256 hash of query logged with outcome

## Read-only mode

All connections default to `read_only: true`. These keywords are rejected:

`INSERT` · `UPDATE` · `DELETE` · `DROP` · `ALTER` · `TRUNCATE` · `CREATE` · `GRANT` · `DENY` · `REVOKE`

Set `"read_only": false` in the connection config to enable writes.

## Banned patterns (all modes)

| Engine | Blocked |
|--------|---------|
| **MSSQL** | `EXEC`, `EXECUTE`, `xp_*`, `sp_*`, `KILL`, `SHUTDOWN`, `OPENROWSET`, `OPENDATASOURCE`, `BULK INSERT` |
| **PostgreSQL** | `COPY`, `pg_read_file`, `pg_write_file`, `lo_import`, `lo_export` |
| **MySQL** | `LOAD DATA`, `INTO OUTFILE`, `INTO DUMPFILE`, `LOAD_FILE` |
| **SQLite** | `ATTACH`, `DETACH` |
| **MongoDB** | `$where`, `$function`, `$accumulator`, `$out`, `$merge` |
| **Fabric KQL** | `externaldata`, `plugin` |

## Per-connection limits

| Limit | Default | Max | Config field |
|-------|---------|-----|--------------|
| Row cap | 50,000 | 500,000 | `max_rows` |
| Query timeout | 30s | 300s | `query_timeout` |

## Audit logging

Every query (allowed or denied) is logged with: tool name, connection ID, read/write mode, SHA-256 hash, and outcome. Passwords in DSN strings are automatically redacted from logs.
