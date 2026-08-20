"""Shared test fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def base_dir(tmp_path: Path) -> Path:
    """Ephemeral base_dir mimicking the repo layout (PRs/ + BEPs/)."""
    (tmp_path / "PRs").mkdir()
    (tmp_path / "BEPs").mkdir()
    return tmp_path


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


@pytest.fixture
def make_pr(base_dir: Path):
    """Factory: `make_pr(number, **fields)` writes a PR_METADATA.json."""

    def _make(number: int | str, **fields) -> Path:
        default = {
            "pr_number": str(number),
            "git_ref": "deadbeef",
            "last_commit": "deadbeef" + "0" * 32,
            "last_updated": "2026-05-11T15:27:31Z",
            "has_schema_changes": True,
            "build_status": "success",
            "authors_count": 1,
        }
        default.update(fields)
        path = base_dir / "PRs" / str(number) / "PR_METADATA.json"
        _write_json(path, default)
        return path

    return _make


@pytest.fixture
def make_bep(base_dir: Path):
    """Factory: `make_bep(number, **fields)` writes a BEP_METADATA.json."""

    def _make(number: int | str, **fields) -> Path:
        default = {
            "bep_number": str(number),
            "title": f"Test BEP {number}",
            "pr_number": 999,
            "pull_request": "https://github.com/bids-standard/bids-specification/pull/999",
            "google_doc": "",
            "status": "review",
            "authors_count": 1,
        }
        default.update(fields)
        path = base_dir / "BEPs" / str(number) / "BEP_METADATA.json"
        _write_json(path, default)
        return path

    return _make
