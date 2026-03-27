from pydantic import BaseModel, Field, field_validator


class ConnectionConfig(BaseModel):
    id: str = Field(..., pattern=r"^[a-z][a-z0-9_]{0,29}$")
    engine: str
    dsn: str
    read_only: bool = True
    query_timeout: int = Field(default=30, ge=1, le=300)
    max_rows: int = Field(default=50_000, ge=1, le=500_000)
    description: str = ""

    @field_validator("engine")
    @classmethod
    def validate_engine(cls, v: str) -> str:
        supported = {"mssql", "postgres", "mysql", "mariadb", "sqlite"}
        if v not in supported:
            raise ValueError(
                f"Unsupported engine '{v}'. Supported: {', '.join(sorted(supported))}"
            )
        return v


class MultiConnectionConfig(BaseModel):
    connections: list[ConnectionConfig] = Field(..., min_length=1, max_length=20)
