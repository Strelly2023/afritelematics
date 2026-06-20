from __future__ import annotations

from afritech.afriprogramming.persistence import _rewrite_sql_for_postgres, _split_sql_script


def test_postgres_insert_or_replace_rewrites_to_conflict_upsert() -> None:
    sql = """
        INSERT OR REPLACE INTO policy_definitions (
            policy_id, organization_id, policy_name, version,
            rule_type, rule_payload_json, active, created_by,
            policy_hash, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    rewritten = _rewrite_sql_for_postgres(sql)

    assert rewritten.startswith("INSERT INTO policy_definitions")
    assert "ON CONFLICT (organization_id, policy_name, version) DO UPDATE SET" in rewritten
    assert "%s" not in rewritten or rewritten.count("%s") == 10


def test_postgres_script_split_drops_pragmas() -> None:
    script = """
    PRAGMA journal_mode=WAL;
    CREATE TABLE example (id TEXT PRIMARY KEY);
    """

    statements = _split_sql_script(script)

    assert statements == ["CREATE TABLE example (id TEXT PRIMARY KEY);"]
