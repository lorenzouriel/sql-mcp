import re
import hashlib
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

WRITE_PATTERNS = [
    r"\bINSERT\b", r"\bUPDATE\b", r"\bDELETE\b",
    r"\bDROP\b", r"\bALTER\b", r"\bTRUNCATE\b", r"\bCREATE\b",
    r"\bGRANT\b", r"\bDENY\b", r"\bREVOKE\b",
]

_BANNED_COMMON = [
    r"\bDROP\b", r"\bALTER\b", r"\bTRUNCATE\b",
    r"\bCREATE\b", r"\bGRANT\b", r"\bREVOKE\b",
]
_BANNED_MSSQL = _BANNED_COMMON + [
    r"\bEXEC\b", r"\bEXECUTE\b", r"\bxp_\w+", r"\bsp_\w+",
    r"\bKILL\b", r"\bSHUTDOWN\b", r"\bOPENROWSET\b",
    r"\bOPENDATASOURCE\b", r"\bBULK\s+INSERT\b",
]
_BANNED_POSTGRES = _BANNED_COMMON + [
    r"\bCOPY\b", r"\bPG_READ_FILE\b", r"\bPG_WRITE_FILE\b",
    r"\bLO_IMPORT\b", r"\bLO_EXPORT\b",
]
_BANNED_MYSQL = _BANNED_COMMON + [
    r"\bLOAD\s+DATA\b", r"\bINTO\s+OUTFILE\b",
    r"\bINTO\s+DUMPFILE\b", r"\bLOAD_FILE\b",
]
_BANNED_SQLITE = _BANNED_COMMON + [r"\bATTACH\b", r"\bDETACH\b"]

# MongoDB MQL — patterns checked on raw (non-normalized) query JSON
_BANNED_MONGODB = [
    r"\$where",       # JavaScript execution
    r"\$function",    # Custom JS aggregation operator
    r"\$accumulator", # Custom JS accumulator
    r"\$out",         # Writes aggregation results to a collection
    r"\$merge",       # Merges aggregation results into a collection
]

# KQL (Fabric Eventhouse) — checked on raw query
_BANNED_KQL = [
    r"(?i)\bexternaldata\b",  # Reads from arbitrary external URLs
    r"(?i)\bplugin\b",        # Arbitrary plugin execution
]

_ENGINE_BANNED: dict[str, list[str]] = {
    "mssql":      _BANNED_MSSQL,
    "postgres":   _BANNED_POSTGRES,
    "mysql":      _BANNED_MYSQL,
    "mariadb":    _BANNED_MYSQL,
    "sqlite":     _BANNED_SQLITE,
    "mongodb":    _BANNED_MONGODB,
    "databricks": _BANNED_POSTGRES,
    "fabric":     _BANNED_MSSQL + _BANNED_KQL,
}

# Engines whose queries must NOT be uppercased before pattern scanning
_RAW_QUERY_ENGINES = {"mongodb"}

# Engines that don't use SELECT syntax (KQL, etc.) — skip the SELECT-only check
# in read-only mode; write operations are still blocked via WRITE_PATTERNS
_NO_SELECT_REQUIRED = {"fabric"}


def get_banned_patterns(engine: str) -> list[str]:
    return _ENGINE_BANNED.get(engine, _BANNED_COMMON)


def hash_sql(sql: str) -> str:
    return hashlib.sha256(sql.encode()).hexdigest()[:16]


def normalize_sql(sql: str) -> str:
    return " ".join(sql.split()).upper()


@dataclass
class SecurityPolicy:
    read_only: bool = True
    query_timeout: int = 30
    max_rows: int = 50_000
    max_query_length: int = 50_000
    engine: str = "mssql"
    banned_patterns: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.banned_patterns:
            self.banned_patterns = get_banned_patterns(self.engine)

    def _has_multiple_statements(self, sql: str) -> bool:
        stripped = sql.strip()
        if stripped.endswith(";"):
            stripped = stripped[:-1].strip()
        if ";" in stripped:
            return True
        if self.engine == "mssql" and re.search(
            r"^\s*GO\s*$", stripped, re.IGNORECASE | re.MULTILINE
        ):
            return True
        return False

    def validate_query(
        self,
        sql: str,
        tool_name: str = "unknown",
        client_id: str = "unknown",
    ) -> tuple[bool, str | None]:
        if not sql or not sql.strip():
            return False, "Empty SQL query"

        if len(sql) > self.max_query_length:
            return False, (
                f"Query exceeds maximum length of {self.max_query_length} characters"
            )

        # Non-SQL engines (e.g. MongoDB MQL) use raw query for pattern scanning
        # to preserve case-sensitive operators like $where, $out, etc.
        use_raw = self.engine in _RAW_QUERY_ENGINES
        normalized = sql if use_raw else normalize_sql(sql)

        for pattern in self.banned_patterns:
            if re.search(pattern, normalized):
                reason = f"Query contains banned pattern: {pattern}"
                logger.warning(
                    "Query denied | tool=%s | reason=%s | sql_hash=%s | client=%s",
                    tool_name, reason, hash_sql(sql), client_id,
                )
                return False, reason

        if not use_raw and self._has_multiple_statements(sql):
            return False, "Multi-statement queries are not allowed"

        if self.read_only and not use_raw:
            for pattern in WRITE_PATTERNS:
                if re.search(pattern, normalized):
                    reason = f"Query contains write operation: {pattern}"
                    logger.warning(
                        "Policy violation | tool=%s | reason=%s | sql_hash=%s | client=%s",
                        tool_name, reason, hash_sql(sql), client_id,
                    )
                    return False, reason
            if self.engine not in _NO_SELECT_REQUIRED and not re.match(
                r"^\s*(SELECT|WITH)\b", normalized
            ):
                return False, "Only SELECT queries are allowed in read-only mode"

        logger.info(
            "Query allowed | tool=%s | mode=%s | sql_hash=%s | client=%s",
            tool_name,
            "read_only" if self.read_only else "write",
            hash_sql(sql),
            client_id,
        )
        return True, None

    def explain(self) -> dict:
        return {
            "read_only": self.read_only,
            "query_timeout_seconds": self.query_timeout,
            "max_rows": self.max_rows,
            "max_query_length": self.max_query_length,
            "engine": self.engine,
            "banned_pattern_count": len(self.banned_patterns),
        }
