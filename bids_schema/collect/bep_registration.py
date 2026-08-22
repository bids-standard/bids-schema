"""Compute BEP registration timestamps from ``bids-website`` git history.

See ``doc/designs/2-extended-stats-plan.md`` §3.6 for the design.

For each BEP entry currently listed in ``data/beps/beps.yml``:

- ``bep_registered``       — commit ``authorDate`` of the earliest commit
  that mentions this BEP number.
- ``googledoc_registered`` — commit ``authorDate`` of the earliest commit
  where the entry has a non-empty ``google_doc`` field (``null`` if the
  entry has never had one).

Both timestamps are written into ``BEPs/<NN>/BEP_METADATA.json`` alongside
a ``_registration_source`` provenance block.
"""

from __future__ import annotations

import logging
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

import yaml

from bids_schema.metadata.io import iter_numeric_subdirs, load_json, write_json_atomic
from bids_schema.metadata.schema import CURRENT_BEP_SCHEMA_VERSION
from bids_schema.metadata.time import now_utc_iso

log = logging.getLogger(__name__)

BIDS_WEBSITE_URL = "https://github.com/bids-standard/bids-website"
BIDS_WEBSITE_PATH = "data/beps/beps.yml"


class GitWalkError(RuntimeError):
    """Raised when git operations against the bids-website clone fail."""


# --- git helpers ----------------------------------------------------------


def _run_git(repo: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, check=False,
    )
    if check and result.returncode != 0:
        raise GitWalkError(
            f"git {' '.join(args)} failed (rc={result.returncode}): "
            f"{(result.stderr or result.stdout).strip()[:400]}"
        )
    return result.stdout


def _ensure_clone(repo: Path) -> None:
    if repo.exists() and (repo / ".git").exists():
        return
    log.info("bids-website clone not found at %s; cloning %s", repo, BIDS_WEBSITE_URL)
    repo.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "clone", BIDS_WEBSITE_URL, str(repo)],
        check=True,
    )


def _try_fetch(repo: Path) -> str | None:
    """Run ``git fetch origin``. Returns None on success, an error string on failure."""
    try:
        _run_git(repo, "fetch", "origin")
        return None
    except GitWalkError as e:
        log.warning("git fetch origin failed for %s: %s", repo, e)
        return str(e)


def _head_sha(repo: Path) -> str:
    return _run_git(repo, "rev-parse", "HEAD").strip()


def _commits_touching(repo: Path, path: str) -> list[tuple[str, str]]:
    """Return ``[(sha, author_iso_date), ...]`` oldest → newest for commits touching ``path``."""
    out = _run_git(
        repo, "log", "--reverse", "--pretty=format:%H\t%aI", "--", path,
    )
    rows: list[tuple[str, str]] = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t", 1)
        if len(parts) == 2:
            rows.append((parts[0], parts[1]))
    return rows


