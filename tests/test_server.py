from __future__ import annotations

from fastapi.testclient import TestClient

from hermes_computer.daemon.server import create_app
from hermes_computer.models import ComputerStatus, PermissionStatus, UISnapshot, UIElement, WindowInfo


class FakeBackend:
    def status(self):
        return ComputerStatus(
            ok=True,
            platform="darwin-test",
            daemon_version="0.1.0",
            permissions=PermissionStatus(
                accessibility_trusted=True,
                screen_capture_available=True,
                platform_supported=True,
            ),
            frontmost_app="TextEdit",
        )

    def list_windows(self):
        return [WindowInfo(window_id=1, owner_pid=100, owner_name="TextEdit", title="Note", bounds={"x": 1, "y": 2, "width": 300, "height": 200})]

    def focus_window(self, **kwargs):
        return {"ok": True, **kwargs}

    def open_application(self, app_name):
        return {"app_name": app_name}

    def capture_screen(self, **kwargs):
        return {"path": "/tmp/capture.png", **kwargs}

    def snapshot_ui(self, **kwargs):
        return UISnapshot(app_name="TextEdit", pid=100, root=UIElement(role="AXWindow", children=[]), node_count=1)

    def click_element(self, **kwargs):
        return {"clicked": kwargs}

    def click_at(self, x, y, button="left", click_count=1):
        return {"x": x, "y": y, "button": button, "click_count": click_count}

    def type_text(self, text):
        return {"text": text}

    def press_keys(self, keys):
        return {"keys": keys}

    def run_workflow(self, steps, continue_on_error=False):
        return {"steps": steps, "continue_on_error": continue_on_error}


def test_server_routes() -> None:
    client = TestClient(create_app(backend=FakeBackend()))
    assert client.get('/health').json()['ok'] is True
    assert client.get('/status').json()['frontmost_app'] == 'TextEdit'
    assert client.get('/windows').json()['windows'][0]['owner_name'] == 'TextEdit'
    assert client.get('/snapshot-ui').json()['snapshot']['app_name'] == 'TextEdit'
    assert client.post('/focus-window', json={'owner_name': 'TextEdit'}).json()['ok'] is True
    assert client.post('/open-application', json={'app_name': 'Safari'}).json()['result']['app_name'] == 'Safari'
    assert client.post('/capture-screen', json={'display': 1, 'format': 'png'}).json()['result']['path'] == '/tmp/capture.png'
    assert client.post('/click-element', json={'text': 'Save'}).json()['result']['clicked']['text'] == 'Save'
    assert client.post('/click-at', json={'x': 10, 'y': 12}).json()['result']['x'] == 10
    assert client.post('/type-text', json={'text': 'hello'}).json()['result']['text'] == 'hello'
    assert client.post('/press-keys', json={'keys': ['command', 'l']}).json()['result']['keys'] == ['command', 'l']
    workflow = client.post('/run-workflow', json={
        'steps': [
            {'action': 'open_application', 'params': {'app_name': 'TextEdit'}},
            {'action': 'type_text', 'params': {'text': 'hello'}},
        ]
    }).json()
    assert workflow['ok'] is True
    assert workflow['results'][0]['action'] == 'open_application'
    assert workflow['results'][1]['action'] == 'type_text'
