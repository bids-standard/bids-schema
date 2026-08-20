"""Tests for the pure-function core of the GraphQL collector.

The `gh api graphql` transport layer is not exercised here; it is
tested manually against a live token. This suite covers the
paginated-response-to-stats-dict transformation, which is the piece
that most benefits from unit coverage.
"""

from __future__ import annotations

import pytest

from bids_schema.collect import github


@pytest.mark.ai_generated
def test_effective_state_walks_backward_past_dismissed_and_commented() -> None:
    # Newest → oldest: DISMISSED (skip), COMMENTED (skip), APPROVED (take)
    entries = [
        ("2026-01-01T00:00:00Z", "APPROVED"),
        ("2026-02-01T00:00:00Z", "COMMENTED"),
        ("2026-03-01T00:00:00Z", "DISMISSED"),
    ]
    assert github._effective_state(entries) == "APPROVED"


@pytest.mark.ai_generated
def test_effective_state_none_when_only_commented() -> None:
    entries = [
        ("2026-01-01T00:00:00Z", "COMMENTED"),
        ("2026-02-01T00:00:00Z", "COMMENTED"),
    ]
    assert github._effective_state(entries) is None


@pytest.mark.ai_generated
def test_effective_state_prefers_most_recent_actionable() -> None:
    entries = [
        ("2026-01-01T00:00:00Z", "APPROVED"),
        ("2026-02-01T00:00:00Z", "CHANGES_REQUESTED"),
    ]
    assert github._effective_state(entries) == "CHANGES_REQUESTED"


@pytest.mark.ai_generated
def test_min_max_ignores_none_values() -> None:
    assert github._min_max([None, "2026-01-05T00:00:00Z", None, "2020-01-01T00:00:00Z"]) == \
        ("2020-01-01T00:00:00Z", "2026-01-05T00:00:00Z")
    assert github._min_max([None, None]) == (None, None)


