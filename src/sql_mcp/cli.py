import asyncio
import argparse
import json
import logging
import os
import sys

from .logging_config import setup_logging
from .models import ConnectionConfig, MultiConnectionConfig
from .registry import ConnectionRegistry, set_registry
from .server import SQLMCPServer


async def _initialize_registry(args: argparse.Namespace) -> ConnectionRegistry:
    registry = ConnectionRegistry()

    if args.config:
        with open(args.config) as f:
            raw = json.load(f)
        cfg = MultiConnectionConfig(**raw)
        results = await registry.register_all(cfg.connections)
        failed = {k: v for k, v in results.items() if v is not None}
        if failed and len(failed) == len(results):
            raise SystemExit(f"All connections failed to register: {failed}")

    elif os.environ.get("SQL_MCP_CONNECTIONS"):
        raw = json.loads(os.environ["SQL_MCP_CONNECTIONS"])
        cfg = MultiConnectionConfig(connections=raw)
        await registry.register_all(cfg.connections)

    elif args.engine and args.dsn:
        conn_cfg = ConnectionConfig(
            id="default",
            engine=args.engine,
            dsn=args.dsn,
            read_only=not args.write if hasattr(args, "write") and args.write else True,
        )
        await registry.register(conn_cfg)

    elif os.environ.get("MSSQL_CONNECTION_STRING"):
        legacy_dsn = os.environ["MSSQL_CONNECTION_STRING"]
        read_only = os.environ.get("READ_ONLY", "true").lower() == "true"
        if os.environ.get("ENABLE_WRITES", "false").lower() == "true":
            if os.environ.get("ADMIN_CONFIRM", ""):
                read_only = False
        conn_cfg = ConnectionConfig(
            id="default",
            engine="mssql",
            dsn=legacy_dsn,
            read_only=read_only,
        )
        await registry.register(conn_cfg)

    else:
        raise SystemExit(
            "No connection configured.\n"
            "Options:\n"
            "  --config connections.json\n"
            "  --engine mssql|postgres|mysql|mariadb|sqlite --dsn <dsn>\n"
            "  SQL_MCP_CONNECTIONS='[...]' (env var)\n"
            "  MSSQL_CONNECTION_STRING=... (legacy)"
        )

    return registry


def _create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="sql-mcp — Universal SQL MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # SQL Server
  sql-mcp --engine mssql --dsn "Driver={ODBC Driver 17 for SQL Server};Server=...;Database=...;UID=...;PWD=..."

  # PostgreSQL
  sql-mcp --engine postgres --dsn "postgresql://user:pass@localhost:5432/mydb"

  # MySQL
  sql-mcp --engine mysql --dsn "mysql://user:pass@localhost:3306/mydb"

  # SQLite
  sql-mcp --engine sqlite --dsn "/path/to/app.db"

  # Multi-connection
  sql-mcp --config connections.json

  # HTTP transport
  sql-mcp --engine postgres --dsn "postgresql://..." --transport http --bind 0.0.0.0:8080

  # Legacy (backward compat)
  MSSQL_CONNECTION_STRING="Driver=..." sql-mcp
        """,
    )
    parser.add_argument(
        "--engine",
        choices=["mssql", "postgres", "mysql", "mariadb", "sqlite"],
        help="Database engine",
    )
    parser.add_argument("--dsn", help="Connection string / DSN")
    parser.add_argument("--config", help="Path to connections.json (multi-connection)")
    parser.add_argument(
        "--write",
        action="store_true",
        default=False,
        help="Enable write operations (default: read-only)",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport mechanism (default: stdio)",
    )
    parser.add_argument(
        "--bind",
        default="127.0.0.1:8080",
        help="Bind address for HTTP transport (default: 127.0.0.1:8080)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
    )
    parser.add_argument(
        "--log-format",
        choices=["json", "text"],
        default="json",
    )
    parser.add_argument("--version", action="version", version="sql-mcp 2.0.0")
    return parser


async def main() -> int:
    parser = _create_parser()
    args = parser.parse_args()
    setup_logging(log_level=args.log_level, log_format=args.log_format)
    logger = logging.getLogger(__name__)

    try:
        registry = await _initialize_registry(args)
        set_registry(registry)
        logger.info(
            "sql-mcp 2.0.0 starting | connections=%d | transport=%s",
            registry.count,
            args.transport,
        )
        server = SQLMCPServer(transport=args.transport, bind=args.bind)
        await server.run()
        return 0
    except SystemExit:
        raise
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        logger.exception("Fatal error: %s", e)
        return 1


def run() -> None:
    sys.exit(asyncio.run(main()))


if __name__ == "__main__":
    run()
