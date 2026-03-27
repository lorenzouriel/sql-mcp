from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from .adapters import create_adapter
from .adapters.base import DatabaseAdapter
from .models import ConnectionConfig
from .security import SecurityPolicy

logger = logging.getLogger(__name__)


@dataclass
class ConnectionEntry:
    config: ConnectionConfig
    adapter: DatabaseAdapter
    policy: SecurityPolicy


class ConnectionRegistry:

    def __init__(self) -> None:
        self._entries: dict[str, ConnectionEntry] = {}

    async def register(self, config: ConnectionConfig) -> None:
        if config.id in self._entries:
            raise ValueError(f"Connection '{config.id}' is already registered.")
        adapter = create_adapter(config.engine)
        await adapter.connect(config.dsn)
        policy = SecurityPolicy(
            read_only=config.read_only,
            query_timeout=config.query_timeout,
            max_rows=config.max_rows,
            engine=config.engine,
        )
        self._entries[config.id] = ConnectionEntry(
            config=config, adapter=adapter, policy=policy
        )
        logger.info(
            "Registered connection '%s' (engine=%s, read_only=%s)",
            config.id, config.engine, config.read_only,
        )

    async def register_all(
        self, configs: list[ConnectionConfig]
    ) -> dict[str, str | None]:
        results: dict[str, str | None] = {}
        for cfg in configs:
            try:
                await self.register(cfg)
                results[cfg.id] = None
            except Exception as exc:
                results[cfg.id] = str(exc)
                logger.error("Failed to register connection '%s': %s", cfg.id, exc)
        return results

    def resolve(self, connection_id: str | None = None) -> ConnectionEntry:
        if connection_id is not None:
            entry = self._entries.get(connection_id)
            if entry is None:
                available = ", ".join(sorted(self._entries.keys()))
                raise ValueError(
                    f"Unknown connection '{connection_id}'. Available: {available}"
                )
            return entry
        if len(self._entries) == 1:
            return next(iter(self._entries.values()))
        if len(self._entries) == 0:
            raise ValueError("No connections registered.")
        available = ", ".join(sorted(self._entries.keys()))
        raise ValueError(
            f"Multiple connections configured ({len(self._entries)}). "
            f"Specify connection_id. Available: {available}"
        )

    def list_connections(self) -> list[dict[str, Any]]:
        return [
            {
                "id": cid,
                "engine": entry.adapter.engine_name,
                "read_only": entry.policy.read_only,
                "description": entry.config.description,
                "status": "connected",
            }
            for cid, entry in self._entries.items()
        ]

    @property
    def count(self) -> int:
        return len(self._entries)

    async def disconnect_all(self) -> None:
        for entry in self._entries.values():
            try:
                await entry.adapter.disconnect()
            except Exception as e:
                logger.warning("Error disconnecting '%s': %s", entry.config.id, e)
        self._entries.clear()


_registry: ConnectionRegistry | None = None


def get_registry() -> ConnectionRegistry:
    if _registry is None:
        raise RuntimeError(
            "ConnectionRegistry not initialized. Call set_registry() first."
        )
    return _registry


def set_registry(registry: ConnectionRegistry) -> None:
    global _registry
    _registry = registry
