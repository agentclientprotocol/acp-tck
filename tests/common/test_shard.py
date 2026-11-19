"""The `--shard K/N` option in `tests/conftest.py` that CI uses to split the suite over runners."""

from __future__ import annotations

import pytest

from conftest import parse_shard, shard_indices


def test_shards_cover_every_item_exactly_once() -> None:
    for count in (0, 1, 7, 1241):
        for n in (1, 3, 4):
            picked = [i for k in range(1, n + 1) for i in shard_indices(count, k, n)]
            assert sorted(picked) == list(range(count))


def test_parse_shard_accepts_k_of_n() -> None:
    assert parse_shard("2/4") == (2, 4)


@pytest.mark.parametrize("value", ["0/4", "5/4", "4", "a/b", "1/2/3"])
def test_parse_shard_rejects_bad_values(value: str) -> None:
    with pytest.raises(pytest.UsageError):
        parse_shard(value)
