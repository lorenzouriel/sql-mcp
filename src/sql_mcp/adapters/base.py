from abc import ABC, abstractmethod
from typing import Any


class DatabaseAdapter(ABC):

    @property
    @abstractmethod
    def engine_name(self) -> str: ...

    @abstractmethod
    async def connect(self, dsn: str) -> None: ...

    @abstractmethod
    async def disconnect(self) -> None: ...

    @abstractmethod
    async def execute_query(
        self,
        sql: str,
        timeout: int = 30,
        max_rows: int = 50_000,
    ) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def list_schemas(self) -> list[str]: ...

    @abstractmethod
    async def list_tables(
        self,
        schema: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def schema_discovery(
        self,
        schema: str | None = None,
    ) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def get_database_info(self) -> dict[str, Any]: ...

    @abstractmethod
    async def check_connection(self) -> bool: ...
