from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 47855
DEFAULT_TIMEOUT_SECONDS = 20.0
APP_NAME = "hermes-computer"


def _expand(path: str) -> Path:
    return Path(path).expanduser().resolve()


@dataclass(frozen=True)
class ComputerConfig:
    host: str = os.environ.get("HERMES_COMPUTER_HOST", DEFAULT_HOST)
    port: int = int(os.environ.get("HERMES_COMPUTER_PORT", str(DEFAULT_PORT)))
    timeout_seconds: float = float(os.environ.get("HERMES_COMPUTER_TIMEOUT", str(DEFAULT_TIMEOUT_SECONDS)))
    home: Path = _expand(os.environ.get("HERMES_COMPUTER_HOME", "~/Library/Application Support/HermesComputer"))

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def log_dir(self) -> Path:
        return self.home / "logs"

    @property
    def run_dir(self) -> Path:
        return self.home / "run"

    @property
    def capture_dir(self) -> Path:
        return self.home / "captures"

    @property
    def pid_file(self) -> Path:
        return self.run_dir / "daemon.pid"

    @property
    def skill_target(self) -> Path:
        hermes_home = _expand(os.environ.get("HERMES_HOME", "~/.hermes"))
        return hermes_home / "skills" / "productivity" / "hermes-computer"

    @property
    def plugin_target(self) -> Path:
        hermes_home = _expand(os.environ.get("HERMES_HOME", "~/.hermes"))
        return hermes_home / "plugins" / "hermes-computer"

    def ensure_dirs(self) -> None:
        for path in (self.home, self.log_dir, self.run_dir, self.capture_dir):
            path.mkdir(parents=True, exist_ok=True)


def get_config() -> ComputerConfig:
    config = ComputerConfig()
    config.ensure_dirs()
    return config
