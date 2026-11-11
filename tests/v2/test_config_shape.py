"""Unit tests for `ACP-CONFIG-201`'s shape helper (shared with `ACP-CONFIG-203`) and the
item-level schema validator it relies on."""

from __future__ import annotations

import pytest

from tck.v2.conformance.test_session_config import _assert_config_options_shape_valid
from tck.v2.validation import validate_def_value


def _select(options):
    return {
        "configId": "verbosity",
        "name": "Verbosity",
        "type": "select",
        "currentValue": "normal",
        "options": options,
    }


_FLAT = [{"value": "normal", "name": "Normal"}]
_GROUPED = [{"groupId": "g", "name": "G", "options": _FLAT}]


def test_empty_config_options_list_is_valid_and_means_none():
    _assert_config_options_shape_valid([])


@pytest.mark.parametrize("options", [_FLAT, _GROUPED])
def test_non_empty_flat_and_grouped_selects_are_valid(options):
    _assert_config_options_shape_valid([_select(options)])


def test_boolean_option_is_valid():
    _assert_config_options_shape_valid(
        [{"configId": "d", "name": "D", "type": "boolean", "currentValue": False}]
    )


def test_select_with_empty_options_is_rejected():
    with pytest.raises(AssertionError, match="options"):
        _assert_config_options_shape_valid([_select([])])


def test_grouped_select_with_an_empty_group_is_rejected():
    grouped = [*_GROUPED, {"groupId": "empty", "name": "Empty", "options": []}]
    with pytest.raises(AssertionError, match="group|options"):
        _assert_config_options_shape_valid([_select(grouped)])


def test_mixed_flat_and_grouped_is_rejected():
    with pytest.raises(AssertionError):
        _assert_config_options_shape_valid([_select([*_FLAT, *_GROUPED])])


def test_validate_def_value_judges_only_the_given_item():
    assert validate_def_value("AvailableCommand", {"type": "command", "name": "a", "description": "d"}) == []
    assert validate_def_value("AvailableCommand", {"name": "a", "description": "d"}) != []
    assert validate_def_value("SessionConfigOption", _select([])) != []
