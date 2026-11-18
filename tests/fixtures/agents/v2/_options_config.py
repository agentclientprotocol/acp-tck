"""Config options and capabilities shared by the `session/options` and initial-config-value defect
fixtures (ACP-OPTIONS-*, ACP-CONFIG-001/210 and ACP-COMMANDS-201 on a `session/options` result): one
select option and one boolean option, and a `session.options` capability.
"""

CAPABILITIES = {"session": {"options": {}}}

FORK_CAPABILITIES = {"session": {"options": {}, "fork": {}}}
"""For the `options_fork_*` fixtures, which break an initial-value rule only on `session/fork`."""


def config_options() -> list[dict]:
    return [
        {
            "configId": "model",
            "name": "Model",
            "type": "select",
            "currentValue": "fast",
            "options": [{"value": "fast", "name": "Fast"}, {"value": "slow", "name": "Slow"}],
        },
        {"configId": "verbose", "name": "Verbose", "type": "boolean", "currentValue": False},
    ]
