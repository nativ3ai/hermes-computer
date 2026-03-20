from __future__ import annotations

from pathlib import Path

from hermes_computer.cli import _install_plugin_tree, _install_skill_tree
from hermes_computer.config import get_config


def test_install_plugin_and_skill(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv('HERMES_HOME', str(tmp_path / '.hermes'))
    config = get_config()
    _install_plugin_tree(config)
    _install_skill_tree(config)

    assert (config.plugin_target / 'plugin.yaml').exists()
    assert (config.plugin_target / '__init__.py').exists()
    assert (config.plugin_target / 'hermes_computer' / 'plugin.py').exists()
    assert (config.skill_target / 'SKILL.md').exists()
    assert (config.skill_target / 'agents' / 'openai.yaml').exists()
