"""Inventory what changed between two ACP spec revisions, and which parts of the TCK it touches.

Usage:
  uv run --package spec-tracker spec-impact <base> <target> --version {v1,v2} [--spec-repo PATH] [--fix]

Prints a Markdown report to stdout for a researcher to interpret: changed files, the sections
each doc hunk falls in, hits on the core docs and `$defs` listed in `spec-tracker/maps/<version>.toml`,
the schema `$ref` closure, docs linking to changed docs, and the requirement ids and ledger
entries whose citations fall in a changed region.

With `--fix` it instead remaps the `.mdx` line citations in `src/tck/<version>/requirements.py`
and `spec-tracker/maps/<version>.toml` from base to target line numbers, in place (see "citation remapping"). It is not
idempotent (a second run would shift the already-remapped lines again), so it refuses unless
`<base>` resolves to the version's pinned `SCHEMA_REVISION` (`tck.<version>.protocol`). Run it
before the re-vendor step bumps the pin, which then blocks a second run.

Read-only on the spec checkout: it only runs `git rev-parse`, `git diff`, `git show` and
`git ls-tree` on the given refs, so the checkout's branch and working tree do not matter.
`--spec-repo` defaults to `$ACP_SPEC_REPO`, else the `check-specification` skill's checkout.

Stdlib only, apart from the `tck` package (registry, pinned revision), which the workspace
provides to `spec-tracker`.
"""

from __future__ import annotations

import argparse
import ast
import importlib
import json
import os
import posixpath
import re
import subprocess
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from .citations import find_line_refs, line_refs, pointer_def, schema_pointers
from .spec_map import (
    INTRO,
    PATH_SEPARATOR,
    CoreDoc,
    Heading,
    SectionError,
    SpecMap,
    load_version_map,
    map_path,
    parse_headings,
    parse_spec_map,
    resolve_section,
)
from .spec_repo import discover_spec_repo

RFDS_DIR = "docs/rfds/"


def draft_dir(version: str) -> str:
    return f"docs/protocol/{version}/draft/"


def schema_path(version: str) -> str:
    return f"schema/{version}/schema.unstable.json"


def scope_paths(version: str) -> tuple[str, ...]:
    return draft_dir(version), f"schema/{version}/", RFDS_DIR


# --- git -------------------------------------------------------------------------------------


class GitError(RuntimeError):
    pass


class SpecRepo:
    """Read-only access to a spec checkout by revision (never touches its working tree)."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._shown: dict[tuple[str, str], str | None] = {}

    def git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.path), "-c", "core.quotePath=false", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
        )
        if result.returncode != 0:
            raise GitError(f"git {' '.join(args)}: {result.stderr.strip()}")
        return result.stdout

    def commit(self, ref: str) -> str:
        return self.git("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").strip()

    def show(self, rev: str, path: str) -> str | None:
        """`path`'s content at `rev`, or `None` when it does not exist there."""
        key = (rev, path)
        if key not in self._shown:
            try:
                self._shown[key] = self.git("show", f"{rev}:{path}")
            except GitError:
                self._shown[key] = None
        return self._shown[key]

    def files(self, rev: str, prefix: str) -> list[str]:
        return self.git("ls-tree", "-r", "--name-only", rev, "--", prefix).splitlines()

    def diff(self, base: str, target: str, paths: Sequence[str], *, name_status: bool = False) -> str:
        args = ["diff", "--no-renames", "--no-color", "--no-ext-diff", "--no-textconv"]
        args += ["--name-status"] if name_status else ["-U0", "--src-prefix=a/", "--dst-prefix=b/"]
        return self.git(*args, base, target, "--", *paths)


# --- diff parsing (also the basis for remapping line citations) ------------------------------


@dataclass(frozen=True)
class Hunk:
    """One `-U0` hunk. With a zero count, the start is the line *after which* the other side's
    lines are inserted (git's convention), so it covers no line on that side."""

    old_start: int
    old_count: int
    new_start: int
    new_count: int

    @property
    def old_lines(self) -> range:
        return range(self.old_start, self.old_start + self.old_count)

    @property
    def new_lines(self) -> range:
        return range(self.new_start, self.new_start + self.new_count)

    def label(self) -> str:
        return f"-{self.old_start},{self.old_count} +{self.new_start},{self.new_count}"


@dataclass(frozen=True)
class FileChange:
    status: str
    """`A` (added), `D` (deleted) or `M` (modified)."""
    path: str
    hunks: tuple[Hunk, ...] = ()


