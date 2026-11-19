"""Config options and capabilities shared by the initial-config-value defect fixtures
(ACP-OPTIONS-004..011): one select option and one boolean option (the boolean one is visible only
to a client that advertised `clientCapabilities.session.configOptions.boolean`), and modes.
"""

CAPABILITIES = {"loadSession": True, "sessionCapabilities": {"options": {}, "resume": {}}}

FORK_CAPABILITIES = {"sessionCapabilities": {"options": {}, "fork": {}}}
"""For the `options_fork_*` fixtures (with `_cursors.CursorsMixin` for `session/fork`): no
`loadSession` or `resume`, so a `sessionId` may be sent to `session/options` only because of
`fork`."""

MODES = {
    "currentModeId": "default",
    "availableModes": [{"id": "default", "name": "Default"}, {"id": "yolo", "name": "YOLO"}],
}


def config_options() -> list[dict]:
    return [
        {
            "id": "model",
            "name": "Model",
            "type": "select",
            "currentValue": "fast",
            "options": [{"value": "fast", "name": "Fast"}, {"value": "slow", "name": "Slow"}],
        },
        {"id": "verbose", "name": "Verbose", "type": "boolean", "currentValue": False},
    ]
