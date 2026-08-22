"""Shared cell formatters + record loaders for the two README renderers.

The formatters are pure functions; the loaders resolve on-disk state to
support the read-through join that lets the BEP renderer reuse
PR-derived facts without triggering re-collection (invariant #1 from
the plan).
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any

from bids_schema.metadata.io import load_json

BIDS_SPEC_REPO = "bids-standard/bids-specification"
BIDS_SCHEMA_REPO = "bids-standard/bids-schema"

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


def format_date_window(first: str | None, last: str | None) -> str:
    """Render two ISO timestamps as ``YYYY-MM-DD → YYYY-MM-DD``. ``—`` if both missing."""
    if not first and not last:
        return "—"
    return f"{format_date(first)} → {format_date(last)}"


def format_reviews(reviews: dict | None) -> str:
    """Render the aggregate review histogram as ``3✅/2❌/7💬``.

    Emoji legend intentionally minimal so the column stays narrow. ``—``
    if the record has no stats block at all.
    """
    if not reviews:
        return "—"
    approved = reviews.get("approved", 0)
    changes = reviews.get("changes_requested", 0)
    commented = reviews.get("commented", 0)
    if approved == changes == commented == 0:
        return "0"
    return f"{approved}✅/{changes}❌/{commented}💬"


def format_activity_span(count: int | None, first: str | None, last: str | None) -> str:
    """Render ``<count> (<first> → <last>)``. ``—`` if count is falsy/absent."""
    if not count:
        return "—"
    return f"{count} ({format_date(first)} → {format_date(last)})"


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


def format_stats_cells(stats: dict) -> dict[str, str]:
    """Return the four stats-derived table cells (reviews / comments /
    unresolved / commit window) from a PR ``stats`` sub-block.

    Every value defaults to ``—`` if the block is missing or absent —
    so v1 records or PRs whose stats haven't been collected yet render
    consistently in both READMEs.
    """
    if not stats:
        return {"reviews": "—", "comments": "—", "unresolved": "—", "commit_window": "—"}
    comments = stats.get("comments") or {}
    threads = stats.get("review_threads") or {}
    commits = stats.get("commits") or {}
    return {
        "reviews":       format_reviews(stats.get("reviews")),
        "comments":      format_activity_span(
                             comments.get("total"),
                             comments.get("first_at"),
                             comments.get("last_at"),
                         ),
        "unresolved":    format_unresolved(threads.get("unresolved")),
        "commit_window": format_date_window(
                             commits.get("first_at"),
                             commits.get("last_at"),
                         ),
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
