SCE Room Presence Server
A real-time indoor positioning server built for the SCE Lab at SJSU. This project uses BLE (Bluetooth Low Energy) and MQTT to track student presence and proximity within the lab environment.

🚀 Tech Stack
Hardware: ESP32 running ESPresense.

Broker: Mosquitto MQTT running in a Docker container.

Automation/UI: Home Assistant (via manual MQTT sensors).

Protocol: MQTT (Publish/Subscribe) with JSON payloads.

🏗 System Architecture
ESP32 Nodes: Scan for specific IRK (Identity Resolving Keys) from registered mobile devices.

MQTT Broker: Receives distance and RSSI data on the topic espresense/devices/phone:<user>/sce.

Clients:

Home Assistant: Triggers automations (e.g., entrance notifications) based on distance thresholds.

Web Wrapper: A custom JavaScript frontend that subscribes directly to the MQTT wildcard topic for real-time dashboarding.

🛠 Setup & Installation
Docker (MQTT Broker)
Bash
docker run -d \
  --name=mosquitto \
  -p 1883:1883 \
  -p 9001:9001 \
  -v $(pwd)/mosquitto.conf:/mosquitto/config/mosquitto.conf \
  eclipse-mosquitto
ESPresense Configuration
Room Name: SCE

Target IDs: Filtered to phone:andrew (and registered peers).

Timeout: 60s (to prevent ghost presence).

📡 MQTT Topic Structure
espresense/devices/+/sce - Wildcard topic for all room activity.

espresense/settings/fingerprints/+ - Topic for remote enrollment of new IRKs.

## TimescaleDB (Postgres) Setup

This project includes a TimescaleDB container configured via `docker-compose.yml`.

1. Copy environment defaults:
   - `cp .env.example .env`
2. Start infrastructure:
   - `docker compose up -d`
3. Verify DB is running:
   - `docker ps`

On first startup, `timescaledb-init.sql` is executed automatically and will:
- Enable `timescaledb` extension
- Create `presence_events` table
- Convert it into a hypertable on `ts`
- Create helpful indexes for query performance

## API Endpoints

- `GET /health`
  - Reports API status, DB status, and MQTT ingester status.
- `GET /enroll/start?device_type=phone&name=andrew`
  - Triggers ESPresense enroll mode over websocket.
- `GET /enroll/cancel`
  - Cancels active ESPresense enroll mode.
- `GET /presence/latest?limit=100&room=sce&paired_only=true`
  - Returns latest record per device.
- `GET /presence/history?minutes=60&limit=1000&room=sce&paired_only=true`
  - Returns recent event history for dashboards/charts.
- `GET /devices/discovered`
  - Returns latest seen device ids from raw presence stream.
- `GET /devices/managed`
  - Returns managed/enrolled device mappings with last seen data.
- `POST /devices/managed`
  - Upserts a managed device mapping (`display_name`, `observed_device_id`, etc.).

## MQTT to DB Buffer

When `main.py` starts, it launches an MQTT ingester thread that subscribes to `MQTT_TOPIC` and writes each message into `presence_events`.

Default env values:
- `MQTT_BROKER=localhost`
- `MQTT_PORT=1883`
- `MQTT_TOPIC=espresense/#`
- `RETENTION_DAYS=90`

Paired-device filtering uses `fingerprint_registry`, populated automatically from retained fingerprint topics under `espresense/settings/fingerprints/+`.

## Simple Frontend

- Open `http://localhost:5055/` for a simple device manager UI.
- Use discovered IDs to map users in `managed_devices`.
- This is an interim HTML frontend before a full React app.
