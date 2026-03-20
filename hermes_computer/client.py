from __future__ import annotations

import requests

from .config import get_config


class ComputerClient:
    def __init__(self, base_url: str | None = None, timeout: float | None = None):
        config = get_config()
        self.base_url = base_url or config.base_url
        self.timeout = timeout if timeout is not None else config.timeout_seconds

    def _request(self, method: str, path: str, **kwargs):
        response = requests.request(method, f"{self.base_url}{path}", timeout=self.timeout, **kwargs)
        response.raise_for_status()
        return response.json()

    def health(self):
        return self._request("GET", "/health")

    def status(self):
        return self._request("GET", "/status")

    def list_windows(self):
        return self._request("GET", "/windows")

    def focus_window(self, payload: dict):
        return self._request("POST", "/focus-window", json=payload)

    def open_application(self, payload: dict):
        return self._request("POST", "/open-application", json=payload)

    def capture_screen(self, payload: dict):
        return self._request("POST", "/capture-screen", json=payload)

    def snapshot_ui(self, depth: int = 3, max_nodes: int = 160):
        return self._request("GET", f"/snapshot-ui?depth={depth}&max_nodes={max_nodes}")

    def click_element(self, payload: dict):
        return self._request("POST", "/click-element", json=payload)

    def click_at(self, payload: dict):
        return self._request("POST", "/click-at", json=payload)

    def type_text(self, payload: dict):
        return self._request("POST", "/type-text", json=payload)

    def press_keys(self, payload: dict):
        return self._request("POST", "/press-keys", json=payload)
