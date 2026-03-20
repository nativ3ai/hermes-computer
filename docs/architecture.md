# Architecture

Hermes Computer is deliberately split into three layers.

## 1. Daemon

The daemon is the macOS boundary.

It owns:

- Accessibility checks
- screen capture
- window discovery
- UI tree inspection
- click / key / text injection

This is the correct place for OS permissions and direct system APIs.

## 2. Plugin

The Hermes plugin exposes tools with schemas that the model can reason over.

That means Hermes sees actions like:

- `computer_list_windows`
- `computer_snapshot_ui`
- `computer_click_element`
- `computer_type_text`

instead of being forced to improvise shell commands.

## 3. Skill

The bundled skill teaches Hermes the operating style:

- inspect first
- focus the app
- snapshot the UI tree
- click by accessibility element
- type only after focus is correct
- use coordinates as fallback, not default

## Why this split matters

A plugin without a daemon is too thin.
A daemon without a skill is too awkward.
A skill without real tools is too brittle.

The full stack is what makes natural-language computer use realistic.
