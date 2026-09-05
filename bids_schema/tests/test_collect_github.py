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
            {"authoredDate": "2020-01-15T09:12:03Z", "committedDate": "2020-01-15T09:12:03Z",
             "login": "alice",
             "author":    {"name": "Alice", "email": "alice@example.org", "login": "alice"},
             "committer": {"name": "Alice", "email": "alice@example.org", "login": "alice"}},
            {"authoredDate": "2026-05-11T15:27:31Z", "committedDate": "2026-05-11T15:27:31Z",
             "login": "bob",
             "author":    {"name": "Bob", "email": "bob@example.org", "login": "bob"},
             "committer": {"name": "Alice", "email": "alice@example.org", "login": "alice"}},
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

    # contributors — alice authored one and committed both, bob authored one
    assert stats["contributors"]["count"] == 2
    assert stats["contributors"]["authors"] == 2
    assert stats["contributors"]["committers"] == 1
    assert stats["contributors"]["by_identity"]["alice"]["committed"] == 2

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
    assert github._classify_error("rate_limit_ceiling: reset in 3600s") == "rate_limit_ceiling"
    assert github._classify_error("Not Found") == "not_found"
    assert github._classify_error("GraphQL parse error") == "graphql_error"
    assert github._classify_error("network unreachable") == "network_error"


@pytest.mark.ai_generated
def test_build_preflight_query_aliases(monkeypatch) -> None:
    query = github._build_preflight_query([1, 42, 999])
    assert "pr1: pullRequest(number:1)" in query
    assert "pr42: pullRequest(number:42)" in query
    assert "pr999: pullRequest(number:999)" in query
    # Only 2 top-level vars (owner + name) — no per-PR $number$
    assert "$owner" in query and "$name" in query


@pytest.mark.ai_generated
def test_preflight_head_shas_batched(monkeypatch) -> None:
    calls = []

    def fake_run(query: str, variables: dict) -> dict:
        calls.append(query)
        # Return a synthetic response with all requested aliases
        aliased = {}
        # Very shallow parser: look for `pr<N>:` in the query text
        import re
        for pr in re.findall(r"pr(\d+):", query):
            aliased[f"pr{pr}"] = {"headRefOid": f"sha_{pr}", "state": "OPEN"}
        return {"repository": aliased, "rateLimit": {"remaining": 5000}}

    monkeypatch.setattr(github, "_run_gh_graphql", fake_run)
    monkeypatch.setattr(github, "PREFLIGHT_BATCH", 3)  # force 2 chunks for 5 PRs
    result = github.preflight_head_shas([1, 2, 3, 4, 5])

    assert len(calls) == 2  # 5 PRs / batch of 3 = 2 round trips
    assert result == {
        1: {"headRefOid": "sha_1", "state": "OPEN"},
        2: {"headRefOid": "sha_2", "state": "OPEN"},
        3: {"headRefOid": "sha_3", "state": "OPEN"},
        4: {"headRefOid": "sha_4", "state": "OPEN"},
        5: {"headRefOid": "sha_5", "state": "OPEN"},
    }


@pytest.mark.ai_generated
def test_preflight_falls_back_per_pr_on_batch_failure(monkeypatch) -> None:
    """If a batch fails as a whole, we retry per-PR so one bad number
    doesn't blind the freshness gate for the whole cohort."""
    call_count = {"total": 0}

    def fake_run(query: str, variables: dict) -> dict:
        call_count["total"] += 1
        # First call (the batch) raises; subsequent per-PR calls succeed
        import re
        prs = re.findall(r"pr(\d+):", query)
        if call_count["total"] == 1 and len(prs) > 1:
            raise github.GHError("simulated batch failure")
        # Per-PR fallback: return a response
        return {
            "repository": {f"pr{pr}": {"headRefOid": f"sha_{pr}", "state": "OPEN"} for pr in prs},
            "rateLimit": {"remaining": 5000},
        }

    monkeypatch.setattr(github, "_run_gh_graphql", fake_run)
    monkeypatch.setattr(github, "PREFLIGHT_BATCH", 10)
    result = github.preflight_head_shas([1, 2, 3])
    assert result == {
        1: {"headRefOid": "sha_1", "state": "OPEN"},
        2: {"headRefOid": "sha_2", "state": "OPEN"},
        3: {"headRefOid": "sha_3", "state": "OPEN"},
    }


