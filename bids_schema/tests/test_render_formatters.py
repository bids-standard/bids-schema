"""Tests for shared render formatters."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from bids_schema.render import formatters as fmt


def _days_ago(n: int) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=n)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")


@pytest.mark.ai_generated
def test_format_date_none() -> None:
    assert fmt.format_date(None) == "—"
    assert fmt.format_date("Unknown") == "—"


@pytest.mark.ai_generated
def test_format_date_iso() -> None:
    assert fmt.format_date("2026-05-11T15:27:31Z") == "2026-05-11"


@pytest.mark.ai_generated
def test_format_reviews_empty() -> None:
    assert fmt.format_reviews(None) == "—"
    assert fmt.format_reviews({}) == "—"
    assert fmt.format_reviews({"approved": 0, "changes_requested": 0, "commented": 0}) == "0"


@pytest.mark.ai_generated
def test_format_reviews_populated() -> None:
    assert fmt.format_reviews({"approved": 3, "changes_requested": 2, "commented": 7}) == "3✅/2❌/7💬"


@pytest.mark.ai_generated
def test_format_reviews_omits_zero_components() -> None:
    """Zero-valued components are dropped rather than rendered as `0✅`."""
    assert fmt.format_reviews({"approved": 1, "changes_requested": 0, "commented": 27}) == "1✅/27💬"
    assert fmt.format_reviews({"approved": 0, "changes_requested": 0, "commented": 5}) == "5💬"
    assert fmt.format_reviews({"approved": 2, "changes_requested": 0, "commented": 0}) == "2✅"
    assert fmt.format_reviews({"approved": 0, "changes_requested": 1, "commented": 8}) == "1❌/8💬"
    # Order stays approved → changes_requested → commented regardless of which drop out
    assert fmt.format_reviews({"approved": 1, "changes_requested": 2, "commented": 3}) == "1✅/2❌/3💬"
    # Missing keys behave like zeros
    assert fmt.format_reviews({"commented": 4}) == "4💬"


@pytest.mark.ai_generated
def test_format_count() -> None:
    assert fmt.format_count(None) == "—"
    assert fmt.format_count(0) == "0"
    assert fmt.format_count(47) == "47"


@pytest.mark.ai_generated
def test_format_unresolved() -> None:
    assert fmt.format_unresolved(None) == "—"
    assert fmt.format_unresolved(0) == "0"
    assert fmt.format_unresolved(6) == "**6**"


@pytest.mark.ai_generated
def test_format_build_indicator() -> None:
    assert fmt.format_build_indicator("success") == "✅"
    assert fmt.format_build_indicator("failed") == "❌"
    assert fmt.format_build_indicator("unknown") == "❓"


@pytest.mark.ai_generated
def test_stale_marker() -> None:
    assert fmt.stale_marker({}) == ""
    assert fmt.stale_marker({"_complete": True}) == ""
    assert fmt.stale_marker({"_complete": False}) == " …"
    assert fmt.stale_marker({"_error": "rate_limit"}) == " ⚠"


@pytest.mark.ai_generated
def test_format_stats_cells_empty_returns_all_dashes() -> None:
    cells = fmt.format_stats_cells({})
    assert set(cells) == set(fmt.STATS_CELL_KEYS)
    assert set(cells.values()) == {"—"}


@pytest.mark.ai_generated
def test_format_stats_cells_populated() -> None:
    cells = fmt.format_stats_cells({
        "pr_created_at": "2018-12-12T18:42:32Z",
        "reviews": {"approved": 3, "changes_requested": 2, "commented": 7},
        "comments": {"total": 47, "first_at": "2020-01-16T00:00:00Z",
                     "last_at": "2026-05-08T00:00:00Z"},
        "review_threads": {"unresolved": 6},
        "commits": {"count": 14, "first_at": "2020-01-15T00:00:00Z",
                    "last_at": "2026-05-11T00:00:00Z"},
    })
    assert set(cells) == set(fmt.STATS_CELL_KEYS)
    assert cells["reviews"] == "3✅/2❌/7💬"
    assert cells["unresolved"] == "**6**"
    assert cells["pr_created"] == "2018-12-12"
    assert cells["commits_count"] == "14"
    assert cells["commits_first"] == "2020-01-15"
    assert cells["commits_last"] == "2026-05-11"
    assert cells["comments_count"] == "47"
    assert cells["comments_first"] == "2020-01-16"
    assert cells["comments_last"] == "2026-05-08"
    assert cells["commenters"] == "—"   # no by_author block in this fixture


@pytest.mark.ai_generated
def test_format_stats_cells_partial_block_dashes_missing_pieces() -> None:
    """A stats block that lacks sub-blocks still yields every key."""
    cells = fmt.format_stats_cells({"reviews": {"approved": 1}})
    assert set(cells) == set(fmt.STATS_CELL_KEYS)
    assert cells["reviews"] == "1✅"
    assert cells["pr_created"] == "—"
    assert cells["commits_count"] == "—"
    assert cells["comments_last"] == "—"


@pytest.mark.ai_generated
def test_format_stats_cells_commenters() -> None:
    cells = fmt.format_stats_cells({
        "comments": {"total": 9, "by_author": {"a": {}, "b": {}, "c": {}}},
    })
    assert cells["commenters"] == "3"
    # `by_author` absent (v1 / uncollected) is "not known", not "zero"
    assert fmt.format_stats_cells({"comments": {"total": 9}})["commenters"] == "—"
    assert fmt.format_stats_cells({"comments": {"by_author": {}}})["commenters"] == "0"


@pytest.mark.ai_generated
def test_format_contributors_prefers_collected_stats() -> None:
    """stats.contributors.count wins over the stale build-time authors_count."""
    record = {
        "authors_count": 2,
        "stats": {"contributors": {"count": 5}},
    }
    assert fmt.format_contributors(record) == "5"


@pytest.mark.ai_generated
def test_format_contributors_falls_back_to_authors_count() -> None:
    assert fmt.format_contributors({"authors_count": 2}) == "2"
    assert fmt.format_contributors({"authors_count": 0}) == "—"
    assert fmt.format_contributors({}) == "—"


@pytest.mark.ai_generated
def test_format_contributors_zero_from_stats_is_not_dash() -> None:
    """A collected count of 0 is a real answer and must not read as uncollected."""
    assert fmt.format_contributors({"stats": {"contributors": {"count": 0}}}) == "0"


@pytest.mark.ai_generated
def test_format_build_cell_success_no_stats() -> None:
    assert fmt.format_build_cell({"build_status": "success"}) == "✅"


@pytest.mark.ai_generated
def test_format_build_cell_with_stale_marker() -> None:
    assert fmt.format_build_cell({
        "build_status": "success",
        "stats": {"_error": "rate_limit"},
    }) == "✅ ⚠"


@pytest.mark.ai_generated
def test_format_actions_cell_success() -> None:
    s = fmt.format_actions_cell("PRs", "518", build_status="success")
    assert "[Schema](./518/schema.json)" in s
    assert "/PRs/518/schema.json" in s
    assert "/PRs/518/schema_pp.json" in s
    assert "Error Log" not in s


@pytest.mark.ai_generated
def test_format_actions_cell_failed_local_error_log() -> None:
    s = fmt.format_actions_cell("PRs", "750", build_status="failed",
                                error_log="bst-output.log")
    assert "[Error Log](./750/bst-output.log)" in s


@pytest.mark.ai_generated
def test_format_actions_cell_failed_bep_error_log_href() -> None:
    """BEP renderer supplies a relative href pointing at sibling PR folder."""
    s = fmt.format_actions_cell("BEPs", "11", build_status="failed",
                                error_log="bst-output.log",
                                error_log_href="../PRs/518/bst-output.log")
    assert "[Error Log](../PRs/518/bst-output.log)" in s


@pytest.mark.ai_generated
def test_bep_activity_badge_unknown_when_never_modified() -> None:
    badge = fmt.bep_activity_badge(None)
    assert badge == {"icon": "\N{MEDIUM WHITE CIRCLE}", "label": "Unknown", "category": "unknown"}


@pytest.mark.ai_generated
def test_bep_activity_badge_fresh() -> None:
    badge = fmt.bep_activity_badge(_days_ago(5))
    assert badge["icon"] == "\N{LARGE GREEN CIRCLE}"
    assert badge["category"] == "fresh"
    assert "5 days ago" in badge["label"]


@pytest.mark.ai_generated
def test_bep_activity_badge_active() -> None:
    badge = fmt.bep_activity_badge(_days_ago(90))
    assert badge["icon"] == "\N{LARGE YELLOW CIRCLE}"
    assert badge["category"] == "active"


@pytest.mark.ai_generated
def test_bep_activity_badge_stale() -> None:
    badge = fmt.bep_activity_badge(_days_ago(400))
    assert badge["icon"] == "\N{LARGE RED CIRCLE}"
    assert badge["category"] == "stale"


@pytest.mark.ai_generated
def test_bep_activity_badge_appends_edit_count() -> None:
    badge = fmt.bep_activity_badge(_days_ago(1), edits_since_last_check=3)
    assert "1 day ago" in badge["label"]
    assert "(+3 edits)" in badge["label"]


@pytest.mark.ai_generated
def test_bep_activity_badge_omits_edit_count_when_zero_or_none() -> None:
    assert "(+" not in fmt.bep_activity_badge(_days_ago(1), edits_since_last_check=0)["label"]
    assert "(+" not in fmt.bep_activity_badge(_days_ago(1), edits_since_last_check=None)["label"]


@pytest.mark.ai_generated
def test_raw_branch_env_override(monkeypatch) -> None:
    # BIDS_SCHEMA_RAW_BRANCH is read at import time; assert current value
    # is either the module default ("main") or whatever the env said at import.
    import importlib
    monkeypatch.setenv("BIDS_SCHEMA_RAW_BRANCH", "some-feature-branch")
    from bids_schema.render import formatters
    importlib.reload(formatters)
    try:
        assert formatters.RAW_BRANCH == "some-feature-branch"
        assert "some-feature-branch" in formatters.raw_url("PRs", "1", "schema.json")
    finally:
        # Restore module default for later tests
        monkeypatch.delenv("BIDS_SCHEMA_RAW_BRANCH", raising=False)
        importlib.reload(formatters)
