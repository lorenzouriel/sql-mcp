# Security

sql-mcp treats security as a first-class concern. Every query passes through a multi-layer validation pipeline before reaching the database.

## Validation pipeline

```
Query input
    │
    ▼
1. Length check         → reject if > MAX_QUERY_LENGTH (default 50,000 chars)
    │
    ▼
2. Normalization        → uppercase, strip comments (SQL engines only)
    │
    ▼
3. Multi-statement      → reject if multiple statements detected
    │
    ▼
4. Write check          → reject DML/DDL if read_only = true
    │
    ▼
5. Banned patterns      → reject per-engine dangerous patterns
    │
    ▼
6. Audit log            → SHA-256 hash of query logged with result
    │
    ▼
  Database
```

## Read-only mode

All connections start in read-only mode (`read_only: true`). In this mode any query containing these keywords is rejected immediately, regardless of context:

`INSERT` · `UPDATE` · `DELETE` · `DROP` · `ALTER` · `TRUNCATE` · `CREATE` · `GRANT` · `DENY` · `REVOKE`

To enable writes, set `"read_only": false` in the connection config or pass `--write` on the command line.

## Engine-specific banned patterns

Each engine has a curated list of patterns blocked in **all** modes (read and write):

| Engine | Blocked patterns |
|--------|-----------------|
| **MSSQL** | `EXEC`, `EXECUTE`, `xp_*`, `sp_*`, `KILL`, `SHUTDOWN`, `OPENROWSET`, `OPENDATASOURCE`, `BULK INSERT` |
| **PostgreSQL** | `COPY`, `pg_read_file`, `pg_write_file`, `lo_import`, `lo_export` |
| **MySQL / MariaDB** | `LOAD DATA`, `INTO OUTFILE`, `INTO DUMPFILE`, `LOAD_FILE` |
| **SQLite** | `ATTACH`, `DETACH` |
| **MongoDB (MQL)** | `$where`, `$function`, `$accumulator`, `$out`, `$merge` |
| **Fabric Eventhouse (KQL)** | `externaldata`, `plugin` |
| **All engines** | `DROP`, `ALTER`, `TRUNCATE`, `CREATE`, `GRANT`, `REVOKE` |

!!! info "Why MongoDB patterns are different"
    MongoDB MQL queries are JSON — operators like `$where` are case-sensitive keys, not SQL keywords. The validator skips SQL normalization for MQL and checks the raw query string directly.

## Multi-statement blocking

Queries containing more than one statement are rejected:

- SQL: semicolons between statements
- MSSQL: `GO` separators
- Exception: trailing semicolons at end-of-query are allowed

This prevents semicolon-chained injection attacks.

## Query length cap

Queries longer than `MAX_QUERY_LENGTH` characters (default: 50,000) are rejected before any parsing occurs. Override with the `MAX_QUERY_LENGTH` environment variable.

## Per-connection limits

Each connection independently enforces:

| Limit | Default | Maximum | Config field |
|-------|---------|---------|--------------|
| Row cap | 50,000 | 500,000 | `max_rows` |
| Query timeout | 30 sec | 300 sec | `query_timeout` |

Long-running queries are terminated at the database level once the timeout fires.

## Audit logging

Every query — allowed or denied — is logged with:

- Tool name
- Connection ID
- Mode (`read_only` or `write`)
- SHA-256 hash of the query text
- Outcome (allowed / denied + reason)

The active policy for any connection can be inspected at runtime via the `get_policy_info` tool.

## Sensitive data redaction

The logging pipeline automatically redacts passwords from DSN strings before they reach log output. Connection strings are safe to include in structured logs.
