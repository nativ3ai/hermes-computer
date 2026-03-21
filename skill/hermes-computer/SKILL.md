---
name: hermes-computer
description: Use the hermes-computer plugin to control a local macOS desktop through Hermes. Use it when the user wants Hermes to open apps, inspect windows, click UI elements, type text, press shortcuts, or capture the screen.
---

# Hermes Computer

Use this skill when Hermes needs to operate the local macOS desktop.

## Preconditions

Before using the tools, confirm the daemon and permissions are ready:

1. Call `computer_status` once at the start of the task or after a clear failure state. Do not keep re-running it unless the environment changed.
2. If the daemon is missing, tell the operator to run `hermes-computer bootstrap`.
3. If Accessibility or Screen Recording is missing, tell the operator to run `hermes-computer open-privacy-settings` and grant access.

## Workflow

Prefer deterministic control over blind clicking.

1. If the target app and action are obvious, prefer a single `computer_run_workflow` call rather than many small tool calls.
2. Use `computer_list_windows` only when the target app or window is ambiguous.
3. Use `computer_focus_window` or `computer_open_application` to bring the right app forward.
4. Use `computer_snapshot_ui` when you need to discover buttons, fields, or labels. Do not snapshot repeatedly if the target is already known.
5. Prefer `computer_click_element` over `computer_click_at` whenever possible.
6. Use `computer_type_text` only after the correct field or app is focused.
7. Use `computer_press_keys` for shortcuts like `command+l`, `command+n`, `enter`, `escape`, and tab navigation.
8. Use `computer_capture_screen` when the operator explicitly wants a screenshot artifact or when visual confirmation is necessary.

## Operating rules

- Do not click raw coordinates unless accessibility targeting is insufficient.
- Re-check the UI tree after major transitions only when needed. Avoid unnecessary confirmatory loops.
- If multiple matches exist, either use the returned ordering with `index`, or ask a clarifying question.
- If a tool returns a permission error, stop and explain which macOS privacy control must be granted.
- If the user asks for a risky or destructive action, summarize the exact action before doing it.
- For simple direct tasks, act first and summarize after. Do not over-explain between each step.

## Good patterns

- `Use computer_run_workflow to open TextEdit, create a document, click the text area, and type the note.`
- `Open Safari, focus the window with GitHub, click the PR search box, and type CaMeL Guard.`
- `Open TextEdit, create a blank note, and type the meeting summary from the last message.`
- `Focus Slack, snapshot the UI tree, and tell me which channels are visible before clicking anything.`

## Bad patterns

- Guessing coordinates without first inspecting windows or the UI tree.
- Typing into an unfocused app.
- Continuing after a permission failure without telling the operator what to fix.
