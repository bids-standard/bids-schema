"""Render ``BEPs/README.md`` from on-disk metadata.

Enforces invariant #1 from the design plan: BEP-side PR facts come from
``fmt.load_pr_record`` at render time — never re-collected into
``BEP_METADATA.json``. The BEP metadata only owns BEP-layer fields
(title, google_doc URL, registration timestamps, doc activity, PR linkage).
"""

from __future__ import annotations

from pathlib import Path

from bids_schema.metadata.io import iter_numeric_subdirs
from bids_schema.render import formatters as fmt

TABLE_HEADER = (
    "| BEP # | Title | Doc Activity | PR # | # Authors | # Commenters | Build | "
    "Reviews | Unresolved | Comments | First comment | Last comment | "
    "BEP registered | Doc registered | Actions |\n"
    "| ----- | ----- | ------------ | ---- | --------- | ------------ | ----- | "
    "------- | ---------- | -------- | ------------- | ------------ | "
    "-------------- | -------------- | ------- |"
)

FOOTER_DEPRECATION_NOTE = (
    "> ⚠ **Note on `BEPs/<NN>/PR_METADATA.json`.** These files are copied "
    "unchanged from the sibling `PRs/<N>/PR_METADATA.json` and are scheduled "
    "for removal in a future cron cycle. Downstream consumers should read "
    "PR-derived facts from `PRs/<N>/PR_METADATA.json` directly."
)


def _format_bep_row(bep_number: str, metadata: dict, base_dir: Path | None) -> str:
    title = metadata.get("title", "Unknown")
    pr_number = metadata.get("pr_number", "")
    google_doc = metadata.get("google_doc", "")

    pr_metadata: dict = {}
    if pr_number:
        pr_metadata = fmt.load_pr_record(pr_number, base_dir=base_dir)

    stats = fmt.stats_of(pr_metadata)
    cells = fmt.format_stats_cells(stats)

    bep_display_number = str(bep_number).zfill(3)
    bep_url = f"https://bids.neuroimaging.io/bep{bep_display_number}"
    bep_display = f"[{bep_display_number}]({bep_url})"

    doc_activity = metadata.get("doc_activity")
    if not google_doc:
        doc_cell = "—"
    elif not doc_activity:
        doc_cell = "⚪ Not checked yet"
    else:
        badge = fmt.bep_activity_badge(
            doc_activity.get("last_modified"),
            doc_activity.get("edits_since_last_check"),
        )
        doc_cell = f"[{badge['icon']} {badge['label']}]({google_doc})"

    pr_link = f"[{pr_number}]({fmt.pr_url(pr_number)})" if pr_number else "—"

    authors_cell = fmt.format_contributors(pr_metadata) if pr_metadata else "—"
    build_cell = fmt.format_build_cell(pr_metadata) if pr_metadata else fmt.format_build_indicator("unknown")

    bep_registered_cell = fmt.format_date(metadata.get("bep_registered"))
    doc_registered_cell = fmt.format_date(metadata.get("googledoc_registered"))

    actions = fmt.format_actions_cell(
        "BEPs", str(bep_number),
        build_status=fmt.build_status_of(pr_metadata),
        error_log=pr_metadata.get("error_log"),
        error_log_href=f"../PRs/{pr_number}/bst-output.log" if pr_number else None,
    )

    return (
        f"| {bep_display} | {title} | {doc_cell} | {pr_link} | {authors_cell} | "
        f"{cells['commenters']} | {build_cell} | "
        f"{cells['reviews']} | {cells['unresolved']} | "
        f"{cells['comments_count']} | {cells['comments_first']} | {cells['comments_last']} | "
        f"{bep_registered_cell} | {doc_registered_cell} | {actions} |"
    )


