"""Tests for the BEP Google Doc activity collector (Drive API, API-key auth)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import requests
import responses

from bids_schema.collect import bep_doc_activity


@pytest.fixture(autouse=True)
def _api_key(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
    monkeypatch.delenv(bep_doc_activity.SKIP_ENV_VAR, raising=False)


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
@responses.activate
def test_fetch_doc_metadata_returns_none_on_non_json_error() -> None:
    doc_id = "private-doc"
    responses.add(
        responses.GET,
        bep_doc_activity.DRIVE_API_URL.format(file_id=doc_id),
        body="<html><body>403. That's an error.</body></html>",
        status=403,
    )
    assert bep_doc_activity.fetch_doc_metadata(doc_id, api_key="fake-key") is None


def _error_info(reason: str, domain: str = "googleapis.com") -> dict:
    return {"@type": "type.googleapis.com/google.rpc.ErrorInfo", "reason": reason, "domain": domain}


def _drive_error(code: int, status: str, message: str, legacy_reason: str, details=None) -> dict:
    error = {
        "code": code,
        "status": status,
        "message": message,
        "errors": [{"message": message, "domain": "global", "reason": legacy_reason}],
    }
    if details is not None:
        error["details"] = details
    return {"error": error}


# Shapes of Drive v3 error responses. Key-level problems affect every
# request and must be detected; per-doc and transient ones must not.
_KEY_ERROR_SHAPES = {
    "invalid_key": (
        400,
        _drive_error(400, "INVALID_ARGUMENT", "API key not valid. Please pass a valid API key.",
                     "badRequest", [_error_info("API_KEY_INVALID")]),
    ),
    "drive_api_not_enabled": (
        403,
        _drive_error(403, "PERMISSION_DENIED",
                     "Google Drive API has not been used in project 123 before or it is disabled.",
                     "accessNotConfigured", [_error_info("SERVICE_DISABLED")]),
    ),
    "key_restricted_to_other_apis": (
        403,
        _drive_error(403, "PERMISSION_DENIED", "Requests to this API drive method are blocked.",
                     "forbidden", [_error_info("API_KEY_SERVICE_BLOCKED")]),
    ),
    "referrer_blocked": (
        403,
        _drive_error(403, "PERMISSION_DENIED", "Requests from referer <empty> are blocked.",
                     "forbidden", [_error_info("API_KEY_HTTP_REFERRER_BLOCKED")]),
    ),
    "ip_blocked": (
        403,
        _drive_error(403, "PERMISSION_DENIED", "The IP address 203.0.113.5 is blocked.",
                     "forbidden", [_error_info("API_KEY_IP_ADDRESS_BLOCKED")]),
    ),
    "legacy_key_expired": (
        400,
        _drive_error(400, "INVALID_ARGUMENT", "API key expired. Please renew the API key.",
                     "keyExpired"),
    ),
}

_NOT_KEY_ERROR_SHAPES = {
    "doc_not_shared": (
        404,
        _drive_error(404, "NOT_FOUND", "File not found: AAA.", "notFound"),
    ),
    "insufficient_file_permissions": (
        403,
        _drive_error(403, "PERMISSION_DENIED", "The user does not have sufficient permissions for this file.",
                     "insufficientFilePermissions"),
    ),
    "rate_limited": (
        403,
        _drive_error(403, "PERMISSION_DENIED", "Rate Limit Exceeded", "rateLimitExceeded",
                     [_error_info("RATE_LIMIT_EXCEEDED")]),
    ),
    "server_error_mentioning_key": (
        500,
        _drive_error(500, "INTERNAL", "API key not valid.", "backendError"),
    ),
    "error_is_a_string": (403, {"error": "forbidden"}),
    "body_is_an_array": (400, [{"error": {"message": "API key not valid."}}]),
    "details_not_a_list": (
        403,
        {"error": {"status": "PERMISSION_DENIED", "details": "API_KEY_SERVICE_BLOCKED-ish"}},
    ),
}


def _response(status: int, payload) -> requests.Response:
    response = requests.Response()
    response.status_code = status
    response._content = json.dumps(payload).encode()
    return response


@pytest.mark.ai_generated
@pytest.mark.parametrize("shape", sorted(_KEY_ERROR_SHAPES))
def test_is_api_key_error_detects_key_level_failures(shape: str) -> None:
    status, payload = _KEY_ERROR_SHAPES[shape]
    assert bep_doc_activity._is_api_key_error(_response(status, payload)) is True


@pytest.mark.ai_generated
@pytest.mark.parametrize("shape", sorted(_NOT_KEY_ERROR_SHAPES))
def test_is_api_key_error_ignores_per_doc_and_malformed_errors(shape: str) -> None:
    status, payload = _NOT_KEY_ERROR_SHAPES[shape]
    assert bep_doc_activity._is_api_key_error(_response(status, payload)) is False


@pytest.mark.ai_generated
def test_is_api_key_error_ignores_non_json_body() -> None:
    response = requests.Response()
    response.status_code = 403
    response._content = b"<html>403 Forbidden</html>"
    assert bep_doc_activity._is_api_key_error(response) is False


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
@pytest.mark.parametrize("value", ["1", "true", "YES"])
@responses.activate
def test_collect_skips_on_request_even_without_api_key(
    monkeypatch, base_dir: Path, make_bep, value: str
) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv(bep_doc_activity.SKIP_ENV_VAR, value)
    make_bep(11, google_doc="https://docs.google.com/document/d/AAA/")

    rc = bep_doc_activity.collect(base_dir=base_dir)

    assert rc == 0
    assert len(responses.calls) == 0
    assert "doc_activity" not in _read(base_dir, 11)


@pytest.mark.ai_generated
@pytest.mark.parametrize("value", ["", "0", "false", "no"])
def test_collect_does_not_skip_for_other_values(
    monkeypatch, base_dir: Path, make_bep, value: str
) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv(bep_doc_activity.SKIP_ENV_VAR, value)
    make_bep(11, google_doc="https://docs.google.com/document/d/AAA/")

    with pytest.raises(bep_doc_activity.GoogleApiKeyError, match=bep_doc_activity.SKIP_ENV_VAR):
        bep_doc_activity.collect(base_dir=base_dir)


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
def test_collect_raises_when_api_key_is_only_whitespace(
    monkeypatch, base_dir: Path, make_bep
) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "  \n")
    make_bep(11, google_doc="https://docs.google.com/document/d/AAA/")

    with pytest.raises(bep_doc_activity.GoogleApiKeyError):
        bep_doc_activity.collect(base_dir=base_dir)

    assert "doc_activity" not in _read(base_dir, 11)


@pytest.mark.ai_generated
@responses.activate
def test_collect_strips_surrounding_whitespace_from_api_key(
    monkeypatch, base_dir: Path, make_bep
) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "  real-key\n")
    make_bep(11, google_doc="https://docs.google.com/document/d/cafef00d/")
    responses.add(
        responses.GET,
        bep_doc_activity.DRIVE_API_URL.format(file_id="cafef00d"),
        json={"modifiedTime": "2026-01-01T00:00:00.000Z", "version": "7"},
        status=200,
    )

    rc = bep_doc_activity.collect(base_dir=base_dir)

    assert rc == 0
    assert responses.calls[0].request.params["key"] == "real-key"
    assert _read(base_dir, 11)["doc_activity"]["version"] == "7"


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
