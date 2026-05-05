import os
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Optional

from psycopg import Connection, connect
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb



DATABASE_URL = os.getenv("DATABASE_URL")


@contextmanager
def get_db() -> Iterator[Connection]:
    conn = connect(DATABASE_URL, row_factory=dict_row)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def check_db_health() -> bool:
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                row = cur.fetchone()
                return bool(row)
    except Exception:
        return False


def ensure_app_schema() -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS fingerprint_registry (
                    device_id TEXT PRIMARY KEY,
                    fingerprint_value TEXT NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS managed_devices (
                    id BIGSERIAL PRIMARY KEY,
                    display_name TEXT NOT NULL UNIQUE,
                    device_type TEXT NOT NULL DEFAULT 'phone',
                    observed_device_id TEXT NOT NULL,
                    fingerprint_device_id TEXT,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cur.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_managed_devices_fingerprint_device_id
                ON managed_devices (fingerprint_device_id)
                WHERE fingerprint_device_id IS NOT NULL
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_managed_devices_observed_device_id
                ON managed_devices (observed_device_id)
                """
            )


def upsert_managed_device(
    *,
    display_name: str,
    observed_device_id: str,
    device_type: str,
    fingerprint_device_id: Optional[str],
    is_active: bool,
) -> Dict[str, Any]:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO managed_devices (
                    display_name,
                    observed_device_id,
                    device_type,
                    fingerprint_device_id,
                    is_active,
                    updated_at
                )
                VALUES (%s, %s, %s, %s, %s, NOW())
                ON CONFLICT (display_name)
                DO UPDATE SET
                    observed_device_id = EXCLUDED.observed_device_id,
                    device_type = EXCLUDED.device_type,
                    fingerprint_device_id = EXCLUDED.fingerprint_device_id,
                    is_active = EXCLUDED.is_active,
                    updated_at = NOW()
                RETURNING
                    id,
                    display_name,
                    observed_device_id,
                    device_type,
                    fingerprint_device_id,
                    is_active,
                    created_at,
                    updated_at
                """,
                (
                    display_name,
                    observed_device_id,
                    device_type,
                    fingerprint_device_id,
                    is_active,
                ),
            )
            row = cur.fetchone()
            return dict(row) if row else {}


def list_managed_devices(limit: int = 500) -> List[Dict[str, Any]]:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    m.id,
                    m.display_name,
                    m.device_type,
                    m.observed_device_id,
                    m.fingerprint_device_id,
                    m.is_active,
                    m.created_at,
                    m.updated_at,
                    p.ts AS last_seen_ts,
                    p.room AS last_seen_room,
                    p.distance_m AS last_distance_m,
                    p.rssi AS last_rssi,
                    p.device_id AS last_live_device_id,
                    p.payload_name AS last_payload_name
                FROM managed_devices m
                LEFT JOIN LATERAL (
                    SELECT
                        ts,
                        room,
                        distance_m,
                        rssi,
                        device_id,
                        payload->>'name' AS payload_name
                    FROM presence_events pe
                    WHERE (
                        pe.device_id = m.observed_device_id
                        OR (
                            m.fingerprint_device_id IS NOT NULL
                            AND pe.device_id = m.fingerprint_device_id
                        )
                        OR (
                            m.fingerprint_device_id IS NOT NULL
                            AND split_part(m.fingerprint_device_id, ':', 1) = pe.device_id
                        )
                    )
                    ORDER BY pe.ts DESC
                    LIMIT 1
                ) p ON TRUE
                ORDER BY m.display_name ASC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()
            return [dict(row) for row in rows]


def set_managed_device_active(
    display_name: str, is_active: bool
) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE managed_devices
                SET is_active = %s,
                    updated_at = NOW()
                WHERE display_name = %s
                RETURNING
                    id,
                    display_name,
                    observed_device_id,
                    device_type,
                    fingerprint_device_id,
                    is_active,
                    created_at,
                    updated_at
                """,
                (is_active, display_name),
            )
            row = cur.fetchone()
            return dict(row) if row else None


def query_fingerprint_by_device_id(device_id: str) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT device_id, fingerprint_value, updated_at
                FROM fingerprint_registry
                WHERE device_id = %s
                """,
                (device_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None


def query_discovered_devices(limit: int = 500) -> List[Dict[str, Any]]:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM (
                    SELECT DISTINCT ON (device_id)
                        device_id,
                        payload->>'name' AS discovered_name,
                        ts,
                        room,
                        distance_m,
                        rssi
                    FROM presence_events
                    ORDER BY device_id, ts DESC
                ) latest
                ORDER BY ts DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()
            return [dict(row) for row in rows]


def upsert_fingerprint(device_id: str, fingerprint_value: str) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO fingerprint_registry (device_id, fingerprint_value, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (device_id)
                DO UPDATE SET
                    fingerprint_value = EXCLUDED.fingerprint_value,
                    updated_at = NOW()
                """,
                (device_id, fingerprint_value),
            )


def insert_presence_event(
    *,
    room: str,
    device_id: str,
    alias: Optional[str],
    distance_m: Optional[float],
    rssi: Optional[int],
    topic: str,
    payload: Dict[str, Any],
) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO presence_events (
                    room,
                    device_id,
                    alias,
                    distance_m,
                    rssi,
                    topic,
                    payload
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (room, device_id, alias, distance_m, rssi, topic, Jsonb(payload)),
            )


def query_latest_presence(
    *,
    limit: int = 100,
    room: Optional[str] = None,
    device_id: Optional[str] = None,
    alias: Optional[str] = None,
    paired_only: bool = False,
) -> List[Dict[str, Any]]:
    conditions = []
    params: List[Any] = []

    if room is not None:
        conditions.append("room = %s")
        params.append(room)
    if device_id is not None:
        conditions.append("device_id = %s")
        params.append(device_id)
    if alias is not None:
        conditions.append("alias = %s")
        params.append(alias)
    if paired_only:
        conditions.append(
            """
            (
                device_id IN (
                    SELECT observed_device_id
                    FROM managed_devices
                    WHERE is_active = TRUE
                )
                OR device_id IN (
                    SELECT fingerprint_device_id
                    FROM managed_devices
                    WHERE is_active = TRUE
                      AND fingerprint_device_id IS NOT NULL
                )
                OR
                device_id IN (SELECT device_id FROM fingerprint_registry)
                OR EXISTS (
                    SELECT 1
                    FROM fingerprint_registry fr
                    WHERE split_part(fr.device_id, ':', 1) = presence_events.device_id
                )
            )
            """
        )

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                WITH latest AS (
                    SELECT DISTINCT ON (device_id)
                        ts,
                        room,
                        device_id,
                        alias,
                        distance_m,
                        rssi,
                        topic,
                        payload
                    FROM presence_events
                    {where_clause}
                    ORDER BY device_id, ts DESC
                )
                SELECT *
                FROM latest
                ORDER BY ts DESC
                LIMIT %s
                """,
                [*params, limit],
            )
            rows = cur.fetchall()
            return [dict(row) for row in rows]


def query_presence_history(
    *,
    minutes: int = 60,
    limit: int = 1000,
    room: Optional[str] = None,
    device_id: Optional[str] = None,
    alias: Optional[str] = None,
    paired_only: bool = False,
) -> List[Dict[str, Any]]:
    conditions = ["ts >= NOW() - (%s * INTERVAL '1 minute')"]
    params: List[Any] = [minutes]

    if room is not None:
        conditions.append("room = %s")
        params.append(room)
    if device_id is not None:
        conditions.append("device_id = %s")
        params.append(device_id)
    if alias is not None:
        conditions.append("alias = %s")
        params.append(alias)
    if paired_only:
        conditions.append(
            """
            (
                device_id IN (
                    SELECT observed_device_id
                    FROM managed_devices
                    WHERE is_active = TRUE
                )
                OR device_id IN (
                    SELECT fingerprint_device_id
                    FROM managed_devices
                    WHERE is_active = TRUE
                      AND fingerprint_device_id IS NOT NULL
                )
                OR
                device_id IN (SELECT device_id FROM fingerprint_registry)
                OR EXISTS (
                    SELECT 1
                    FROM fingerprint_registry fr
                    WHERE split_part(fr.device_id, ':', 1) = presence_events.device_id
                )
            )
            """
        )

    where_clause = "WHERE " + " AND ".join(conditions)

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT
                    ts,
                    room,
                    device_id,
                    alias,
                    distance_m,
                    rssi,
                    topic,
                    payload
                FROM presence_events
                {where_clause}
                ORDER BY ts DESC
                LIMIT %s
                """,
                [*params, limit],
            )
            rows = cur.fetchall()
            return [dict(row) for row in rows]


def query_fingerprint_registry(limit: int = 200) -> List[Dict[str, Any]]:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT device_id, fingerprint_value, updated_at
                FROM fingerprint_registry
                ORDER BY updated_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()
            return [dict(row) for row in rows]


def ensure_retention_policy(days: int = 90) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT add_retention_policy(
                    'presence_events',
                    drop_after => make_interval(days => %s),
                    if_not_exists => TRUE
                )
                """,
                (days,),
            )
