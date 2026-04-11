import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Query
from dotenv import load_dotenv

from db import (
    check_db_health,
    ensure_retention_policy,
    query_latest_presence,
    query_presence_history,
)
from espresense_wrapper import ESPresenseWrapper, ESPresenseWrapperError
from mqtt_ingester import MQTTIngester


load_dotenv()


ESPRESENSE_BASE_URL = os.getenv("ESPRESENSE_BASE_URL", "http://10.251.10.179")
ESPRESENSE_TIMEOUT_SECONDS = float(os.getenv("ESPRESENSE_TIMEOUT_SECONDS", "5.0"))
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "90"))


ingester = MQTTIngester()


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_retention_policy(RETENTION_DAYS)
    ingester.start()
    yield
    ingester.stop()


app = FastAPI(title="BLETrack Main API", version="1.0.0", lifespan=lifespan)

client = ESPresenseWrapper(
    base_url=ESPRESENSE_BASE_URL,
    timeout_seconds=ESPRESENSE_TIMEOUT_SECONDS,
)


@app.get("/health")
def health() -> dict:
    ingester_status = ingester.status()
    return {
        "ok": True,
        "service": "bletrack-api",
        "espresense_base_url": ESPRESENSE_BASE_URL,
        "database_ok": check_db_health(),
        "mqtt_ingester": ingester_status,
    }


@app.get("/enroll/start")
def enroll_start(
    device_type: str = Query(default="phone", min_length=1),
    name: str = Query(default="new_device", min_length=1),
) -> dict:
    try:
        result = client.start_enrollment(device_type=device_type, name=name)
        return result
    except ESPresenseWrapperError as exc:
        return {
            "ok": False,
            "error": "espresense_connection_error",
            "message": str(exc),
        }


@app.get("/enroll/cancel")
def enroll_cancel() -> dict:
    try:
        result = client.cancel_enrollment()
        return result
    except ESPresenseWrapperError as exc:
        return {
            "ok": False,
            "error": "espresense_connection_error",
            "message": str(exc),
        }


@app.get("/presence/latest")
def presence_latest(
    limit: int = Query(default=100, ge=1, le=1000),
    room: Optional[str] = Query(default=None),
    device_id: Optional[str] = Query(default=None),
    alias: Optional[str] = Query(default=None),
) -> dict:
    rows = query_latest_presence(
        limit=limit,
        room=room,
        device_id=device_id,
        alias=alias,
    )
    return {
        "ok": True,
        "count": len(rows),
        "data": rows,
    }


@app.get("/presence/history")
def presence_history(
    minutes: int = Query(default=60, ge=1, le=60 * 24 * 30),
    limit: int = Query(default=1000, ge=1, le=5000),
    room: Optional[str] = Query(default=None),
    device_id: Optional[str] = Query(default=None),
    alias: Optional[str] = Query(default=None),
) -> dict:
    rows = query_presence_history(
        minutes=minutes,
        limit=limit,
        room=room,
        device_id=device_id,
        alias=alias,
    )
    return {
        "ok": True,
        "count": len(rows),
        "minutes": minutes,
        "data": rows,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=5055, reload=True)
