from __future__ import annotations

import json
import os
import threading
import webbrowser
from pathlib import Path

import objc
import requests
import uvicorn
from AppKit import (
    NSApp,
    NSApplication,
    NSApplicationActivationPolicyRegular,
    NSBackingStoreBuffered,
    NSButton,
    NSButtonTypeMomentaryPushIn,
    NSInformationalRequest,
    NSMakeRect,
    NSTextField,
    NSWindow,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskMiniaturizable,
    NSWindowStyleMaskResizable,
    NSWindowStyleMaskTitled,
)
from Foundation import NSObject, NSTimer
from PyObjCTools import AppHelper

from .cli import _install_plugin_tree, _install_skill_tree
from .config import get_config
from .daemon.server import create_app
from .mac.backend import MacComputerBackend


class DaemonController:
    def __init__(self):
        self.config = get_config()
        self.server = None
        self.thread = None
        self.external = False

    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            return
        try:
            response = requests.get(f"{self.config.base_url}/health", timeout=1.0)
            if response.ok:
                self.external = True
                return
        except Exception:
            pass
        config = uvicorn.Config(create_app(), host=self.config.host, port=self.config.port, log_level="warning")
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(target=self.server.run, daemon=True)
        self.thread.start()
        self.config.pid_file.write_text(str(os.getpid()))

    def stop(self) -> None:
        if self.external:
            return
        if self.server is not None:
            self.server.should_exit = True
        self.config.pid_file.unlink(missing_ok=True)


class HermesComputerApp(NSObject):
    def applicationDidFinishLaunching_(self, notification) -> None:
        self.config = get_config()
        self.backend = MacComputerBackend(self.config)
        self.daemon = DaemonController()
        self.daemon.start()
        _install_plugin_tree(self.config)
        _install_skill_tree(self.config)
        self._build_window()
        self.refresh_(None)
        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(2.0, self, "refresh:", None, True)

    def applicationWillTerminate_(self, notification) -> None:
        if hasattr(self, "timer") and self.timer:
            self.timer.invalidate()
        self.daemon.stop()

    @objc.python_method
    def _build_window(self) -> None:
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(240.0, 240.0, 700.0, 420.0),
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskMiniaturizable | NSWindowStyleMaskResizable,
            NSBackingStoreBuffered,
            False,
        )
        self.window.setTitle_("Hermes Computer")
        content = self.window.contentView()

        self.title_label = self._label(24, 360, 652, 28, "Hermes Computer")
        self.subtitle_label = self._label(24, 334, 652, 20, "App-backed macOS desktop control for Hermes")
        self.status_label = self._label(24, 260, 652, 64, "Loading status...")
        self.paths_label = self._label(24, 156, 652, 84, "")

        buttons = [
            ("Refresh", "refresh:", 24),
            ("Open Privacy Settings", "openPrivacy:", 150),
            ("Install Into Hermes", "installIntoHermes:", 346),
            ("Open Docs", "openDocs:", 520),
        ]
        for title, selector, x in buttons:
            content.addSubview_(self._button(x, 98, 150, 34, title, selector))

        self.window.contentView().addSubview_(self.title_label)
        self.window.contentView().addSubview_(self.subtitle_label)
        self.window.contentView().addSubview_(self.status_label)
        self.window.contentView().addSubview_(self.paths_label)
        self.window.center()
        self.window.makeKeyAndOrderFront_(None)
        NSApp.activateIgnoringOtherApps_(True)

    @objc.python_method
    def _label(self, x: float, y: float, width: float, height: float, value: str) -> NSTextField:
        field = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, width, height))
        field.setStringValue_(value)
        field.setBezeled_(False)
        field.setDrawsBackground_(False)
        field.setEditable_(False)
        field.setSelectable_(True)
        return field

    @objc.python_method
    def _button(self, x: float, y: float, width: float, height: float, title: str, selector: str) -> NSButton:
        button = NSButton.alloc().initWithFrame_(NSMakeRect(x, y, width, height))
        button.setTitle_(title)
        button.setBezelStyle_(1)
        button.setButtonType_(NSButtonTypeMomentaryPushIn)
        button.setTarget_(self)
        button.setAction_(selector)
        return button

    def refresh_(self, sender) -> None:
        perms = self.backend.permission_status(prompt=False)
        lines = [
            f"Daemon: running on {self.config.base_url}",
            f"Accessibility: {'granted' if perms.accessibility_trusted else 'missing'}",
            f"Screen Recording: {'granted' if perms.screen_capture_available else 'missing'}",
            f"Frontmost app: {self.backend._frontmost_application_name() or 'unknown'}",
        ]
        if perms.detail:
            lines.append("")
            lines.append(perms.detail)
        self.status_label.setStringValue_("\n".join(lines))
        self.paths_label.setStringValue_(
            "\n".join(
                [
                    f"Plugin: {self.config.plugin_target}",
                    f"Skill: {self.config.skill_target}",
                    f"Captures: {self.config.capture_dir}",
                ]
            )
        )

    def openPrivacy_(self, sender) -> None:
        import subprocess
        subprocess.run(["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"], check=False)
        subprocess.run(["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture"], check=False)

    def installIntoHermes_(self, sender) -> None:
        _install_plugin_tree(self.config)
        _install_skill_tree(self.config)
        self.refresh_(None)

    def openDocs_(self, sender) -> None:
        webbrowser.open((Path(__file__).resolve().parents[1] / "README.md").as_uri())


def main() -> None:
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyRegular)
    delegate = HermesComputerApp.alloc().init()
    app.setDelegate_(delegate)
    AppHelper.runEventLoop()


if __name__ == "__main__":
    main()
