from __future__ import annotations

import json
import platform
import sys
import time
from pathlib import Path
from typing import Any

from ..config import ComputerConfig
from ..models import ComputerStatus, PermissionStatus, UIElement, UISnapshot, WindowInfo

try:
    from Cocoa import NSWorkspace
    from AppKit import NSRunningApplication, NSApplicationActivateIgnoringOtherApps
    from AppKit import NSBitmapImageRep, NSJPEGFileType, NSPNGFileType
    from Quartz import (
        CGEventCreateMouseEvent,
        CGEventCreateKeyboardEvent,
        CGEventKeyboardSetUnicodeString,
        CGEventPost,
        CGEventSetFlags,
        CGDisplayCreateImage,
        CGMainDisplayID,
        CGWindowListCopyWindowInfo,
        CGPointMake,
        kCGEventFlagMaskAlternate,
        kCGEventFlagMaskCommand,
        kCGEventFlagMaskControl,
        kCGEventFlagMaskShift,
        kCGEventLeftMouseDown,
        kCGEventLeftMouseUp,
        kCGEventMouseMoved,
        kCGEventRightMouseDown,
        kCGEventRightMouseUp,
        kCGHIDEventTap,
        kCGWindowListOptionOnScreenOnly,
        kCGNullWindowID,
    )
    from ApplicationServices import (
        AXIsProcessTrustedWithOptions,
        AXUIElementCopyActionNames,
        AXUIElementCopyAttributeValue,
        AXUIElementCreateApplication,
        AXUIElementPerformAction,
        AXValueGetType,
        AXValueGetValue,
        kAXChildrenAttribute,
        kAXDescriptionAttribute,
        kAXEnabledAttribute,
        kAXFocusedWindowAttribute,
        kAXIdentifierAttribute,
        kAXPositionAttribute,
        kAXPressAction,
        kAXRoleAttribute,
        kAXSizeAttribute,
        kAXSubroleAttribute,
        kAXTitleAttribute,
        kAXValueAttribute,
        kAXValueCGPointType,
        kAXValueCGSizeType,
        kAXWindowsAttribute,
        kAXTrustedCheckOptionPrompt,
    )
    import Quartz
except Exception:  # pragma: no cover - handled by doctor/status
    NSWorkspace = None
    Quartz = None

KEY_CODE_MAP = {
    "a": 0,
    "s": 1,
    "d": 2,
    "f": 3,
    "h": 4,
    "g": 5,
    "z": 6,
    "x": 7,
    "c": 8,
    "v": 9,
    "b": 11,
    "q": 12,
    "w": 13,
    "e": 14,
    "r": 15,
    "y": 16,
    "t": 17,
    "1": 18,
    "2": 19,
    "3": 20,
    "4": 21,
    "6": 22,
    "5": 23,
    "=": 24,
    "9": 25,
    "7": 26,
    "-": 27,
    "8": 28,
    "0": 29,
    "]": 30,
    "o": 31,
    "u": 32,
    "[": 33,
    "i": 34,
    "p": 35,
    "l": 37,
    "j": 38,
    "'": 39,
    "k": 40,
    ";": 41,
    "\\": 42,
    ",": 43,
    "/": 44,
    "n": 45,
    "m": 46,
    ".": 47,
    "enter": 36,
    "return": 36,
    "tab": 48,
    "space": 49,
    "escape": 53,
    "esc": 53,
    "delete": 51,
    "backspace": 51,
    "up": 126,
    "down": 125,
    "left": 123,
    "right": 124,
}
MODIFIER_FLAGS = {
    "command": kCGEventFlagMaskCommand if Quartz else 0,
    "cmd": kCGEventFlagMaskCommand if Quartz else 0,
    "shift": kCGEventFlagMaskShift if Quartz else 0,
    "control": kCGEventFlagMaskControl if Quartz else 0,
    "ctrl": kCGEventFlagMaskControl if Quartz else 0,
    "option": kCGEventFlagMaskAlternate if Quartz else 0,
    "alt": kCGEventFlagMaskAlternate if Quartz else 0,
}


class DesktopControlError(RuntimeError):
    pass


class PermissionDeniedError(DesktopControlError):
    pass


