import logging
from datetime import datetime
from typing import Any

from .metrics import server_ready

logger = logging.getLogger(__name__)


async def health_check() -> dict[str, Any]:
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
    }


async def readiness_check() -> dict[str, Any]:
    try:
        from .registry import get_registry
        registry = get_registry()
    except RuntimeError:
        server_ready.set(0)
        return {
            "status": "not_ready",
            "connections": {},
            "timestamp": datetime.utcnow().isoformat(),
        }

    connection_statuses: dict[str, bool] = {}
    for conn in registry.list_connections():
        entry = registry.resolve(conn["id"])
        connection_statuses[conn["id"]] = await entry.adapter.check_connection()

    all_ready = bool(connection_statuses) and all(connection_statuses.values())
    server_ready.set(1 if all_ready else 0)

    return {
        "status": "ready" if all_ready else "not_ready",
        "connections": connection_statuses,
        "timestamp": datetime.utcnow().isoformat(),
    }


async def get_server_info() -> dict[str, Any]:
    try:
        from .registry import get_registry
        connections = get_registry().list_connections()
    except RuntimeError:
        connections = []
    return {
        "name": "sql-mcp",
        "version": "2.0.0",
        "connections": connections,
    }


async def get_metrics_endpoint() -> str:
    from .metrics import get_metrics_text
    return get_metrics_text()
