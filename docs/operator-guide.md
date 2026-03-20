# Operator Guide

## First run

1. Install the repo and build the app:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pip install '.[app]'
hermes-computer install-plugin
hermes-computer build-app
hermes-computer install-app
hermes-computer open-app
```

2. Grant macOS privacy permissions when the app opens:

- Accessibility
- Screen Recording

3. Verify:

```bash
hermes-computer doctor
hermes-computer status
```

## Best operating pattern in Hermes

The most reliable sequence is:

1. `computer_list_windows`
2. `computer_focus_window` or `computer_open_application`
3. `computer_snapshot_ui`
4. `computer_click_element`
5. `computer_type_text` or `computer_press_keys`

Use `computer_click_at` only if accessibility targeting is not enough.

## Example prompts

- `Open Safari and tell me which GitHub windows are visible.`
- `Focus TextEdit, inspect the UI tree, and click the document body.`
- `Open Notes, create a new note, and type the summary from the last message.`
- `Capture the current screen and return the saved file path.`

## Failure handling

If Hermes reports that the daemon is unavailable:

```bash
hermes-computer open-app
```

If Hermes reports missing permissions:

```bash
hermes-computer open-privacy-settings
```

Then re-run:

```bash
hermes-computer doctor
```
