from __future__ import annotations

from unittest.mock import MagicMock

from hermes_computer.plugin import register


class DummyContext:
    def __init__(self):
        self.calls = []

    def register_tool(self, **kwargs):
        self.calls.append(kwargs)


def test_registers_expected_tools() -> None:
    ctx = DummyContext()
    register(ctx)
    names = {call['name'] for call in ctx.calls}
    assert 'computer_status' in names
    assert 'computer_list_windows' in names
    assert 'computer_snapshot_ui' in names
    assert 'computer_click_element' in names
    assert 'computer_type_text' in names
    assert 'computer_press_keys' in names
