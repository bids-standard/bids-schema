"""Atomic read-modify-write helpers for JSON metadata files, plus the
canonical emitters for ``PR_METADATA.json`` and ``BEP_METADATA.json``.

The write path is deliberately atomic: write to ``<path>.tmp``, ``os.replace``
onto ``<path>``. A crashed / killed collector never leaves partially-written
JSON on disk.

Per design plan §2 ("Bash stays out of the JSON we care about"),
``PR_METADATA.json`` and ``BEP_METADATA.json`` are only ever written
through the ``write_*_metadata`` helpers here — the bash pipeline
delegates via the ``bids-schema metadata write-pr`` / ``write-bep``
subcommands.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from pathlib import Path

from bids_schema.metadata.schema import (
    CURRENT_BEP_SCHEMA_VERSION,
    CURRENT_PR_SCHEMA_VERSION,
)
from bids_schema.metadata.time import now_utc_iso


def load_json(path: Path | str) -> dict:
    """Read a JSON file. Missing / malformed → empty dict."""
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def write_json_atomic(path: Path | str, data: dict, *, indent: int = 2) -> None:
    """Write ``data`` to ``path`` atomically via a ``.tmp`` sibling + rename."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=indent, sort_keys=False)
        f.write("\n")
    os.replace(tmp, p)


def update_json_atomic(path: Path | str, mutate: Callable[[dict], dict]) -> dict:
    """Read ``path`` (or ``{}``), apply ``mutate`` in-place, atomically write back.

    Returns the post-mutation dict.

    ``mutate`` may modify in-place and return the same dict, or return a new one.
    """
    current = load_json(path)
    updated = mutate(current)
    if updated is None:
        updated = current
    write_json_atomic(path, updated)
    return updated


def iter_numeric_subdirs(root: Path | str) -> list[Path]:
    """Return numeric-named subdirectories of ``root`` sorted numerically.

    Non-directory / non-numeric entries are filtered out. Empty list if
    ``root`` doesn't exist or isn't a directory.
    """
    p = Path(root)
    if not p.is_dir():
        return []
    return sorted(
        (d for d in p.iterdir() if d.is_dir() and d.name.isdigit()),
        key=lambda d: int(d.name),
    )


# --- canonical metadata emitters -----------------------------------------


def write_pr_metadata(
    output_dir: Path | str,
    *,
    pr_number: str,
    git_ref: str,
    last_commit: str,
    authors_count: int,
    build_status: str,
    error_message: str | None = None,
    error_log: str | None = None,
) -> Path:
    """Emit a ``PR_METADATA.json`` (schema v2) for a freshly-built PR.

    Used by ``tools/inject-schema-pr`` via ``bids-schema metadata write-pr``.
    Does NOT populate the ``stats`` sub-block — that's the collector's job
    (``bids_schema.collect.github``).
    """
    if build_status not in ("success", "failed"):
        raise ValueError(f"build_status must be 'success' or 'failed', got {build_status!r}")
    record: dict = {
        "_schema_version": CURRENT_PR_SCHEMA_VERSION,
        "pr_number": str(pr_number),
        "git_ref": git_ref,
        "last_commit": last_commit,
        "last_updated": now_utc_iso(),
        "has_schema_changes": True,
        "build_status": build_status,
        "authors_count": authors_count,
    }
    if build_status == "failed":
        record["error_message"] = error_message or "Build failed"
        record["error_log"] = error_log or "bst-output.log"
    path = Path(output_dir) / "PR_METADATA.json"
    write_json_atomic(path, record)
    return path


def write_bep_metadata(
    output_dir: Path | str,
    *,
    bep_number: str,
    title: str,
    pr_number: int | str,
    pull_request: str,
    google_doc: str = "",
    status: str = "review",
    authors_count: int = 0,
) -> Path:
    """Emit a ``BEP_METADATA.json`` (schema v2) for a BEP.

    Used by ``tools/process-bep-schemas`` after copying the PR schema.
    Does NOT populate registration timestamps — those come from
    ``bids_schema.collect.bep_registration`` in a later phase.
    """
    record: dict = {
        "_schema_version": CURRENT_BEP_SCHEMA_VERSION,
        "bep_number": str(bep_number),
        "title": title,
        "pr_number": int(pr_number),
        "pull_request": pull_request,
        "google_doc": google_doc,
        "status": status,
        "authors_count": authors_count,
    }
    path = Path(output_dir) / "BEP_METADATA.json"
    write_json_atomic(path, record)
    return path
