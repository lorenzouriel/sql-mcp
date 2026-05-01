# Docker

## Production image

The `scripts/Dockerfile` builds an image with all database drivers pre-installed, including Microsoft ODBC Driver 17 for SQL Server.

```bash
# Build
docker build -f scripts/Dockerfile -t sql-mcp .

# Single connection — PostgreSQL
docker run --rm -i sql-mcp \
  --engine postgres \
  --dsn "postgresql://user:pass@host.docker.internal:5432/mydb"

# Multi-connection config file
docker run --rm -i \
  -v /path/to/connections.json:/app/connections.json \
  sql-mcp --config /app/connections.json

# HTTP transport (service mesh / sidecar)
docker run --rm -p 8080:8080 sql-mcp \
  --engine postgres \
  --dsn "postgresql://user:pass@db:5432/mydb" \
  --transport http \
  --bind 0.0.0.0:8080
```

## HTTP endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Liveness — `{"status": "alive"}` |
| `GET /ready` | Readiness — verifies all connections reachable |
| `GET /info` | Server metadata and registered connection list |
| `GET /metrics` | Prometheus metrics (text format) |

## Local development containers

```bash
# Start Postgres, MySQL, MongoDB, MSSQL
docker compose -f scripts/docker-compose.yml up -d

# Stop and remove containers
docker compose -f scripts/docker-compose.yml down
```

| Service | Image | Port |
|---------|-------|------|
| PostgreSQL | `postgres:15` | 5432 |
| MySQL | `mysql:8` | 3306 |
| MongoDB | `mongo:7` | 27017 |
| MSSQL | `mcr.microsoft.com/mssql/server:2022-latest` | 1434 |