class MacComputerBackend:
    def __init__(self, config: ComputerConfig):
        self.config = config

    @staticmethod
    def supported() -> bool:
        return platform.system() == "Darwin" and NSWorkspace is not None and Quartz is not None

    def permission_status(self, prompt: bool = False) -> PermissionStatus:
        if not self.supported():
            return PermissionStatus(platform_supported=False, detail="macOS with PyObjC is required")
        options = {kAXTrustedCheckOptionPrompt: bool(prompt)} if prompt else None
        trusted = bool(AXIsProcessTrustedWithOptions(options))
        screen_capture_available = self._probe_screen_capture()
        executable = Path(sys.executable).resolve()
        issues: list[str] = []
        if not trusted:
            issues.append(
                "Grant Accessibility access in System Settings > Privacy & Security > Accessibility for "
                f"{executable}."
            )
        if not screen_capture_available:
            issues.append(
                "Grant Screen Recording access in System Settings > Privacy & Security > Screen Recording for "
                f"{executable}."
            )
        detail = " ".join(issues) if issues else None
        return PermissionStatus(
            accessibility_trusted=trusted,
            screen_capture_available=screen_capture_available,
            platform_supported=True,
            detail=detail,
        )

    def status(self) -> ComputerStatus:
        permissions = self.permission_status(prompt=False)
        frontmost = self._frontmost_application_name()
        return ComputerStatus(
            ok=permissions.platform_supported,
            platform=platform.platform(),
            daemon_version="0.1.0",
            permissions=permissions,
            frontmost_app=frontmost,
        )

    def list_windows(self) -> list[WindowInfo]:
        self._require_supported()
        windows = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID) or []
        focused_name = self._frontmost_application_name()
        items: list[WindowInfo] = []
        for raw in windows:
            owner_name = str(raw.get("kCGWindowOwnerName", ""))
            bounds = raw.get("kCGWindowBounds", {}) or {}
            title = str(raw.get("kCGWindowName", "") or "")
            item = WindowInfo(
                window_id=int(raw.get("kCGWindowNumber", 0)),
                owner_pid=int(raw.get("kCGWindowOwnerPID", 0)),
                owner_name=owner_name,
                title=title,
                bounds={
                    "x": float(bounds.get("X", 0.0)),
                    "y": float(bounds.get("Y", 0.0)),
                    "width": float(bounds.get("Width", 0.0)),
                    "height": float(bounds.get("Height", 0.0)),
                },
                layer=int(raw.get("kCGWindowLayer", 0)),
                is_onscreen=bool(raw.get("kCGWindowIsOnscreen", True)),
                is_focused=owner_name == focused_name,
            )
            if item.bounds["width"] <= 0 or item.bounds["height"] <= 0:
                continue
            if item.layer != 0:
                continue
            items.append(item)
        return items

    def focus_window(self, *, window_id: int | None = None, owner_name: str | None = None, title_contains: str | None = None) -> dict[str, Any]:
        self._require_supported()
        windows = self.list_windows()
        target = None
        for win in windows:
            if window_id is not None and win.window_id == window_id:
                target = win
                break
            if owner_name and win.owner_name.lower() != owner_name.lower():
                continue
            if title_contains and title_contains.lower() not in win.title.lower():
                continue
            if owner_name or title_contains:
                target = win
                break
        if target is None:
            raise DesktopControlError("No matching window found")
        self._activate_pid(target.owner_pid)
        return {"window_id": target.window_id, "owner_name": target.owner_name, "title": target.title}

    def open_application(self, app_name: str) -> dict[str, Any]:
        self._require_supported()
        ok = NSWorkspace.sharedWorkspace().launchApplication_(app_name)
        if not ok:
            raise DesktopControlError(f"Unable to activate application: {app_name}")
        activated = self._activate_named_application(app_name)
        if not activated:
            raise DesktopControlError(f"Launched {app_name} but could not activate it")
        time.sleep(0.15)
        return {"app_name": app_name}

    def capture_screen(self, *, display: int = 1, fmt: str = "png") -> dict[str, Any]:
        self._require_supported()
        path = self.config.capture_dir / f"capture-{int(time.time() * 1000)}.{fmt}"
        image = CGDisplayCreateImage(CGMainDisplayID())
        if image is None:
            raise DesktopControlError("CGDisplayCreateImage failed")
        bitmap = NSBitmapImageRep.alloc().initWithCGImage_(image)
        file_type = NSPNGFileType if fmt == "png" else NSJPEGFileType
        data = bitmap.representationUsingType_properties_(file_type, None)
        if data is None:
            raise DesktopControlError("Unable to encode screenshot data")
        if not data.writeToFile_atomically_(str(path), True):
            raise DesktopControlError("Unable to write screenshot file")
        return {"path": str(path), "display": display, "format": fmt, "bytes": path.stat().st_size}

    def snapshot_ui(self, *, depth: int = 3, max_nodes: int = 160) -> UISnapshot:
        self._require_accessibility()
        app_name, pid = self._frontmost_application()
        app = AXUIElementCreateApplication(pid)
        err, focused_window = AXUIElementCopyAttributeValue(app, kAXFocusedWindowAttribute, None)
        if err != 0 or focused_window is None:
            err, windows = AXUIElementCopyAttributeValue(app, kAXWindowsAttribute, None)
            if err != 0 or not windows:
                raise DesktopControlError("Unable to access frontmost window through Accessibility")
            focused_window = windows[0]
        window_title = self._read_string_attr(focused_window, kAXTitleAttribute)
        counter = {"count": 0, "truncated": False}
        root = self._snapshot_element(focused_window, depth=depth, max_nodes=max_nodes, counter=counter)
        return UISnapshot(app_name=app_name, pid=pid, window_title=window_title, root=root, node_count=counter["count"], truncated=counter["truncated"])

    def click_element(self, *, text: str | None = None, role: str | None = None, index: int = 0, exact: bool = False) -> dict[str, Any]:
        self._require_accessibility()
        app_name, pid = self._frontmost_application()
        app = AXUIElementCreateApplication(pid)
        err, focused_window = AXUIElementCopyAttributeValue(app, kAXFocusedWindowAttribute, None)
        if err != 0 or focused_window is None:
            raise DesktopControlError("Unable to access the focused window")
        matches: list[tuple[Any, dict[str, Any]]] = []
        self._collect_matches(focused_window, matches, text=text, role=role, exact=exact)
        if not matches:
            raise DesktopControlError("No matching accessibility element found")
        if index >= len(matches):
            raise DesktopControlError(f"Requested index {index} but only found {len(matches)} matches")
        element, meta = matches[index]
        err = AXUIElementPerformAction(element, kAXPressAction)
        if err != 0:
            position = self._read_point_attr(element, kAXPositionAttribute)
            size = self._read_size_attr(element, kAXSizeAttribute)
            if position and size:
                self.click_at(position["x"] + size["width"] / 2.0, position["y"] + size["height"] / 2.0)
            else:
                raise DesktopControlError(f"Accessibility press failed with code {err}")
        return {"app_name": app_name, "match": meta, "match_index": index}

    def click_at(self, x: float, y: float, button: str = "left", click_count: int = 1) -> dict[str, Any]:
        self._require_accessibility()
        self._post_click(x, y, button=button, click_count=click_count)
        return {"x": x, "y": y, "button": button, "click_count": click_count}

    def type_text(self, text: str) -> dict[str, Any]:
        self._require_accessibility()
        for char in text:
            self._post_unicode_keypress(char)
            time.sleep(0.004)
        return {"text": text, "chars": len(text)}

    def press_keys(self, keys: list[str]) -> dict[str, Any]:
        self._require_accessibility()
        normalized = [k.lower() for k in keys]
        modifiers = [k for k in normalized if k in MODIFIER_FLAGS]
        mains = [k for k in normalized if k not in MODIFIER_FLAGS]
        if len(mains) != 1:
            raise DesktopControlError("press_keys expects exactly one non-modifier key")
        key = mains[0]
        self._post_keypress(key, modifiers)
        return {"keys": normalized}

    def _snapshot_element(self, element: Any, *, depth: int, max_nodes: int, counter: dict[str, Any]) -> UIElement:
        counter["count"] += 1
        if counter["count"] > max_nodes:
            counter["truncated"] = True
            return UIElement(role="AXTruncated")
        role = self._read_string_attr(element, kAXRoleAttribute) or "AXUnknown"
        subrole = self._read_string_attr(element, kAXSubroleAttribute)
        title = self._read_string_attr(element, kAXTitleAttribute)
        description = self._read_string_attr(element, kAXDescriptionAttribute)
        value = self._read_scalar_attr(element, kAXValueAttribute)
        identifier = self._read_string_attr(element, kAXIdentifierAttribute)
        enabled = self._read_bool_attr(element, kAXEnabledAttribute)
        position = self._read_point_attr(element, kAXPositionAttribute)
        size = self._read_size_attr(element, kAXSizeAttribute)
        actions = self._read_actions(element)
        children: list[UIElement] = []
        if depth > 0 and not counter["truncated"]:
            err, raw_children = AXUIElementCopyAttributeValue(element, kAXChildrenAttribute, None)
            if err == 0 and raw_children:
                for child in raw_children[:25]:
                    children.append(self._snapshot_element(child, depth=depth - 1, max_nodes=max_nodes, counter=counter))
                    if counter["truncated"]:
                        break
        return UIElement(
            role=role,
            subrole=subrole,
            title=title,
            description=description,
            value=value,
            identifier=identifier,
            enabled=enabled,
            position=position,
            size=size,
            actions=actions,
            children=children,
        )

    def _collect_matches(self, element: Any, matches: list[tuple[Any, dict[str, Any]]], *, text: str | None, role: str | None, exact: bool) -> None:
        meta = {
            "role": self._read_string_attr(element, kAXRoleAttribute),
            "title": self._read_string_attr(element, kAXTitleAttribute),
            "description": self._read_string_attr(element, kAXDescriptionAttribute),
            "value": self._read_scalar_attr(element, kAXValueAttribute),
        }
        if self._matches(meta, text=text, role=role, exact=exact):
            matches.append((element, meta))
        err, raw_children = AXUIElementCopyAttributeValue(element, kAXChildrenAttribute, None)
        if err == 0 and raw_children:
            for child in raw_children[:50]:
                self._collect_matches(child, matches, text=text, role=role, exact=exact)

    @staticmethod
    def _matches(meta: dict[str, Any], *, text: str | None, role: str | None, exact: bool) -> bool:
        if role:
            role_match = (meta.get("role") or "").lower()
            if role.lower() not in role_match:
                return False
        if not text:
            return True
        haystacks = [str(meta.get("title") or ""), str(meta.get("description") or ""), str(meta.get("value") or "")]
        needle = text.lower()
        if exact:
            return any(h.lower() == needle for h in haystacks if h)
        return any(needle in h.lower() for h in haystacks if h)

    @staticmethod
    def _read_actions(element: Any) -> list[str]:
        err, actions = AXUIElementCopyActionNames(element, None)
        if err != 0 or not actions:
            return []
        return [str(action) for action in actions]

    @staticmethod
    def _read_string_attr(element: Any, attr: str) -> str | None:
        err, value = AXUIElementCopyAttributeValue(element, attr, None)
        if err != 0 or value is None:
            return None
        return str(value)

    @staticmethod
    def _read_scalar_attr(element: Any, attr: str) -> str | None:
        err, value = AXUIElementCopyAttributeValue(element, attr, None)
        if err != 0 or value is None:
            return None
        if isinstance(value, str):
            return value
        if isinstance(value, (int, float, bool)):
            return str(value)
        return None

    @staticmethod
    def _read_bool_attr(element: Any, attr: str) -> bool | None:
        err, value = AXUIElementCopyAttributeValue(element, attr, None)
        if err != 0 or value is None:
            return None
        return bool(value)

    @staticmethod
    def _read_point_attr(element: Any, attr: str) -> dict[str, float] | None:
        err, value = AXUIElementCopyAttributeValue(element, attr, None)
        if err != 0 or value is None:
            return None
        if AXValueGetType(value) != kAXValueCGPointType:
            return None
        ok, point = AXValueGetValue(value, kAXValueCGPointType, None)
        if not ok:
            return None
        return {"x": float(point.x), "y": float(point.y)}

    @staticmethod
    def _read_size_attr(element: Any, attr: str) -> dict[str, float] | None:
        err, value = AXUIElementCopyAttributeValue(element, attr, None)
        if err != 0 or value is None:
            return None
        if AXValueGetType(value) != kAXValueCGSizeType:
            return None
        ok, size = AXValueGetValue(value, kAXValueCGSizeType, None)
        if not ok:
            return None
        return {"width": float(size.width), "height": float(size.height)}

    def _probe_screen_capture(self) -> bool:
        try:
            result = self.capture_screen(display=1, fmt="png")
            Path(result["path"]).unlink(missing_ok=True)
            return True
        except Exception:
            return False

    @staticmethod
    def _frontmost_application_name() -> str | None:
        if NSWorkspace is None:
            return None
        app = NSWorkspace.sharedWorkspace().frontmostApplication()
        return str(app.localizedName()) if app else None

    @staticmethod
    def _frontmost_application() -> tuple[str, int]:
        if NSWorkspace is None:
            raise DesktopControlError("NSWorkspace unavailable")
        app = NSWorkspace.sharedWorkspace().frontmostApplication()
        if app is None:
            raise DesktopControlError("Unable to determine the frontmost application")
        return str(app.localizedName()), int(app.processIdentifier())

    @staticmethod
    def _activate_pid(pid: int) -> bool:
        app = NSRunningApplication.runningApplicationWithProcessIdentifier_(pid)
        if app is None:
            return False
        return bool(app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps))

    @staticmethod
    def _activate_named_application(app_name: str) -> bool:
        running = NSWorkspace.sharedWorkspace().runningApplications() or []
        matches = [app for app in running if str(app.localizedName() or "") == app_name]
        if not matches:
            return False
        return bool(matches[0].activateWithOptions_(NSApplicationActivateIgnoringOtherApps))

    def _post_click(self, x: float, y: float, *, button: str, click_count: int) -> None:
        point = CGPointMake(float(x), float(y))
        CGEventPost(kCGHIDEventTap, CGEventCreateMouseEvent(None, kCGEventMouseMoved, point, 0))
        down = kCGEventRightMouseDown if button == "right" else kCGEventLeftMouseDown
        up = kCGEventRightMouseUp if button == "right" else kCGEventLeftMouseUp
        for _ in range(max(1, int(click_count))):
            CGEventPost(kCGHIDEventTap, CGEventCreateMouseEvent(None, down, point, 0))
            CGEventPost(kCGHIDEventTap, CGEventCreateMouseEvent(None, up, point, 0))
            time.sleep(0.04)

    def _post_keypress(self, key: str, modifiers: list[str]) -> None:
        if key not in KEY_CODE_MAP:
            raise DesktopControlError(f"Unsupported key: {key}")
        keycode = KEY_CODE_MAP[key]
        down = CGEventCreateKeyboardEvent(None, keycode, True)
        up = CGEventCreateKeyboardEvent(None, keycode, False)
        flags = 0
        for modifier in modifiers:
            flags |= MODIFIER_FLAGS[modifier]
        if flags:
            CGEventSetFlags(down, flags)
            CGEventSetFlags(up, flags)
        CGEventPost(kCGHIDEventTap, down)
        CGEventPost(kCGHIDEventTap, up)

    def _post_unicode_keypress(self, char: str) -> None:
        down = CGEventCreateKeyboardEvent(None, 0, True)
        up = CGEventCreateKeyboardEvent(None, 0, False)
        CGEventKeyboardSetUnicodeString(down, len(char), char)
        CGEventKeyboardSetUnicodeString(up, len(char), char)
        CGEventPost(kCGHIDEventTap, down)
        CGEventPost(kCGHIDEventTap, up)

    def _require_supported(self) -> None:
        if not self.supported():
            raise DesktopControlError("hermes-computer is macOS-only and requires PyObjC")

    def _require_accessibility(self) -> None:
        status = self.permission_status(prompt=False)
        if not status.accessibility_trusted:
            raise PermissionDeniedError(status.detail or "Accessibility permission is required")