_HUNK_HEADER = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def parse_hunk_header(line: str) -> Hunk | None:
    m = _HUNK_HEADER.match(line)
    if not m:
        return None
    old_start, old_count, new_start, new_count = m.groups()
    return Hunk(
        int(old_start),
        1 if old_count is None else int(old_count),
        int(new_start),
        1 if new_count is None else int(new_count),
    )


def parse_diff(text: str) -> dict[str, list[Hunk]]:
    """Hunks per path from `git diff -U0` output (`a/`/`b/` prefixes, no renames)."""
    hunks: dict[str, list[Hunk]] = {}
    old_path = path = None
    for line in text.splitlines():
        if line.startswith("diff --git "):
            old_path = path = None
        elif line.startswith("--- "):
            old_path = line[4:].removeprefix("a/")
        elif line.startswith("+++ "):
            new = line[4:]
            path = old_path if new == "/dev/null" else new.removeprefix("b/")
            if path is not None:  # a `+++` line without a preceding `---` is not a git diff
                hunks.setdefault(path, [])
        elif path is not None and (hunk := parse_hunk_header(line)):
            hunks[path].append(hunk)
    return hunks


def parse_name_status(text: str) -> list[tuple[str, str]]:
    changes = []
    for line in text.splitlines():
        status, _, path = line.partition("\t")
        if path:
            changes.append((status[0], path))
    return changes


def file_changes(repo: SpecRepo, base: str, target: str, version: str) -> dict[str, FileChange]:
    paths = scope_paths(version)
    hunks = parse_diff(repo.diff(base, target, paths))
    return {
        path: FileChange(status, path, tuple(hunks.get(path, ())))
        for status, path in parse_name_status(repo.diff(base, target, paths, name_status=True))
    }


