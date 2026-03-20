from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path

import typer
import uvicorn

from .config import APP_NAME, get_config
from .daemon.server import create_app
from .mac.backend import MacComputerBackend

app = typer.Typer(add_completion=False, help="Hermes Computer: local macOS daemon and Hermes plugin installer.")


@app.command("doctor")
def doctor(prompt: bool = typer.Option(False, help="Prompt for macOS Accessibility approval if needed.")) -> None:
    config = get_config()
    backend = MacComputerBackend(config)
    status = backend.permission_status(prompt=prompt)
    payload = {
        "platform": sys.platform,
        "supported": backend.supported(),
        "accessibility_trusted": status.accessibility_trusted,
        "screen_capture_available": status.screen_capture_available,
        "detail": status.detail,
        "daemon_url": config.base_url,
    }
    typer.echo(json.dumps(payload, indent=2))


@app.command("daemon")
def daemon(host: str = typer.Option(None), port: int = typer.Option(None)) -> None:
    config = get_config()
    uvicorn.run(create_app(), host=host or config.host, port=port or config.port, log_level="info")


@app.command("start-daemon")
def start_daemon(background: bool = typer.Option(True, help="Run the daemon in the background.")) -> None:
    config = get_config()
    if _is_running(config.pid_file):
        typer.echo(f"already running pid={config.pid_file.read_text().strip()}")
        raise typer.Exit(0)
    if not background:
        daemon()
        raise typer.Exit(0)
    log_path = config.log_dir / "daemon.log"
    cmd = [sys.executable, "-m", "hermes_computer.cli", "daemon"]
    with log_path.open("a", encoding="utf-8") as log_file:
        proc = subprocess.Popen(cmd, stdout=log_file, stderr=log_file, start_new_session=True)
    config.pid_file.write_text(str(proc.pid))
    typer.echo(json.dumps({"ok": True, "pid": proc.pid, "log": str(log_path)}))


@app.command("stop-daemon")
def stop_daemon() -> None:
    config = get_config()
    if not config.pid_file.exists():
        typer.echo(json.dumps({"ok": True, "detail": "not running"}))
        raise typer.Exit(0)
    pid = int(config.pid_file.read_text().strip())
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    config.pid_file.unlink(missing_ok=True)
    typer.echo(json.dumps({"ok": True, "pid": pid}))


@app.command("status")
def status() -> None:
    config = get_config()
    backend = MacComputerBackend(config)
    payload = {
        "daemon_running": _is_running(config.pid_file),
        "pid": config.pid_file.read_text().strip() if config.pid_file.exists() else None,
        "permissions": backend.permission_status(prompt=False).model_dump(),
        "plugin_target": str(config.plugin_target),
        "skill_target": str(config.skill_target),
    }
    typer.echo(json.dumps(payload, indent=2))


@app.command("install-plugin")
def install_plugin(hermes_home: str = typer.Option(None, help="Override Hermes home, defaults to ~/.hermes")) -> None:
    if hermes_home:
        os.environ["HERMES_HOME"] = hermes_home
    config = get_config()
    _install_plugin_tree(config)
    _install_skill_tree(config)
    typer.echo(json.dumps({
        "ok": True,
        "plugin": str(config.plugin_target),
        "skill": str(config.skill_target),
    }, indent=2))


@app.command("bootstrap")
def bootstrap(
    hermes_home: str = typer.Option(None, help="Override Hermes home, defaults to ~/.hermes"),
    start: bool = typer.Option(True, help="Start the daemon after installing the plugin."),
    prompt_permissions: bool = typer.Option(True, help="Prompt for Accessibility permissions during doctor."),
    prefer_app: bool = typer.Option(False, help="If available, open the installed macOS app instead of only starting the CLI daemon."),
) -> None:
    if hermes_home:
        os.environ["HERMES_HOME"] = hermes_home
    install_plugin(hermes_home=hermes_home)
    doctor(prompt=prompt_permissions)
    if prefer_app:
        app_path = _installed_app_path()
        if app_path.exists():
            subprocess.run(["open", str(app_path)], check=False)
            raise typer.Exit(0)
    if start:
        start_daemon(background=True)


@app.command("open-privacy-settings")
def open_privacy_settings() -> None:
    subprocess.run(["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"], check=False)
    subprocess.run(["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture"], check=False)
    typer.echo("opened")


@app.command("build-app")
def build_app(clean: bool = typer.Option(True, help="Remove previous build/dist directories before packaging.")) -> None:
    repo_root = _repo_root()
    if clean:
        shutil.rmtree(repo_root / "build", ignore_errors=True)
        shutil.rmtree(repo_root / "dist", ignore_errors=True)
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name",
        "Hermes Computer",
        "--windowed",
        "--noconfirm",
        "--add-data",
        "plugin.yaml:.",
        "--add-data",
        "hermes_computer:hermes_computer",
        "--add-data",
        "skill:skill",
        "--hidden-import",
        "AppKit",
        "--hidden-import",
        "Foundation",
        "--hidden-import",
        "Quartz",
        "--hidden-import",
        "ApplicationServices",
        "scripts/hermes_computer_app.py",
    ]
    subprocess.run(cmd, cwd=repo_root, check=True)
    app_path = _built_app_path()
    typer.echo(json.dumps({"ok": app_path.exists(), "app": str(app_path)}, indent=2))


@app.command("install-app")
def install_app(build_if_missing: bool = typer.Option(True, help="Build the app first if no local dist app exists.")) -> None:
    app_path = _built_app_path()
    if not app_path.exists():
        if not build_if_missing:
            raise typer.BadParameter("No built app found. Run `hermes-computer build-app` first.")
        build_app(clean=True)
        app_path = _built_app_path()
    target = _installed_app_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(app_path, target)
    typer.echo(json.dumps({"ok": True, "installed_app": str(target)}, indent=2))


@app.command("open-app")
def open_app(installed: bool = typer.Option(True, help="Open the installed app from ~/Applications if present.")) -> None:
    target = _installed_app_path() if installed else _built_app_path()
    if not target.exists():
        raise typer.BadParameter(f"App not found at {target}.")
    subprocess.run(["open", str(target)], check=False)
    typer.echo(str(target))


def _repo_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS")).resolve()
    return Path(__file__).resolve().parents[1]


def _built_app_path() -> Path:
    return _repo_root() / "dist" / "Hermes Computer.app"


def _installed_app_path() -> Path:
    return Path.home() / "Applications" / "Hermes Computer.app"


def _install_plugin_tree(config) -> None:
    target = config.plugin_target
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    repo_root = _repo_root()
    shutil.copy2(repo_root / "plugin.yaml", target / "plugin.yaml")
    shutil.copytree(repo_root / "hermes_computer", target / "hermes_computer")
    (target / "__init__.py").write_text("from .hermes_computer.plugin import register\n", encoding="utf-8")


def _install_skill_tree(config) -> None:
    source = _repo_root() / "skill" / "hermes-computer"
    target = config.skill_target
    if target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)


def _is_running(pid_file: Path) -> bool:
    if not pid_file.exists():
        return False
    try:
        pid = int(pid_file.read_text().strip())
        os.kill(pid, 0)
        return True
    except Exception:
        pid_file.unlink(missing_ok=True)
        return False


def main() -> None:
    app()


if __name__ == "__main__":
    main()
