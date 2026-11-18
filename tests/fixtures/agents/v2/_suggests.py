"""Shared mixin for fixtures that send `prompt_suggestions_update` (ACP-SUGGEST-001..004).

Only to a client that advertised `capabilities.session.promptSuggestions`, so ACP-CLIENTCAP-008's
connections stay clean. By default, when it accepts a `session/prompt` with a non-empty list
current, the agent withdraws it (`suggestions: []`) right after the response, and sends a fresh
list after the turn's idle. A fixture overrides `_suggestion_list` (the content) or `_resuggest`
(False: send the list once, after the first turn of a session, and never replace or withdraw it).
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

    def _send_user_message_update(self, session_id: Any, message_id: str, prompt: Any) -> None:
        # The prompt was accepted (its response is out): the earlier list is out of date.
        if self._suggestions_advertised() and self._resuggest and self._current_suggestions.get(session_id):
            self._send_suggestions(session_id, [])
        super()._send_user_message_update(session_id, message_id, prompt)

    def _send_idle_update(self, session_id: Any, stop_reason: str | None) -> None:
        super()._send_idle_update(session_id, stop_reason)
        if (
            self._suggestions_advertised()
            and session_id in self._sessions
            and (self._resuggest or session_id not in self._current_suggestions)
        ):
            self._send_suggestions(session_id, list(self._suggestion_list))