def overlaps(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    return a_start <= b_end and b_start <= a_end


def hunk_touches_base_range(hunk: Hunk, start: int, end: int) -> bool:
    """Whether `hunk` changes base lines `start..end`: it replaces or removes one of them, or
    inserts text strictly inside the range (an insertion at either edge leaves it intact)."""
    if hunk.old_count:
        return overlaps(hunk.old_start, hunk.old_start + hunk.old_count - 1, start, end)
    return start <= hunk.old_start and hunk.old_start + 1 <= end


def hunk_overlaps(hunk: Hunk, side: str, start: int, end: int) -> bool:
    """Whether the hunk's own lines on `side` (`base` or `target`) overlap `start..end`."""
    lines = hunk.old_lines if side == "base" else hunk.new_lines
    return bool(lines) and overlaps(lines[0], lines[-1], start, end)


# --- sections --------------------------------------------------------------------------------


_TAG = re.compile(r"<[^>]+>")


def plain_title(title: str) -> str:
    """A heading title without inline HTML (`schema.mdx` wraps names in `<span>`s)."""
    return _TAG.sub("", title).strip()


def heading_path_at(headings: Sequence[Heading], line: int) -> str:
    """The heading path (`"A > B"`, plain titles) enclosing `line`; `(intro)` before the first
    heading."""
    stack: list[Heading] = []
    for heading in headings:
        if heading.line > line:
            break
        while stack and stack[-1].level >= heading.level:
            stack.pop()
        stack.append(heading)
    return PATH_SEPARATOR.join(plain_title(h.title) for h in stack) if stack else INTRO


def hunk_side(hunk: Hunk) -> str:
    """`base` for removed or modified text, `target` for a pure insertion."""
    return "base" if hunk.old_count else "target"


def hunk_sections(hunk: Hunk, base_text: str | None, target_text: str | None) -> list[str]:
    """Section addresses the hunk's lines fall in, on the side `hunk_side` picks."""
    base = hunk_side(hunk) == "base"
    text = base_text if base else target_text
    lines = hunk.old_lines if base else hunk.new_lines
    headings = parse_headings(text or "")
    return list(dict.fromkeys(heading_path_at(headings, line) for line in lines))


def section_ranges(text: str) -> list[tuple[Heading, int]]:
    """Every heading with the last line of its section (subsections included)."""
    headings = parse_headings(text)
    last = len(text.splitlines())
    ranges = []
    for index, heading in enumerate(headings):
        end = next((h.line - 1 for h in headings[index + 1 :] if h.level <= heading.level), last)
        ranges.append((heading, end))
    return ranges


def changed_headings(change: FileChange, base_text: str | None, target_text: str | None) -> set[str]:
    """Titles of the sections (at base or target) that a hunk overlaps; every heading of a
    removed or added doc."""
    titles = set()
    for text, side in ((base_text, "base"), (target_text, "target")):
        for heading, end in section_ranges(text or ""):
            if change.status != "M" or any(hunk_overlaps(h, side, heading.line, end) for h in change.hunks):
                titles.add(heading.title)
    return titles


# --- core docs -------------------------------------------------------------------------------


@dataclass(frozen=True)
class CoreHit:
    core: CoreDoc
    section: str | None
    """`None` for a whole-doc core entry."""
    hunks: tuple[Hunk, ...]


def core_hits(
    core_docs: Iterable[CoreDoc],
    changes: dict[str, FileChange],
    base_text: dict[str, str | None],
    target_text: dict[str, str | None],
) -> tuple[list[CoreHit], list[str]]:
    """Core entries a hunk touches, plus notes on core sections that did not resolve. A section
    entry is hit when a hunk overlaps its range at base (removed/modified lines) or at target
    (added/modified lines)."""
    hits, notes = [], []
    for core in core_docs:
        change = changes.get(core.path)
        if change is None:
            continue
        if not core.sections or change.status != "M":
            hits.append(CoreHit(core, None, change.hunks))
            continue
        for section in core.sections:
            ranges: dict[str, tuple[int, int]] = {}
            for side, texts in (("base", base_text), ("target", target_text)):
                try:
                    ranges[side] = resolve_section(texts[core.path] or "", section)
                except SectionError as error:
                    notes.append(f"`{core.path}` section `{section}` at {side}: {error}")
            touched = tuple(
                hunk for hunk in change.hunks if any(hunk_overlaps(hunk, side, *ranges[side]) for side in ranges)
            )
            if touched:
                hits.append(CoreHit(core, section, touched))
    return hits, notes


# --- schema ----------------------------------------------------------------------------------

ROOT = "(root)"
"""Pseudo-definition for everything in the schema outside `$defs`."""


def schema_nodes(schema: dict[str, Any] | None) -> dict[str, Any]:
    if not schema:
        return {}
    nodes = dict(schema.get("$defs", {}))
    nodes[ROOT] = {key: value for key, value in schema.items() if key != "$defs"}
    return nodes


@dataclass(frozen=True)
class DefChanges:
    added: tuple[str, ...]
    removed: tuple[str, ...]
    changed: tuple[str, ...]

    def status(self, name: str) -> str | None:
        for label in ("added", "removed", "changed"):
            if name in getattr(self, label):
                return label
        return None

    @property
    def direct(self) -> set[str]:
        return {*self.added, *self.removed, *self.changed}


def diff_defs(base: dict[str, Any], target: dict[str, Any]) -> DefChanges:
    def canonical(node: Any) -> str:
        return json.dumps(node, sort_keys=True)

    return DefChanges(
        added=tuple(sorted(set(target) - set(base))),
        removed=tuple(sorted(set(base) - set(target))),
        changed=tuple(sorted(n for n in set(base) & set(target) if canonical(base[n]) != canonical(target[n]))),
    )


def refs_in(node: Any) -> set[str]:
    """`$defs` names referenced anywhere inside `node` via local `$ref`s."""
    found = set()
    stack = [node]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            ref = item.get("$ref")
            if isinstance(ref, str) and ref.startswith("#") and (name := pointer_def(ref[1:])):
                found.add(name)
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
    return found


def ref_closure(direct: set[str], *graphs: dict[str, Any]) -> dict[str, set[str]]:
    """Definitions (not themselves in `direct`) that transitively `$ref` a definition in
    `direct`, each with the directly changed definitions it reaches. Edges come from every
    given node map, so a reference that exists only at base or only at target still counts."""
    referrers: dict[str, set[str]] = {}
    for nodes in graphs:
        for name, node in nodes.items():
            for ref in refs_in(node):
                referrers.setdefault(ref, set()).add(name)
    reaches: dict[str, set[str]] = {}
    for changed in direct:
        seen, stack = {changed}, [changed]
        while stack:
            for referrer in referrers.get(stack.pop(), ()):
                if referrer not in seen:
                    seen.add(referrer)
                    stack.append(referrer)
        for name in seen - direct:
            reaches.setdefault(name, set()).add(changed)
    return reaches


@dataclass(frozen=True)
class SchemaImpact:
    defs: DefChanges
    closure: dict[str, set[str]]


def schema_impact(base_json: str | None, target_json: str | None) -> SchemaImpact:
    base = schema_nodes(json.loads(base_json) if base_json else None)
    target = schema_nodes(json.loads(target_json) if target_json else None)
    defs = diff_defs(base, target)
    return SchemaImpact(defs, ref_closure(defs.direct, base, target))


# --- links -----------------------------------------------------------------------------------

_SITE = re.compile(r"^https?://(?:www\.)?agentclientprotocol\.com(?=/|$)")
_SCHEME = re.compile(r"^[a-z][a-z0-9+.-]*:", re.IGNORECASE)
_STABLE_TREE = re.compile(r"^docs/protocol/(v\d+)/(?!draft/)")
_MD_LINK = re.compile(r"\]\(\s*<?([^)\s>]+)>?(?:\s+[\"'][^)]*[\"'])?\s*\)")
_HREF = re.compile(r"""\bhref=(?:"([^"]+)"|'([^']+)')""")
_FENCE = re.compile(r"^\s*(```|~~~)")


def slugify(title: str) -> str:
    """Approximate heading anchor: plain title, lowercase, punctuation other than `/`, `_` and
    `-` dropped, spaces to hyphens (`3. Agent Reports Output` -> `3-agent-reports-output`;
    `session/new` -> `session/new`, linked as `#session%2Fnew`)."""
    slug = re.sub(r"[^\w\s/-]", "", plain_title(title).lower())
    return re.sub(r"\s+", "-", slug.strip())


def normalize_link(url: str, from_path: str) -> tuple[str, str | None] | None:
    """The spec-repo doc path (and anchor) a link in `from_path` points at, or `None` for an
    external link. Site-absolute (`/protocol/v1/x`), full-URL and relative links are resolved;
    links into a version's stable tree are mapped onto its draft tree."""
    url = _SITE.sub("", url)
    if _SCHEME.match(url) or url.startswith("//"):
        return None
    url, _, anchor = url.partition("#")
    url = url.partition("?")[0]
    if not url:
        return from_path, anchor or None
    if url.startswith("/"):
        path = "docs" + posixpath.normpath(url)
    else:
        path = posixpath.normpath(posixpath.join(posixpath.dirname(from_path), url))
    path = path.rstrip("/")
    if not path.endswith((".mdx", ".md")):
        path += ".mdx"
    return _STABLE_TREE.sub(r"docs/protocol/\1/draft/", path), anchor or None


def doc_links(text: str) -> list[tuple[int, str]]:
    """`(line, url)` for every markdown link and `href` attribute outside code fences."""
    links = []
    in_fence = False
    for number, line in enumerate(text.splitlines(), 1):
        if _FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        links += [(number, url) for url in _MD_LINK.findall(line)]
        links += [(number, a or b) for a, b in _HREF.findall(line)]
    return links


@dataclass(frozen=True)
class LinkHit:
    source: str
    line: int
    anchor: str | None
    anchor_status: str | None
    """`changed section`, `unchanged section` or `unknown anchor`; `None` without an anchor."""


def link_fan_out(
    sources: dict[str, str],
    changed_docs: dict[str, tuple[set[str], set[str]]],
) -> dict[str, list[LinkHit]]:
    """Links from `sources` (path -> target text) into each changed doc. `changed_docs` maps a
    doc path to (slugs of its changed sections, slugs of all its sections)."""
    fan_out: dict[str, list[LinkHit]] = {path: [] for path in changed_docs}
    for source, text in sorted(sources.items()):
        for line, url in doc_links(text):
            resolved = normalize_link(url, source)
            if resolved is None or resolved[0] == source or resolved[0] not in changed_docs:
                continue
            path, anchor = resolved
            status = None
            if anchor:
                changed, known = changed_docs[path]
                slug = unquote(anchor).lower()
                status = "changed section" if slug in changed else "unchanged section" if slug in known else "unknown anchor"
            fan_out[path].append(LinkHit(source, line, anchor, status))
    return fan_out


# --- citations -------------------------------------------------------------------------------


def citation_hits(citation: str, version: str, changes: dict[str, FileChange], schema: SchemaImpact) -> list[str]:
    """Why `citation` falls in a changed region (empty when it does not)."""
    hits = []
    for ref in line_refs(citation):
        change = changes.get(ref.path)
        if change is None:
            continue
        rfd = ref.path.startswith(RFDS_DIR)
        if change.status != "M":
            hits.append(f"cites `{ref.path}`, which was {'removed' if change.status == 'D' else 'added'}")
            continue
        if not ref.ranges:
            hits.append(f"cites all of `{ref.path}`, which changed")
            continue
        touched = [
            (start, end, [h for h in change.hunks if hunk_touches_base_range(h, start, end)])
            for start, end in ref.ranges
        ]
        for start, end, hunks in touched:
            if hunks:
                lines = str(start) if start == end else f"{start}-{end}"
                hits.append(f"`{ref.path}:{lines}` overlaps hunk {', '.join(f'`{h.label()}`' for h in hunks)}")
        if rfd and not any(hunks for *_, hunks in touched):
            hits.append(f"cites changed RFD `{ref.path}` (cited lines untouched)")
    for pointer in schema_pointers(citation, version):
        name = pointer_def(pointer) or ROOT
        if status := schema.defs.status(name):
            hits.append(f"`#{pointer}`: `{name}` {status}")
        elif name in schema.closure:
            via = _names(sorted(schema.closure[name]), _VIA_LIMIT)
            hits.append(f"`#{pointer}`: `{name}` in $ref closure of {via}")
    return list(dict.fromkeys(hits))


# --- citation remapping (--fix) --------------------------------------------------------------


def last_base_line(hunk: Hunk) -> int:
    """The last base line a hunk covers; for an insertion, the line it comes after."""
    return hunk.old_start + hunk.old_count - 1 if hunk.old_count else hunk.old_start


def remap_range(hunks: Sequence[Hunk], start: int, end: int) -> tuple[tuple[int, int] | None, list[Hunk]]:
    """Base lines `start..end` at target, or `None` plus the hunks that change them. A range that
    no hunk touches moves as a whole by the net size of the hunks above it."""
    touching = [h for h in hunks if hunk_touches_base_range(h, start, end)]
    if touching:
        return None, touching
    offset = sum(h.new_count - h.old_count for h in hunks if last_base_line(h) < start)
    return (start + offset, end + offset), []


@dataclass(frozen=True)
class Remapped:
    old: str
    """The citation element as written, `path:lines`."""
    new: str | None
    """Its target-revision form; `None` when it could not be mapped (left as written)."""
    why: str = ""
    """For an unmapped element: the hunks (or other reason) that prevent it."""


def remap_citation(text: str, changes: dict[str, FileChange]) -> tuple[str, list[Remapped]]:
    """`text` with the line numbers of its `.mdx` citations moved from base to target, and what
    was rewritten or could not be. Only digits change: ranges and comma lists keep their shape,
    and an element that cannot be mapped stays as written."""
    out = text
    results: list[Remapped] = []
    for match in reversed(find_line_refs(text)):
        path, span = match.ref.path, match.spec_span
        change = changes.get(path)
        if change is None or change.status == "A" or span is None:
            continue
        elements, new_elements, ref_results = text[span[0] : span[1]].split(","), [], []
        for element in elements:
            start, _, end = element.partition("-")
            first, last = int(start), int(end or start)
            if not path.endswith(".mdx"):
                mapped, why = None, "line citations into a non-doc file are not remapped"
            elif change.status == "D":
                mapped, why = None, "file removed"
            else:
                mapped, hunks = remap_range(change.hunks, first, last)
                why = "overlaps hunk " + ", ".join(f"`{h.label()}`" for h in hunks)
            if mapped is None:
                new_elements.append(element)
                ref_results.append(Remapped(f"{path}:{element}", None, why))
                continue
            new = f"{mapped[0]}-{mapped[1]}" if "-" in element else str(mapped[0])
            new_elements.append(new)
            if new != element:
                ref_results.append(Remapped(f"{path}:{element}", f"{path}:{new}"))
        out = out[: span[0]] + ",".join(new_elements) + out[span[1] :]
        results = ref_results + results
    return out, results


Labelled = tuple[str, Remapped]


def _char_offsets(source: str, node: ast.expr) -> tuple[int, int]:
    """`node`'s `(start, end)` as indexes into `source` (ast columns are UTF-8 byte offsets)."""
    lines = source.split("\n")
    starts = [0]
    for line in lines:
        starts.append(starts[-1] + len(line) + 1)

    def offset(lineno: int, col: int) -> int:
        return starts[lineno - 1] + len(lines[lineno - 1].encode()[:col].decode())

    assert node.end_lineno is not None and node.end_col_offset is not None
    return offset(node.lineno, node.col_offset), offset(node.end_lineno, node.end_col_offset)


def fix_requirements_source(source: str, changes: dict[str, FileChange]) -> tuple[str, list[Labelled]]:
    """Remap the `citation=` of every `Requirement(...)` in `source`, editing the text in place
    so the diff is line numbers only."""
    edits: list[tuple[int, int, str]] = []
    results: list[Labelled] = []
    for node in ast.walk(ast.parse(source)):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "Requirement"):
            continue
        keywords = {kw.arg: kw.value for kw in node.keywords}
        req_id, citation = keywords.get("id"), keywords.get("citation")
        if not (isinstance(req_id, ast.Constant) and isinstance(citation, ast.expr)):
            continue
        start, end = _char_offsets(source, citation)
        new, remapped = remap_citation(source[start:end], changes)
        results += [(str(req_id.value), item) for item in remapped]
        if new != source[start:end]:
            edits.append((start, end, new))
    for start, end, new in sorted(edits, reverse=True):
        source = source[:start] + new + source[end:]
    return source, results


