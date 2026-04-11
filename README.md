BLETrack

BLETrack is a FastAPI service for tracking BLE presence data from ESPresense through MQTT, storing it in TimescaleDB, and exposing a simple web dashboard for enrollment and device mapping.

## Architecture (Brief)

The data flow is:

1. ESPresense publishes device observations and fingerprint topics to MQTT.
2. A background MQTT ingester in the API subscribes to `espresense/#`.
3. Presence events are written to `presence_events` (Timescale hypertable).
4. Fingerprint topics are written to `fingerprint_registry`.
5. The FastAPI app exposes endpoints for health, enrollment, presence queries, and managed device mappings.
6. `index.html` (served by FastAPI) calls those endpoints for live monitoring and admin actions.

Core components:

- `main.py`: FastAPI app and HTTP routes.
- `mqtt_ingester.py`: MQTT subscriber and DB writes.
- `db.py`: schema setup and SQL queries.
- `espresense_wrapper.py`: calls ESPresense enrollment APIs.
- `index.html`: lightweight dashboard UI.

## Tech Stack

- Python 3 + FastAPI
- PostgreSQL + TimescaleDB
- Mosquitto MQTT broker
- ESPresense nodes (ESP32)
- Plain HTML/JS dashboard (served at `/`)

## Quick Start

1. Create local env file:

```bash
cp .env.example .env
```

2. Start infrastructure:

```bash
docker compose up -d
```

3. Run the API:

```bash
python main.py
```

4. Open the dashboard:

- `http://localhost:5055/`

## MQTT Topics

- Presence stream: `espresense/devices/+/+`
- Fingerprint registry: `espresense/settings/fingerprints/+`

Notes:

- Presence payloads are stored as raw JSON in `presence_events.payload`.
- Fingerprint topics are used to determine paired/enrolled identities.

## Database Notes

`timescaledb-init.sql` initializes the main time-series table (`presence_events`) and indexes.

App-managed tables:

- `fingerprint_registry`: latest fingerprint value by fingerprint device ID.
- `managed_devices`: user-defined mapping between observed IDs and friendly names/types.

Retention:

- `RETENTION_DAYS` controls data retention policy for `presence_events` (default: `90`).

## API Endpoints

- `GET /health`
  - Service, DB, and MQTT ingester status.
- `GET /enroll/start?device_type=phone&name=my_device`
  - Starts ESPresense enrollment mode.
- `GET /enroll/cancel`
  - Cancels enrollment mode.
- `POST /espresense/filter`
  - Updates ESPresense include/exclude filters via `/wifi/extras` form submit.
  - JSON body: `{"include": "phone:andrew_iphone", "exclude": "enroll_mode"}`
- `POST /pair/finalize`
  - Finalizes a device pairing from fingerprint ID, upserts `managed_devices`, and auto-rebuilds ESPresense include filter from active paired devices.
  - JSON body: `{"public_name": "Andrew iPhone", "device_type": "phone", "fingerprint_device_id": "phone:andrew_iphone"}`
- `POST /pair/remove`
  - Marks a paired device inactive and auto-rebuilds ESPresense include filter.
  - JSON body: `{"public_name": "Andrew iPhone"}`
- `GET /dashboard/current?limit=500`
  - Returns only active paired devices with current online/offline status and latest signal snapshot.
- `GET /presence/latest?limit=100&room=sce&paired_only=true`
  - Latest event per `device_id`.
- `GET /presence/history?minutes=60&limit=1000&room=sce&paired_only=true`
  - Presence history window.
- `GET /debug/fingerprints?limit=200`
  - Fingerprint registry rows.
- `GET /devices/discovered?limit=500`
  - Latest discovered raw device IDs.
- `GET /devices/managed?limit=500`
  - Managed mappings with last-seen join.
- `POST /devices/managed`
  - Upserts managed mapping (`display_name`, `observed_device_id`, `device_type`, `fingerprint_device_id`, `is_active`).

## Configuration

Common environment variables:

- `DATABASE_URL`
- `MQTT_BROKER` (default: `localhost`)
- `MQTT_PORT` (default: `1883`)
- `MQTT_TOPIC` (default: `espresense/#`)
- `ESPRESENSE_BASE_URL`
- `ESPRESENSE_TIMEOUT_SECONDS` (default: `5.0`)
- `RETENTION_DAYS` (default: `90`)

See `.env.example` for the full template.
