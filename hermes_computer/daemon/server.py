from __future__ import annotations

import time

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
    WorkflowRequest,
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

    @app.post("/run-workflow")
    def run_workflow(payload: WorkflowRequest):
        results = []
        actions = {
            "focus_window": lambda params: guard(backend.focus_window, **params),
            "open_application": lambda params: guard(backend.open_application, params["app_name"]),
            "capture_screen": lambda params: guard(
                backend.capture_screen,
                display=int(params.get("display", 1)),
                fmt=str(params.get("format", "png")),
            ),
            "snapshot_ui": lambda params: guard(
                backend.snapshot_ui,
                depth=int(params.get("depth", 3)),
                max_nodes=int(params.get("max_nodes", 160)),
            ).model_dump(),
            "click_element": lambda params: guard(backend.click_element, **params),
            "click_at": lambda params: guard(
                backend.click_at,
                float(params["x"]),
                float(params["y"]),
                button=str(params.get("button", "left")),
                click_count=int(params.get("click_count", 1)),
            ),
            "type_text": lambda params: guard(backend.type_text, str(params["text"])),
            "press_keys": lambda params: guard(backend.press_keys, list(params["keys"])),
        }
        for index, step in enumerate(payload.steps):
            try:
                result = actions[step.action](step.params)
                results.append({"index": index, "action": step.action, "ok": True, "result": result})
            except HTTPException as exc:
                results.append({"index": index, "action": step.action, "ok": False, "error": exc.detail, "status_code": exc.status_code})
                if not payload.continue_on_error:
                    return {"ok": False, "results": results}
            if step.pause_ms > 0:
                time.sleep(step.pause_ms / 1000.0)
        return {"ok": all(result["ok"] for result in results), "results": results}

    return app
