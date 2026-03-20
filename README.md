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