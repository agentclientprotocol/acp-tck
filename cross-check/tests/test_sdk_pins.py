"""`sdk-pins.sh` must stay consistent with the Python SDK pin in `pyproject.toml`."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

CROSS_CHECK = Path(__file__).resolve().parent.parent


def _pins() -> dict[str, str]:
    text = (CROSS_CHECK / "sdk-pins.sh").read_text(encoding="utf-8")
    return dict(re.findall(r"^([A-Z_]+)=(\S+)$", text, flags=re.MULTILINE))


def test_python_pin_matches_pyproject():
    deps = tomllib.loads((CROSS_CHECK / "pyproject.toml").read_text(encoding="utf-8"))["project"][
        "dependencies"
    ]
    pinned = [d.split("==", 1)[1] for d in deps if d.startswith("agent-client-protocol==")]
    assert pinned, "pyproject.toml must pin agent-client-protocol with =="
    assert pinned == [_pins()["PYTHON_SDK_TAG"]], (
        "agent-client-protocol pin in pyproject.toml differs from PYTHON_SDK_TAG in sdk-pins.sh"
    )


def test_pins_are_full_shas():
    pins = _pins()
    for key in ("RUST_SDK_SHA", "PYTHON_SDK_SHA"):
        assert re.fullmatch(r"[0-9a-f]{40}", pins[key]), key
