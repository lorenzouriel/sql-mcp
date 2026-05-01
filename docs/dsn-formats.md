# DSN Formats

Connection string syntax for every supported engine.

## SQL Server (MSSQL)

```
Driver={ODBC Driver 17 for SQL Server};Server=host,port;Database=db;UID=user;PWD=pass;TrustServerCertificate=yes;Encrypt=no;
```

| Parameter | Description |
|-----------|-------------|
| `Driver` | Use `ODBC Driver 17 for SQL Server` or `ODBC Driver 18 for SQL Server` |
| `Server` | Host and port separated by a comma — e.g. `localhost,1433` |
| `Database` | Target database name |
| `UID` / `PWD` | SQL Server login credentials |
| `TrustServerCertificate` | Set to `yes` for self-signed certs (dev/Docker) |

## PostgreSQL

```
postgresql://user:pass@host:5432/db
```

Standard libpq URI format. For SSL: `postgresql://user:pass@host:5432/db?sslmode=require`

## MySQL / MariaDB

```
mysql://user:pass@host:3306/db
```

## SQLite

```
/absolute/path/to/file.db
```

Use `:memory:` for an in-memory database (useful for testing).

## MongoDB

```
mongodb://user:pass@host:27017/db?authSource=admin
```

!!! warning "authSource is almost always required"
    Users created via `MONGO_INITDB_ROOT_USERNAME` / `MONGO_INITDB_ROOT_PASSWORD` (Docker) live in the `admin` database, not the application database. Without `?authSource=admin` you will get **Authentication failed (code 18)**.

    For Atlas: use the full `mongodb+srv://` URI provided in the Atlas connection dialog.

## Databricks

```
databricks://token@<host>?http_path=<path>[&catalog=<catalog>][&schema=<schema>]
```

| Parameter | Description |
|-----------|-------------|
| `token` | Personal access token (PAT) from your Databricks workspace settings |
| `host` | Workspace hostname — e.g. `dbc-xxxxxxx.cloud.databricks.com` |
| `http_path` | SQL Warehouse HTTP path — e.g. `/sql/1.0/warehouses/abc123` |
| `catalog` | *(optional)* Sets the active catalog on connect |
| `schema` | *(optional)* Sets the active schema on connect |

**Where to find these values:**

1. Go to your Databricks workspace → **SQL Warehouses**
2. Click your warehouse → **Connection details** tab
3. Copy the **Server hostname** and **HTTP path**
4. Generate a PAT: User menu → **Settings** → **Developer** → **Access tokens**

Example:
```
databricks://dapi1234567890abcdef@dbc-73f8aa16-0899.cloud.databricks.com?http_path=/sql/1.0/warehouses/abc123&catalog=main&schema=ecommerce
```

## Microsoft Fabric — Warehouse (T-SQL)

```
Driver={ODBC Driver 18 for SQL Server};Server=<workspace>.datawarehouse.fabric.microsoft.com;UID=user@org.com;PWD=pass;Authentication=ActiveDirectoryPassword;Encrypt=yes;
```

!!! tip "Use ActiveDirectoryPassword for background processes"
    `ActiveDirectoryInteractive` requires a browser popup and won't work in a headless MCP server. `ActiveDirectoryAzCli` requires `az login` in the same session. **`ActiveDirectoryPassword`** is the only method that works non-interactively.

**Where to find the server hostname:**

1. Open your Fabric workspace → **Warehouse** item
2. Click the warehouse → **Settings**
3. Copy the **SQL connection string** — it ends in `.datawarehouse.fabric.microsoft.com`

## Microsoft Fabric — Eventhouse (KQL)

```
kql://<cluster_hostname>/<database>
```

Example:
```
kql://mycluster.eastus.kusto.fabric.microsoft.com/MyDatabase
```

Authentication uses Azure CLI (`az login`). Run `az login` before starting the MCP server when using Eventhouse.