_LEDGER_TABLE = re.compile(r"^\s*\[\[not_requirement\]\]")
_LEDGER_CITATION = re.compile(r"^\s*citation\s*=")


def fix_spec_map_text(text: str, changes: dict[str, FileChange]) -> tuple[str, list[Labelled]]:
    """Remap each ledger entry's `citation = "..."` line in a spec map file."""
    ledger = parse_spec_map(text).not_requirements
    lines = text.split("\n")
    results: list[Labelled] = []
    index = -1
    for number, line in enumerate(lines):
        if _LEDGER_TABLE.match(line):
            index += 1
        elif index >= 0 and _LEDGER_CITATION.match(line):
            lines[number], remapped = remap_citation(line, changes)
            results += [(f"ledger `{ledger[index].statement}`", item) for item in remapped]
    return "\n".join(lines), results


@dataclass
class FixResult:
    rewritten: list[Labelled] = field(default_factory=list)
    review: list[Labelled] = field(default_factory=list)


def apply_fix(requirements: Path, spec_map: Path, changes: dict[str, FileChange]) -> FixResult:
    """Remap citations in both files in place (only those that changed are rewritten)."""
    result = FixResult()
    for path, fixer in ((requirements, fix_requirements_source), (spec_map, fix_spec_map_text)):
        original = path.read_bytes().decode("utf-8")
        fixed, remapped = fixer(original, changes)
        if fixed != original:
            path.write_bytes(fixed.encode("utf-8"))
        result.rewritten += [item for item in remapped if item[1].new is not None]
        result.review += [item for item in remapped if item[1].new is None]
    return result


