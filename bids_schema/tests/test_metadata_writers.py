"""Tests for the canonical PR/BEP metadata writers + iter_numeric_subdirs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bids_schema.metadata.io import (
    iter_numeric_subdirs,
    write_bep_metadata,
    write_pr_metadata,
)


@pytest.mark.ai_generated
def test_iter_numeric_subdirs_filters_and_sorts(tmp_path: Path) -> None:
    for name in ["10", "2", "100", "not-a-number", "README.md"]:
        (tmp_path / name).mkdir()
    (tmp_path / "3.txt").write_text("not a dir")
    result = iter_numeric_subdirs(tmp_path)
    assert [p.name for p in result] == ["2", "10", "100"]


@pytest.mark.ai_generated
def test_iter_numeric_subdirs_missing_root(tmp_path: Path) -> None:
    assert iter_numeric_subdirs(tmp_path / "does-not-exist") == []


@pytest.mark.ai_generated
def test_iter_numeric_subdirs_empty(tmp_path: Path) -> None:
    assert iter_numeric_subdirs(tmp_path) == []


@pytest.mark.ai_generated
def test_write_pr_metadata_success(tmp_path: Path) -> None:
    write_pr_metadata(
        tmp_path,
        pr_number="518", git_ref="refs/pull/origin/518/merge",
        last_commit="deadbeef" + "0" * 32, authors_count=2,
        build_status="success",
    )
    data = json.loads((tmp_path / "PR_METADATA.json").read_text())
    assert data["_schema_version"] == 2
    assert data["pr_number"] == "518"
    assert data["build_status"] == "success"
    assert data["authors_count"] == 2
    assert data["has_schema_changes"] is True
    assert "error_message" not in data
    assert "error_log" not in data


@pytest.mark.ai_generated
def test_write_pr_metadata_failure_includes_error_fields(tmp_path: Path) -> None:
    write_pr_metadata(
        tmp_path,
        pr_number="750", git_ref="x", last_commit="y",
        authors_count=1,
        build_status="failed",
        error_message="ValueError: broken schema",
        error_log="bst-output.log",
    )
    data = json.loads((tmp_path / "PR_METADATA.json").read_text())
    assert data["build_status"] == "failed"
    assert data["error_message"] == "ValueError: broken schema"
    assert data["error_log"] == "bst-output.log"


@pytest.mark.ai_generated
def test_write_pr_metadata_rejects_bad_status(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        write_pr_metadata(
            tmp_path, pr_number="1", git_ref="x", last_commit="y",
            authors_count=0, build_status="pending",
        )


@pytest.mark.ai_generated
def test_write_bep_metadata(tmp_path: Path) -> None:
    write_bep_metadata(
        tmp_path,
        bep_number="11", title="Structural preprocessing",
        pr_number=518,
        pull_request="https://github.com/bids-standard/bids-specification/pull/518",
        google_doc="https://docs.google.com/document/d/AAA/",
        authors_count=2,
    )
    data = json.loads((tmp_path / "BEP_METADATA.json").read_text())
    assert data["_schema_version"] == 3
    assert data["bep_number"] == "11"
    assert data["pr_number"] == 518  # int per contract
    assert data["title"] == "Structural preprocessing"
    assert data["status"] == "review"
