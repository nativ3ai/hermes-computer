from __future__ import annotations

import json

from .client import ComputerClient

TOOLSET = "hermes-computer"


def _client() -> ComputerClient:
    return ComputerClient()


def _json(payload) -> str:
    return json.dumps(payload, ensure_ascii=True)


def check_computer_available() -> tuple[bool, str | None]:
    try:
        _client().health()
        return True, None
    except Exception as exc:
        return False, f"hermes-computer daemon unavailable: {exc}. Start it with `hermes-computer start-daemon` or `hermes-computer bootstrap`."


def computer_status(args: dict, **kwargs) -> str:
    return _json(_client().status())


def list_windows(args: dict, **kwargs) -> str:
    return _json(_client().list_windows())


def focus_window(args: dict, **kwargs) -> str:
    payload = {k: v for k, v in args.items() if v is not None}
    return _json(_client().focus_window(payload))


def capture_screen(args: dict, **kwargs) -> str:
    payload = {"format": args.get("format", "png"), "display": args.get("display", 1)}
    return _json(_client().capture_screen(payload))


def snapshot_ui(args: dict, **kwargs) -> str:
    return _json(_client().snapshot_ui(depth=int(args.get("depth", 3)), max_nodes=int(args.get("max_nodes", 160))))


def click_element(args: dict, **kwargs) -> str:
    payload = {k: v for k, v in args.items() if v is not None}
    return _json(_client().click_element(payload))


def click_at(args: dict, **kwargs) -> str:
    return _json(_client().click_at({
        "x": args["x"],
        "y": args["y"],
        "button": args.get("button", "left"),
        "click_count": args.get("click_count", 1),
    }))


def type_text(args: dict, **kwargs) -> str:
    return _json(_client().type_text({"text": args["text"]}))


def press_keys(args: dict, **kwargs) -> str:
    return _json(_client().press_keys({"keys": args["keys"]}))


def open_application(args: dict, **kwargs) -> str:
    return _json(_client().open_application({"app_name": args["app_name"]}))


def run_workflow(args: dict, **kwargs) -> str:
    payload = {
        "steps": args["steps"],
        "continue_on_error": bool(args.get("continue_on_error", False)),
    }
    return _json(_client().run_workflow(payload))
