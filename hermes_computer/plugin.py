from __future__ import annotations

from .tools import (
    TOOLSET,
    capture_screen,
    check_computer_available,
    click_at,
    click_element,
    computer_status,
    focus_window,
    list_windows,
    open_application,
    press_keys,
    run_workflow,
    snapshot_ui,
    type_text,
)


def register(ctx) -> None:
    ctx.register_tool(
        name="computer_run_workflow",
        toolset=TOOLSET,
        schema={
            "name": "computer_run_workflow",
            "description": "Run a short sequence of desktop actions in one call. Prefer this for direct, deterministic tasks like opening an app, clicking a field, typing text, and pressing a shortcut.",
            "parameters": {
                "type": "object",
                "properties": {
                    "steps": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "action": {
                                    "type": "string",
                                    "enum": [
                                        "focus_window",
                                        "open_application",
                                        "capture_screen",
                                        "snapshot_ui",
                                        "click_element",
                                        "click_at",
                                        "type_text",
                                        "press_keys",
                                    ],
                                },
                                "params": {"type": "object"},
                                "pause_ms": {"type": "integer", "minimum": 0, "maximum": 5000, "default": 0},
                            },
                            "required": ["action"],
                            "additionalProperties": False,
                        },
                        "minItems": 1,
                    },
                    "continue_on_error": {"type": "boolean", "default": False},
                },
                "required": ["steps"],
                "additionalProperties": False,
            },
        },
        handler=run_workflow,
        check_fn=check_computer_available,
        is_async=False,
        description="Run a batched desktop workflow.",
        emoji="⚡",
    )
    ctx.register_tool(
        name="computer_status",
        toolset=TOOLSET,
        schema={
            "name": "computer_status",
            "description": "Inspect the local hermes-computer daemon status, platform support, and permission state.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        handler=computer_status,
        check_fn=check_computer_available,
        is_async=False,
        description="Inspect computer-control daemon status.",
        emoji="🖥️",
    )
    ctx.register_tool(
        name="computer_list_windows",
        toolset=TOOLSET,
        schema={
            "name": "computer_list_windows",
            "description": "List visible desktop windows so Hermes can target the correct app or window before acting.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        handler=list_windows,
        check_fn=check_computer_available,
        is_async=False,
        description="List visible desktop windows.",
        emoji="🪟",
    )
    ctx.register_tool(
        name="computer_focus_window",
        toolset=TOOLSET,
        schema={
            "name": "computer_focus_window",
            "description": "Focus a window or application by owner name, title match, or exact window id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "window_id": {"type": "integer"},
                    "owner_name": {"type": "string"},
                    "title_contains": {"type": "string"},
                },
                "additionalProperties": False,
            },
        },
        handler=focus_window,
        check_fn=check_computer_available,
        is_async=False,
        description="Focus a visible window.",
        emoji="🎯",
    )
    ctx.register_tool(
        name="computer_open_application",
        toolset=TOOLSET,
        schema={
            "name": "computer_open_application",
            "description": "Open or activate an installed macOS application by name.",
            "parameters": {
                "type": "object",
                "properties": {"app_name": {"type": "string", "description": "Application name, e.g. Safari or TextEdit."}},
                "required": ["app_name"],
                "additionalProperties": False,
            },
        },
        handler=open_application,
        check_fn=check_computer_available,
        is_async=False,
        description="Open or activate an app.",
        emoji="🚀",
    )
    ctx.register_tool(
        name="computer_capture_screen",
        toolset=TOOLSET,
        schema={
            "name": "computer_capture_screen",
            "description": "Capture the current screen and return the saved image path for inspection or later use.",
            "parameters": {
                "type": "object",
                "properties": {
                    "display": {"type": "integer", "default": 1},
                    "format": {"type": "string", "enum": ["png", "jpg"], "default": "png"},
                },
                "additionalProperties": False,
            },
        },
        handler=capture_screen,
        check_fn=check_computer_available,
        is_async=False,
        description="Capture the active screen.",
        emoji="📸",
    )
    ctx.register_tool(
        name="computer_snapshot_ui",
        toolset=TOOLSET,
        schema={
            "name": "computer_snapshot_ui",
            "description": "Read the frontmost application's accessibility tree so Hermes can identify actionable buttons, fields, toggles, and labels without guessing by pixels.",
            "parameters": {
                "type": "object",
                "properties": {
                    "depth": {"type": "integer", "minimum": 1, "maximum": 6, "default": 3},
                    "max_nodes": {"type": "integer", "minimum": 20, "maximum": 500, "default": 160},
                },
                "additionalProperties": False,
            },
        },
        handler=snapshot_ui,
        check_fn=check_computer_available,
        is_async=False,
        description="Snapshot the frontmost accessibility tree.",
        emoji="🧭",
    )
    ctx.register_tool(
        name="computer_click_element",
        toolset=TOOLSET,
        schema={
            "name": "computer_click_element",
            "description": "Click an accessibility element in the frontmost window by matching its text, role, or both.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text/title/description to match."},
                    "role": {"type": "string", "description": "Optional role filter like AXButton or AXTextField."},
                    "index": {"type": "integer", "minimum": 0, "default": 0},
                    "exact": {"type": "boolean", "default": False},
                },
                "additionalProperties": False,
            },
        },
        handler=click_element,
        check_fn=check_computer_available,
        is_async=False,
        description="Click a matched UI element.",
        emoji="🖱️",
    )
    ctx.register_tool(
        name="computer_click_at",
        toolset=TOOLSET,
        schema={
            "name": "computer_click_at",
            "description": "Click absolute screen coordinates. Use this only when accessibility targeting is insufficient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "number"},
                    "y": {"type": "number"},
                    "button": {"type": "string", "enum": ["left", "right"], "default": "left"},
                    "click_count": {"type": "integer", "minimum": 1, "maximum": 3, "default": 1},
                },
                "required": ["x", "y"],
                "additionalProperties": False,
            },
        },
        handler=click_at,
        check_fn=check_computer_available,
        is_async=False,
        description="Click screen coordinates.",
        emoji="📍",
    )
    ctx.register_tool(
        name="computer_type_text",
        toolset=TOOLSET,
        schema={
            "name": "computer_type_text",
            "description": "Type literal text into the currently focused field or app.",
            "parameters": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
                "additionalProperties": False,
            },
        },
        handler=type_text,
        check_fn=check_computer_available,
        is_async=False,
        description="Type text into the focused UI.",
        emoji="⌨️",
    )
    ctx.register_tool(
        name="computer_press_keys",
        toolset=TOOLSET,
        schema={
            "name": "computer_press_keys",
            "description": "Press a key chord like [\"command\", \"l\"] or a special key like [\"enter\"].",
            "parameters": {
                "type": "object",
                "properties": {
                    "keys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                    }
                },
                "required": ["keys"],
                "additionalProperties": False,
            },
        },
        handler=press_keys,
        check_fn=check_computer_available,
        is_async=False,
        description="Press a key or key chord.",
        emoji="🎹",
    )
