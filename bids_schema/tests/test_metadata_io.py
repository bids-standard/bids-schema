"""Tests for atomic read-modify-write helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bids_schema.metadata.io import load_json, update_json_atomic, write_json_atomic


@pytest.mark.ai_generated
def test_load_json_missing_returns_empty(tmp_path: Path) -> None:
    assert load_json(tmp_path / "does-not-exist.json") == {}


@pytest.mark.ai_generated
def test_load_json_malformed_returns_empty(tmp_path: Path) -> None:
    p = tmp_path / "broken.json"
    p.write_text("{not json")
    assert load_json(p) == {}


@pytest.mark.ai_generated
def test_write_json_atomic_creates_parents(tmp_path: Path) -> None:
    p = tmp_path / "nested" / "dir" / "out.json"
    write_json_atomic(p, {"a": 1})
    assert json.loads(p.read_text()) == {"a": 1}


@pytest.mark.ai_generated
def test_write_json_atomic_leaves_no_tmp_on_success(tmp_path: Path) -> None:
    p = tmp_path / "out.json"
    write_json_atomic(p, {"a": 1})
    assert list(tmp_path.iterdir()) == [p]


@pytest.mark.ai_generated
def test_update_json_atomic_merges(tmp_path: Path) -> None:
    p = tmp_path / "out.json"
    write_json_atomic(p, {"a": 1, "b": 2})

    def mutate(d: dict) -> dict:
        d["c"] = 3
        return d

    result = update_json_atomic(p, mutate)
    assert result == {"a": 1, "b": 2, "c": 3}
    assert json.loads(p.read_text()) == {"a": 1, "b": 2, "c": 3}


@pytest.mark.ai_generated
def test_update_json_atomic_on_missing_file(tmp_path: Path) -> None:
    p = tmp_path / "new.json"

    def mutate(d: dict) -> dict:
        d["stats"] = {"foo": "bar"}
        return d

    result = update_json_atomic(p, mutate)
    assert result == {"stats": {"foo": "bar"}}
    assert p.exists()
