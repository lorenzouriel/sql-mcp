# Installation Options

Install only the drivers you need to keep the dependency footprint small.

## Python extras

| Extra | Packages installed | Use when |
|-------|--------------------|----------|
| `sql-mcp[mssql]` | `pyodbc>=4.0.35` | Microsoft SQL Server |
| `sql-mcp[postgres]` | `psycopg2-binary>=2.9.0` | PostgreSQL |
| `sql-mcp[mysql]` | `mysql-connector-python>=8.0.0` | MySQL or MariaDB |
| `sql-mcp[mongodb]` | `pymongo>=4.6.0` | MongoDB |
| `sql-mcp[databricks]` | `databricks-sql-connector>=3.0.0` | Databricks SQL Warehouse |
| `sql-mcp[fabric]` | `pyodbc>=4.0.35`, `azure-kusto-data>=4.0.0` | Microsoft Fabric (Warehouse + Eventhouse) |
| `sql-mcp[all]` | All of the above | Every engine at once |
| `sql-mcp[dev]` | pytest, black, ruff, mypy, testcontainers | Development / CI |

SQLite is always available — `sqlite3` ships with Python.

## Soft-loading

MongoDB, Databricks, and Fabric adapters are **soft-loaded**. If their driver packages are not installed, those adapters are excluded from the registry at startup and the server continues running for the remaining engines. You will see a log line like:

```
INFO  MongoDBAdapter not registered — pymongo not installed
```

## System requirements for MSSQL and Fabric

Both MSSQL and Fabric Warehouse use the Microsoft ODBC driver.

=== "Linux"

    ```bash
    # Ubuntu / Debian
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
    curl https://packages.microsoft.com/config/ubuntu/22.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
    apt-get update
    ACCEPT_EULA=Y apt-get install -y msodbcsql17
    ```

=== "macOS"

    ```bash
    brew install microsoft/mssql-release/msodbcsql17
    ```

=== "Windows"

    Download and run the installer:
    [ODBC Driver 17](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server) |
    [ODBC Driver 18](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)

Use **ODBC Driver 17** for standard MSSQL. Use **ODBC Driver 18** for Microsoft Fabric Warehouse.

## Using uv (recommended for development)

```bash
git clone https://github.com/lorenzouriel/universal-db-mcp.git
cd universal-db-mcp
uv sync --extra all --extra dev
```

## Using pip + venv

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[all,dev]"
```