def render_fix(result: FixResult, version: str, base: str, target: str) -> str:
    out = [
        f"# Citation remap ({version}): `{base[:12]}` -> `{target[:12]}`",
        "",
        f"## Needs review ({len(result.review)})",
        "",
        "Left as written: the cited lines are inside a changed region, so no new line numbers can be derived.",
        "",
    ]
    out += [f"- {label}: `{item.old}` {item.why}" for label, item in result.review] or ["None."]
    out += ["", f"## Rewritten ({len(result.rewritten)})", ""]
    out += [f"- {label}: `{item.old}` -> `{item.new}`" for label, item in result.rewritten] or ["None."]
    out += [
        "",
        "## Summary",
        "",
        f"- {len(result.rewritten)} citation elements rewritten, {len(result.review)} need review.",
        "- The revision pin (`SCHEMA_REVISION` / `SPEC_REVISION`) is untouched.",
    ]
    return "\n".join(out) + "\n"


def version_files(version: str) -> tuple[Path, Path]:
    """The version's `requirements.py` and spec map file."""
    requirements = Path(importlib.import_module(f"tck.{version}.requirements").__file__ or "")
    return requirements, map_path(version)


def pinned_revision(version: str) -> str:
    """The spec commit the version's citations are currently pinned to."""
    return importlib.import_module(f"tck.{version}.protocol").SCHEMA_REVISION


