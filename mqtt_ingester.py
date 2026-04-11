import json
import os
import threading
from typing import Any, Dict, Optional

import paho.mqtt.client as mqtt

from db import insert_presence_event


class MQTTIngester:
    def __init__(self) -> None:
        self.broker = self._env_or_default("MQTT_BROKER", "localhost")
        self.port = int(self._env_or_default("MQTT_PORT", "1883"))
        self.topic = self._env_or_default("MQTT_TOPIC", "espresense/devices/+/+")
        self._client = mqtt.Client()
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._connected = False
        self._processed_count = 0
        self._failed_count = 0
        self._last_error: Optional[str] = None

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        self._connected = False
        try:
            self._client.loop_stop()
            self._client.disconnect()
        except Exception:
            pass

    def status(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "connected": self._connected,
            "broker": self.broker,
            "port": self.port,
            "topic": self.topic,
            "processed_count": self._processed_count,
            "failed_count": self._failed_count,
            "last_error": self._last_error,
        }

    def _run(self) -> None:
        try:
            self._client.connect(self.broker, self.port, 60)
            self._client.loop_forever()
        except Exception as exc:
            self._connected = False
            self._last_error = str(exc)

    def _on_connect(
        self, client: mqtt.Client, userdata: Any, flags: Dict[str, Any], rc: int
    ) -> None:
        if rc == 0:
            self._connected = True
            client.subscribe(self.topic)
        else:
            self._connected = False

    def _on_message(
        self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage
    ) -> None:
        try:
            parsed = self._safe_json(msg.payload)
            topic = msg.topic
            room, device_id, alias = self._parse_topic(topic)
            distance_m = (
                self._as_float(parsed.get("distance"))
                if isinstance(parsed, dict)
                else None
            )
            rssi = (
                self._as_int(parsed.get("rssi")) if isinstance(parsed, dict) else None
            )

            insert_presence_event(
                room=room,
                device_id=device_id,
                alias=alias,
                distance_m=distance_m,
                rssi=rssi,
                topic=topic,
                payload=parsed if isinstance(parsed, dict) else {},
            )
            self._processed_count += 1
        except Exception:
            self._failed_count += 1
            self._last_error = "failed_to_insert_presence_event"
            return

    @staticmethod
    def _safe_json(raw: bytes) -> Dict[str, Any]:
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    @staticmethod
    def _as_float(value: Any) -> Optional[float]:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _as_int(value: Any) -> Optional[int]:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_topic(topic: str) -> tuple[str, str, Optional[str]]:
        parts = topic.split("/")
        device_id = parts[2] if len(parts) > 2 else "unknown"
        room = parts[3] if len(parts) > 3 else "unknown"
        alias = None
        if device_id.startswith("phone:"):
            alias = device_id.split(":", 1)[1]
        return room, device_id, alias

    @staticmethod
    def _env_or_default(name: str, default: str) -> str:
        value = os.getenv(name)
        if value is None or value.strip() == "":
            return default
        return value
