from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class PermissionStatus(BaseModel):
    accessibility_trusted: bool = False
    screen_capture_available: bool = False
    platform_supported: bool = False
    detail: str | None = None


class ComputerStatus(BaseModel):
    ok: bool
    platform: str
    daemon_version: str
    permissions: PermissionStatus
    frontmost_app: str | None = None


class WindowInfo(BaseModel):
    window_id: int
    owner_pid: int
    owner_name: str
    title: str = ""
    bounds: dict[str, float]
    layer: int = 0
    is_onscreen: bool = True
    is_focused: bool = False


class UIElement(BaseModel):
    role: str
    subrole: str | None = None
    title: str | None = None
    description: str | None = None
    value: str | None = None
    identifier: str | None = None
    enabled: bool | None = None
    position: dict[str, float] | None = None
    size: dict[str, float] | None = None
    actions: list[str] = Field(default_factory=list)
    children: list["UIElement"] = Field(default_factory=list)


class UISnapshot(BaseModel):
    app_name: str
    pid: int
    window_title: str | None = None
    root: UIElement
    node_count: int
    truncated: bool = False


class FocusWindowRequest(BaseModel):
    window_id: int | None = None
    owner_name: str | None = None
    title_contains: str | None = None


class OpenApplicationRequest(BaseModel):
    app_name: str


class ClickAtRequest(BaseModel):
    x: float
    y: float
    button: Literal["left", "right"] = "left"
    click_count: int = 1


class ClickElementRequest(BaseModel):
    text: str | None = None
    role: str | None = None
    index: int = 0
    exact: bool = False


class TypeTextRequest(BaseModel):
    text: str


class PressKeysRequest(BaseModel):
    keys: list[str]


class CaptureScreenRequest(BaseModel):
    format: Literal["png", "jpg"] = "png"
    display: int = 1


class OperationResult(BaseModel):
    ok: bool
    detail: str
    data: dict[str, Any] = Field(default_factory=dict)


UIElement.model_rebuild()
