from __future__ import annotations

from fastapi import FastAPI, HTTPException

from ..config import get_config
from ..models import (
    CaptureScreenRequest,
    ClickAtRequest,
    ClickElementRequest,
    FocusWindowRequest,
    OpenApplicationRequest,
    PressKeysRequest,
    TypeTextRequest,
)
from ..mac.backend import DesktopControlError, MacComputerBackend, PermissionDeniedError


def create_app(backend: MacComputerBackend | None = None) -> FastAPI:
    config = get_config()
    backend = backend or MacComputerBackend(config)
    app = FastAPI(title="hermes-computer", version="0.1.0")

    def guard(callable_, *args, **kwargs):
        try:
            return callable_(*args, **kwargs)
        except PermissionDeniedError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except DesktopControlError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/health")
    def health():
        return {"ok": True, "service": "hermes-computer", "version": "0.1.0"}

    @app.get("/status")
    def status():
        return backend.status().model_dump()

    @app.get("/windows")
    def windows():
        return {"windows": [w.model_dump() for w in guard(backend.list_windows)]}

    @app.post("/focus-window")
    def focus_window(payload: FocusWindowRequest):
        return {"ok": True, "result": guard(backend.focus_window, **payload.model_dump())}

    @app.post("/open-application")
    def open_application(payload: OpenApplicationRequest):
        return {"ok": True, "result": guard(backend.open_application, payload.app_name)}

    @app.post("/capture-screen")
    def capture_screen(payload: CaptureScreenRequest):
        return {"ok": True, "result": guard(backend.capture_screen, display=payload.display, fmt=payload.format)}

    @app.get("/snapshot-ui")
    def snapshot_ui(depth: int = 3, max_nodes: int = 160):
        return {"snapshot": guard(backend.snapshot_ui, depth=depth, max_nodes=max_nodes).model_dump()}

    @app.post("/click-element")
    def click_element(payload: ClickElementRequest):
        return {"ok": True, "result": guard(backend.click_element, **payload.model_dump())}

    @app.post("/click-at")
    def click_at(payload: ClickAtRequest):
        return {"ok": True, "result": guard(backend.click_at, payload.x, payload.y, button=payload.button, click_count=payload.click_count)}

    @app.post("/type-text")
    def type_text(payload: TypeTextRequest):
        return {"ok": True, "result": guard(backend.type_text, payload.text)}

    @app.post("/press-keys")
    def press_keys(payload: PressKeysRequest):
        return {"ok": True, "result": guard(backend.press_keys, payload.keys)}

    return app
