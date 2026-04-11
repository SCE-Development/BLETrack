import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
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
    query_fingerprint_by_device_id,
    query_discovered_devices,
    query_fingerprint_registry,
    query_latest_presence,
    query_presence_history,
    set_managed_device_active,
    upsert_managed_device,
)
from espresense_wrapper import ESPresenseWrapper, ESPresenseWrapperError
from mqtt_ingester import MQTTIngester


load_dotenv()


ESPRESENSE_BASE_URL = os.getenv("ESPRESENSE_BASE_URL", "http://10.251.212.248")
ESPRESENSE_TIMEOUT_SECONDS = float(os.getenv("ESPRESENSE_TIMEOUT_SECONDS", "5.0"))
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "90"))
ONLINE_TIMEOUT_SECONDS = int(os.getenv("ONLINE_TIMEOUT_SECONDS", "60"))


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


class FilterUpdateRequest(BaseModel):
    include: Optional[str] = None
    exclude: Optional[str] = None


class PairFinalizeRequest(BaseModel):
    public_name: str = Field(min_length=1, max_length=120)
    device_type: str = Field(default="phone", min_length=1, max_length=50)
    fingerprint_device_id: Optional[str] = Field(default=None, max_length=255)
    observed_device_id: Optional[str] = Field(default=None, max_length=255)


class DeviceRemoveRequest(BaseModel):
    public_name: str = Field(min_length=1, max_length=120)


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


@app.post("/espresense/filter")
def update_filter(payload: FilterUpdateRequest) -> dict:
    include = payload.include.strip() if payload.include is not None else None
    exclude = payload.exclude.strip() if payload.exclude is not None else None

    if include == "":
        include = ""
    if exclude == "":
        exclude = ""

    if include is None and exclude is None:
        return {
            "ok": False,
            "error": "invalid_request",
            "message": "At least one of include or exclude is required.",
        }

    try:
        return client.update_filters(include=include, exclude=exclude)
    except ESPresenseWrapperError as exc:
        return {
            "ok": False,
            "error": "espresense_connection_error",
            "message": str(exc),
        }


def _build_filter_from_active_devices() -> str:
    rows = list_managed_devices(limit=2000)
    include_ids = []
    for row in rows:
        if not row.get("is_active"):
            continue
        fingerprint_id = (row.get("fingerprint_device_id") or "").strip()
        observed_id = (row.get("observed_device_id") or "").strip()
        value = fingerprint_id or observed_id
        if value:
            include_ids.append(value)
    unique = sorted(set(include_ids))
    return ", ".join(unique)


def _is_online(last_seen_ts: object) -> bool:
    if not isinstance(last_seen_ts, datetime):
        return False

    ts = last_seen_ts
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)

    age_seconds = (datetime.now(timezone.utc) - ts).total_seconds()
    return age_seconds <= ONLINE_TIMEOUT_SECONDS


@app.post("/pair/finalize")
def pair_finalize(payload: PairFinalizeRequest) -> dict:
    fingerprint_device_id = (payload.fingerprint_device_id or "").strip()
    observed_device_id = (payload.observed_device_id or "").strip()

    if not fingerprint_device_id and not observed_device_id:
        return {
            "ok": False,
            "error": "invalid_request",
            "message": "Provide fingerprint_device_id or observed_device_id.",
        }

    if fingerprint_device_id:
        fingerprint_row = query_fingerprint_by_device_id(fingerprint_device_id)
        if not fingerprint_row:
            return {
                "ok": False,
                "error": "fingerprint_not_found",
                "message": f"Fingerprint '{fingerprint_device_id}' was not found in registry.",
            }
        observed_device_id = fingerprint_device_id.split(":", 1)[0]

    managed = upsert_managed_device(
        display_name=payload.public_name.strip(),
        observed_device_id=observed_device_id,
        device_type=payload.device_type.strip(),
        fingerprint_device_id=fingerprint_device_id if fingerprint_device_id else None,
        is_active=True,
    )

    include_value = _build_filter_from_active_devices()
    filter_result = client.update_filters(include=include_value)

    return {
        "ok": True,
        "data": {
            "managed_device": managed,
            "pairing_mode": "fingerprint" if fingerprint_device_id else "observed_id",
            "filter_include": include_value,
            "filter_result": filter_result,
        },
    }


@app.get("/pair/candidates")
def pair_candidates(limit: int = Query(default=200, ge=1, le=2000)) -> dict:
    managed_rows = list_managed_devices(limit=2000)
    active_ids = {
        str(r.get("observed_device_id", "")).strip()
        for r in managed_rows
        if r.get("is_active") and r.get("observed_device_id")
    }

    latest_rows = query_latest_presence(limit=limit)
    candidates = []
    seen_ids = set()

    for row in latest_rows:
        device_id = str(row.get("device_id", "")).strip()
        if not device_id or device_id in active_ids or device_id in seen_ids:
            continue
        if device_id.startswith("node:"):
            continue

        payload = row.get("payload") or {}
        payload_name = payload.get("name") if isinstance(payload, dict) else None
        looks_personal = (
            device_id in {"phone", "tablet", "watch"}
            or device_id.startswith(("phone:", "tablet:", "watch:", "irk:"))
            or bool(payload_name)
        )
        if not looks_personal:
            continue

        candidates.append(
            {
                "observed_device_id": device_id,
                "live_name": payload_name,
                "room": row.get("room"),
                "last_seen_ts": row.get("ts"),
            }
        )
        seen_ids.add(device_id)

    return {
        "ok": True,
        "count": len(candidates),
        "data": candidates,
    }


@app.post("/pair/remove")
def pair_remove(payload: DeviceRemoveRequest) -> dict:
    public_name = payload.public_name.strip()
    updated = set_managed_device_active(public_name, False)
    if not updated:
        return {
            "ok": False,
            "error": "not_found",
            "message": f"Device '{public_name}' was not found.",
        }

    include_value = _build_filter_from_active_devices()
    filter_result = client.update_filters(include=include_value)

    return {
        "ok": True,
        "data": {
            "managed_device": updated,
            "filter_include": include_value,
            "filter_result": filter_result,
        },
    }


@app.get("/dashboard/current")
def dashboard_current(limit: int = Query(default=200, ge=1, le=2000)) -> dict:
    managed_rows = list_managed_devices(limit=limit)
    active_rows = [r for r in managed_rows if r.get("is_active")]

    data = []
    for row in active_rows:
        fingerprint_id = row.get("fingerprint_device_id")
        observed_id = row.get("observed_device_id")
        last_seen_ts = row.get("last_seen_ts")
        online = _is_online(last_seen_ts)

        data.append(
            {
                "public_name": row.get("display_name"),
                "device_type": row.get("device_type"),
                "fingerprint_device_id": fingerprint_id,
                "observed_device_id": observed_id,
                "is_online": online,
                "status": "online" if online else "offline",
                "online_timeout_seconds": ONLINE_TIMEOUT_SECONDS,
                "last_seen_ts": last_seen_ts,
                "room": row.get("last_seen_room"),
                "distance_m": row.get("last_distance_m"),
                "rssi": row.get("last_rssi"),
                "payload_name": row.get("last_payload_name"),
                "live_device_id": row.get("last_live_device_id"),
            }
        )

    return {
        "ok": True,
        "count": len(data),
        "data": data,
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
