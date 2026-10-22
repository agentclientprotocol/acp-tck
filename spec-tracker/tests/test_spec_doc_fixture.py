"""The `spec_doc` fixture's skip-locally / fail-in-CI behavior, against a throwaway git repo."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from conftest import read_spec_doc

_GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com"]


@pytest.fixture
def spec_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "spec"
    repo.mkdir()
    (repo / "doc.mdx").write_text("hello\n")
    subprocess.run([*_GIT, "-C", str(repo), "init", "-q"], check=True)
    subprocess.run([*_GIT, "-C", str(repo), "add", "doc.mdx"], check=True)
    subprocess.run([*_GIT, "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    sha = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    return repo, sha


MISSING_REVISION = "0" * 40


def test_reads_file_at_revision(spec_repo, monkeypatch):
    repo, sha = spec_repo
    monkeypatch.setenv("CI", "true")
    assert read_spec_doc(repo, sha, "doc.mdx") == "hello\n"


def test_missing_file_at_present_revision_is_an_assertion_error_even_locally(spec_repo, monkeypatch):
    repo, sha = spec_repo
    monkeypatch.delenv("CI", raising=False)
    with pytest.raises(AssertionError, match="does not exist"):
        read_spec_doc(repo, sha, "nope.mdx")


@pytest.mark.parametrize("case", ["no_checkout", "missing_revision", "not_a_repo"])
def test_unavailable_spec_skips_locally(case, spec_repo, tmp_path, monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    repo, sha = spec_repo
    args = {
        "no_checkout": (None, sha),
        "missing_revision": (repo, MISSING_REVISION),
        "not_a_repo": (tmp_path / "empty", sha),
    }[case]
    with pytest.raises(pytest.skip.Exception):
        read_spec_doc(args[0], args[1], "doc.mdx")


@pytest.mark.parametrize("case", ["no_checkout", "missing_revision", "not_a_repo"])
def test_unavailable_spec_fails_under_ci(case, spec_repo, tmp_path, monkeypatch):
    monkeypatch.setenv("CI", "true")
    repo, sha = spec_repo
    args = {
        "no_checkout": (None, sha),
        "missing_revision": (repo, MISSING_REVISION),
        "not_a_repo": (tmp_path / "empty", sha),
    }[case]
    with pytest.raises(pytest.fail.Exception, match="CI is set"):
        read_spec_doc(args[0], args[1], "doc.mdx")
