"""Tests for shared render formatters."""

from __future__ import annotations

import pytest

from bids_schema.render import formatters as fmt


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
