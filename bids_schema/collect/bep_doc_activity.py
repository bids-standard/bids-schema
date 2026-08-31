"""Fetch Google Drive activity metadata for BEP Google Docs.

Populates the ``doc_activity`` block of ``BEPs/<NN>/BEP_METADATA.json``
so the BEP dashboard can show how recently — and how much — each BEP's
Google Doc has actually been touched, alongside the existing
``bep_registered`` / ``googledoc_registered`` git-history timestamps.

Ported from the ``markmikkelsen/bids-website/tree/bep-dashboard``
(``tools/build/fetch_bep_doc_activity.py`` + ``macros/macros.py``),
adapted to merge into the per-BEP ``BEP_METADATA.json`` that this repo
already treats as the single source of truth for BEP-layer facts,
instead of a separate ``beps_status.yml``.

This only reads file *metadata* via the Drive API using a plain API
key — it therefore only works for BEP Google Docs shared as "Anyone
with the link can view" (or more open), which is the norm for BEP
drafts. Docs that are not link-shared simply keep whatever
``doc_activity`` was last recorded (or stay unrecorded, which the
renderer shows as "not checked yet"). Two fields come out of this:

- ``last_modified``: when the doc was last edited (Drive's ``modifiedTime``).
- ``version``: an integer Google increments on every save. Comparing it
  to the value recorded on the *previous* run gives a rough "how many
  edits since we last checked" count — useful extra signal, and still
  just an API-key call (unlike comment counts or full revision
  history, which need OAuth/a service account).

Requires the ``GOOGLE_API_KEY`` environment variable, pointing at an API
key with the Google Drive API enabled. A missing key — or a key the
Drive API rejects as invalid — is a hard error: ``collect`` raises
``GoogleApiKeyError`` rather than skipping the phase. (A per-doc
403/404 because a single BEP doc isn't link-shared is *not* a key
problem and is still handled gracefully — that doc keeps its last
recorded ``doc_activity``.)

Public entry point: ``collect(only, force, base_dir)``. Returns a
process-exit code (0 = OK); raises ``GoogleApiKeyError`` when the API
key is missing or invalid.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import requests

from bids_schema.metadata.io import iter_numeric_subdirs, load_json, write_json_atomic
from bids_schema.metadata.schema import CURRENT_BEP_SCHEMA_VERSION
from bids_schema.metadata.time import now_utc_iso

log = logging.getLogger(__name__)


class GoogleApiKeyError(RuntimeError):
    """The ``GOOGLE_API_KEY`` is missing, or the Drive API rejected it."""


# Substrings that mark a Drive API error as an API-key problem (bad key,
# expired key, referer/IP restriction) rather than a per-file permission
# issue. Matched case-insensitively against the error's status, message,
# and per-error ``reason`` fields, gated on a 400/401/403 status.
_API_KEY_ERROR_MARKERS = (
    "api key not valid",
    "api_key_invalid",
    "api_key_service_blocked",
    "keyinvalid",
    "keyexpired",
    "iprefererblocked",
    "ipreferernotallowed",
)

DRIVE_FILE_ID_RE = re.compile(r"/d/([a-zA-Z0-9_-]+)")
DRIVE_API_URL = "https://www.googleapis.com/drive/v3/files/{file_id}"
DRIVE_FIELDS = "modifiedTime,version,name"
REQUEST_TIMEOUT = 15

# Freshness floor: at the twice-daily `inject` cadence, this keeps actual
# Drive API calls to roughly once a day per BEP. `BEP_DOC_ACTIVITY_MAX_AGE`
# overrides (seconds).
DEFAULT_MAX_AGE_SECONDS = 20 * 60 * 60
MAX_AGE_SECONDS = int(
    os.environ.get("BEP_DOC_ACTIVITY_MAX_AGE", DEFAULT_MAX_AGE_SECONDS)
)


def extract_doc_id(google_doc_url: str) -> str | None:
    """Pull the Drive file id out of a Google Doc URL."""
    match = DRIVE_FILE_ID_RE.search(google_doc_url)
    return match.group(1) if match else None


def _is_api_key_error(response: requests.Response) -> bool:
    """True when a non-200 Drive response blames the API key itself.

    Distinguishes "this key is bad" (fatal, affects every request) from
    "this particular doc isn't link-shared" (a 403/404 we tolerate).
    """
    if response.status_code not in (400, 401, 403):
        return False
    try:
        error = response.json().get("error", {}) or {}
    except ValueError:
        return False
    haystack = " ".join(
        str(part)
        for part in (
            error.get("status", ""),
            error.get("message", ""),
            *(
                e.get("reason", "")
                for e in error.get("errors", [])
                if isinstance(e, dict)
            ),
        )
    ).lower()
    return any(marker in haystack for marker in _API_KEY_ERROR_MARKERS)


def fetch_doc_metadata(doc_id: str, api_key: str) -> dict | None:
    """Return ``{"modified_time": ..., "version": ...}``, or ``None``.

    ``version`` comes back from the Drive API as a stringified int64;
    it is returned as-is here (still a string) and parsed by callers.

    Raises ``GoogleApiKeyError`` when the response indicates the API key
    is invalid/expired/blocked — that condition is not per-doc and there
    is no point continuing the run.
    """
    response = requests.get(
        DRIVE_API_URL.format(file_id=doc_id),
        params={"fields": DRIVE_FIELDS, "key": api_key},
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code != 200:
        if _is_api_key_error(response):
            raise GoogleApiKeyError(
                f"Google Drive API rejected GOOGLE_API_KEY "
                f"(HTTP {response.status_code}): {response.text[:200]}"
            )
        log.warning(
            "Could not fetch metadata for doc %s (HTTP %s): %s",
            doc_id,
            response.status_code,
            response.text[:200],
        )
        return None

    data = response.json()
    return {
        "modified_time": data.get("modifiedTime"),
        "version": data.get("version"),
    }


def compute_edits_since_last_check(
    previous_version: str | None, current_version: str | None
) -> int | None:
    """Diff two Drive ``version`` values into an edit count.

    Returns ``None`` when there's nothing to compare against (first
    time this BEP is checked) or the values can't be parsed. A
    negative diff would mean the doc's version went backwards, which
    shouldn't happen — treated as "nothing to report" rather than
    trusted.
    """
    if previous_version is None or current_version is None:
        return None
    try:
        diff = int(current_version) - int(previous_version)
    except (TypeError, ValueError):
        return None
    return diff if diff >= 0 else None


def _is_fresh(existing: dict) -> bool:
    if not existing or existing.get("_error"):
        return False
    checked_at = existing.get("checked_at")
    if not checked_at:
        return False
    try:
        checked_dt = datetime.fromisoformat(checked_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    age = (datetime.now(timezone.utc) - checked_dt).total_seconds()
    return age < MAX_AGE_SECONDS


def collect(
    only: list[str] | None = None, force: bool = False, base_dir: Path | None = None
) -> int:
    """Refresh ``doc_activity`` in every ``BEPs/<NN>/BEP_METADATA.json`` with a Google Doc.

    Returns a process-exit code (0 = OK; no ``BEPs/`` directory just
    means "nothing to do"). Raises ``GoogleApiKeyError`` when
    ``GOOGLE_API_KEY`` is unset or the Drive API rejects it.
    """
    logging.basicConfig(
        level=os.environ.get("BIDS_SCHEMA_LOGLEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(message)s",
    )
    root = base_dir or Path.cwd()
    bep_root = root / "BEPs"

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise GoogleApiKeyError(
            "GOOGLE_API_KEY is not set; cannot collect BEP Google Doc activity. "
            "Set it to a Google Drive API key with the Drive API enabled."
        )

    if not bep_root.is_dir():
        log.info("No BEPs/ directory at %s; nothing to collect.", root)
        return 0

    only_set = {str(x).lstrip("0") for x in (only or []) if str(x).lstrip("0")}
    num_updated = 0
    num_skipped = 0
    num_errored = 0

    for bep_dir in iter_numeric_subdirs(bep_root):
        bep_number_norm = bep_dir.name.lstrip("0") or "0"
        if only_set and bep_number_norm not in only_set:
            num_skipped += 1
            continue

        record_path = bep_dir / "BEP_METADATA.json"
        record = load_json(record_path)
        if not record:
            continue

        google_doc = record.get("google_doc")
        if not google_doc:
            continue

        existing = record.get("doc_activity") or {}
        if not force and _is_fresh(existing):
            num_skipped += 1
            continue

        doc_id = extract_doc_id(google_doc)
        if doc_id is None:
            log.warning(
                "BEP %s: could not parse a doc id out of %r", bep_dir.name, google_doc
            )
            continue

        metadata = fetch_doc_metadata(doc_id, api_key)
        checked_at = now_utc_iso()

        if metadata is None or metadata["modified_time"] is None:
            # Keep whatever was last recorded rather than blanking it out —
            # a transient 403/404 shouldn't make a BEP look unchecked.
            if existing:
                existing["_error"] = True
                existing["checked_at"] = checked_at
                record["doc_activity"] = existing
                record["_schema_version"] = CURRENT_BEP_SCHEMA_VERSION
                write_json_atomic(record_path, record)
            num_errored += 1
            continue

        edits_since_last_check = compute_edits_since_last_check(
            existing.get("version"), metadata["version"]
        )

        record["doc_activity"] = {
            "last_modified": metadata["modified_time"],
            "version": metadata["version"],
            "edits_since_last_check": edits_since_last_check,
            "checked_at": checked_at,
            "_error": None,
        }
        record["_schema_version"] = CURRENT_BEP_SCHEMA_VERSION
        write_json_atomic(record_path, record)
        num_updated += 1

    log.info(
        "Done. updated=%d skipped=%d errored=%d", num_updated, num_skipped, num_errored
    )
    return 0
