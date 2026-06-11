#!/usr/bin/env python3
"""Migrate authoritative AfriRide data from SQLite to PostgreSQL."""

from __future__ import annotations

import argparse
import sys

from afriride_system.backend.determinism import (
    collect_ride_snapshot,
    compare_ride_snapshots,
    persist_derived_snapshots,
    trace_ride_ids,
)
from afriride_system.backend.storage import AfriRideStorage, is_postgres_locator


def main() -> int:
    args = _parse_args()
    source = AfriRideStorage(args.sqlite_path)
    target = AfriRideStorage(args.postgres_url)

    if source.backend != "sqlite":
        raise SystemExit("source must be a SQLite database path")
    if not is_postgres_locator(args.postgres_url):
        raise SystemExit("target must be a PostgreSQL URL")

    if args.truncate_target:
        target.reset()

    _copy_table(
        source,
        target,
        select_sql="""
            SELECT driver_id, online
            FROM drivers
            ORDER BY driver_id
        """,
        insert_sql="""
            INSERT INTO drivers (driver_id, online)
            VALUES (?, ?)
            ON CONFLICT(driver_id) DO UPDATE SET
                online = excluded.online
        """,
        row_mapper=lambda row: (row["driver_id"], row["online"]),
    )
    _copy_table(
        source,
        target,
        select_sql="""
            SELECT ride_id, passenger_id, pickup, destination, status,
                   assigned_driver, trace_hash, state_hash, events_json
            FROM rides
            ORDER BY ride_id
        """,
        insert_sql="""
            INSERT INTO rides (
                ride_id,
                passenger_id,
                pickup,
                destination,
                status,
                assigned_driver,
                trace_hash,
                state_hash,
                events_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ride_id) DO UPDATE SET
                passenger_id = excluded.passenger_id,
                pickup = excluded.pickup,
                destination = excluded.destination,
                status = excluded.status,
                assigned_driver = excluded.assigned_driver,
                trace_hash = excluded.trace_hash,
                state_hash = excluded.state_hash,
                events_json = excluded.events_json
        """,
        row_mapper=lambda row: (
            row["ride_id"],
            row["passenger_id"],
            row["pickup"],
            row["destination"],
            row["status"],
            row["assigned_driver"],
            row["trace_hash"],
            row["state_hash"],
            row["events_json"],
        ),
    )
    _copy_table(
        source,
        target,
        select_sql="""
            SELECT event_id, ride_id, event_type, created_at, payload_json
            FROM ride_events
            ORDER BY event_id
        """,
        insert_sql="""
            INSERT INTO ride_events (
                event_id,
                ride_id,
                event_type,
                created_at,
                payload_json
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(event_id) DO NOTHING
        """,
        row_mapper=lambda row: (
            row["event_id"],
            row["ride_id"],
            row["event_type"],
            row["created_at"],
            row["payload_json"],
        ),
    )
    _copy_table(
        source,
        target,
        select_sql="""
            SELECT trace_row_id, event_id, sequence_id, device_id, actor_type,
                   actor_id, action, payload_json, local_timestamp,
                   normalized_timestamp, app_version, test_mode, ride_id,
                   transition, previous_hash, event_hash
            FROM trace_events
            ORDER BY sequence_id
        """,
        insert_sql="""
            INSERT INTO trace_events (
                trace_row_id,
                event_id,
                sequence_id,
                device_id,
                actor_type,
                actor_id,
                action,
                payload_json,
                local_timestamp,
                normalized_timestamp,
                app_version,
                test_mode,
                ride_id,
                transition,
                previous_hash,
                event_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(event_id) DO NOTHING
        """,
        row_mapper=lambda row: (
            row["trace_row_id"],
            row["event_id"],
            row["sequence_id"],
            row["device_id"],
            row["actor_type"],
            row["actor_id"],
            row["action"],
            row["payload_json"],
            row["local_timestamp"],
            row["normalized_timestamp"],
            row["app_version"],
            row["test_mode"],
            row["ride_id"],
            row["transition"],
            row["previous_hash"],
            row["event_hash"],
        ),
    )
    _copy_table(
        source,
        target,
        select_sql="""
            SELECT idempotency_key, fingerprint, result_json
            FROM idempotency_records
            ORDER BY idempotency_key
        """,
        insert_sql="""
            INSERT INTO idempotency_records (
                idempotency_key,
                fingerprint,
                result_json
            ) VALUES (?, ?, ?)
            ON CONFLICT(idempotency_key) DO UPDATE SET
                fingerprint = excluded.fingerprint,
                result_json = excluded.result_json
        """,
        row_mapper=lambda row: (
            row["idempotency_key"],
            row["fingerprint"],
            row["result_json"],
        ),
    )

    if target.backend == "postgres":
        _sync_sequences(target)

    if not args.skip_derived_rebuild:
        _rebuild_derived(target)

    if args.verify:
        mismatches = _verify(source, target)
        if mismatches:
            for message in mismatches:
                print(message, file=sys.stderr)
            return 1

    print("SQLite to PostgreSQL migration completed.")
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sqlite-path", required=True, help="Path to source SQLite database")
    parser.add_argument("--postgres-url", required=True, help="Target PostgreSQL connection URL")
    parser.add_argument(
        "--truncate-target",
        action="store_true",
        help="Delete target data before import",
    )
    parser.add_argument(
        "--skip-derived-rebuild",
        action="store_true",
        help="Skip rebuilding replay/evidence/receipt projections on target",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Compare replay/evidence/receipt outputs between source and target",
    )
    return parser.parse_args()


def _copy_table(source, target, *, select_sql: str, insert_sql: str, row_mapper) -> None:
    with source.connect() as source_connection:
        rows = source_connection.execute(select_sql).fetchall()
    with target.connect() as target_connection:
        for row in rows:
            target_connection.execute(insert_sql, row_mapper(row))


def _sync_sequences(target: AfriRideStorage) -> None:
    with target.connect() as connection:
        connection.execute(
            """
            SELECT setval(
                pg_get_serial_sequence('ride_events', 'event_id'),
                COALESCE((SELECT MAX(event_id) FROM ride_events), 1),
                true
            )
            """
        )
        connection.execute(
            """
            SELECT setval(
                pg_get_serial_sequence('trace_events', 'trace_row_id'),
                COALESCE((SELECT MAX(trace_row_id) FROM trace_events), 1),
                true
            )
            """
        )


def _rebuild_derived(target: AfriRideStorage) -> None:
    with target.connect() as connection:
        connection.execute("DELETE FROM replay_snapshots")
        connection.execute("DELETE FROM evidence_records")
        connection.execute("DELETE FROM receipt_records")
    for ride_id in trace_ride_ids(target):
        persist_derived_snapshots(target, collect_ride_snapshot(target, ride_id))


def _verify(source: AfriRideStorage, target: AfriRideStorage) -> list[str]:
    messages: list[str] = []
    source_ride_ids = trace_ride_ids(source)
    target_ride_ids = trace_ride_ids(target)
    if source_ride_ids != target_ride_ids:
        messages.append(
            f"ride id mismatch: source={list(source_ride_ids)} target={list(target_ride_ids)}"
        )
        return messages
    for ride_id in source_ride_ids:
        source_snapshot = collect_ride_snapshot(source, ride_id)
        target_snapshot = collect_ride_snapshot(target, ride_id)
        diffs = compare_ride_snapshots(source_snapshot, target_snapshot)
        if diffs:
            messages.append(f"{ride_id}: determinism mismatch -> {diffs}")
    return messages


if __name__ == "__main__":
    raise SystemExit(main())
