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
    """Section addresses that are core (see `resolve_section`); empty means the whole doc."""
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
_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")

PATH_SEPARATOR = " > "
INTRO = "(intro)"


class SectionError(SpecMapError):
    """A section address matches no heading, or more than one."""


@dataclass(frozen=True)
class Heading:
    title: str
    level: int
    line: int
    """1-based line number of the heading line."""


def parse_headings(text: str) -> list[Heading]:
    """Headings of a markdown/MDX doc in order, ignoring `#` lines inside code fences and the
    leading `---` frontmatter block."""
    lines = text.splitlines()
    start = 0
    if lines and lines[0].strip() == "---":
        closing = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
        start = 0 if closing is None else closing + 1
    headings = []
    in_fence = False
    for index in range(start, len(lines)):
        line = lines[index]
        if _FENCE.match(line):
            in_fence = not in_fence
        elif not in_fence and (m := _HEADING.match(line)):
            headings.append(Heading(m.group(2), len(m.group(1)), index + 1))
    return headings


def markdown_headings(text: str) -> list[str]:
    """Heading titles of a markdown/MDX doc in order."""
    return [h.title for h in parse_headings(text)]


def _subtree_end(headings: list[Heading], index: int, last_line: int) -> int:
    """Last line of the section whose heading is `headings[index]`, subsections included."""
    for later in headings[index + 1 :]:
        if later.level <= headings[index].level:
            return later.line - 1
    return last_line


def _children(headings: list[Heading], index: int) -> list[int]:
    """Indexes of the direct child headings of `headings[index]`."""
    children = []
    for i in range(index + 1, len(headings)):
        if headings[i].level <= headings[index].level:
            break
        if not children or headings[i].level == headings[children[0]].level:
            children.append(i)
    return children


def resolve_section(text: str, address: str) -> tuple[int, int]:
    """The 1-based inclusive line range `address` covers in `text`.

    `address` is a heading title, or titles joined by ` > ` from a heading down through direct
    children (`"Agent > Baseline Methods"`). The first title may match a heading at any depth;
    exactly one heading must match. A section covers its subsections. A trailing `(intro)`
    narrows the range to the section's own text, up to its first child heading; `"(intro)"`
    alone is everything before the doc's first heading (frontmatter included). Raises
    `SectionError` unless exactly one non-empty range matches.
    """
    lines = text.splitlines()
    headings = parse_headings(text)
    parts = address.split(PATH_SEPARATOR)
    if not all(part.strip() for part in parts):
        raise SectionError(f"empty title in section address {address!r}")
    parts = [part.strip() for part in parts]
    intro = parts[-1] == INTRO
    if intro:
        parts = parts[:-1]
    if INTRO in parts:
        raise SectionError(f"{INTRO!r} is only valid as the last part of {address!r}")

    if not parts:
        end = headings[0].line - 1 if headings else len(lines)
        if not any(line.strip() for line in lines[:end]):
            raise SectionError(f"doc has no text before its first heading ({address!r})")
        return 1, end

    candidates = [i for i, h in enumerate(headings) if h.title == parts[0]]
    for part in parts[1:]:
        candidates = [
            child
            for index in candidates
            for child in _children(headings, index)
            if headings[child].title == part
        ]
    if len(candidates) != 1:
        problem = "matches no heading" if not candidates else f"is ambiguous ({len(candidates)} matches)"
        raise SectionError(f"section address {address!r} {problem}; headings: {markdown_headings(text)}")
    index = candidates[0]
    end = _subtree_end(headings, index, len(lines))
    if intro and (children := _children(headings, index)):
        end = headings[children[0]].line - 1
    return headings[index].line, end
