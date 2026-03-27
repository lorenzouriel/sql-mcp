import pytest
from sql_mcp.security import SecurityPolicy, get_banned_patterns


def _policy(engine: str = "mssql", read_only: bool = True) -> SecurityPolicy:
    return SecurityPolicy(read_only=read_only, engine=engine)


class TestReadOnlyEnforcement:

    def test_allows_select(self):
        ok, reason = _policy().validate_query("SELECT 1")
        assert ok is True
        assert reason is None

    def test_blocks_insert(self):
        ok, reason = _policy().validate_query("INSERT INTO t VALUES (1)")
        assert ok is False
        assert reason is not None

    def test_blocks_update(self):
        ok, reason = _policy().validate_query("UPDATE t SET col=1")
        assert ok is False

    def test_blocks_delete(self):
        ok, reason = _policy().validate_query("DELETE FROM t")
        assert ok is False

    def test_blocks_non_select_in_read_only(self):
        ok, reason = _policy().validate_query("WITH cte AS (SELECT 1) INSERT INTO t SELECT * FROM cte")
        assert ok is False

    def test_write_allowed_when_disabled(self):
        p = _policy(read_only=False)
        ok, _ = p.validate_query("INSERT INTO t VALUES (1)")
        assert ok is True


class TestBannedKeywords:

    def test_mssql_blocks_exec(self):
        ok, reason = _policy("mssql").validate_query("EXEC sp_help")
        assert ok is False

    def test_mssql_blocks_xp_cmdshell(self):
        ok, reason = _policy("mssql").validate_query("EXEC xp_cmdshell 'dir'")
        assert ok is False

    def test_postgres_blocks_copy(self):
        ok, _ = _policy("postgres").validate_query("COPY t FROM '/etc/passwd'")
        assert ok is False

    def test_postgres_blocks_pg_read_file(self):
        ok, _ = _policy("postgres").validate_query("SELECT pg_read_file('/etc/passwd')")
        assert ok is False

    def test_mysql_blocks_load_data(self):
        ok, _ = _policy("mysql").validate_query("LOAD DATA INFILE '/etc/passwd' INTO TABLE t")
        assert ok is False

    def test_sqlite_blocks_attach(self):
        ok, _ = _policy("sqlite").validate_query("ATTACH '/etc/passwd' AS other")
        assert ok is False

    def test_common_drop_blocked_on_all_engines(self):
        for engine in ("mssql", "postgres", "mysql", "sqlite"):
            ok, _ = _policy(engine).validate_query("DROP TABLE t")
            assert ok is False, f"DROP should be blocked on {engine}"


class TestMultiStatement:

    def test_blocks_semicolon_separated(self):
        ok, reason = _policy().validate_query("SELECT 1; SELECT 2")
        assert ok is False
        assert "Multi-statement" in (reason or "")

    def test_allows_trailing_semicolon(self):
        ok, _ = _policy().validate_query("SELECT 1;")
        assert ok is True

    def test_mssql_blocks_go_separator(self):
        ok, _ = _policy("mssql").validate_query("SELECT 1\nGO\nSELECT 2")
        assert ok is False

    def test_postgres_allows_go_in_query(self):
        # 'GO' is not a separator in Postgres
        ok, _ = _policy("postgres", read_only=False).validate_query(
            "SELECT * FROM go_table"
        )
        assert ok is True


class TestEdgeCases:

    def test_empty_query(self):
        ok, reason = _policy().validate_query("")
        assert ok is False
        assert reason is not None

    def test_whitespace_only(self):
        ok, _ = _policy().validate_query("   ")
        assert ok is False

    def test_query_too_long(self):
        p = SecurityPolicy(max_query_length=10)
        ok, _ = p.validate_query("SELECT * FROM very_long_table_name")
        assert ok is False

    def test_explain_returns_dict(self):
        p = _policy("postgres")
        info = p.explain()
        assert info["engine"] == "postgres"
        assert "read_only" in info
        assert "banned_pattern_count" in info


class TestGetBannedPatterns:

    def test_known_engines_return_lists(self):
        for engine in ("mssql", "postgres", "mysql", "mariadb", "sqlite"):
            patterns = get_banned_patterns(engine)
            assert isinstance(patterns, list)
            assert len(patterns) > 0

    def test_unknown_engine_returns_common(self):
        patterns = get_banned_patterns("oracle")
        assert isinstance(patterns, list)
