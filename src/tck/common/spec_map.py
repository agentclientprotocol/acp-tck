"""Loader for a version's `spec_map.toml`: which spec docs and schema `$defs` are cross-cutting
("core"), and a ledger of rules the TCK deliberately does not test.

Stdlib only (`tomllib`). Each version package points at its own file (`tck.v1.spec_map`,
`tck.v2.spec_map`); this module holds the version-agnostic parsing.
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path


class SpecMapError(ValueError):
    """The spec map file is malformed."""


@dataclass(frozen=True)
class CoreDoc:
    path: str
    """Repo-relative path inside the spec repo, e.g. `docs/protocol/v1/draft/transports.mdx`."""
    sections: tuple[str, ...]
    """Heading titles that are core; empty means the whole doc. A section covers its subsections."""
    code: tuple[str, ...]
    """Repo-relative TCK paths that implement the doc's cross-cutting rules."""
    reason: str


@dataclass(frozen=True)
class NotRequirement:
    citation: str
    statement: str
    reason: str


@dataclass(frozen=True)
class SpecMap:
    core_docs: tuple[CoreDoc, ...]
    core_defs: tuple[str, ...]
    """Names under the schema's `$defs` whose changes are treated like a core doc change."""
    not_requirements: tuple[NotRequirement, ...]


def _strings(table: dict, key: str, where: str) -> tuple[str, ...]:
    value = table.get(key, [])
    if not isinstance(value, list) or not all(isinstance(v, str) and v.strip() for v in value):
        raise SpecMapError(f"{where}: {key!r} must be a list of non-empty strings")
    return tuple(value)


def _text(table: dict, key: str, where: str) -> str:
    value = table.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SpecMapError(f"{where}: {key!r} must be a non-empty string")
    return value


def _reject_unknown(table: dict, allowed: set[str], where: str) -> None:
    unknown = set(table) - allowed
    if unknown:
        raise SpecMapError(f"{where}: unknown key(s) {sorted(unknown)}")


def parse_spec_map(text: str) -> SpecMap:
    data = tomllib.loads(text)
    if "core_defs" not in data:
        raise SpecMapError("spec map: 'core_defs' is required (use [] for none)")
    _reject_unknown(data, {"core_defs", "core_doc", "not_requirement"}, "spec map")
    core_docs = []
    for i, table in enumerate(data.get("core_doc", [])):
        where = f"core_doc[{i}]"
        _reject_unknown(table, {"path", "sections", "code", "reason"}, where)
        core_docs.append(
            CoreDoc(
                path=_text(table, "path", where),
                sections=_strings(table, "sections", where),
                code=_strings(table, "code", where),
                reason=_text(table, "reason", where),
            )
        )
    ledger = []
    for i, table in enumerate(data.get("not_requirement", [])):
        where = f"not_requirement[{i}]"
        _reject_unknown(table, {"citation", "statement", "reason"}, where)
        ledger.append(
            NotRequirement(
                citation=_text(table, "citation", where),
                statement=_text(table, "statement", where),
                reason=_text(table, "reason", where),
            )
        )
    return SpecMap(
        core_docs=tuple(core_docs),
        core_defs=_strings(data, "core_defs", "spec map"),
        not_requirements=tuple(ledger),
    )


def load_spec_map(path: Path) -> SpecMap:
    return parse_spec_map(path.read_text(encoding="utf-8"))


_FENCE = re.compile(r"^\s*(```|~~~)")
_HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$")


def markdown_headings(text: str) -> list[str]:
    """Heading titles of a markdown/MDX doc in order, ignoring `#` lines inside code fences."""
    titles = []
    in_fence = False
    for line in text.splitlines():
        if _FENCE.match(line):
            in_fence = not in_fence
        elif not in_fence and (m := _HEADING.match(line)):
            titles.append(m.group(1))
    return titles
