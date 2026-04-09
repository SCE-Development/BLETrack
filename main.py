import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query

from espresense_wrapper import ESPresenseWrapper, ESPresenseWrapperError


ESPRESENSE_BASE_URL = os.getenv("ESPRESENSE_BASE_URL", "http://10.251.10.179")
ESPRESENSE_TIMEOUT_SECONDS = float(os.getenv("ESPRESENSE_TIMEOUT_SECONDS", "5.0"))


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(title="BLETrack Main API", version="1.0.0", lifespan=lifespan)

client = ESPresenseWrapper(
    base_url=ESPRESENSE_BASE_URL,
    timeout_seconds=ESPRESENSE_TIMEOUT_SECONDS,
)


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "service": "bletrack-api",
        "espresense_base_url": ESPRESENSE_BASE_URL,
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=5055, reload=True)