# --- report ----------------------------------------------------------------------------------


@dataclass
class Report:
    version: str
    base: str
    target: str
    changes: dict[str, FileChange]
    sections: dict[str, list[tuple[Hunk, list[str]]]]
    core: list[CoreHit]
    core_notes: list[str]
    schema: SchemaImpact
    core_defs: list[tuple[str, str]]
    fan_out: dict[str, list[LinkHit]]
    affected: list[tuple[str, list[str]]] = field(default_factory=list)

    @property
    def escalate(self) -> bool:
        return bool(self.core or self.core_defs)


def analyze(
    repo: SpecRepo,
    base: str,
    target: str,
    version: str,
    spec_map: SpecMap,
    entries: Sequence[tuple[str, str]],
) -> Report:
    """Build the report. `entries` are `(label, citation)` pairs: requirement ids and ledger
    entries."""
    changes = file_changes(repo, base, target, version)
    base_text = {path: repo.show(base, path) for path in changes}
    target_text = {path: repo.show(target, path) for path in changes}
    drafts = [path for path in changes if path.startswith(draft_dir(version)) and path.endswith(".mdx")]
    sections = {
        path: [(h, hunk_sections(h, base_text[path], target_text[path])) for h in changes[path].hunks]
        for path in drafts
    }
    core_docs = list(spec_map.core_docs)
    for core in core_docs:
        base_text.setdefault(core.path, repo.show(base, core.path))
        target_text.setdefault(core.path, repo.show(target, core.path))
    core, core_notes = core_hits(core_docs, changes, base_text, target_text)

    schema = schema_impact(repo.show(base, schema_path(version)), repo.show(target, schema_path(version)))
    core_defs = []
    for name in spec_map.core_defs:
        if status := schema.defs.status(name):
            core_defs.append((name, f"{status} directly"))
        elif name in schema.closure:
            core_defs.append((name, "via $ref closure of " + _names(sorted(schema.closure[name]), _VIA_LIMIT)))

    changed_docs = {}
    for path, change in changes.items():
        if path.endswith(".mdx"):
            all_titles = {h.title for t in (base_text[path], target_text[path]) for h in parse_headings(t or "")}
            changed = changed_headings(change, base_text[path], target_text[path])
            changed_docs[path] = ({slugify(t) for t in changed}, {slugify(t) for t in all_titles})
    sources = {
        path: repo.show(target, path) or ""
        for path in repo.files(target, draft_dir(version))
        if path.endswith(".mdx")
    }
    fan_out = link_fan_out(sources, changed_docs)

    affected = [(label, hits) for label, citation in entries if (hits := citation_hits(citation, version, changes, schema))]
    return Report(version, base, target, changes, sections, core, core_notes, schema, core_defs, fan_out, affected)