@pytest.mark.ai_generated
def test_derive_stats_end_to_end() -> None:
    fetched = {
        "pr_meta": {
            "state": "OPEN",
            "createdAt": "2020-01-15T09:12:03Z",
            "updatedAt": "2026-05-11T15:27:31Z",
            "reviewDecision": "CHANGES_REQUESTED",
            "headRefOid": "abc123",
        },
        "commits": [
            {"authoredDate": "2020-01-15T09:12:03Z", "committedDate": "2020-01-15T09:12:03Z", "login": "alice"},
            {"authoredDate": "2026-05-11T15:27:31Z", "committedDate": "2026-05-11T15:27:31Z", "login": "bob"},
        ],
        "reviews": [
            {"state": "APPROVED", "submittedAt": "2025-02-01T10:00:00Z", "login": "alice"},
            {"state": "COMMENTED", "submittedAt": "2026-05-08T14:00:00Z", "login": "alice"},
            {"state": "CHANGES_REQUESTED", "submittedAt": "2025-03-11T09:00:00Z", "login": "bob"},
            {"state": "APPROVED", "submittedAt": "2026-05-10T18:00:00Z", "login": "bob"},
        ],
        "issue_comments": [
            {"createdAt": "2020-01-16T10:00:00Z", "login": "alice"},
            {"createdAt": "2020-01-18T08:00:00Z", "login": "bob"},
        ],
        "review_threads": [
            {
                "id": "t1", "isResolved": False, "isOutdated": False,
                "comment_count": 3,
                "first_comment": {"createdAt": "2024-11-01T12:00:00Z", "login": "alice"},
                "comments_truncated": False, "_paginated": False,
            },
            {
                "id": "t2", "isResolved": False, "isOutdated": True,
                "comment_count": 2,
                "first_comment": {"createdAt": "2024-10-11T09:30:00Z", "login": "bob"},
                "comments_truncated": False, "_paginated": False,
            },
            {
                "id": "t3", "isResolved": True, "isOutdated": False,
                "comment_count": 1,
                "first_comment": {"createdAt": "2023-01-01T00:00:00Z", "login": "alice"},
                "comments_truncated": False, "_paginated": False,
            },
        ],
        "_complete": True,
        "_error": None,
    }

    stats = github.derive_stats(fetched, source_head_sha="abc123")

    # Meta
    assert stats["_source_head_sha"] == "abc123"
    assert stats["_complete"] is True
    assert stats["_error"] is None
    assert stats["pr_state"] == "OPEN"
    assert stats["review_decision"] == "CHANGES_REQUESTED"

    # commits
    assert stats["commits"]["count"] == 2
    assert stats["commits"]["first_at"] == "2020-01-15T09:12:03Z"
    assert stats["commits"]["last_at"] == "2026-05-11T15:27:31Z"

    # reviews aggregate
    assert stats["reviews"]["approved"] == 2
    assert stats["reviews"]["commented"] == 1
    assert stats["reviews"]["changes_requested"] == 1
    assert stats["reviews"]["total"] == 4

    # reviews by author — alice's most recent is COMMENTED → last_state COMMENTED,
    # but effective_state should be APPROVED (walk back past COMMENTED).
    alice = stats["reviews"]["by_author"]["alice"]
    assert alice["approved"] == 1
    assert alice["commented"] == 1
    assert alice["last_state"] == "COMMENTED"
    assert alice["effective_state"] == "APPROVED"

    # bob: most recent is APPROVED; effective same.
    bob = stats["reviews"]["by_author"]["bob"]
    assert bob["approved"] == 1
    assert bob["changes_requested"] == 1
    assert bob["last_state"] == "APPROVED"
    assert bob["effective_state"] == "APPROVED"

    # comments (issue + first-of-thread)
    # 2 issue comments + 3 threads with first_comment → 5 events
    assert stats["comments"]["issue_count"] == 2
    assert stats["comments"]["review_thread_count"] == 6  # 3+2+1
    assert stats["comments"]["total"] == 8
    assert stats["comments"]["first_at"] == "2020-01-16T10:00:00Z" or \
           stats["comments"]["first_at"] == "2023-01-01T00:00:00Z" or \
           stats["comments"]["first_at"] == "2024-10-11T09:30:00Z"
    # actually first is the earliest across issue-comments + first-comments:
    # earliest is 2020-01-16 (issue comment)
    assert stats["comments"]["first_at"] == "2020-01-16T10:00:00Z"

    # review threads
    assert stats["review_threads"]["total"] == 3
    assert stats["review_threads"]["unresolved"] == 2
    assert stats["review_threads"]["unresolved_active"] == 1
    assert stats["review_threads"]["unresolved_outdated"] == 1
    # unresolved_by_author only counts unresolved threads (t1 alice, t2 bob)
    assert stats["review_threads"]["unresolved_by_author"]["alice"]["count"] == 1
    assert stats["review_threads"]["unresolved_by_author"]["bob"]["count"] == 1


@pytest.mark.ai_generated
def test_derive_stats_uses_ghost_for_missing_login() -> None:
    fetched = {
        "pr_meta": {"state": "OPEN", "headRefOid": "x"},
        "commits": [],
        "reviews": [{"state": "APPROVED", "submittedAt": "2026-01-01T00:00:00Z", "login": None}],
        "issue_comments": [{"createdAt": "2026-01-02T00:00:00Z", "login": None}],
        "review_threads": [],
        "_complete": True, "_error": None,
    }
    stats = github.derive_stats(fetched, source_head_sha="x")
    assert "ghost" in stats["reviews"]["by_author"]
    assert "ghost" in stats["comments"]["by_author"]


@pytest.mark.ai_generated
def test_is_fresh_gate() -> None:
    from datetime import datetime, timezone
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    fresh = {
        "_complete": True, "_error": None,
        "_source_head_sha": "abc", "_collected_at": now_iso,
    }
    assert github._is_fresh(fresh, "abc") is True
    # Head moved → not fresh
    assert github._is_fresh(fresh, "def") is False
    # Incomplete → not fresh
    assert github._is_fresh({**fresh, "_complete": False}, "abc") is False
    # Error → not fresh
    assert github._is_fresh({**fresh, "_error": "rate_limit"}, "abc") is False
    # Empty → not fresh
    assert github._is_fresh({}, "abc") is False


@pytest.mark.ai_generated
def test_classify_error() -> None:
    assert github._classify_error("Something rate limit hit") == "rate_limit"
    assert github._classify_error("Not Found") == "not_found"
    assert github._classify_error("GraphQL parse error") == "graphql_error"
    assert github._classify_error("network unreachable") == "network_error"
