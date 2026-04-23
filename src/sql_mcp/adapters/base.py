from abc import ABC, abstractmethod
from typing import Any


class DatabaseAdapter(ABC):

    @property
    @abstractmethod
    def engine_name(self) -> str: ...

    @property
    def query_language(self) -> str:
        """Query language token: sql | sparksql | mql | kql. Defaults to 'sql'."""
        return "sql"

    @property
    def supports_sql(self) -> bool:
        """True if execute_query() accepts SQL strings."""
        return self.query_language in ("sql", "sparksql")

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

    async def execute_native_query(
        self,
        query: str,
        collection: str,
        timeout: int = 30,
        max_rows: int = 50_000,
    ) -> list[dict[str, Any]]:
        """Execute a native (non-SQL) query such as MQL for MongoDB.
        SQL adapters raise NotImplementedError — use execute_query() instead."""
        raise NotImplementedError(
            f"Engine '{self.engine_name}' does not support native queries. "
            f"Use execute_query() with {self.query_language.upper()} syntax instead."
        )

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
