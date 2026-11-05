"""Tests for ``BEPs/dashboard.json`` (consumed by the bids-website BEPs page)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bids_schema.render import bep_dashboard

STATS = {
    "_collected_at": "2026-05-10T00:00:00Z",
    "_complete": True,
    "_error": None,
    "pr_state": "OPEN",
    "reviews": {"approved": 3, "changes_requested": 0, "commented": 1, "dismissed": 5},
    "comments": {"total": 12, "first_at": "2020-01-16T00:00:00Z",
                 "last_at": "2026-05-08T00:00:00Z",
                 "by_author": {"a": {}, "b": {}, "c": {}}},
    "review_threads": {"unresolved": 2},
    "contributors": {"count": 4},
}


@pytest.mark.ai_generated
def test_empty_bep_list() -> None:
    doc = bep_dashboard.render([])
    assert doc["_schema_version"] == bep_dashboard.DASHBOARD_SCHEMA_VERSION
    assert doc["beps"] == {}
    assert doc["data_as_of"] is None


@pytest.mark.ai_generated
def test_joins_pr_stats_and_doc_activity(base_dir: Path, make_pr, make_bep) -> None:
    make_pr(518, stats=STATS)
    make_bep(11, title="Structural preprocessing", pr_number=518,
             google_doc="https://docs.google.com/document/d/1YG2g/",
             bep_registered="2024-06-15T00:00:00Z",
             doc_activity={"last_modified": "2026-05-01T00:00:00Z",
                           "edits_since_last_check": 2,
                           "checked_at": "2026-05-11T00:00:00Z", "_error": None})

    out = bep_dashboard.render_to_disk(base_dir=base_dir)
    assert out == base_dir / "BEPs" / "dashboard.json"
    doc = json.loads(out.read_text())

    entry = doc["beps"]["11"]
    assert entry["bep_number"] == "011"
    assert entry["title"] == "Structural preprocessing"
    assert entry["pr_number"] == 518
    assert entry["pr_url"].endswith("/pull/518")
    assert entry["schema_url"].endswith("/BEPs/11/schema_pp.json")
    assert entry["bep_registered"] == "2024-06-15T00:00:00Z"
    assert entry["doc_activity"]["edits_since_last_check"] == 2

    pr = entry["pr"]
    assert pr["build_status"] == "success"
    assert pr["authors"] == 4            # stats.contributors wins over authors_count
    assert pr["commenters"] == 3
    # Only the displayed review components are exported.
    assert pr["reviews"] == {"approved": 3, "changes_requested": 0, "commented": 1}
    assert pr["unresolved_threads"] == 2
    assert pr["comments"]["total"] == 12
    assert pr["comments"]["last_at"] == "2026-05-08T00:00:00Z"

    # Newest collection timestamp across inputs, not the wall clock.
    assert doc["data_as_of"] == "2026-05-11T00:00:00Z"


@pytest.mark.ai_generated
def test_missing_pr_record_and_doc(base_dir: Path, make_bep) -> None:
    make_bep(21, pr_number=1680)  # no PRs/1680/
    doc = bep_dashboard.render(
        [("21", json.loads((base_dir / "BEPs/21/BEP_METADATA.json").read_text()))],
        base_dir=base_dir,
    )
    entry = doc["beps"]["21"]
    assert entry["pr"] is None
    assert entry["schema_url"] is None
    assert entry["google_doc"] is None
    assert entry["doc_activity"] is None


@pytest.mark.ai_generated
def test_failed_build_has_no_schema_url_and_falls_back_to_seed_authors(
    base_dir: Path, make_pr, make_bep
) -> None:
    make_pr(750, build_status="failed", authors_count=2)  # no stats block
    make_bep(30, pr_number=750)
    doc = json.loads(bep_dashboard.render_to_disk(base_dir=base_dir).read_text())
    entry = doc["beps"]["30"]
    assert entry["schema_url"] is None
    assert entry["pr"]["build_status"] == "failed"
    assert entry["pr"]["authors"] == 2
    assert entry["pr"]["commenters"] is None
    assert entry["pr"]["reviews"] is None


@pytest.mark.ai_generated
def test_output_is_deterministic(base_dir: Path, make_pr, make_bep) -> None:
    make_pr(518, stats=STATS)
    make_bep(11, pr_number=518)
    first = bep_dashboard.render_to_disk(base_dir=base_dir).read_text()
    second = bep_dashboard.render_to_disk(base_dir=base_dir).read_text()
    assert first == second
