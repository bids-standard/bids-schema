"""Render ``BEPs/dashboard.json`` — one machine-readable BEP activity feed.

This is the single file downstream consumers (notably the BEPs page on
``bids-website``) fetch to show BEP activity, so they never re-implement
collection or the BEP ↔ PR join.

Same invariants as the README renderers: reads only on-disk metadata, makes
no HTTP calls, and joins PR-derived facts from ``PRs/<N>/PR_METADATA.json``
at render time.

The output carries **raw values** (counts, ISO-8601 timestamps), not
pre-formatted cells: consumers compute relative values such as "edited N
days ago" at view time, so the feed never goes stale between cycles. The
file is deterministic — ``data_as_of`` is the newest collection timestamp
found in the inputs, not the wall clock — so a cycle with no new data
produces no diff.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from bids_schema.metadata.io import iter_numeric_subdirs
from bids_schema.render import formatters as fmt

#: Bump on any backwards-incompatible change to the output layout.
DASHBOARD_SCHEMA_VERSION = 1

OUTPUT_NAME = "dashboard.json"


def _pr_block(pr_metadata: dict) -> dict[str, Any] | None:
    """PR-derived facts for one BEP, or ``None`` if the PR record is missing."""
    if not pr_metadata:
        return None
    stats = fmt.stats_of(pr_metadata)
    comments = stats.get("comments") or {}
    reviews = stats.get("reviews") or {}
    threads = stats.get("review_threads") or {}
    contributors = stats.get("contributors") or {}

    if contributors.get("count") is not None:
        authors = contributors["count"]
    else:
        # Seed value from schema-build time; see fmt.format_contributors.
        authors = pr_metadata.get("authors_count")

    return {
        "build_status": fmt.build_status_of(pr_metadata),
        "state": stats.get("pr_state"),
        "created_at": stats.get("pr_created_at"),
        "updated_at": stats.get("pr_updated_at"),
        "review_decision": stats.get("review_decision"),
        "authors": authors,
        "commenters": len(comments["by_author"]) if "by_author" in comments else None,
        "reviews": {
            key: reviews.get(key, 0) for key, _ in fmt.REVIEW_COMPONENTS
        } if reviews else None,
        "unresolved_threads": threads.get("unresolved"),
        "comments": {
            "total": comments.get("total"),
            "first_at": comments.get("first_at"),
            "last_at": comments.get("last_at"),
        } if comments else None,
        "collected_at": stats.get("_collected_at"),
        "stats_complete": stats.get("_complete") if stats else None,
        "stats_error": stats.get("_error") if stats else None,
    }


def _doc_block(metadata: dict) -> dict[str, Any] | None:
    activity = metadata.get("doc_activity")
    if not activity:
        return None
    return {
        "last_modified": activity.get("last_modified"),
        "edits_since_last_check": activity.get("edits_since_last_check"),
        "checked_at": activity.get("checked_at"),
        "error": activity.get("_error"),
    }


def build_entry(bep_number: str, metadata: dict, base_dir: Path | None = None) -> dict[str, Any]:
    """One BEP's dashboard entry."""
    pr_number = metadata.get("pr_number") or None
    pr_metadata = fmt.load_pr_record(pr_number, base_dir=base_dir) if pr_number else {}
    has_schema = pr_metadata.get("build_status") == "success"
    return {
        "bep_number": str(bep_number).zfill(3),
        "title": metadata.get("title"),
        "google_doc": metadata.get("google_doc") or None,
        "doc_activity": _doc_block(metadata),
        "pr_number": int(pr_number) if pr_number else None,
        "pr_url": fmt.pr_url(pr_number) if pr_number else None,
        "pr": _pr_block(pr_metadata),
        "schema_url": fmt.raw_url("BEPs", str(bep_number), "schema_pp.json") if has_schema else None,
        "bep_registered": metadata.get("bep_registered"),
        "googledoc_registered": metadata.get("googledoc_registered"),
    }


def _data_as_of(entries: dict[str, dict]) -> str | None:
    stamps = []
    for e in entries.values():
        if e["pr"] and e["pr"]["collected_at"]:
            stamps.append(e["pr"]["collected_at"])
        if e["doc_activity"] and e["doc_activity"]["checked_at"]:
            stamps.append(e["doc_activity"]["checked_at"])
    return max(stamps) if stamps else None


def render(bep_records: list[tuple[str, dict]], base_dir: Path | None = None) -> dict[str, Any]:
    """Build the dashboard document from already-loaded BEP records."""
    entries = {
        str(int(num)): build_entry(str(int(num)), md, base_dir=base_dir)
        for num, md in sorted(bep_records, key=lambda kv: int(kv[0]))
        if md
    }
    return {
        "_schema_version": DASHBOARD_SCHEMA_VERSION,
        "source": f"https://github.com/{fmt.BIDS_SCHEMA_REPO}",
        "data_as_of": _data_as_of(entries),
        "thresholds_days": {
            "fresh": fmt.FRESH_AFTER_DAYS,
            "active": fmt.ACTIVE_AFTER_DAYS,
        },
        "beps": entries,
    }


def render_to_disk(base_dir: Path | None = None) -> Path:
    """Enumerate ``BEPs/[0-9]*`` and write ``BEPs/dashboard.json``."""
    root = base_dir or Path.cwd()
    bep_root = root / "BEPs"
    records: list[tuple[str, dict]] = []
    for bep_dir in iter_numeric_subdirs(bep_root):
        metadata = fmt.load_bep_record(bep_dir.name, base_dir=root)
        if metadata:
            records.append((bep_dir.name, metadata))

    doc = render(records, base_dir=root)
    out = bep_root / OUTPUT_NAME
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    print(f"Generated {out.relative_to(root)} with {len(doc['beps'])} BEPs")
    return out


if __name__ == "__main__":  # pragma: no cover
    render_to_disk()
