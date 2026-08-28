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


#: Column order of the rendered PR table, for index-based cell assertions.
COLUMNS = [
    "PR #", "# Authors", "# Commenters", "Build", "Created", "Reviews", "Unresolved",
    "Commits", "First commit", "Last commit",
    "Comments", "First comment", "Last comment", "Head", "Actions",
]


def _cells(row: str) -> list[str]:
    """Split a Markdown row into cells (dropping the leading/trailing `|`)."""
    return [c.strip() for c in row.split("|")[1:-1]]


@pytest.mark.ai_generated
def test_table_header_matches_expected_columns() -> None:
    header_row = pr_readme.TABLE_HEADER.splitlines()[0]
    assert _cells(header_row) == COLUMNS


@pytest.mark.ai_generated
def test_v1_record_renders_dashes_in_new_columns() -> None:
    body = pr_readme.render([("518", {
        "pr_number": "518",
        "last_commit": "8bcb4d678f0de6a7f34f775fbbc80468ad618f5f",
        "build_status": "success",
        "authors_count": 2,
    })])
    row = next(line for line in body.splitlines() if line.startswith("| [518]"))
    cells = dict(zip(COLUMNS, _cells(row)))
    assert cells["PR #"].startswith("[518]")
    # v1 record has no stats, so the build-time authors_count is the fallback
    assert cells["# Authors"] == "2"
    assert cells["Build"] == "✅"
    # Every stats-derived column is "—" for a v1 record
    for col in ("# Commenters", "Created", "Reviews", "Unresolved", "Commits",
                "First commit", "Last commit", "Comments", "First comment",
                "Last comment"):
        assert cells[col] == "—", col
    assert cells["Head"].startswith("[8bcb4d678f]")


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
            "pr_created_at": "2020-06-30T19:44:32Z",
            "reviews": {"approved": 3, "changes_requested": 2, "commented": 7},
            "comments": {"total": 47, "first_at": "2020-01-16T00:00:00Z",
                         "last_at": "2026-05-08T00:00:00Z",
                         "by_author": {"a": {}, "b": {}, "c": {}, "d": {}}},
            "review_threads": {"unresolved": 6},
            "commits": {"count": 14, "first_at": "2020-01-15T09:00:00Z",
                        "last_at": "2026-05-11T15:00:00Z"},
            "contributors": {"count": 5, "authors": 4, "committers": 2},
        },
    })])
    row = next(line for line in body.splitlines() if line.startswith("| [518]"))
    cells = dict(zip(COLUMNS, _cells(row)))
    # Collected contributor count supersedes the build-time authors_count of 2
    assert cells["# Authors"] == "5"
    assert cells["# Commenters"] == "4"
    assert cells["Created"] == "2020-06-30"
    assert cells["Reviews"] == "3✅/2❌/7💬"
    assert cells["Unresolved"] == "**6**"
    assert cells["Commits"] == "14"
    assert cells["First commit"] == "2020-01-15"
    assert cells["Last commit"] == "2026-05-11"
    assert cells["Comments"] == "47"
    assert cells["First comment"] == "2020-01-16"
    assert cells["Last comment"] == "2026-05-08"


@pytest.mark.ai_generated
def test_reviews_cell_drops_zero_components() -> None:
    body = pr_readme.render([("352", {
        "_schema_version": 2,
        "pr_number": "352",
        "last_commit": "376e7696b0bbfeb7b2347989beabec5f9833e59e",
        "build_status": "success",
        "authors_count": 2,
        "stats": {
            "_complete": True,
            "_error": None,
            "reviews": {"approved": 1, "changes_requested": 0, "commented": 27},
        },
    })])
    row = next(line for line in body.splitlines() if line.startswith("| [352]"))
    assert "1✅/27💬" in row
    assert "0❌" not in row


@pytest.mark.ai_generated
def test_force_pushed_pr_shows_created_before_first_commit() -> None:
    """Regression guard for PR #105: comments predate every surviving commit.

    A force-push replaced the branch's original commits, so ``First commit``
    is years after the PR was opened. ``Created`` must still show the PR's
    real start date, which is not later than the first comment.
    """
    body = pr_readme.render([("105", {
        "_schema_version": 2,
        "pr_number": "105",
        "last_commit": "fc5f90ce1010d915b4f2d241efc5df1904756276",
        "build_status": "success",
        "authors_count": 1,
        "stats": {
            "_complete": True,
            "_error": None,
            "pr_created_at": "2018-12-12T18:42:32Z",
            "comments": {"total": 49, "first_at": "2018-12-12T18:52:00Z",
                         "last_at": "2024-06-26T12:08:03Z"},
            "commits": {"count": 5, "first_at": "2022-04-22T18:53:57Z",
                        "last_at": "2023-03-13T20:07:24Z"},
        },
    })])
    row = next(line for line in body.splitlines() if line.startswith("| [105]"))
    cells = dict(zip(COLUMNS, _cells(row)))
    assert cells["Created"] == "2018-12-12"
    assert cells["First comment"] == "2018-12-12"
    assert cells["First commit"] == "2022-04-22"
    assert cells["Created"] <= cells["First comment"] < cells["First commit"]
    # The README explains the discrepancy rather than leaving it looking like a bug
    assert "force-push" in body


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