_STATUS = {"A": "added", "D": "removed", "M": "modified"}
_VIA_LIMIT = 8


def _names(names: Iterable[str], limit: int | None = None) -> str:
    names = list(names)
    if not names:
        return "none"
    shown = ", ".join(f"`{n}`" for n in names[:limit])
    return shown + (f" and {len(names) - limit} more" if limit is not None and len(names) > limit else "")


def render(report: Report) -> str:
    out = [
        f"# Spec impact ({report.version}): `{report.base[:12]}` -> `{report.target[:12]}`",
        "",
        f"Base `{report.base}`, target `{report.target}`. Scope: {_names(scope_paths(report.version))}.",
        "",
        "## 1. Changed files",
        "",
    ]
    out += [f"- {_STATUS.get(c.status, c.status)}: `{c.path}`" for c in report.changes.values()] or ["None."]

    out += ["", "## 2. Doc hunks -> sections", "", "Base-side sections for removed or modified text, target-side for pure additions.", ""]
    if not report.sections:
        out.append("No draft doc changed.")
    for path, hunks in report.sections.items():
        out.append(f"### `{path}` ({_STATUS.get(report.changes[path].status, '?')})")
        out.append("")
        out += [f"- `{h.label()}` ({hunk_side(h)}): {' | '.join(f'`{s}`' for s in secs) or 'no lines'}" for h, secs in hunks]
        out.append("")

    out += ["", "## 3. Core hits", ""]
    for hit in report.core:
        where = "whole doc" if hit.section is None else f"section `{hit.section}`"
        hunks = ", ".join(f"`{h.label()}`" for h in hit.hunks) or "file " + _STATUS[report.changes[hit.core.path].status]
        out.append(f"- `{hit.core.path}` ({where}): {hunks}; code: {_names(hit.core.code)}")
    if not report.core:
        out.append("No core doc or section touched.")
    out += [f"- note: {note}" for note in report.core_notes]

    defs = report.schema.defs
    out += [
        "",
        "## 4. Schema",
        "",
        f"`$defs` compared between base and target `{schema_path(report.version)}` (`{ROOT}` = everything outside `$defs`).",
        "",
        f"- Added: {_names(defs.added)}",
        f"- Removed: {_names(defs.removed)}",
        f"- Changed: {_names(defs.changed)}",
        f"- `$ref` closure ({len(report.schema.closure)} defs that transitively reference a changed def):",
    ]
    out += [f"  - `{name}` -> {_names(sorted(via), _VIA_LIMIT)}" for name, via in sorted(report.schema.closure.items())]
    out.append("- Core `$defs` hit: " + ("; ".join(f"`{n}` ({why})" for n, why in report.core_defs) or "none"))

    out += ["", "## 5. Link fan-out", "", f"Docs under `{draft_dir(report.version)}` at target that link to a changed doc.", ""]
    for path, links in report.fan_out.items():
        if not links:
            continue
        out.append(f"### `{path}`")
        out.append("")
        for link in links:
            anchor = f" `#{link.anchor}` ({link.anchor_status})" if link.anchor else ""
            out.append(f"- `{link.source}:{link.line}`{anchor}")
        out.append("")
    if not any(report.fan_out.values()):
        out.append("No links into a changed doc.")

    out += ["", "## 6. Affected entries", ""]
    out += [f"- {label}: " + "; ".join(hits) for label, hits in report.affected] or ["None."]

    linked = sum(len(v) for v in report.fan_out.values())
    by_kind = {
        "draft docs": sum(p.startswith(draft_dir(report.version)) for p in report.changes),
        "schema files": sum(p.startswith(f"schema/{report.version}/") for p in report.changes),
        "RFDs": sum(p.startswith(RFDS_DIR) for p in report.changes),
    }
    out += [
        "",
        "## Summary",
        "",
        f"- Changed files: {len(report.changes)} ({', '.join(f'{n} {k}' for k, n in by_kind.items())}); "
        f"doc hunks: {sum(len(h) for h in report.sections.values())}.",
        f"- `$defs`: {len(defs.added)} added, {len(defs.removed)} removed, {len(defs.changed)} changed; "
        f"closure: {len(report.schema.closure)}.",
        f"- Links into changed docs: {linked}.",
        f"- Affected entries: {sum(not l.startswith('ledger') for l, _ in report.affected)} requirements, "
        f"{sum(l.startswith('ledger') for l, _ in report.affected)} ledger entries.",
        "- Core hit: "
        + (
            "**yes, escalate** ("
            + "; ".join(
                [f"`{h.core.path}`" + (f" > `{h.section}`" if h.section else "") for h in report.core]
                + [f"`$defs/{n}`" for n, _ in report.core_defs]
            )
            + ")"
            if report.escalate
            else "no"
        ),
    ]
    return "\n".join(out) + "\n"


