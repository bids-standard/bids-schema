"""Tests for the BEP README renderer, including read-through join."""

from __future__ import annotations

from pathlib import Path

import pytest

from bids_schema.render import bep_readme


@pytest.mark.ai_generated
def test_empty_bep_list_still_renders() -> None:
    body = bep_readme.render([])
    assert "*No BEP schemas currently available*" in body
    assert "# BIDS Extension Proposals (BEPs) Schemas" in body


@pytest.mark.ai_generated
def test_render_to_disk_joins_pr_stats(base_dir: Path, make_pr, make_bep) -> None:
    # PR record with a stats block
    make_pr(518, authors_count=2, build_status="success", **{"_schema_version": 2})
    # Inject stats block manually into that record
    import json
    pr_path = base_dir / "PRs" / "518" / "PR_METADATA.json"
    pr_data = json.loads(pr_path.read_text())
    pr_data["stats"] = {
        "_complete": True,
        "_error": None,
        "reviews": {"approved": 3, "changes_requested": 0, "commented": 1},
        "comments": {"total": 12, "first_at": "2020-01-16T00:00:00Z",
                     "last_at": "2026-05-08T00:00:00Z"},
        "review_threads": {"unresolved": 2},
    }
    pr_path.write_text(json.dumps(pr_data))

    # BEP linked to that PR — no PR-derived fields on this record.
    make_bep(11, title="Structural preprocessing", pr_number=518,
             google_doc="https://docs.google.com/document/d/1YG2g/")

    out = bep_readme.render_to_disk(base_dir=base_dir)
    body = out.read_text()

    # BEP number rendered with zero-padding + link
    assert "[011]" in body
    # PR link rendered
    assert "pull/518" in body
    # Google Doc has a URL but no doc_activity collected yet
    assert "⚪ Not checked yet" in body
    # PR stats joined from sibling PR_METADATA.json
    row = next(line for line in body.splitlines() if "[011]" in line)
    # Zero-valued changes_requested component dropped from the row (the legend
    # still mentions `0❌` as a counter-example, so assert on the row only).
    assert "3✅/1💬" in row
    assert "0❌" not in row
    assert "**2**" in row
    cells = [c.strip() for c in row.split("|")[1:-1]]
    # ... | Comments | First comment | Last comment | ...
    assert cells[8] == "12"
    assert cells[9] == "2020-01-16"
    assert cells[10] == "2026-05-08"


@pytest.mark.ai_generated
def test_render_bep_with_no_google_doc_shows_dash(base_dir: Path, make_bep) -> None:
    make_bep(21, title="No doc BEP", google_doc="")
    body = bep_readme.render_to_disk(base_dir=base_dir).read_text()
    row = next(line for line in body.splitlines() if "[021]" in line)
    cells = [c.strip() for c in row.split("|")]
    # Columns: '', BEP #, Title, Doc Activity, PR #, ...
    assert cells[3] == "—"


@pytest.mark.ai_generated
def test_render_bep_renders_doc_activity_badge(base_dir: Path, make_bep) -> None:
    make_bep(
        22, title="Active doc BEP",
        google_doc="https://docs.google.com/document/d/XYZ/",
        doc_activity={
            "last_modified": "2026-08-20T00:00:00.000Z",
            "version": "5",
            "edits_since_last_check": 2,
            "checked_at": "2026-08-20T00:00:00Z",
            "_error": None,
        },
    )
    body = bep_readme.render_to_disk(base_dir=base_dir).read_text()
    row = next(line for line in body.splitlines() if "[022]" in line)
    assert "docs.google.com/document/d/XYZ" in row
    assert "Edited" in row and "day" in row


@pytest.mark.ai_generated
def test_render_bep_with_missing_pr_record_uses_dashes(base_dir: Path, make_bep) -> None:
    make_bep(42, title="Orphan BEP", pr_number=99999)  # no PR file on disk
    out = bep_readme.render_to_disk(base_dir=base_dir)
    body = out.read_text()
    row = next(line for line in body.splitlines() if "[042]" in line)
    # No PR record → stats columns are "—"
    assert "| — |" in row


@pytest.mark.ai_generated
def test_bep_renders_registration_dates(base_dir: Path, make_pr, make_bep) -> None:
    make_pr(518)
    make_bep(11, pr_number=518,
             bep_registered="2018-05-12T14:03:11Z",
             googledoc_registered="2019-11-02T08:30:00Z")
    body = bep_readme.render_to_disk(base_dir=base_dir).read_text()
    row = next(line for line in body.splitlines() if "[011]" in line)
    assert "2018-05-12" in row
    assert "2019-11-02" in row


@pytest.mark.ai_generated
def test_footer_deprecation_note_present(base_dir: Path, make_pr, make_bep) -> None:
    make_pr(518)
    make_bep(11, pr_number=518)
    body = bep_readme.render_to_disk(base_dir=base_dir).read_text()
    assert "BEPs/<NN>/PR_METADATA.json" in body
    assert "scheduled for removal" in body
