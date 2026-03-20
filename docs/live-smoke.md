# Live Smoke Test

These checks validate the add-on on a real macOS machine.

## Safe baseline

```bash
hermes-computer doctor
hermes-computer status
```

Expected:

- daemon reports as reachable
- Accessibility and Screen Recording status are explicit

## Hermes-side smoke

Inside Hermes:

- `Use computer_status and summarize the result in one line.`
- `Use computer_list_windows and tell me the first three visible window owner names.`

## Full interactive smoke

After granting permissions:

- `Open TextEdit.`
- `Snapshot the frontmost UI tree.`
- `Click the main editor area.`
- `Type: Hermes Computer smoke test.`
- `Press enter.`
- `Capture the current screen and return the saved path.`

That sequence validates:

- plugin loading
- daemon reachability
- window targeting
- accessibility tree reads
- click injection
- text entry
- screenshot capture