def registry_entries(version: str) -> list[tuple[str, str]]:
    """`(label, citation)` for every requirement and ledger entry of `version`."""
    registry = importlib.import_module(f"tck.{version}.requirements").REGISTRY
    spec_map = load_version_map(version)
    entries = [(req_id, requirement.citation) for req_id, requirement in registry.items()]
    entries += [(f"ledger `{entry.statement}`", entry.citation) for entry in spec_map.not_requirements]
    return entries


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0] or None)
    parser.add_argument("base", help="base spec revision (e.g. the commit pinned in VENDORED.md)")
    parser.add_argument("target", help="target spec revision")
    parser.add_argument("--version", required=True, choices=("v1", "v2"))
    parser.add_argument("--spec-repo", type=Path, help="spec checkout (default: $ACP_SPEC_REPO, else check-specification's)")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="remap `.mdx` line citations in the version's requirements.py and its spec map in place, "
        "instead of printing the report",
    )
    args = parser.parse_args(argv)

    path = args.spec_repo or discover_spec_repo()
    if path is None:
        parser.error("no spec checkout: pass --spec-repo or set ACP_SPEC_REPO")
    repo = SpecRepo(path)
    try:
        base, target = repo.commit(args.base), repo.commit(args.target)
    except GitError as error:
        parser.error(f"{path}: cannot resolve revision ({error})")
    if args.fix:
        pin = pinned_revision(args.version)
        if base != pin:
            parser.error(
                f"--fix remaps citations from the pinned revision, but base {base} is not the "
                f"{args.version} pin {pin}; citations may already be remapped (nothing was changed)"
            )
        changes = file_changes(repo, base, target, args.version)
        result = apply_fix(*version_files(args.version), changes)
        sys.stdout.write(render_fix(result, args.version, base, target))
        return 0
    spec_map = load_version_map(args.version)
    report = analyze(repo, base, target, args.version, spec_map, registry_entries(args.version))
    sys.stdout.write(render(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