def render(bep_records: list[tuple[str, dict]], base_dir: Path | None = None) -> str:
    """Build the full ``BEPs/README.md`` body given already-loaded BEP records.

    ``base_dir`` scopes the read-through join to sibling ``PRs/<N>/`` records;
    ``None`` uses ``Path.cwd()``.
    """
    body_lines = [
        "# BIDS Extension Proposals (BEPs) Schemas",
        "",
        "This directory contains automatically generated schemas for BIDS Extension Proposals.",
        "Each BEP schema is linked to the Pull Request in `bids-specification` that owns it.",
        "",
        "## Overview",
        "",
        "BIDS Extension Proposals (BEPs) are community-driven extensions to the BIDS specification.",
        "This directory provides compiled schemas for BEPs whose associated PR modifies the schema.",
        "",
        "Each subdirectory corresponds to a BEP number and contains:",
        "- `schema.json` — the compiled BIDS schema (pretty-printed alongside as `schema_pp.json`)",
        "- `BEP_METADATA.json` — BEP-layer metadata: title, `google_doc` URL, PR linkage,",
        "  registration timestamps (`bep_registered`, `googledoc_registered`), and",
        "  (schema v3+) `doc_activity` — how recently the Google Doc itself was edited,",
        "  fetched via the Google Drive API (see `bids_schema.collect.bep_doc_activity`).",
        "  PR-derived facts (author count, build status, review counts, …) are joined at",
        "  render time from the sibling `PRs/<N>/PR_METADATA.json` — never re-collected.",
        "",
        "## Active BEP Schemas",
        "",
    ]

    if not bep_records:
        body_lines.append("*No BEP schemas currently available*")
    else:
        body_lines.append(TABLE_HEADER)
        bep_records_sorted = sorted(
            bep_records,
            key=lambda kv: int(kv[0]) if str(kv[0]).isdigit() else 0,
        )
        for bep_number, metadata in bep_records_sorted:
            if not metadata:
                continue
            body_lines.append(_format_bep_row(str(bep_number), metadata, base_dir=base_dir))

    body_lines.extend([
        "",
        "Column legend: **Doc Activity** = 🟢 edited in the last 30 days / 🟡 edited in "
        "the last 6 months / 🔴 not edited in over 6 months / ⚪ unknown (not checked yet, "
        "or the doc isn't publicly viewable), linking to the Google Doc itself; "
        "**# Authors** = distinct people behind the linked PR\u2019s commits, "
        "counting both the author and the committer of each commit and keyed on GitHub "
        "account rather than on name; **# Commenters** = distinct accounts that commented "
        "on that PR. **Reviews** = submitted reviews as "
        "`approved✅ / changes_requested❌ / commented💬`, zero-valued components omitted "
        "(so `1✅/27💬`, not `1✅/0❌/27💬`); "
        "**Unresolved** = count of unresolved inline review threads (bolded if > 0); "
        "**Comments** / **First comment** / **Last comment** = issue comments plus review threads "
        "on the linked PR, count and dates split so each can be sorted independently; "
        "**BEP registered** = date the BEP entry was first added to `bids-website:data/beps/beps.yml`; "
        "**Doc registered** = date a `google_doc` URL was first attached to that entry. "
        "See [`PRs/README.md`](../PRs/) for the full per-PR commit statistics.",
        "",
        FOOTER_DEPRECATION_NOTE,
        "",
        "## How to Use BEP Schemas",
        "",
        "1. **Accessing a schema**: navigate to `BEPs/<bep_number>/schema.json`.",
        "2. **Checking metadata**: view `BEPs/<bep_number>/BEP_METADATA.json`.",
        "3. **Finding the source PR**: follow the PR link in the table above.",
        "",
        "## BEP Process",
        "",
        "1. **Draft** — initial proposal and discussion",
        "2. **Under Review** — active development and community feedback",
        "3. **Accepted** — approved for inclusion in BIDS",
        "4. **Archived** — historical BEPs no longer under active development",
        "",
        "## Automation",
        "",
        f"[![Inject](https://github.com/{fmt.BIDS_SCHEMA_REPO}/actions/workflows/inject.yml/badge.svg)]"
        f"(https://github.com/{fmt.BIDS_SCHEMA_REPO}/actions/workflows/inject.yml)",
        "",
        "BEP schemas are synchronised with their PRs by the "
        f"[Schema Injection workflow](https://github.com/{fmt.BIDS_SCHEMA_REPO}/actions/workflows/inject.yml).",
        "",
        "## Related Resources",
        "",
        "- [PR Schemas](../PRs/) — all Pull Request schemas",
        "- [Released Versions](../versions/) — official BIDS schema releases",
        "- [BIDS Website — BEPs](https://bids.neuroimaging.io/beps) — official BEP documentation",
        f"- [BIDS Specification Repository](https://github.com/{fmt.BIDS_SPEC_REPO})",
        "",
    ])
    return "\n".join(body_lines)


def render_to_disk(base_dir: Path | None = None) -> Path:
    """Enumerate ``BEPs/[0-9]*``, load metadata, write ``BEPs/README.md``.

    Returns the path written. Missing directory still writes a valid
    README with the "no schemas" placeholder.
    """
    root = base_dir or Path.cwd()
    bep_root = root / "BEPs"
    records: list[tuple[str, dict]] = []
    for bep_dir in iter_numeric_subdirs(bep_root):
        metadata = fmt.load_bep_record(bep_dir.name, base_dir=root)
        if metadata:
            records.append((bep_dir.name, metadata))

    body = render(records, base_dir=root)
    out = bep_root / "README.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(body)
    print(f"Generated {out.relative_to(root)} with {len(records)} BEP schemas")
    return out


if __name__ == "__main__":  # pragma: no cover
    render_to_disk()
