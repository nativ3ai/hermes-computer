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

_APP_DELEGATE = None


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
    @objc.python_method
    def start(self) -> None:
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
            NSMakeRect(240.0, 240.0, 760.0, 450.0),
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskMiniaturizable | NSWindowStyleMaskResizable,
            NSBackingStoreBuffered,
            False,
        )
        self.window.setTitle_("Hermes Computer")
        content = self.window.contentView()

        self.title_label = self._label(24, 388, 700, 28, "Hermes Computer")
        self.subtitle_label = self._label(24, 362, 700, 20, "App-backed macOS desktop control for Hermes")
        self.status_label = self._label(24, 270, 700, 88, "Loading status...")
        self.install_status_label = self._label(24, 236, 700, 22, "Hermes install: checking...")
        self.action_status_label = self._label(24, 210, 700, 18, "")
        self.paths_label = self._label(24, 112, 700, 86, "")

        self.refresh_button = self._button(24, 58, 120, 34, "Refresh", "refresh:")
        self.accessibility_button = self._button(160, 58, 170, 34, "Open Accessibility", "openAccessibility:")
        self.screen_recording_button = self._button(346, 58, 190, 34, "Open Screen Recording", "openScreenRecording:")
        self.install_button = self._button(552, 58, 150, 34, "Install Into Hermes", "installIntoHermes:")
        self.docs_button = self._button(24, 20, 120, 28, "Open Docs", "openDocs:")

        for button in (
            self.refresh_button,
            self.accessibility_button,
            self.screen_recording_button,
            self.install_button,
            self.docs_button,
        ):
            content.addSubview_(button)

        self.window.contentView().addSubview_(self.title_label)
        self.window.contentView().addSubview_(self.subtitle_label)
        self.window.contentView().addSubview_(self.status_label)
        self.window.contentView().addSubview_(self.install_status_label)
        self.window.contentView().addSubview_(self.action_status_label)
        self.window.contentView().addSubview_(self.paths_label)
        self.window.center()
        self.window.setReleasedWhenClosed_(False)
        self.window.makeKeyAndOrderFront_(None)
        self.window.orderFrontRegardless()
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
        install_state = self._install_state()
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
        self.install_status_label.setStringValue_(f"Hermes install: {install_state['label']}")
        self.install_button.setTitle_("Reinstall Into Hermes" if install_state["installed"] else "Install Into Hermes")
        self.paths_label.setStringValue_(
            "\n".join(
                [
                    f"Plugin: {self.config.plugin_target}",
                    f"Skill: {self.config.skill_target}",
                    f"Captures: {self.config.capture_dir}",
                ]
            )
        )

    @objc.python_method
    def _install_state(self) -> dict[str, object]:
        plugin_ok = (self.config.plugin_target / "plugin.yaml").exists()
        skill_ok = (self.config.skill_target / "SKILL.md").exists()
        installed = plugin_ok and skill_ok
        if installed:
            label = "installed in ~/.hermes"
        else:
            missing = []
            if not plugin_ok:
                missing.append("plugin")
            if not skill_ok:
                missing.append("skill")
            label = "missing " + " + ".join(missing)
        return {"installed": installed, "label": label}

    def openAccessibility_(self, sender) -> None:
        import subprocess
        subprocess.run(["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"], check=False)

    def openScreenRecording_(self, sender) -> None:
        import subprocess
        subprocess.run(["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture"], check=False)

    def installIntoHermes_(self, sender) -> None:
        self.action_status_label.setStringValue_("Installing plugin and skill into ~/.hermes ...")
        self.install_button.setEnabled_(False)
        _install_plugin_tree(self.config)
        _install_skill_tree(self.config)
        self.action_status_label.setStringValue_("Install complete.")
        self.install_button.setEnabled_(True)
        self.refresh_(None)

    def openDocs_(self, sender) -> None:
        webbrowser.open("https://github.com/nativ3ai/hermes-computer")


def main() -> None:
    global _APP_DELEGATE
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyRegular)
    delegate = HermesComputerApp.alloc().init()
    _APP_DELEGATE = delegate
    app.setDelegate_(delegate)
    AppHelper.callAfter(delegate.start)
    AppHelper.runEventLoop()


if __name__ == "__main__":
    main()
