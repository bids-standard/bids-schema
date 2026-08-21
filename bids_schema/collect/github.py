"""Collect per-PR stats via ``gh api graphql`` and write into
``PRs/<N>/PR_METADATA.json`` (nested ``stats`` block).

See ``doc/designs/2-extended-stats-plan.md`` §3.5 for the design.

Public entry point: ``collect(only, force)``. Returns a process-exit code
(0 = OK, non-zero = at least one PR failed unrecoverably at the CLI level).
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from bids_schema.metadata.io import iter_numeric_subdirs, load_json, write_json_atomic
from bids_schema.metadata.schema import CURRENT_PR_SCHEMA_VERSION
from bids_schema.metadata.time import now_utc_iso

log = logging.getLogger(__name__)

BIDS_SPEC_OWNER = "bids-standard"
BIDS_SPEC_NAME = "bids-specification"

DEFAULT_MAX_AGE_SECONDS = 6 * 60 * 60           # 6h freshness floor
DEFAULT_MAX_INNER_QUERIES = 10                  # cap for per-thread comment paging
DEFAULT_RATE_LIMIT_MIN_REMAINING = 500          # sleep when below this
DEFAULT_RATE_LIMIT_MAX_SLEEP = 20 * 60          # 20 min cap on sleep
DEFAULT_PREFLIGHT_BATCH = 50                    # PRs per aliased pre-flight query

# `PR_STATS_MAX_AGE` and `PR_STATS_MAX_AGE_SECONDS` both accepted (integer
# seconds); the shorter form matches the plan spec (§3.5).
MAX_AGE_SECONDS = int(
    os.environ.get("PR_STATS_MAX_AGE")
    or os.environ.get("PR_STATS_MAX_AGE_SECONDS", DEFAULT_MAX_AGE_SECONDS)
)
MAX_INNER_QUERIES = int(os.environ.get("PR_STATS_MAX_INNER_QUERIES", DEFAULT_MAX_INNER_QUERIES))
PREFLIGHT_BATCH = int(os.environ.get("PR_STATS_PREFLIGHT_BATCH", DEFAULT_PREFLIGHT_BATCH))

# --- GraphQL queries -----------------------------------------------------

def _build_preflight_query(pr_numbers: list[int]) -> str:
    """Build one aliased GraphQL query fetching headRefOid + state for many PRs.

    Aliases are of the form ``pr<N>`` (safe: `pr_numbers` come from
    directory names filtered by `str.isdigit`, so no injection surface).
    Cost is ~2 nodes per PR — a 50-PR batch is well under GitHub's
    500k-node complexity budget.
    """
    aliases = "\n".join(
        f"    pr{pr}: pullRequest(number:{pr}) {{ number headRefOid state }}"
        for pr in pr_numbers
    )
    return (
        "query($owner:String!,$name:String!) {\n"
        "  repository(owner:$owner,name:$name) {\n"
        f"{aliases}\n"
        "  }\n"
        "  rateLimit { remaining resetAt cost }\n"
        "}\n"
    )

FULL_QUERY = """
query($owner:String!,$name:String!,$number:Int!,
      $cCur:String,$rCur:String,$icCur:String,$tCur:String) {
  repository(owner:$owner,name:$name) {
    pullRequest(number:$number) {
      state createdAt updatedAt reviewDecision headRefOid
      commits(first:100, after:$cCur) {
        totalCount pageInfo{hasNextPage endCursor}
        nodes{commit{committedDate authoredDate author{user{login}}}}
      }
      reviews(first:100, after:$rCur) {
        totalCount pageInfo{hasNextPage endCursor}
        nodes{state submittedAt author{login}}
      }
      comments(first:100, after:$icCur) {
        totalCount pageInfo{hasNextPage endCursor}
        nodes{createdAt author{login}}
      }
      reviewThreads(first:50, after:$tCur) {
        totalCount pageInfo{hasNextPage endCursor}
        nodes{
          id isResolved isOutdated
          comments(first:5){
            totalCount pageInfo{hasNextPage endCursor}
            nodes{createdAt author{login}}
          }
        }
      }
    }
    rateLimit{remaining resetAt cost}
  }
}
"""

THREAD_COMMENTS_QUERY = """
query($id:ID!,$cur:String) {
  node(id:$id) {
    ... on PullRequestReviewThread {
      comments(first:100, after:$cur) {
        totalCount pageInfo{hasNextPage endCursor}
        nodes{createdAt author{login}}
      }
    }
  }
  rateLimit{remaining resetAt cost}
}
"""


# --- gh transport --------------------------------------------------------


class GHError(RuntimeError):
    """Raised for ``gh`` transport failures — network, HTTP, GraphQL errors."""


def _run_gh_graphql(query: str, variables: dict) -> dict:
    gh = shutil.which("gh")
    if not gh:
        raise GHError("`gh` CLI not on PATH")
    cmd = [gh, "api", "graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        if isinstance(value, int):
            cmd.extend(["-F", f"{key}={value}"])
        elif value is None:
            continue
        else:
            cmd.extend(["-f", f"{key}={value}"])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except OSError as e:
        raise GHError(f"gh invocation failed: {e}") from e
    if result.returncode != 0:
        raise GHError(
            f"gh api graphql failed (rc={result.returncode}): "
            f"{(result.stderr or result.stdout).strip()[:500]}"
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise GHError(f"gh returned non-JSON: {result.stdout[:200]}") from e
    if "errors" in payload:
        raise GHError(f"GraphQL errors: {payload['errors']}")
    return payload["data"]


def _maybe_wait_for_rate_limit(rate_limit: dict | None) -> None:
    """Sleep until reset if remaining < threshold, or raise ``rate_limit_ceiling``
    if the reset is farther out than we're willing to wait.
    """
    if not rate_limit:
        return
    remaining = int(rate_limit.get("remaining", 5000))
    if remaining >= DEFAULT_RATE_LIMIT_MIN_REMAINING:
        return
    reset_at = rate_limit.get("resetAt")
    if not reset_at:
        return
    try:
        reset_dt = datetime.fromisoformat(reset_at.replace("Z", "+00:00"))
    except ValueError:
        return
    now = datetime.now(timezone.utc)
    delta = (reset_dt - now).total_seconds()
    if delta <= 0:
        return
    if delta > DEFAULT_RATE_LIMIT_MAX_SLEEP:
        raise GHError(
            f"rate_limit_ceiling: rate limit exhausted (remaining={remaining}), "
            f"reset in {delta:.0f}s exceeds max sleep budget of "
            f"{DEFAULT_RATE_LIMIT_MAX_SLEEP}s"
        )
    sleep_for = delta + 5
    log.warning("Rate limit low (%s remaining). Sleeping %.0fs until reset.",
                remaining, sleep_for)
    time.sleep(sleep_for)


# --- Pre-flight: batch cheap headRefOid query ----------------------------


def preflight_head_shas(pr_numbers: list[int]) -> dict[int, dict]:
    """Aliased pre-flight: fetch ``headRefOid`` + ``state`` for many PRs in
    one GraphQL round trip per ``PREFLIGHT_BATCH`` chunk.

    Returns ``{pr_number: {headRefOid, state}}``. PRs whose alias is
    absent from the response (deleted, moved) are simply omitted.

    Falls back to per-PR queries if a batch fails as a whole — that way
    one bad PR number can't blind the freshness gate for all of them.
    """
    result: dict[int, dict] = {}
    if not pr_numbers:
        return result
    for i in range(0, len(pr_numbers), PREFLIGHT_BATCH):
        chunk = pr_numbers[i:i + PREFLIGHT_BATCH]
        query = _build_preflight_query(chunk)
        try:
            data = _run_gh_graphql(
                query,
                {"owner": BIDS_SPEC_OWNER, "name": BIDS_SPEC_NAME},
            )
            _maybe_wait_for_rate_limit(data.get("rateLimit"))
            repo_block = data.get("repository") or {}
            for pr in chunk:
                node = repo_block.get(f"pr{pr}") or {}
                if node:
                    result[pr] = {
                        "headRefOid": node.get("headRefOid"),
                        "state": node.get("state"),
                    }
        except GHError as e:
            log.warning("Aliased preflight batch failed (%d PRs); falling back per-PR: %s",
                        len(chunk), e)
            for pr in chunk:
                try:
                    data = _run_gh_graphql(
                        _build_preflight_query([pr]),
                        {"owner": BIDS_SPEC_OWNER, "name": BIDS_SPEC_NAME},
                    )
                    _maybe_wait_for_rate_limit(data.get("rateLimit"))
                    node = ((data.get("repository") or {}).get(f"pr{pr}")) or {}
                    if node:
                        result[pr] = {
                            "headRefOid": node.get("headRefOid"),
                            "state": node.get("state"),
                        }
                except GHError as inner:
                    log.warning("Preflight for PR #%s failed: %s", pr, inner)
    return result


# --- Freshness gate ------------------------------------------------------


def _is_fresh(existing_stats: dict, head_now: str | None) -> bool:
    if not existing_stats:
        return False
    if not existing_stats.get("_complete"):
        return False
    if existing_stats.get("_error"):
        return False
    if head_now and existing_stats.get("_source_head_sha") != head_now:
        return False
    collected_at = existing_stats.get("_collected_at")
    if not collected_at:
        return False
    try:
        collected_dt = datetime.fromisoformat(collected_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    age = (datetime.now(timezone.utc) - collected_dt).total_seconds()
    return age < MAX_AGE_SECONDS


# --- Full-fetch: paginate all connections --------------------------------


def _paginate_pr(pr_number: int) -> dict:
    """Fetch a PR with full pagination on all four top-level connections.

    Returns a normalised dict with everything the derivation stage needs::

        {
          "pr_meta": {state, createdAt, updatedAt, reviewDecision, headRefOid},
          "commits":       [{authoredDate, committedDate, login}],
          "reviews":       [{state, submittedAt, login}],
          "issue_comments":[{createdAt, login}],
          "review_threads":[{id, isResolved, isOutdated,
                             comment_count, first_comment: {createdAt, login} | None,
                             comments_truncated: bool}],
          "_complete": bool,
          "_error": str | None,
        }
    """
    commits: list[dict] = []
    reviews: list[dict] = []
    issue_comments: list[dict] = []
    review_threads: list[dict] = []

    c_cur = r_cur = ic_cur = t_cur = None
    pr_meta: dict = {}
    complete = True
    error_msg: str | None = None
    threads_paginated_inner = 0

    # First round drives all four connections. When a given connection
    # becomes exhausted, its cursor stays None-with-hasNextPage-false and
    # the API returns 0 nodes for it — cheap.
    while True:
        data = _run_gh_graphql(FULL_QUERY, {
            "owner": BIDS_SPEC_OWNER, "name": BIDS_SPEC_NAME, "number": pr_number,
            "cCur": c_cur, "rCur": r_cur, "icCur": ic_cur, "tCur": t_cur,
        })
        _maybe_wait_for_rate_limit(data.get("repository", {}).get("rateLimit"))
        pr = (data.get("repository") or {}).get("pullRequest") or {}
        if not pr:
            raise GHError(f"PR #{pr_number} not found in response")
        if not pr_meta:
            pr_meta = {
                "state": pr.get("state"),
                "createdAt": pr.get("createdAt"),
                "updatedAt": pr.get("updatedAt"),
                "reviewDecision": pr.get("reviewDecision"),
                "headRefOid": pr.get("headRefOid"),
            }

        for section, cursor_key, dest, extract in [
            ("commits",       "cCur",  commits,        _extract_commit),
            ("reviews",       "rCur",  reviews,        _extract_review),
            ("comments",      "icCur", issue_comments, _extract_issue_comment),
        ]:
            block = pr.get(section) or {}
            for node in block.get("nodes") or []:
                dest.append(extract(node))

        # reviewThreads has structural variation; handle separately.
        rt_block = pr.get("reviewThreads") or {}
        for node in rt_block.get("nodes") or []:
            entry = _extract_review_thread(node)
            if entry["comments_truncated"] and threads_paginated_inner < MAX_INNER_QUERIES:
                try:
                    _extend_thread_comments(entry)
                    threads_paginated_inner += 1
                except GHError as inner_err:
                    log.warning("PR #%s thread %s pagination failed: %s",
                                pr_number, entry["id"], inner_err)
                    complete = False
                    error_msg = "review_thread_comments_truncated"
            review_threads.append(entry)

        # Compute next cursors, stop when all four are done.
        any_more = False
        for section, cursor_var in [
            ("commits", "c_cur"), ("reviews", "r_cur"),
            ("comments", "ic_cur"), ("reviewThreads", "t_cur"),
        ]:
            block = pr.get(section) or {}
            page_info = block.get("pageInfo") or {}
            if page_info.get("hasNextPage"):
                any_more = True
                new_cur = page_info.get("endCursor")
                if cursor_var == "c_cur":
                    c_cur = new_cur
                elif cursor_var == "r_cur":
                    r_cur = new_cur
                elif cursor_var == "ic_cur":
                    ic_cur = new_cur
                elif cursor_var == "t_cur":
                    t_cur = new_cur

        # If reviewThreads had more inner pages than we can afford to chase,
        # flag incompleteness but don't loop forever.
        if threads_paginated_inner >= MAX_INNER_QUERIES:
            for entry in review_threads:
                if entry["comments_truncated"] and not entry.get("_paginated"):
                    complete = False
                    error_msg = error_msg or "review_thread_comments_truncated"

        if not any_more:
            break

    return {
        "pr_meta": pr_meta,
        "commits": commits,
        "reviews": reviews,
        "issue_comments": issue_comments,
        "review_threads": review_threads,
        "_complete": complete,
        "_error": error_msg,
    }


def _extract_commit(node: dict) -> dict:
    commit = node.get("commit") or {}
    author_user = ((commit.get("author") or {}).get("user") or {})
    return {
        "authoredDate": commit.get("authoredDate"),
        "committedDate": commit.get("committedDate"),
        "login": author_user.get("login"),
    }


def _extract_review(node: dict) -> dict:
    return {
        "state": node.get("state"),
        "submittedAt": node.get("submittedAt"),
        "login": (node.get("author") or {}).get("login"),
    }


def _extract_issue_comment(node: dict) -> dict:
    return {
        "createdAt": node.get("createdAt"),
        "login": (node.get("author") or {}).get("login"),
    }


def _extract_review_thread(node: dict) -> dict:
    comments = node.get("comments") or {}
    comment_nodes = comments.get("nodes") or []
    first_comment = None
    if comment_nodes:
        first = comment_nodes[0]
        first_comment = {
            "createdAt": first.get("createdAt"),
            "login": (first.get("author") or {}).get("login"),
        }
    return {
        "id": node.get("id"),
        "isResolved": bool(node.get("isResolved")),
        "isOutdated": bool(node.get("isOutdated")),
        "comment_count": comments.get("totalCount", len(comment_nodes)),
        "first_comment": first_comment,
        "comments_truncated": bool((comments.get("pageInfo") or {}).get("hasNextPage")),
        "_paginated": False,
    }


def _extend_thread_comments(entry: dict) -> None:
    """Follow ``entry.id``'s comments to determine the true first comment (oldest).

    We don't accumulate every comment — we only need `first_comment` and
    `comment_count`. The initial page already had `first: 5` earliest
    comments, so the *oldest* is on that page (GraphQL default order is
    oldest→newest). Extending pagination doesn't change ``first_comment``;
    it only verifies the count is not truncated.
    """
    cursor = None
    total = entry["comment_count"]
    while True:
        data = _run_gh_graphql(THREAD_COMMENTS_QUERY, {"id": entry["id"], "cur": cursor})
        _maybe_wait_for_rate_limit(data.get("rateLimit"))
        node = data.get("node") or {}
        block = node.get("comments") or {}
        total = block.get("totalCount", total)
        page_info = block.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
    entry["comment_count"] = total
    entry["comments_truncated"] = False
    entry["_paginated"] = True


# --- Aggregation ---------------------------------------------------------


def _min_max(values: list[str | None]) -> tuple[str | None, str | None]:
    filtered = sorted(v for v in values if v)
    if not filtered:
        return None, None
    return filtered[0], filtered[-1]


def _effective_state(states_by_time: list[tuple[str, str]]) -> str | None:
    """Walk reviews reverse-chronologically; return first state that is not
    COMMENTED and not DISMISSED. Matches GitHub's reviewers-sidebar heuristic.
    """
    for _submitted_at, state in sorted(states_by_time, reverse=True):
        if state in ("COMMENTED", "DISMISSED"):
            continue
        return state
    return None


def derive_stats(fetched: dict, source_head_sha: str | None) -> dict:
    """Turn the paginated raw response into the final ``stats`` block dict."""
    commits = fetched["commits"]
    reviews = fetched["reviews"]
    issue_comments = fetched["issue_comments"]
    review_threads = fetched["review_threads"]

    # commits
    commit_first, commit_last = _min_max([c["authoredDate"] for c in commits])

    # reviews aggregate
    state_counts: dict[str, int] = defaultdict(int)
    for r in reviews:
        state_counts[(r["state"] or "UNKNOWN").upper()] += 1
    total_reviews = len(reviews)

    # reviews by author
    by_author: dict[str, list[dict]] = defaultdict(list)
    for r in reviews:
        login = r["login"] or "ghost"
        by_author[login].append(r)

    reviews_by_author: dict[str, dict] = {}
    for login, entries in by_author.items():
        histo: dict[str, int] = defaultdict(int)
        for e in entries:
            histo[(e["state"] or "UNKNOWN").upper()] += 1
        first_at, last_at = _min_max([e["submittedAt"] for e in entries])
        latest_state = max(entries, key=lambda e: e["submittedAt"] or "")["state"]
        eff_state = _effective_state([(e["submittedAt"] or "", e["state"] or "") for e in entries])
        reviews_by_author[login] = {
            "approved":          histo.get("APPROVED", 0),
            "commented":         histo.get("COMMENTED", 0),
            "changes_requested": histo.get("CHANGES_REQUESTED", 0),
            "dismissed":         histo.get("DISMISSED", 0),
            "pending":           histo.get("PENDING", 0),
            "first_at":          first_at,
            "last_at":           last_at,
            "last_state":        latest_state,
            "effective_state":   eff_state,
            "total":             len(entries),
        }

    # comments = union of issue-comments + first-comments of review threads
    comment_events = list(issue_comments)
    for thread in review_threads:
        fc = thread["first_comment"]
        if fc:
            comment_events.append(fc)
    comment_events_dates = [c.get("createdAt") for c in comment_events]
    review_thread_total = sum(t["comment_count"] for t in review_threads)

    # comments by author (only the events above, i.e. issue + thread-openers)
    comments_by_login: dict[str, list[str | None]] = defaultdict(list)
    for c in comment_events:
        comments_by_login[c.get("login") or "ghost"].append(c.get("createdAt"))
    comments_by_author = {}
    for login, times in comments_by_login.items():
        first_at, last_at = _min_max(times)
        comments_by_author[login] = {
            "count":    len(times),
            "first_at": first_at,
            "last_at":  last_at,
        }

    # unresolved review threads
    unresolved = [t for t in review_threads if not t["isResolved"]]
    unresolved_active = [t for t in unresolved if not t["isOutdated"]]
    unresolved_outdated = [t for t in unresolved if t["isOutdated"]]

    unresolved_by_login: dict[str, list[str | None]] = defaultdict(list)
    for t in unresolved:
        fc = t["first_comment"] or {}
        unresolved_by_login[fc.get("login") or "ghost"].append(fc.get("createdAt"))
    unresolved_by_author = {}
    for login, times in unresolved_by_login.items():
        first_at, last_at = _min_max(times)
        unresolved_by_author[login] = {
            "count":    len(times),
            "first_at": first_at,
            "last_at":  last_at,
        }

    comment_first, comment_last = _min_max(comment_events_dates)
    total_comments = len(issue_comments) + review_thread_total

    return {
        "_source_head_sha": source_head_sha or fetched["pr_meta"].get("headRefOid"),
        "_collected_at":    now_utc_iso(),
        "_complete":        bool(fetched["_complete"]),
        "_error":           fetched["_error"],

        "pr_state":         fetched["pr_meta"].get("state"),
        "pr_created_at":    fetched["pr_meta"].get("createdAt"),
        "pr_updated_at":    fetched["pr_meta"].get("updatedAt"),
        "review_decision":  fetched["pr_meta"].get("reviewDecision"),

        "commits": {
            "count":    len(commits),
            "first_at": commit_first,
            "last_at":  commit_last,
        },

        "reviews": {
            "approved":          state_counts.get("APPROVED", 0),
            "changes_requested": state_counts.get("CHANGES_REQUESTED", 0),
            "commented":         state_counts.get("COMMENTED", 0),
            "dismissed":         state_counts.get("DISMISSED", 0),
            "pending":           state_counts.get("PENDING", 0),
            "total":             total_reviews,
            "by_author":         reviews_by_author,
        },

        "comments": {
            "issue_count":         len(issue_comments),
            "review_thread_count": review_thread_total,
            "total":               total_comments,
            "first_at":            comment_first,
            "last_at":             comment_last,
            "by_author":           comments_by_author,
        },

        "review_threads": {
            "total":                len(review_threads),
            "unresolved":           len(unresolved),
            "unresolved_active":    len(unresolved_active),
            "unresolved_outdated":  len(unresolved_outdated),
            "unresolved_by_author": unresolved_by_author,
        },
    }


# --- Top-level orchestration ---------------------------------------------


def _list_pr_numbers(base_dir: Path) -> list[int]:
    return [int(p.name) for p in iter_numeric_subdirs(base_dir / "PRs")]


def _write_error_stats(path: Path, existing_record: dict, error_code: str,
                       head_now: str | None) -> None:
    """Set ``stats._error`` on an existing record without wiping earlier data.

    If the record has no ``stats`` block at all, create a minimal one so
    the renderer at least shows the ⚠ marker.
    """
    stats = dict(existing_record.get("stats") or {})
    stats["_error"] = error_code
    stats["_complete"] = False
    if head_now:
        stats["_source_head_sha"] = stats.get("_source_head_sha") or head_now
    stats["_collected_at"] = stats.get("_collected_at") or now_utc_iso()
    existing_record["stats"] = stats
    existing_record["_schema_version"] = CURRENT_PR_SCHEMA_VERSION
    write_json_atomic(path, existing_record)


def collect(only: list[str] | None = None, force: bool = False,
            base_dir: Path | None = None) -> int:
    """Batch-collect PR stats for all (or ``--only``) PRs on disk.

    Writes each ``PRs/<N>/PR_METADATA.json`` in place, one at a time
    (mid-run rate-limit hit leaves earlier successes on disk).
    """
    logging.basicConfig(level=os.environ.get("BIDS_SCHEMA_LOGLEVEL", "INFO"),
                        format="%(asctime)s %(levelname)s %(message)s")
    root = base_dir or Path.cwd()

    all_prs = _list_pr_numbers(root)
    if only:
        wanted = {int(x) for x in only if str(x).isdigit()}
        pr_numbers = [n for n in all_prs if n in wanted]
    else:
        pr_numbers = all_prs

    if not pr_numbers:
        log.info("No PRs to collect (base_dir=%s).", root)
        return 0

    log.info("Collecting stats for %d PR(s).", len(pr_numbers))

    if not shutil.which("gh"):
        log.error("`gh` CLI not found on PATH; cannot collect PR stats.")
        return 2

    # Pre-flight: batch cheap headRefOid so we can skip fresh PRs without
    # paying the full-query cost.
    heads_by_pr = preflight_head_shas(pr_numbers) if not force else {}
    num_collected = 0
    num_skipped = 0
    num_errored = 0

    for pr_number in pr_numbers:
        record_path = root / "PRs" / str(pr_number) / "PR_METADATA.json"
        record = load_json(record_path) or {"pr_number": str(pr_number)}
        head_now = (heads_by_pr.get(pr_number) or {}).get("headRefOid")

        if not force and _is_fresh(record.get("stats") or {}, head_now):
            num_skipped += 1
            log.debug("PR #%s: stats fresh, skipping.", pr_number)
            continue

        try:
            fetched = _paginate_pr(pr_number)
            stats = derive_stats(fetched, source_head_sha=head_now)
            record["stats"] = stats
            record["_schema_version"] = CURRENT_PR_SCHEMA_VERSION
            write_json_atomic(record_path, record)
            num_collected += 1
            log.info("PR #%s: stats updated (%d reviews, %d threads, %d unresolved).",
                     pr_number,
                     stats["reviews"]["total"],
                     stats["review_threads"]["total"],
                     stats["review_threads"]["unresolved"])
        except GHError as e:
            log.warning("PR #%s: %s", pr_number, e)
            _write_error_stats(record_path, record, _classify_error(str(e)), head_now)
            num_errored += 1

    log.info("Done. collected=%d skipped=%d errored=%d.",
             num_collected, num_skipped, num_errored)
    return 0


def _classify_error(msg: str) -> str:
    lower = msg.lower()
    if "rate_limit_ceiling" in lower or "rate limit ceiling" in lower:
        return "rate_limit_ceiling"
    if "rate limit" in lower or "abuse detection" in lower:
        return "rate_limit"
    if "not found" in lower or "404" in lower:
        return "not_found"
    if "graphql" in lower:
        return "graphql_error"
    return "network_error"
