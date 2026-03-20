---
name: hermes-computer
description: Use the hermes-computer plugin to control a local macOS desktop through Hermes. Use it when the user wants Hermes to open apps, inspect windows, click UI elements, type text, press shortcuts, or capture the screen.
---

# Hermes Computer

Use this skill when Hermes needs to operate the local macOS desktop.

## Preconditions

Before using the tools, confirm the daemon and permissions are ready:

1. Call `computer_status`.
2. If the daemon is missing, tell the operator to run `hermes-computer bootstrap`.
3. If Accessibility or Screen Recording is missing, tell the operator to run `hermes-computer open-privacy-settings` and grant access.

## Workflow

Prefer deterministic control over blind clicking.

1. Start with `computer_list_windows` to see candidate apps and windows.
2. Use `computer_focus_window` or `computer_open_application` to bring the right app forward.
3. Use `computer_snapshot_ui` to inspect the accessibility tree of the focused window.
4. Prefer `computer_click_element` over `computer_click_at` whenever possible.
5. Use `computer_type_text` only after the correct field or app is focused.
6. Use `computer_press_keys` for shortcuts like `command+l`, `enter`, `escape`, and tab navigation.
7. Use `computer_capture_screen` when the operator needs a screenshot artifact.

## Operating rules

- Do not click raw coordinates unless accessibility targeting is insufficient.
- Re-check the UI tree after major transitions instead of assuming the screen stayed the same.
- If multiple matches exist, either use the returned ordering with `index`, or ask a clarifying question.
- If a tool returns a permission error, stop and explain which macOS privacy control must be granted.
- If the user asks for a risky or destructive action, summarize the exact action before doing it.

## Good patterns

- `Open Safari, focus the window with GitHub, click the PR search box, and type CaMeL Guard.`
- `Open TextEdit, create a blank note, and type the meeting summary from the last message.`
- `Focus Slack, snapshot the UI tree, and tell me which channels are visible before clicking anything.`

## Bad patterns

- Guessing coordinates without first inspecting windows or the UI tree.
- Typing into an unfocused app.
- Continuing after a permission failure without telling the operator what to fix.
