"""Shared mixin for fixtures that send `prompt_suggestions_update` (ACP-SUGGEST-001..004).

Only to a client that advertised `clientCapabilities.session.promptSuggestions`, so
ACP-CLIENTCAP-008's `clientCapabilities: {}` connection stays clean. By default, when it accepts a
`session/prompt` with a non-empty list current, the agent first withdraws it (`suggestions: []`),
then, after the response, sends a fresh list. A fixture overrides `_suggestion_list` (the content)
or `_resuggest` (False: send the list once, after the first prompt of a session, and never
replace or withdraw it).
"""

from __future__ import annotations

from typing import Any

TEXT_SUGGESTIONS: list[dict[str, Any]] = [
    {"prompt": [{"type": "text", "text": "Run the test suite and fix what breaks"}]},
    {
        "prompt": [
            {"type": "text", "text": "Add tests for "},
            {"type": "resource_link", "uri": "file:///tmp/parser.rs", "name": "parser.rs"},
        ]
    },
]


class SuggestsMixin:
    _suggestion_list: list[dict[str, Any]] = TEXT_SUGGESTIONS
    _resuggest = True

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._current_suggestions: dict[Any, list[dict[str, Any]]] = {}

    def _suggestions_advertised(self) -> bool:
        session_caps = self._client_capabilities.get("session")
        return isinstance(session_caps, dict) and session_caps.get("promptSuggestions") is not None

    def _send_suggestions(self, session_id: Any, suggestions: list[dict[str, Any]]) -> None:
        self._current_suggestions[session_id] = suggestions
        update = {"sessionUpdate": "prompt_suggestions_update", "suggestions": suggestions}
        self._notify("session/update", {"sessionId": session_id, "update": update})

    def _handle_prompt(self, msg_id: Any, params: dict[str, Any]) -> None:
        session_id = params.get("sessionId")
        active = session_id in self._sessions and self._suggestions_advertised()
        if active and self._resuggest and self._current_suggestions.get(session_id):
            self._send_suggestions(session_id, [])
        super()._handle_prompt(msg_id, params)
        if active and (self._resuggest or session_id not in self._current_suggestions):
            self._send_suggestions(session_id, list(self._suggestion_list))
