"""Render ``PRs/README.md`` from on-disk metadata.

Pure-function API:

- ``render(pr_records) -> str`` — build the Markdown given a list of
  ``(pr_number, metadata_dict)`` tuples. No filesystem I/O.
- ``render_to_disk(base_dir=None)`` — enumerate ``PRs/*``, load each
  ``PR_METADATA.json``, write ``PRs/README.md``.

Extra v2 columns are emitted whenever a record has a ``stats`` block;
records missing the block render ``—`` in the new columns (backwards
compatibility).
"""

from __future__ import annotations

from pathlib import Path

from bids_schema.metadata.io import iter_numeric_subdirs
from bids_schema.render import formatters as fmt

TABLE_HEADER = (
    "| PR # | # Authors | # Commenters | Build | Created | Reviews | Unresolved | "
    "Commits | First commit | Last commit | "
    "Comments | First comment | Last comment | Head | Actions |\n"
    "| ---- | --------- | ------------ | ----- | ------- | ------- | ---------- | "
    "------- | ------------ | ----------- | "
    "-------- | ------------- | ------------ | ---- | ------- |"
)


def _format_pr_row(pr_number: str, metadata: dict) -> str:
    stats = fmt.stats_of(metadata)
    cells = fmt.format_stats_cells(stats)

    pr_link = f"[{pr_number}]({fmt.pr_url(pr_number)})"
    authors_cell = fmt.format_contributors(metadata)
    build_cell = fmt.format_build_cell(metadata)

    head_raw = metadata.get("last_commit", "Unknown")
    if head_raw and head_raw != "Unknown":
        head_cell = f"[{head_raw[:10]}]({fmt.commit_url(head_raw)})"
    else:
        head_cell = "—"

    actions = fmt.format_actions_cell(
        "PRs", pr_number,
        build_status=fmt.build_status_of(metadata),
        error_log=metadata.get("error_log"),
    )

    return (
        f"| {pr_link} | {authors_cell} | {cells['commenters']} | {build_cell} | "
        f"{cells['pr_created']} | {cells['reviews']} | {cells['unresolved']} | "
        f"{cells['commits_count']} | {cells['commits_first']} | {cells['commits_last']} | "
        f"{cells['comments_count']} | {cells['comments_first']} | {cells['comments_last']} | "
        f"{head_cell} | {actions} |"
    )


def render(pr_records: list[tuple[str, dict]]) -> str:
    """Build the full ``PRs/README.md`` body given already-loaded records."""
    body_lines = [
        "# BIDS Specification PR Schemas",
        "",
        "This directory contains automatically generated schemas from Pull "
        "Requests to the BIDS specification that modify the schema files.",
        "",
        "## Overview",
        "",
        "Each subdirectory corresponds to a Pull Request (PR) number and contains:",
        "- `schema.json` — the compiled BIDS schema (pretty-printed alongside as `schema_pp.json`)",
        "- `PR_METADATA.json` — metadata about the PR: build status, author count,",
        "  and (schema v2+) an activity `stats` block with review / comment / thread counts.",
        "",
        "## Active PR Schemas",
        "",
    ]

    if not pr_records:
        body_lines.append("*No PR schemas currently available*")
    else:
        body_lines.append(TABLE_HEADER)
        pr_records_sorted = sorted(
            pr_records,
            key=lambda kv: int(kv[0]) if str(kv[0]).isdigit() else 0,
        )
        for pr_number, metadata in pr_records_sorted:
            if not metadata:
                continue
            body_lines.append(_format_pr_row(str(pr_number), metadata))

    body_lines.extend([
        "",
        "Column legend: **# Authors** = distinct people behind the commits on the PR "
        "branch, counting both the author and the committer of each commit and keyed on "
        "GitHub account (so one person who has committed under two name spellings, or who "
        "landed someone else\u2019s patch, is counted once \u2014 unlike `git shortlog`, which "
        "reads only the author field and groups by name); GitHub\u2019s own web-flow identity "
        "and `[bot]` accounts are excluded. "
        "**# Commenters** = distinct accounts that left an issue comment or opened a review "
        "thread. **Created** = when the PR was opened; "
        "**Reviews** = submitted reviews as `approved✅ / changes_requested❌ / commented💬`, "
        "zero-valued components omitted (so `1✅/27💬`, not `1✅/0❌/27💬`); "
        "**Unresolved** = count of unresolved inline review threads (bolded if > 0); "
        "**Commits** / **First commit** / **Last commit** = number of commits currently on the "
        "PR branch and their author-date range; **Comments** / **First comment** / **Last comment** = "
        "issue comments plus review threads and their date range; **Head** = the commit the schema "
        "here was built from. Counts and dates are separate columns so each can be sorted "
        "independently. An empty cell (`—`) means the stats block hasn't been collected yet.",
        "",
        "> **Why can `First comment` predate `First commit`?** The commit columns describe the "
        "commits *currently* on the PR branch. A force-push (rebase, squash, branch recreation) "
        "replaces them, and GitHub only reports what survived — so on a long-lived PR the "
        "earliest surviving commit can post-date the PR itself by years. `Created` is the PR's "
        "real start date; comments are never older than that.",
        "",
        "## How to Use PR Schemas",
        "",
        "1. **Accessing a schema**: navigate to `PRs/<pr_number>/schema.json` (or `schema_pp.json` for pretty).",
        "2. **Checking metadata**: view `PRs/<pr_number>/PR_METADATA.json`.",
        "3. **Raw schema files**: not stored — only the compiled schema is kept to reduce repo size.",
        "",
        "## Automation",
        "",
        f"[![Inject](https://github.com/{fmt.BIDS_SCHEMA_REPO}/actions/workflows/inject.yml/badge.svg)]"
        f"(https://github.com/{fmt.BIDS_SCHEMA_REPO}/actions/workflows/inject.yml)",
        "",
        "PR schemas and their stats blocks are refreshed on a cron cadence by the "
        f"[Schema Injection workflow](https://github.com/{fmt.BIDS_SCHEMA_REPO}/actions/workflows/inject.yml).",
        "",
        "## Related Resources",
        "",
        "- [BEP Schemas](../BEPs/) — BIDS Extension Proposal schemas",
        "- [Released Versions](../versions/) — official BIDS schema releases",
        f"- [BIDS Specification Repository](https://github.com/{fmt.BIDS_SPEC_REPO})",
        "",
    ])
    return "\n".join(body_lines)


def render_to_disk(base_dir: Path | None = None) -> Path:
    """Enumerate ``PRs/[0-9]*``, load metadata, write ``PRs/README.md``.

    Returns the path written. Empty PR sets still produce a valid README
    with the "no schemas" placeholder.
    """
    root = base_dir or Path.cwd()
    pr_root = root / "PRs"
    records: list[tuple[str, dict]] = []
    for pr_dir in iter_numeric_subdirs(pr_root):
        metadata = fmt.load_pr_record(pr_dir.name, base_dir=root)
        if metadata:
            records.append((pr_dir.name, metadata))

    body = render(records)
    out = pr_root / "README.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(body)
    print(f"Generated {out.relative_to(root)} with {len(records)} PR schemas")
    return out


if __name__ == "__main__":  # pragma: no cover
    render_to_disk()
