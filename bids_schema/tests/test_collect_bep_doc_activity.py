"""Tests for the BEP Google Doc activity collector (Drive API, API-key auth)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import responses

from bids_schema.collect import bep_doc_activity


@pytest.fixture(autouse=True)
def _api_key(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")


def _read(base_dir: Path, number) -> dict:
    return json.loads((base_dir / "BEPs" / str(number) / "BEP_METADATA.json").read_text())


@pytest.mark.ai_generated
def test_extract_doc_id_from_typical_url() -> None:
    doc_id = "1kyw9mGgacNqeMbp4xZet3RnDhcMmf4_BmRgKaOkO2Sc"
    url = f"https://docs.google.com/document/d/{doc_id}/edit"
    assert bep_doc_activity.extract_doc_id(url) == doc_id


@pytest.mark.ai_generated
def test_extract_doc_id_returns_none_when_unparseable() -> None:
    assert bep_doc_activity.extract_doc_id("https://example.org/not-a-doc") is None


@pytest.mark.ai_generated
@responses.activate
def test_fetch_doc_metadata_success() -> None:
    doc_id = "abc123"
    responses.add(
        responses.GET,
        bep_doc_activity.DRIVE_API_URL.format(file_id=doc_id),
        json={"modifiedTime": "2026-01-15T10:00:00.000Z", "version": "42", "name": "BEP doc"},
        status=200,
    )
    metadata = bep_doc_activity.fetch_doc_metadata(doc_id, api_key="fake-key")
    assert metadata == {"modified_time": "2026-01-15T10:00:00.000Z", "version": "42"}


@pytest.mark.ai_generated
@responses.activate
def test_fetch_doc_metadata_returns_none_on_error() -> None:
    doc_id = "private-doc"
    responses.add(
        responses.GET,
        bep_doc_activity.DRIVE_API_URL.format(file_id=doc_id),
        json={
            "error": {
                "code": 403,
                "status": "PERMISSION_DENIED",
                "message": "The caller does not have permission",
                "errors": [{"reason": "insufficientFilePermissions"}],
            }
        },
        status=403,
    )
    assert bep_doc_activity.fetch_doc_metadata(doc_id, api_key="fake-key") is None


@pytest.mark.ai_generated
@responses.activate
def test_fetch_doc_metadata_raises_on_invalid_api_key() -> None:
    doc_id = "any-doc"
    responses.add(
        responses.GET,
        bep_doc_activity.DRIVE_API_URL.format(file_id=doc_id),
        json={
            "error": {
                "code": 400,
                "status": "INVALID_ARGUMENT",
                "message": "API key not valid. Please pass a valid API key.",
            }
        },
        status=400,
    )
    with pytest.raises(bep_doc_activity.GoogleApiKeyError):
        bep_doc_activity.fetch_doc_metadata(doc_id, api_key="bad-key")


@pytest.mark.ai_generated
def test_compute_edits_since_last_check_diffs_versions() -> None:
    assert bep_doc_activity.compute_edits_since_last_check("10", "15") == 5


@pytest.mark.ai_generated
def test_compute_edits_since_last_check_none_without_previous() -> None:
    assert bep_doc_activity.compute_edits_since_last_check(None, "15") is None


@pytest.mark.ai_generated
def test_compute_edits_since_last_check_none_on_unparseable_values() -> None:
    assert bep_doc_activity.compute_edits_since_last_check("abc", "15") is None


@pytest.mark.ai_generated
def test_compute_edits_since_last_check_none_when_version_decreases() -> None:
    assert bep_doc_activity.compute_edits_since_last_check("20", "15") is None


@pytest.mark.ai_generated
def test_collect_raises_without_api_key(monkeypatch, base_dir: Path, make_bep) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    make_bep(11, google_doc="https://docs.google.com/document/d/AAA/")

    with pytest.raises(bep_doc_activity.GoogleApiKeyError):
        bep_doc_activity.collect(base_dir=base_dir)

    assert "doc_activity" not in _read(base_dir, 11)


@pytest.mark.ai_generated
@responses.activate
def test_collect_raises_on_invalid_api_key(base_dir: Path, make_bep) -> None:
    make_bep(11, google_doc="https://docs.google.com/document/d/AAA/")
    responses.add(
        responses.GET,
        bep_doc_activity.DRIVE_API_URL.format(file_id="AAA"),
        json={"error": {"status": "INVALID_ARGUMENT", "message": "API key not valid."}},
        status=400,
    )

    with pytest.raises(bep_doc_activity.GoogleApiKeyError):
        bep_doc_activity.collect(base_dir=base_dir)


@pytest.mark.ai_generated
def test_collect_skips_beps_without_a_google_doc(base_dir: Path, make_bep) -> None:
    make_bep(11, google_doc="")

    rc = bep_doc_activity.collect(base_dir=base_dir)

    assert rc == 0
    assert "doc_activity" not in _read(base_dir, 11)


@pytest.mark.ai_generated
@responses.activate
def test_collect_records_new_entry_on_success(base_dir: Path, make_bep) -> None:
    make_bep(11, google_doc="https://docs.google.com/document/d/cafef00d/")
    responses.add(
        responses.GET,
        bep_doc_activity.DRIVE_API_URL.format(file_id="cafef00d"),
        json={"modifiedTime": "2026-08-01T00:00:00.000Z", "version": "7"},
        status=200,
    )

    rc = bep_doc_activity.collect(base_dir=base_dir)

    assert rc == 0
    activity = _read(base_dir, 11)["doc_activity"]
    assert activity["last_modified"] == "2026-08-01T00:00:00.000Z"
    assert activity["version"] == "7"
    # First time this BEP is checked — nothing to diff against yet.
    assert activity["edits_since_last_check"] is None
    assert activity["_error"] is None
    assert "checked_at" in activity


@pytest.mark.ai_generated
@responses.activate
def test_collect_computes_edit_delta_against_previous_run(base_dir: Path, make_bep) -> None:
    make_bep(
        101, google_doc="https://docs.google.com/document/d/f00dcafe/",
        doc_activity={
            "last_modified": "2026-08-01T00:00:00.000Z",
            "version": "12",
            "edits_since_last_check": None,
            "checked_at": "2020-01-01T00:00:00Z",  # stale -> not fresh, forces re-fetch
            "_error": None,
        },
    )
    responses.add(
        responses.GET,
        bep_doc_activity.DRIVE_API_URL.format(file_id="f00dcafe"),
        json={"modifiedTime": "2026-08-15T00:00:00.000Z", "version": "20"},
        status=200,
    )

    rc = bep_doc_activity.collect(base_dir=base_dir)

    assert rc == 0
    activity = _read(base_dir, 101)["doc_activity"]
    assert activity["version"] == "20"
    assert activity["edits_since_last_check"] == 8


@pytest.mark.ai_generated
@responses.activate
def test_collect_keeps_previous_entry_on_fetch_failure(base_dir: Path, make_bep) -> None:
    """A transient fetch failure must not blank out a known-good status."""
    make_bep(
        99, google_doc="https://docs.google.com/document/d/deadbeef/",
        doc_activity={
            "last_modified": "2025-06-01T00:00:00.000Z",
            "version": "3",
            "edits_since_last_check": None,
            "checked_at": "2020-01-01T00:00:00Z",  # stale -> forces re-fetch
            "_error": None,
        },
    )
    responses.add(
        responses.GET,
        bep_doc_activity.DRIVE_API_URL.format(file_id="deadbeef"),
        body="server error",
        status=500,
    )

    rc = bep_doc_activity.collect(base_dir=base_dir)

    assert rc == 0
    activity = _read(base_dir, 99)["doc_activity"]
    assert activity["last_modified"] == "2025-06-01T00:00:00.000Z"
    assert activity["version"] == "3"
    assert activity["_error"] is True


@pytest.mark.ai_generated
def test_collect_respects_freshness_gate_unless_forced(base_dir: Path, make_bep) -> None:
    make_bep(
        11, google_doc="https://docs.google.com/document/d/AAA/",
        doc_activity={
            "last_modified": "2026-08-01T00:00:00.000Z",
            "version": "1",
            "edits_since_last_check": None,
            "checked_at": bep_doc_activity.now_utc_iso(),  # just checked -> fresh
            "_error": None,
        },
    )

    # No responses registered at all — a real fetch attempt would error.
    rc = bep_doc_activity.collect(base_dir=base_dir)

    assert rc == 0
    assert _read(base_dir, 11)["doc_activity"]["version"] == "1"


@pytest.mark.ai_generated
def test_collect_only_filters_to_requested_beps(base_dir: Path, make_bep) -> None:
    make_bep(11, google_doc="")
    make_bep(12, google_doc="")

    # Both have no google_doc, so nothing to fetch either way — this just
    # exercises that `only` doesn't blow up and scopes iteration.
    rc = bep_doc_activity.collect(base_dir=base_dir, only=["11"])

    assert rc == 0
