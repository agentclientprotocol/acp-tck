"""Regression test: `acp-tck` runs its inner pytest with a private, per-run `--basetemp`.

pytest's default basetemp root is shared per user, so concurrent `acp-tck` runs raced in its
`pytest-current` symlink cleanup and crashed at session finish. `pytest.main` is monkeypatched,
so no inner session runs.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import tck


def _run_main(monkeypatch: pytest.MonkeyPatch, rc: int = 0, raises: bool = False) -> tuple[list[str], Path]:
    seen: list[str] = []

    def fake_main(args: list[str]) -> int:
        seen[:] = args
        basetemp = Path(args[args.index("--basetemp") + 1])
        assert basetemp.is_dir()
        (basetemp / "leftover").write_text("x")
        if raises:
            raise RuntimeError("boom")
        return rc

    monkeypatch.setattr(tck.pytest, "main", fake_main)
    try:
        result = tck.main(["--", "python", "agent.py"])
    except RuntimeError:
        assert raises
    else:
        assert result == rc
    return seen, Path(seen[seen.index("--basetemp") + 1])


def test_inner_pytest_gets_private_basetemp_removed_afterwards(monkeypatch: pytest.MonkeyPatch) -> None:
    args, basetemp = _run_main(monkeypatch, rc=3)
    assert basetemp.name.startswith("acp-tck-")
    assert not basetemp.exists()
    assert args.count("--basetemp") == 1


def test_each_run_gets_a_fresh_basetemp(monkeypatch: pytest.MonkeyPatch) -> None:
    _, first = _run_main(monkeypatch)
    _, second = _run_main(monkeypatch)
    assert first != second


def test_basetemp_removed_even_if_pytest_main_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    _, basetemp = _run_main(monkeypatch, raises=True)
    assert not basetemp.exists()
