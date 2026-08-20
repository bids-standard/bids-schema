"""Shared cell formatters + record loaders for the two README renderers.

The formatters are pure functions; the loaders resolve on-disk state to
support the read-through join that lets the BEP renderer reuse
PR-derived facts without triggering re-collection (invariant #1 from
the plan).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from bids_schema.metadata.io import load_json

BIDS_SPEC_REPO = "bids-standard/bids-specification"
BIDS_SCHEMA_REPO = "bids-standard/bids-schema"
RAW_BRANCH = "enh-prs-and-beps"


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
