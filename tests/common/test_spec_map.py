"""Unit tests for `tck.common.spec_map`: the TOML parser's shape checks and the heading scanner."""

from __future__ import annotations

import pytest

from tck.common.spec_map import SpecMapError, markdown_headings, parse_spec_map

_MINIMAL = 'core_defs = ["ErrorCode"]\n'


def test_parses_core_docs_defs_and_ledger():
    spec_map = parse_spec_map(
        _MINIMAL
        + """
[[core_doc]]
path = "docs/protocol/v1/draft/a.mdx"
sections = ["One", "Two"]
code = ["src/x.py"]
reason = "why"

[[core_doc]]
path = "docs/protocol/v1/draft/b.mdx"
reason = "whole doc"

[[not_requirement]]
citation = "c @ abc"
statement = "s"
reason = "r"
"""
    )
    assert spec_map.core_defs == ("ErrorCode",)
    first, second = spec_map.core_docs
    assert (first.path, first.sections, first.code, first.reason) == (
        "docs/protocol/v1/draft/a.mdx",
        ("One", "Two"),
        ("src/x.py",),
        "why",
    )
    assert second.sections == () and second.code == ()
    (entry,) = spec_map.not_requirements
    assert (entry.citation, entry.statement, entry.reason) == ("c @ abc", "s", "r")


def test_empty_ledger_is_allowed():
    assert parse_spec_map(_MINIMAL).not_requirements == ()


@pytest.mark.parametrize(
    "extra, message",
    [
        ('[[core_doc]]\npath = "p"\n', "'reason'"),
        ('[[core_doc]]\nreason = "r"\n', "'path'"),
        ('[[core_doc]]\npath = "p"\nreason = "r"\nsections = "One"\n', "'sections'"),
        ('[[core_doc]]\npath = "p"\nreason = "r"\ncodes = []\n', "unknown key"),
        ('[[not_requirement]]\ncitation = "c"\nstatement = "s"\n', "'reason'"),
        ('[[not_requirement]]\ncitation = "c"\nstatement = " "\nreason = "r"\n', "'statement'"),
        ('[[not_requirement]]\ncitation = "c"\nstatement = "s"\nreason = "r"\nextra = 1\n', "unknown key"),
        ("[[stray]]\n", "unknown key"),
    ],
)
def test_malformed_entries_are_rejected(extra, message):
    with pytest.raises(SpecMapError, match=message):
        parse_spec_map(_MINIMAL + extra)


def test_core_defs_is_required():
    with pytest.raises(SpecMapError, match="core_defs"):
        parse_spec_map("")
    # An empty list is still a list of strings, so a map with no core defs is valid.
    assert parse_spec_map("core_defs = []").core_defs == ()


def test_markdown_headings_ignores_code_fences_and_trailing_hashes():
    text = (
        "# Title\n"
        "intro\n"
        "## The `_meta` Field\n"
        "```bash\n"
        "# not a heading\n"
        "```\n"
        "### Sub ###\n"
        "#no-space is not a heading\n"
        "~~~\n"
        "## also fenced\n"
        "~~~\n"
        "#### Last\n"
    )
    assert markdown_headings(text) == ["Title", "The `_meta` Field", "Sub", "Last"]
