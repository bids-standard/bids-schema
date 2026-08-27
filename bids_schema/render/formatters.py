"""Shared cell formatters + record loaders for the two README renderers.

The formatters are pure functions; the loaders resolve on-disk state to
support the read-through join that lets the BEP renderer reuse
PR-derived facts without triggering re-collection (invariant #1 from
the plan).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bids_schema.metadata.io import load_json

BIDS_SPEC_REPO = "bids-standard/bids-specification"
BIDS_SCHEMA_REPO = "bids-standard/bids-schema"

# Thresholds (days since a BEP's Google Doc was last edited) used by
# `bep_activity_badge` to turn `doc_activity.last_modified` into a
# traffic-light badge on the BEPs README. Ported from bids-website's
# `macros.bep_activity_badge` (bep-dashboard branch).
FRESH_AFTER_DAYS = 30
ACTIVE_AFTER_DAYS = 180

# Branch that the "Raw" / "Pretty" table links point at. Defaults to
# ``main`` so links resolve once this PR is merged; override with
# ``BIDS_SCHEMA_RAW_BRANCH`` when rendering from a feature branch that
# hasn't been merged yet.
RAW_BRANCH = os.environ.get("BIDS_SCHEMA_RAW_BRANCH", "main")


def pr_url(pr_number: str | int) -> str:
    return f"https://github.com/{BIDS_SPEC_REPO}/pull/{pr_number}"


def commit_url(sha: str) -> str:
    return f"https://github.com/{BIDS_SPEC_REPO}/commit/{sha}"


def raw_url(kind: str, folder: str, filename: str) -> str:
    return (
        f"https://raw.githubusercontent.com/{BIDS_SCHEMA_REPO}/"
        f"refs/heads/{RAW_BRANCH}/{kind}/{folder}/{filename}"
    )


def format_date(iso: str | None) -> str:
    """Render an ISO-8601 timestamp as ``YYYY-MM-DD``. ``None``/``"Unknown"`` → ``—``."""
    if not iso or iso == "Unknown":
        return "—"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return iso
    return dt.strftime("%Y-%m-%d")


#: ``stats.reviews`` keys rendered by :func:`format_reviews`, in display order.
REVIEW_COMPONENTS = (
    ("approved",          "✅"),
    ("changes_requested", "❌"),
    ("commented",         "💬"),
)


def format_reviews(reviews: dict | None) -> str:
    """Render the aggregate review histogram as ``3✅/2❌/7💬``.

    Zero-valued components are omitted so the cell stays scannable —
    ``{approved: 1, changes_requested: 0, commented: 27}`` renders as
    ``1✅/27💬`` rather than ``1✅/0❌/27💬``. ``—`` if the record has no
    stats block at all, ``0`` if every component is zero.
    """
    if not reviews:
        return "—"
    parts = [
        f"{reviews.get(key, 0)}{emoji}"
        for key, emoji in REVIEW_COMPONENTS
        if reviews.get(key, 0)
    ]
    if not parts:
        return "0"
    return "/".join(parts)


def format_count(count: int | None) -> str:
    """Render a bare count for its own sortable column. ``None`` → ``—``, ``0`` → ``0``."""
    if count is None:
        return "—"
    return str(count)


def format_unresolved(n: int | None) -> str:
    """Render unresolved-thread count. ``None`` (not collected) → ``—``,
    ``0`` → ``"0"``, positive → bolded."""
    if n is None:
        return "—"
    if n == 0:
        return "0"
    return f"**{n}**"


def format_build_indicator(build_status: str) -> str:
    if build_status == "success":
        return "✅"
    if build_status == "failed":
        return "❌"
    return "❓"


def build_status_of(record: dict) -> str:
    return record.get("build_status", "unknown")


def stats_of(record: dict) -> dict[str, Any]:
    """Return the ``stats`` sub-block of a PR metadata record (v2), or ``{}``."""
    return record.get("stats") or {}


def load_pr_record(pr_number: str | int, base_dir: Path | None = None) -> dict:
    """Load ``PRs/<N>/PR_METADATA.json``. Missing → ``{}``.

    Tolerates absence of the ``stats`` sub-tree — callers can safely
    ``.get("stats", {}).get(...)``.
    """
    root = base_dir or Path.cwd()
    return load_json(root / "PRs" / str(pr_number) / "PR_METADATA.json")


def load_bep_record(bep_number: str | int, base_dir: Path | None = None) -> dict:
    """Load ``BEPs/<NN>/BEP_METADATA.json``. Missing → ``{}``."""
    root = base_dir or Path.cwd()
    return load_json(root / "BEPs" / str(bep_number) / "BEP_METADATA.json")


def bep_activity_badge(
    last_modified: str | None, edits_since_last_check: int | None = None
) -> dict[str, str]:
    """Turn a BEP Google Doc's ``modifiedTime`` into a display badge.

    ``edits_since_last_check`` (a diff of the Drive API's ``version``
    field between two collector runs) is appended to the label when
    available, giving a rough sense of *how much* changed, not just
    *whether* it did.

    Returns a dict with ``icon``, ``label`` and ``category`` so callers
    only need to display values, not compute them. ``last_modified``
    missing/falsy → an "Unknown" badge (never collected, or the doc
    isn't publicly viewable).
    """
    if not last_modified:
        return {
            "icon": "\N{MEDIUM WHITE CIRCLE}",
            "label": "Unknown",
            "category": "unknown",
        }

    modified = datetime.fromisoformat(last_modified.replace("Z", "+00:00"))
    days = (datetime.now(timezone.utc) - modified).days

    if days <= FRESH_AFTER_DAYS:
        icon, category = "\N{LARGE GREEN CIRCLE}", "fresh"
    elif days <= ACTIVE_AFTER_DAYS:
        icon, category = "\N{LARGE YELLOW CIRCLE}", "active"
    else:
        icon, category = "\N{LARGE RED CIRCLE}", "stale"

    label = f"Edited {days} day{'s' if days != 1 else ''} ago"
    if edits_since_last_check:
        label += (
            f" (+{edits_since_last_check} edit"
            f"{'s' if edits_since_last_check != 1 else ''})"
        )

    return {"icon": icon, "label": label, "category": category}


def stale_marker(stats: dict) -> str:
    """Small suffix if the stats collection was incomplete or errored."""
    if not stats:
        return ""
    if stats.get("_error"):
        return " ⚠"
    if stats.get("_complete") is False:
        return " …"
    return ""


# --- Aggregated helpers used by both renderers ---------------------------


#: Keys returned by :func:`format_stats_cells`. Counts and dates are kept in
#: separate cells so each gets its own sortable column in the rendered table
#: (a combined ``47 (2020-01-16 → 2026-05-08)`` cell sorts as a string, which
#: is useless for every ordering one actually wants).
STATS_CELL_KEYS = (
    "reviews",
    "unresolved",
    "pr_created",
    "commits_count", "commits_first", "commits_last",
    "comments_count", "comments_first", "comments_last",
)


def format_stats_cells(stats: dict) -> dict[str, str]:
    """Return the stats-derived table cells from a PR ``stats`` sub-block.

    Keys are :data:`STATS_CELL_KEYS`. Every value defaults to ``—`` if the
    block is missing or absent — so v1 records or PRs whose stats haven't
    been collected yet render consistently in both READMEs.

    ``pr_created`` is the PR's own creation date, which is **not** the same
    as ``commits_first``: a force-push (rebase, squash, branch recreation)
    replaces the branch's commits, so on an old PR the earliest surviving
    commit can post-date the PR — and its comments — by years. Showing both
    makes that discrepancy legible instead of looking like a bug.
    """
    if not stats:
        return dict.fromkeys(STATS_CELL_KEYS, "—")
    comments = stats.get("comments") or {}
    threads = stats.get("review_threads") or {}
    commits = stats.get("commits") or {}
    return {
        "reviews":        format_reviews(stats.get("reviews")),
        "unresolved":     format_unresolved(threads.get("unresolved")),
        "pr_created":     format_date(stats.get("pr_created_at")),
        "commits_count":  format_count(commits.get("count")),
        "commits_first":  format_date(commits.get("first_at")),
        "commits_last":   format_date(commits.get("last_at")),
        "comments_count": format_count(comments.get("total")),
        "comments_first": format_date(comments.get("first_at")),
        "comments_last":  format_date(comments.get("last_at")),
    }


def format_build_cell(record: dict) -> str:
    """Build indicator + optional stale marker for a record's ``stats`` block."""
    return f"{format_build_indicator(build_status_of(record))}{stale_marker(stats_of(record))}"


def format_actions_cell(
    kind: str,
    folder: str,
    *,
    build_status: str,
    error_log: str | None = None,
    error_log_href: str | None = None,
) -> str:
    """Build the ``[Schema] \\| [Raw] \\| [Pretty] [\\| Error Log]`` triple.

    - ``kind`` is ``"PRs"`` or ``"BEPs"`` — controls the raw-URL folder.
    - ``folder`` is the on-disk directory name (``str(pr_number)`` or
      ``str(bep_number)``).
    - When ``build_status == "failed"`` and ``error_log`` is truthy,
      an Error Log link is appended. Its href is ``error_log_href`` if
      given (BEP renderer passes ``../PRs/<N>/bst-output.log``), otherwise
      the sibling ``./<folder>/bst-output.log``.
    """
    schema_path = f"./{folder}/schema.json"
    actions = (
        f"[Schema]({schema_path}) \\| "
        f"[Raw]({raw_url(kind, folder, 'schema.json')}) \\| "
        f"[Pretty]({raw_url(kind, folder, 'schema_pp.json')})"
    )
    if build_status == "failed" and error_log:
        href = error_log_href or f"./{folder}/bst-output.log"
        actions += f" \\| [Error Log]({href})"
    return actions
