"""Tests for the PR README renderer."""

from __future__ import annotations

from pathlib import Path

import pytest

from bids_schema.render import pr_readme


@pytest.mark.ai_generated
def test_empty_pr_list_still_renders() -> None:
    body = pr_readme.render([])
    assert "*No PR schemas currently available*" in body
    assert "# BIDS Specification PR Schemas" in body


@pytest.mark.ai_generated
def test_v1_record_renders_dashes_in_new_columns() -> None:
    body = pr_readme.render([("518", {
        "pr_number": "518",
        "last_commit": "8bcb4d678f0de6a7f34f775fbbc80468ad618f5f",
        "build_status": "success",
        "authors_count": 2,
    })])
    row = next(line for line in body.splitlines() if line.startswith("| [518]"))
    # Split into cells (drop empty first/last from leading/trailing `|`)
    cells = [c.strip() for c in row.split("|")[1:-1]]
    # Layout: PR # | Authors | Build | Reviews | Comments | Unresolved | Commit window | Last commit | Actions
    assert cells[0].startswith("[518]")
    assert cells[1] == "2"
    assert cells[2] == "✅"
    # New v2 columns: reviews, comments, unresolved, commit window — all "—" for v1 record
    assert cells[3] == "—"
    assert cells[4] == "—"
    assert cells[5] == "—"
    assert cells[6] == "—"
    assert cells[7].startswith("[8bcb4d678f]")


@pytest.mark.ai_generated
def test_v2_record_renders_stats() -> None:
    body = pr_readme.render([("518", {
        "_schema_version": 2,
        "pr_number": "518",
        "last_commit": "8bcb4d678f0de6a7f34f775fbbc80468ad618f5f",
        "build_status": "success",
        "authors_count": 2,
        "stats": {
            "_complete": True,
            "_error": None,
            "reviews": {"approved": 3, "changes_requested": 2, "commented": 7},
            "comments": {"total": 47, "first_at": "2020-01-16T00:00:00Z",
                         "last_at": "2026-05-08T00:00:00Z"},
            "review_threads": {"unresolved": 6},
            "commits": {"count": 14, "first_at": "2020-01-15T09:00:00Z",
                        "last_at": "2026-05-11T15:00:00Z"},
        },
    })])
    row = next(line for line in body.splitlines() if line.startswith("| [518]"))
    assert "3✅/2❌/7💬" in row
    assert "**6**" in row
    assert "47 (2020-01-16 → 2026-05-08)" in row
    assert "2020-01-15 → 2026-05-11" in row


@pytest.mark.ai_generated
def test_stats_error_puts_warning_marker() -> None:
    body = pr_readme.render([("518", {
        "_schema_version": 2,
        "pr_number": "518",
        "last_commit": "8bcb4d678f0de6a7f34f775fbbc80468ad618f5f",
        "build_status": "success",
        "authors_count": 2,
        "stats": {"_complete": False, "_error": "rate_limit"},
    })])
    row = next(line for line in body.splitlines() if line.startswith("| [518]"))
    assert " ⚠" in row


@pytest.mark.ai_generated
def test_render_to_disk_writes_file(base_dir: Path, make_pr) -> None:
    make_pr(518, build_status="success", authors_count=2)
    make_pr(1108, build_status="failed", error_log="bst-output.log")
    out = pr_readme.render_to_disk(base_dir=base_dir)
    assert out == base_dir / "PRs" / "README.md"
    body = out.read_text()
    assert "[518]" in body
    assert "[1108]" in body
    # Sorted numerically
    assert body.index("[518]") < body.index("[1108]")
    # Failed row keeps error-log link
    assert "Error Log" in body
