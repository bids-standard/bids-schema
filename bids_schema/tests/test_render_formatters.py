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
def test_format_date_window() -> None:
    assert fmt.format_date_window(None, None) == "—"
    assert fmt.format_date_window("2020-01-15T09:00:00Z", "2026-05-11T15:27:31Z") == \
        "2020-01-15 → 2026-05-11"


@pytest.mark.ai_generated
def test_format_reviews_empty() -> None:
    assert fmt.format_reviews(None) == "—"
    assert fmt.format_reviews({}) == "—"
    assert fmt.format_reviews({"approved": 0, "changes_requested": 0, "commented": 0}) == "0"


@pytest.mark.ai_generated
def test_format_reviews_populated() -> None:
    assert fmt.format_reviews({"approved": 3, "changes_requested": 2, "commented": 7}) == "3✅/2❌/7💬"


@pytest.mark.ai_generated
def test_format_unresolved() -> None:
    assert fmt.format_unresolved(None) == "—"
    assert fmt.format_unresolved(0) == "0"
    assert fmt.format_unresolved(6) == "**6**"


@pytest.mark.ai_generated
def test_format_activity_span() -> None:
    assert fmt.format_activity_span(None, None, None) == "—"
    assert fmt.format_activity_span(0, None, None) == "—"
    assert fmt.format_activity_span(
        47, "2020-01-16T10:00:00Z", "2026-05-08T18:12:33Z"
    ) == "47 (2020-01-16 → 2026-05-08)"


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
    assert cells == {"reviews": "—", "comments": "—", "unresolved": "—", "commit_window": "—"}


@pytest.mark.ai_generated
def test_format_stats_cells_populated() -> None:
    cells = fmt.format_stats_cells({
        "reviews": {"approved": 3, "changes_requested": 2, "commented": 7},
        "comments": {"total": 47, "first_at": "2020-01-16T00:00:00Z",
                     "last_at": "2026-05-08T00:00:00Z"},
        "review_threads": {"unresolved": 6},
        "commits": {"first_at": "2020-01-15T00:00:00Z", "last_at": "2026-05-11T00:00:00Z"},
    })
    assert cells["reviews"] == "3✅/2❌/7💬"
    assert cells["comments"] == "47 (2020-01-16 → 2026-05-08)"
    assert cells["unresolved"] == "**6**"
    assert cells["commit_window"] == "2020-01-15 → 2026-05-11"


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
