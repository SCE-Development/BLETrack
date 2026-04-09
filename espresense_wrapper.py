import json
import time
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from websocket import WebSocketException, WebSocketTimeoutException, create_connection


class ESPresenseWrapperError(Exception):
    pass


class ESPresenseWrapper:
    def __init__(self, base_url: str, timeout_seconds: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def start_enrollment(self, device_type: str, name: str) -> Dict[str, Any]:
        payload = f"{device_type}|{name}"
        return self._send_command("enroll", payload)

    def cancel_enrollment(self) -> Dict[str, Any]:
        return self._send_command("cancelEnroll")

    def _send_command(
        self, command: str, payload: Optional[str] = None
    ) -> Dict[str, Any]:
        ws_url = self._build_ws_url()
        message: Dict[str, Any] = {"command": command}
        if payload is not None:
            message["payload"] = payload

        try:
            ws = create_connection(ws_url, timeout=self.timeout_seconds)
        except (WebSocketException, OSError) as exc:
            raise ESPresenseWrapperError(
                f"Failed to connect to ESPresense websocket at {ws_url}"
            ) from exc

        try:
            ws.send(json.dumps(message))

            deadline = time.time() + self.timeout_seconds
            while time.time() < deadline:
                try:
                    raw = ws.recv()
                except WebSocketTimeoutException:
                    continue

                parsed = self._safe_json(raw)
                if command == "enroll":
                    state = parsed.get("state", {}) if isinstance(parsed, dict) else {}
                    if state.get("enrolling") is True:
                        return {
                            "ok": True,
                            "command": command,
                            "request": message,
                            "ack": parsed,
                        }
                elif command == "cancelEnroll":
                    state = parsed.get("state", {}) if isinstance(parsed, dict) else {}
                    if state.get("enrolling") is False:
                        return {
                            "ok": True,
                            "command": command,
                            "request": message,
                            "ack": parsed,
                        }

            return {
                "ok": False,
                "command": command,
                "request": message,
                "ack": None,
                "error": "timeout",
                "message": "Command sent but no matching state ack before timeout.",
            }
        except WebSocketException as exc:
            raise ESPresenseWrapperError(
                "Failed while sending/receiving websocket messages"
            ) from exc
        finally:
            ws.close()

    def _build_ws_url(self) -> str:
        parsed = urlparse(self.base_url)
        scheme = "wss" if parsed.scheme == "https" else "ws"
        host = parsed.netloc
        if not host:
            host = parsed.path
        return f"{scheme}://{host}/ws"

    @staticmethod
    def _safe_json(raw: Any) -> Dict[str, Any]:
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")
        if not isinstance(raw, str):
            return {}
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}


if __name__ == "__main__":
    client = ESPresenseWrapper("http://10.251.10.179")
    print(client.start_enrollment("s", "s"))
