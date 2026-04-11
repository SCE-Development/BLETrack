import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from db import (
    check_db_health,
    ensure_app_schema,
    ensure_retention_policy,
    list_managed_devices,
    query_discovered_devices,
    query_fingerprint_registry,
    query_latest_presence,
    query_presence_history,
    upsert_managed_device,
)
from espresense_wrapper import ESPresenseWrapper, ESPresenseWrapperError
from mqtt_ingester import MQTTIngester


load_dotenv()


ESPRESENSE_BASE_URL = os.getenv("ESPRESENSE_BASE_URL", "http://10.251.212.248")
ESPRESENSE_TIMEOUT_SECONDS = float(os.getenv("ESPRESENSE_TIMEOUT_SECONDS", "5.0"))
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "90"))


ingester = MQTTIngester()


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_app_schema()
    ensure_retention_policy(RETENTION_DAYS)
    ingester.start()
    yield
    ingester.stop()


app = FastAPI(title="BLETrack Main API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = ESPresenseWrapper(
    base_url=ESPRESENSE_BASE_URL,
    timeout_seconds=ESPRESENSE_TIMEOUT_SECONDS,
)


class ManagedDeviceUpsertRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    observed_device_id: str = Field(min_length=1, max_length=255)
    device_type: str = Field(default="phone", min_length=1, max_length=50)
    fingerprint_device_id: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = True


@app.get("/")
def root() -> FileResponse:
    return FileResponse("index.html")


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
    paired_only: bool = Query(default=False),
) -> dict:
    rows = query_latest_presence(
        limit=limit,
        room=room,
        device_id=device_id,
        alias=alias,
        paired_only=paired_only,
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
    paired_only: bool = Query(default=False),
) -> dict:
    rows = query_presence_history(
        minutes=minutes,
        limit=limit,
        room=room,
        device_id=device_id,
        alias=alias,
        paired_only=paired_only,
    )
    return {
        "ok": True,
        "count": len(rows),
        "minutes": minutes,
        "data": rows,
    }


@app.get("/debug/fingerprints")
def debug_fingerprints(limit: int = Query(default=200, ge=1, le=2000)) -> dict:
    rows = query_fingerprint_registry(limit=limit)
    return {
        "ok": True,
        "count": len(rows),
        "data": rows,
    }


@app.get("/devices/discovered")
def discovered_devices(limit: int = Query(default=500, ge=1, le=2000)) -> dict:
    rows = query_discovered_devices(limit=limit)
    return {
        "ok": True,
        "count": len(rows),
        "data": rows,
    }


@app.get("/devices/managed")
def managed_devices(limit: int = Query(default=500, ge=1, le=2000)) -> dict:
    rows = list_managed_devices(limit=limit)
    return {
        "ok": True,
        "count": len(rows),
        "data": rows,
    }


@app.post("/devices/managed")
def upsert_device(payload: ManagedDeviceUpsertRequest) -> dict:
    row = upsert_managed_device(
        display_name=payload.display_name.strip(),
        observed_device_id=payload.observed_device_id.strip(),
        device_type=payload.device_type.strip(),
        fingerprint_device_id=payload.fingerprint_device_id.strip()
        if payload.fingerprint_device_id
        else None,
        is_active=payload.is_active,
    )
    return {
        "ok": True,
        "data": row,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=5055, reload=True)
