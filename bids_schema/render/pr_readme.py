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

from bids_schema.render import formatters as fmt

TABLE_HEADER = (
    "| PR # | Authors | Build | Reviews | Comments | Unresolved | "
    "Commit window | Last commit | Actions |\n"
    "| ---- | ------- | ----- | ------- | -------- | ---------- | "
    "------------- | ----------- | ------- |"
)


def _format_pr_row(pr_number: str, metadata: dict) -> str:
    stats = fmt.stats_of(metadata)

    pr_link = f"[{pr_number}]({fmt.pr_url(pr_number)})"
    authors_count = str(metadata.get("authors_count", 0))
    build_status = fmt.build_status_of(metadata)
    build_indicator = fmt.format_build_indicator(build_status)

    reviews_cell = fmt.format_reviews(stats.get("reviews")) if stats else "—"

    comments_block = stats.get("comments") or {}
    comments_cell = fmt.format_activity_span(
        comments_block.get("total"),
        comments_block.get("first_at"),
        comments_block.get("last_at"),
    )

    threads_block = stats.get("review_threads") or {}
    unresolved_cell = fmt.format_unresolved(threads_block.get("unresolved"))

    commits_block = stats.get("commits") or {}
    commit_window = fmt.format_date_window(
        commits_block.get("first_at"),
        commits_block.get("last_at"),
    )

    last_commit_raw = metadata.get("last_commit", "Unknown")
    if last_commit_raw and last_commit_raw != "Unknown":
        last_commit_cell = f"[{last_commit_raw[:10]}]({fmt.commit_url(last_commit_raw)})"
    else:
        last_commit_cell = "—"

    schema_path = f"./{pr_number}/schema.json"
    actions = (
        f"[Schema]({schema_path}) \\| "
        f"[Raw]({fmt.raw_url('PRs', pr_number, 'schema.json')}) \\| "
        f"[Pretty]({fmt.raw_url('PRs', pr_number, 'schema_pp.json')})"
    )
    if build_status == "failed" and metadata.get("error_log"):
        actions += f" \\| [Error Log](./{pr_number}/bst-output.log)"

    marker = fmt.stale_marker(stats)
    if marker:
        build_indicator = f"{build_indicator}{marker}"

    return (
        f"| {pr_link} | {authors_count} | {build_indicator} | "
        f"{reviews_cell} | {comments_cell} | {unresolved_cell} | "
        f"{commit_window} | {last_commit_cell} | {actions} |"
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
        "Column legend: **Reviews** = `approved✅ / changes_requested❌ / commented💬`; "
        "**Unresolved** = count of unresolved inline review threads (bolded if > 0); "
        "**Commit window** = first → last commit dates on the PR branch. "
        "An empty cell (`—`) means the stats block hasn't been collected yet.",
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
    if pr_root.is_dir():
        for pr_dir in sorted(pr_root.iterdir()):
            if not pr_dir.is_dir() or not pr_dir.name.isdigit():
                continue
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
