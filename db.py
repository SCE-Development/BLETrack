import os
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Optional

from dotenv import load_dotenv
from psycopg import Connection, connect
from psycopg.rows import dict_row


load_dotenv()


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://bletrack:bletrack_dev_password@localhost:5432/bletrack",
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
                (room, device_id, alias, distance_m, rssi, topic, payload),
            )


def query_latest_presence(
    *,
    limit: int = 100,
    room: Optional[str] = None,
    device_id: Optional[str] = None,
    alias: Optional[str] = None,
) -> List[Dict[str, Any]]:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
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
                    WHERE (%s IS NULL OR room = %s)
                      AND (%s IS NULL OR device_id = %s)
                      AND (%s IS NULL OR alias = %s)
                    ORDER BY device_id, ts DESC
                )
                SELECT *
                FROM latest
                ORDER BY ts DESC
                LIMIT %s
                """,
                (room, room, device_id, device_id, alias, alias, limit),
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
) -> List[Dict[str, Any]]:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
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
                WHERE ts >= NOW() - (%s * INTERVAL '1 minute')
                  AND (%s IS NULL OR room = %s)
                  AND (%s IS NULL OR device_id = %s)
                  AND (%s IS NULL OR alias = %s)
                ORDER BY ts DESC
                LIMIT %s
                """,
                (minutes, room, room, device_id, device_id, alias, alias, limit),
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
