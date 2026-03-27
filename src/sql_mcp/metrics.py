import time
import logging
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest

logger = logging.getLogger(__name__)

REGISTRY = CollectorRegistry()

queries_executed_total = Counter(
    "sql_queries_executed_total",
    "Total queries executed",
    ["tool_name", "engine", "connection_id", "status"],
    registry=REGISTRY,
)
queries_blocked_total = Counter(
    "sql_queries_blocked_total",
    "Total queries blocked by policy",
    ["reason", "engine", "connection_id"],
    registry=REGISTRY,
)
errors_total = Counter(
    "sql_errors_total",
    "Total errors",
    ["error_type", "engine"],
    registry=REGISTRY,
)
query_duration_seconds = Histogram(
    "sql_query_duration_seconds",
    "Query latency in seconds",
    ["tool_name", "engine", "connection_id"],
    registry=REGISTRY,
)
query_rows_returned = Histogram(
    "sql_query_rows_returned",
    "Rows returned per query",
    ["tool_name", "engine"],
    buckets=[1, 10, 100, 1000, 10000, 50000],
    registry=REGISTRY,
)
active_queries = Gauge(
    "sql_active_queries",
    "Number of currently active queries",
    registry=REGISTRY,
)
active_connections = Gauge(
    "sql_active_connections",
    "Number of active database connections",
    ["engine"],
    registry=REGISTRY,
)
server_ready = Gauge(
    "sql_server_ready",
    "Server readiness (1=ready, 0=not ready)",
    registry=REGISTRY,
)


def record_query_blocked(
    reason: str,
    engine: str = "unknown",
    connection_id: str = "default",
) -> None:
    queries_blocked_total.labels(
        reason=reason, engine=engine, connection_id=connection_id
    ).inc()


def get_metrics_text() -> str:
    return generate_latest(REGISTRY).decode("utf-8")


class MetricsContext:
    def __init__(
        self,
        tool_name: str,
        engine: str = "unknown",
        connection_id: str = "default",
    ):
        self.tool_name = tool_name
        self.engine = engine
        self.connection_id = connection_id
        self.start_time: float = 0.0
        self.rows: int = 0

    def __enter__(self) -> "MetricsContext":
        self.start_time = time.time()
        active_queries.inc()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        duration = time.time() - self.start_time
        active_queries.dec()
        status = "error" if exc_type else "success"
        queries_executed_total.labels(
            tool_name=self.tool_name,
            engine=self.engine,
            connection_id=self.connection_id,
            status=status,
        ).inc()
        query_duration_seconds.labels(
            tool_name=self.tool_name,
            engine=self.engine,
            connection_id=self.connection_id,
        ).observe(duration)
        if exc_type is None:
            query_rows_returned.labels(
                tool_name=self.tool_name, engine=self.engine
            ).observe(self.rows)
        elif exc_type is not None:
            errors_total.labels(
                error_type=exc_type.__name__, engine=self.engine
            ).inc()
        return False

    def set_rows(self, count: int) -> None:
        self.rows = count
