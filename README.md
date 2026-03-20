# Hermes Computer

Hermes Computer is a standalone macOS-first add-on for Hermes Agent. It combines:

- a native macOS app wrapper that owns permissions and runs the local daemon
- a Hermes plugin that exposes computer-use tools
- a bundled skill that teaches Hermes how to operate the desktop safely

The target is simple: let a user ask Hermes to operate the local computer in natural language, with deterministic UI targeting where possible instead of raw pixel guessing.

## Scope

Current scope is macOS-first.

What it supports today:

- list visible windows
- focus a window or activate an app
- capture the screen
- snapshot the frontmost accessibility tree
- click accessibility elements by text or role
- click absolute coordinates as a fallback
- type text
- press key chords

This is the right foundation for high-quality desktop control. A pure `SKILL.md` would not be enough; the daemon owns OS permissions, state, and event injection.

## Architecture

```text
Hermes -> plugin tools -> localhost daemon -> macOS Accessibility + Quartz + screencapture
```

The plugin/daemon split keeps the implementation testable and keeps macOS-specific logic out of Hermes core.

## Install

```bash
cd hermes-computer
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pip install '.[app]'
hermes-computer install-plugin
hermes-computer build-app
hermes-computer install-app
hermes-computer open-app
```

The app is now the preferred runtime. It owns the permission prompts and runs the local daemon inside the app process.

If you want the old developer-only path, you can still run:

```bash
hermes-computer start-daemon
```

### Quick bootstrap

```bash
hermes-computer bootstrap --prefer-app
```

That installs the plugin + skill, runs diagnostics, and opens the installed app if present.

If you do not have the app built yet, run:

```bash
pip install '.[app]'
hermes-computer build-app
hermes-computer install-app
```

## Required macOS permissions

Hermes Computer needs:

- Accessibility
- Screen Recording

Open them with:

```bash
hermes-computer open-privacy-settings
```

Then verify:

```bash
hermes-computer doctor
hermes-computer status
```

## Usage from Hermes

Once installed, Hermes can use the plugin tools directly through natural language.

Examples:

- `Open Safari and focus the GitHub window.`
- `Snapshot the frontmost UI tree and tell me which buttons are visible.`
- `Open TextEdit, click the body, and type the summary from the last message.`
- `Capture the current screen and give me the saved path.`

## Operator model

Hermes Computer prefers deterministic control:

1. inspect windows
2. focus the target app
3. snapshot the accessibility tree
4. click by element match
5. fall back to coordinates only when necessary

That is the same operational philosophy you want for reliable desktop agents.

## Commands

```bash
hermes-computer doctor
hermes-computer bootstrap
hermes-computer build-app
hermes-computer install-app
hermes-computer open-app
hermes-computer start-daemon
hermes-computer stop-daemon
hermes-computer status
hermes-computer open-privacy-settings
```

## Testing

Unit tests cover:

- daemon routes
- plugin installation flow
- tool registration shape

A live smoke test on macOS should additionally confirm:

1. `computer_list_windows`
2. `computer_capture_screen`
3. `computer_open_application` on TextEdit or Safari
4. `computer_snapshot_ui` once Accessibility is granted

## Limitations

- macOS only
- quality depends on Accessibility access being granted
- OCR fallback is not implemented yet; the first pass is accessibility-first
- complex drag-and-drop and multi-monitor workflows are not fully tuned yet

## Repo contents

- `hermes_computer/daemon/` — local FastAPI daemon
- `hermes_computer/macapp.py` — native macOS app wrapper
- `hermes_computer/mac/` — macOS backend
- `hermes_computer/plugin.py` — Hermes plugin registration
- `skill/hermes-computer/` — bundled skill
- `tests/` — unit tests