def _show_blob(repo: Path, sha: str, path: str) -> str | None:
    """Return ``git show <sha>:<path>``, or ``None`` if the path doesn't exist at that revision."""
    result = subprocess.run(
        ["git", "-C", str(repo), "show", f"{sha}:{path}"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def _iter_yaml_entries(text: str) -> Iterator[dict]:
    """Yield entries from a beps.yml revision. Malformed revisions yield nothing."""
    try:
        data = yaml.safe_load(text) or []
    except yaml.YAMLError:
        return
    if not isinstance(data, list):
        return
    for entry in data:
        if isinstance(entry, dict):
            yield entry


def _normalise_iso(iso: str) -> str:
    """Normalise ``git log`` `%aI` output to a UTC ``Z``-suffixed ISO string."""
    try:
        dt = datetime.fromisoformat(iso)
    except ValueError:
        return iso
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --- walking algorithm ----------------------------------------------------


def walk_history(repo: Path, path: str = BIDS_WEBSITE_PATH) -> tuple[dict[str, str], dict[str, str]]:
    """Walk the given YAML file's history oldest → newest.

    Returns ``(bep_registered, googledoc_registered)`` — both mapping
    normalised BEP number string → ISO date of the first commit where
    the condition became true.
    """
    bep_registered: dict[str, str] = {}
    googledoc_registered: dict[str, str] = {}

    commits = _commits_touching(repo, path)
    for sha, author_iso in commits:
        blob = _show_blob(repo, sha, path)
        if blob is None:
            continue
        for entry in _iter_yaml_entries(blob):
            number = str(entry.get("number", "")).lstrip("0")
            if not number:
                continue
            if number not in bep_registered:
                bep_registered[number] = _normalise_iso(author_iso)
            if number not in googledoc_registered and entry.get("google_doc"):
                googledoc_registered[number] = _normalise_iso(author_iso)

    return bep_registered, googledoc_registered


# --- freshness gate -------------------------------------------------------


def _all_records_up_to_date(bep_root: Path, walked_ref: str) -> bool:
    """True if every ``BEP_METADATA.json`` under ``bep_root`` already carries
    ``_registration_source.walked_ref == walked_ref``.
    """
    bep_dirs = iter_numeric_subdirs(bep_root)
    if not bep_dirs:
        return False
    for bep_dir in bep_dirs:
        meta = load_json(bep_dir / "BEP_METADATA.json")
        if not meta:
            return False
        source = meta.get("_registration_source") or {}
        if source.get("walked_ref") != walked_ref:
            return False
    return True


# --- top-level orchestration ----------------------------------------------


def collect(only: list[str] | None = None,
            force: bool = False,
            skip_fetch: bool = False,
            base_dir: Path | None = None,
            website_repo: Path | None = None) -> int:
    """Compute and merge registration timestamps into ``BEPs/<NN>/BEP_METADATA.json``.

    Returns a process-exit code (0 = OK; non-zero = unrecoverable error).
    """
    logging.basicConfig(level=os.environ.get("BIDS_SCHEMA_LOGLEVEL", "INFO"),
                        format="%(asctime)s %(levelname)s %(message)s")
    root = base_dir or Path.cwd()
    repo = website_repo or Path(os.environ.get("BIDS_WEBSITE_REPO",
                                               str(root.parent / "bids-website")))
    bep_root = root / "BEPs"

    try:
        _ensure_clone(repo)
    except subprocess.CalledProcessError as e:
        log.error("Failed to clone bids-website: %s", e)
        return 2

    fetch_error: str | None = None
    if not skip_fetch:
        fetch_error = _try_fetch(repo)

    try:
        head = _head_sha(repo)
    except GitWalkError as e:
        log.error("Cannot resolve HEAD in %s: %s", repo, e)
        return 2

    if not force and _all_records_up_to_date(bep_root, head):
        log.info("All BEP records already reference walked_ref=%s; skipping.", head[:10])
        return 0

    log.info("Walking %s at %s ...", BIDS_WEBSITE_PATH, head[:10])
    try:
        bep_registered, googledoc_registered = walk_history(repo)
    except GitWalkError as e:
        log.error("Git walk failed: %s", e)
        return 2

    if not bep_root.is_dir():
        log.info("No BEPs/ directory at %s; nothing to update.", root)
        return 0

    only_set = {str(x).lstrip("0") for x in (only or []) if str(x).lstrip("0")}
    num_updated = 0
    num_skipped = 0

    for bep_dir in iter_numeric_subdirs(bep_root):
        bep_number_norm = bep_dir.name.lstrip("0") or "0"
        if only_set and bep_number_norm not in only_set:
            num_skipped += 1
            continue

        record_path = bep_dir / "BEP_METADATA.json"
        record = load_json(record_path)
        if not record:
            log.debug("No BEP_METADATA.json under %s; skipping.", bep_dir)
            continue

        registered = bep_registered.get(bep_number_norm)
        gdoc_registered = googledoc_registered.get(bep_number_norm)

        record["_schema_version"] = CURRENT_BEP_SCHEMA_VERSION
        record["bep_registered"] = registered
        record["googledoc_registered"] = gdoc_registered
        source_block: dict = {
            "repo":      "bids-standard/bids-website",
            "path":      BIDS_WEBSITE_PATH,
            "walked_at": now_utc_iso(),
            "walked_ref": head,
        }
        if fetch_error:
            source_block["_fetch_error"] = fetch_error
        record["_registration_source"] = source_block

        write_json_atomic(record_path, record)
        num_updated += 1

    log.info("Done. updated=%d skipped=%d walked_ref=%s%s",
             num_updated, num_skipped, head[:10],
             " (fetch error, walk against stale history)" if fetch_error else "")
    return 0