@pytest.mark.ai_generated
def test_maybe_wait_for_rate_limit_raises_ceiling(monkeypatch) -> None:
    """When the rate-limit reset is farther than max sleep budget,
    raise rate_limit_ceiling instead of sleeping."""
    from datetime import datetime, timezone, timedelta

    # Reset time is 2 hours in the future — well past MAX_SLEEP (20 min)
    reset_future = (datetime.now(timezone.utc) + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    with pytest.raises(github.GHError, match="rate_limit_ceiling"):
        github._maybe_wait_for_rate_limit({"remaining": 5, "resetAt": reset_future})


@pytest.mark.ai_generated
def test_maybe_wait_for_rate_limit_no_op_when_headroom(monkeypatch) -> None:
    """No sleep, no raise if remaining is above threshold."""
    slept = []
    monkeypatch.setattr(github.time, "sleep", lambda s: slept.append(s))
    github._maybe_wait_for_rate_limit({"remaining": 4999, "resetAt": "2099-01-01T00:00:00Z"})
    assert slept == []


@pytest.mark.ai_generated
def test_write_error_stats_preserves_previously_good_data(tmp_path, monkeypatch) -> None:
    """A transient failure must not wipe an earlier successful stats block."""
    import json
    pr_dir = tmp_path / "PRs" / "518"
    pr_dir.mkdir(parents=True)
    good_record = {
        "_schema_version": 2,
        "pr_number": "518",
        "build_status": "success",
        "authors_count": 2,
        "stats": {
            "_complete": True, "_error": None,
            "_source_head_sha": "abc123",
            "_collected_at": "2026-08-01T00:00:00Z",
            "reviews": {"approved": 3, "changes_requested": 0, "commented": 1, "total": 4},
            "commits": {"count": 5, "first_at": "x", "last_at": "y"},
        },
    }
    (pr_dir / "PR_METADATA.json").write_text(json.dumps(good_record))

    github._write_error_stats(pr_dir / "PR_METADATA.json", good_record, "rate_limit", "def456")

    reloaded = json.loads((pr_dir / "PR_METADATA.json").read_text())
    stats = reloaded["stats"]
    assert stats["_error"] == "rate_limit"
    assert stats["_complete"] is False
    # Preserved:
    assert stats["reviews"]["total"] == 4
    assert stats["commits"]["count"] == 5
    # _source_head_sha kept if already present (never blindly overwritten)
    assert stats["_source_head_sha"] == "abc123"


@pytest.mark.ai_generated
def test_write_error_stats_on_bare_record(tmp_path) -> None:
    """Fresh record (no prior stats) still gets a minimal stats stub."""
    import json
    pr_dir = tmp_path / "PRs" / "999"
    pr_dir.mkdir(parents=True)
    record = {"pr_number": "999"}
    (pr_dir / "PR_METADATA.json").write_text(json.dumps(record))

    github._write_error_stats(pr_dir / "PR_METADATA.json", record, "network_error", None)

    reloaded = json.loads((pr_dir / "PR_METADATA.json").read_text())
    assert reloaded["stats"]["_error"] == "network_error"
    assert reloaded["stats"]["_complete"] is False
    assert reloaded["_schema_version"] == 2


@pytest.mark.ai_generated
def test_collect_only_filters_scope(tmp_path, monkeypatch) -> None:
    """github.collect(only=[...]) restricts which PRs are queried."""
    import json
    # Two PRs on disk
    for n in (100, 200):
        d = tmp_path / "PRs" / str(n)
        d.mkdir(parents=True)
        (d / "PR_METADATA.json").write_text(json.dumps({"pr_number": str(n)}))

    queried: list[int] = []

    def fake_run(query, variables):
        # For preflight, return a matching alias for whatever was requested
        if "headRefOid state" in query and "query" in query:
            import re
            aliased = {}
            for pr in re.findall(r"pr(\d+):", query):
                aliased[f"pr{pr}"] = {"headRefOid": f"sha_{pr}", "state": "OPEN"}
            return {"repository": aliased, "rateLimit": {"remaining": 5000}}
        # Full query — record which PR
        if "commits(first:100" in query:
            queried.append(int(variables["number"]))
            return {
                "repository": {
                    "pullRequest": {
                        "state": "OPEN", "createdAt": "2020-01-01T00:00:00Z",
                        "updatedAt": "2020-01-02T00:00:00Z", "reviewDecision": None,
                        "headRefOid": "any",
                        "commits":       {"totalCount": 0, "pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": []},
                        "reviews":       {"totalCount": 0, "pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": []},
                        "comments":      {"totalCount": 0, "pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": []},
                        "reviewThreads": {"totalCount": 0, "pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": []},
                    },
                },
                "rateLimit": {"remaining": 5000},
            }
        return {"repository": {}, "rateLimit": {"remaining": 5000}}

    monkeypatch.setattr(github.shutil, "which", lambda cmd: "/usr/bin/gh" if cmd == "gh" else None)
    monkeypatch.setattr(github, "_run_gh_graphql", fake_run)

    rc = github.collect(only=["100"], base_dir=tmp_path, force=True)
    assert rc == 0
    assert queried == [100]  # PR 200 not touched


@pytest.mark.ai_generated
def test_paginate_pr_follows_commit_cursors(monkeypatch) -> None:
    """`_paginate_pr` follows `hasNextPage` on `commits` across two pages."""
    call_ix = {"i": 0}

    def fake_run(query, variables):
        call_ix["i"] += 1
        if call_ix["i"] == 1:
            # First page: commits has 2 entries and a next page
            return {
                "repository": {
                    "pullRequest": {
                        "state": "OPEN", "createdAt": "x", "updatedAt": "y",
                        "reviewDecision": None, "headRefOid": "sha",
                        "commits": {
                            "totalCount": 3,
                            "pageInfo": {"hasNextPage": True, "endCursor": "cursor1"},
                            "nodes": [
                                {"commit": {"authoredDate": "2020-01-01T00:00:00Z",
                                            "committedDate": "2020-01-01T00:00:00Z",
                                            "author": {"user": {"login": "a"}}}},
                                {"commit": {"authoredDate": "2020-01-02T00:00:00Z",
                                            "committedDate": "2020-01-02T00:00:00Z",
                                            "author": {"user": {"login": "b"}}}},
                            ],
                        },
                        "reviews":       {"totalCount": 0, "pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": []},
                        "comments":      {"totalCount": 0, "pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": []},
                        "reviewThreads": {"totalCount": 0, "pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": []},
                    },
                },
                "rateLimit": {"remaining": 5000},
            }
        # Second page: one more commit; connection exhausted.
        return {
            "repository": {
                "pullRequest": {
                    "state": "OPEN", "createdAt": "x", "updatedAt": "y",
                    "reviewDecision": None, "headRefOid": "sha",
                    "commits": {
                        "totalCount": 3,
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                        "nodes": [
                            {"commit": {"authoredDate": "2020-01-03T00:00:00Z",
                                        "committedDate": "2020-01-03T00:00:00Z",
                                        "author": {"user": {"login": "c"}}}},
                        ],
                    },
                    "reviews":       {"totalCount": 0, "pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": []},
                    "comments":      {"totalCount": 0, "pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": []},
                    "reviewThreads": {"totalCount": 0, "pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": []},
                },
                "rateLimit": {"remaining": 5000},
            },
        }

    monkeypatch.setattr(github, "_run_gh_graphql", fake_run)
    fetched = github._paginate_pr(518)
    assert len(fetched["commits"]) == 3
    assert [c["login"] for c in fetched["commits"]] == ["a", "b", "c"]
    assert fetched["_complete"] is True
    assert call_ix["i"] == 2  # first + second page


# --- contributor identity resolution ------------------------------------


def _commit(author, committer=None):
    """Build the shape `_extract_commit` produces. Actors are (name, email, login)."""
    def actor(a):
        if a is None:
            return {"name": None, "email": None, "login": None}
        name, email, login = a
        return {"name": name, "email": email, "login": login}
    return {"author": actor(author), "committer": actor(committer)}


@pytest.mark.ai_generated
def test_resolve_contributors_counts_committers_too() -> None:
    """Landing someone else's patch is a contribution `git shortlog` never shows."""
    commits = [
        _commit(("Alice", "alice@example.org", "alice"),
                ("Bob", "bob@example.org", "bob")),
    ]
    out = github.resolve_contributors(commits)
    assert out["count"] == 2
    assert out["authors"] == 1
    assert out["committers"] == 1
    assert out["by_identity"]["alice"]["authored"] == 1
    assert out["by_identity"]["bob"]["committed"] == 1


@pytest.mark.ai_generated
def test_resolve_contributors_folds_two_name_spellings() -> None:
    """The real bids-specification#2307 case: one address, two display names.

    `git shortlog -sn | wc -l` reports 6 contributors there; keying on the
    account/address gives the correct 5.
    """
    commits = [
        _commit(("Chris Markiewicz", "markiewicz@stanford.edu", "effigies")),
        _commit(("Christopher J. Markiewicz", "markiewicz@stanford.edu", "effigies")),
    ]
    out = github.resolve_contributors(commits)
    assert out["count"] == 1
    assert out["by_identity"]["effigies"]["authored"] == 2


@pytest.mark.ai_generated
def test_resolve_contributors_folds_unresolved_email_into_login() -> None:
    """Same person, one commit GitHub matched to an account and one it did not."""
    commits = [
        _commit(("Chris Markiewicz", "markiewicz@stanford.edu", "effigies")),
        _commit(("Christopher J. Markiewicz", "markiewicz@stanford.edu", None)),
    ]
    out = github.resolve_contributors(commits)
    assert out["count"] == 1
    assert out["by_identity"]["effigies"]["authored"] == 2


@pytest.mark.ai_generated
def test_resolve_contributors_excludes_github_web_flow_and_bots() -> None:
    commits = [
        _commit(("Alice", "alice@example.org", "alice"),
                ("GitHub", "noreply@github.com", None)),
        _commit(("dependabot[bot]", "x@example.org", "dependabot[bot]")),
    ]
    out = github.resolve_contributors(commits)
    assert out["count"] == 1
    assert set(out["by_identity"]) == {"alice"}


@pytest.mark.ai_generated
def test_resolve_contributors_keeps_per_user_noreply_addresses() -> None:
    """`…@users.noreply.github.com` is a real person, unlike `noreply@github.com`."""
    commits = [
        _commit(("Cody Baker", "51133164+CodyCBakerPhD@users.noreply.github.com", None)),
    ]
    out = github.resolve_contributors(commits)
    assert out["count"] == 1


@pytest.mark.ai_generated
def test_resolve_contributors_empty() -> None:
    out = github.resolve_contributors([])
    assert out == {"count": 0, "authors": 0, "committers": 0, "by_identity": {}}


@pytest.mark.ai_generated
def test_extract_commit_captures_both_actors() -> None:
    node = {"commit": {
        "authoredDate": "2020-01-01T00:00:00Z",
        "committedDate": "2020-01-02T00:00:00Z",
        "author": {"name": "Alice", "email": "alice@example.org",
                   "user": {"login": "alice"}},
        "committer": {"name": "Bob", "email": "bob@example.org",
                      "user": {"login": "bob"}},
    }}
    out = github._extract_commit(node)
    assert out["login"] == "alice"          # back-compat: authoring login
    assert out["author"]["login"] == "alice"
    assert out["committer"]["login"] == "bob"
    assert out["committer"]["email"] == "bob@example.org"


@pytest.mark.ai_generated
def test_extract_commit_tolerates_null_actors() -> None:
    """GraphQL returns null `user` for unregistered emails, and null actors exist."""
    out = github._extract_commit({"commit": {"authoredDate": "x", "committedDate": "y"}})
    assert out["author"] == {"name": None, "email": None, "login": None}
    assert out["committer"] == {"name": None, "email": None, "login": None}
    assert github.resolve_contributors([out])["count"] == 0
