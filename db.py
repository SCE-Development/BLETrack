import os
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Optional

from dotenv import load_dotenv
from psycopg import Connection, connect
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


load_dotenv()


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://bletrack:bletrack_dev_password@localhost:5433/bletrack",
)


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
