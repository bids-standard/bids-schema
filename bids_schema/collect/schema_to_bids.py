"""Map BIDS schema releases to BIDS versions (``versions/schema_to_bids.json``).

Validators such as bids-validator-deno report only the version of the BIDS
*schema* they validated against, not the version of the BIDS *standard*
(bids-standard/bids-validator#10). ``bids-specification`` tags every schema
release as ``schema-<version>`` and every BIDS release as ``v<X.Y.Z>``, so
the mapping can be derived from its git history alone
(bids-standard/bids-schema#20).

Each ``schema-*`` tag yields one record, keyed by the version in the tag name:

- ``bids_version``        — ``X.Y.Z`` when the tagged commit is BIDS release
  ``vX.Y.Z``; otherwise ``X.Y.Z+N-g<sha>``, where ``vX.Y.Z`` is the nearest
  preceding BIDS release and ``N`` the number of commits since it — i.e.
  ``git describe`` with the semver build-metadata marker, as in
  ``tools/version_component.sh``. ``null`` if no BIDS release precedes it.
- ``schema_bids_version`` — ``src/schema/BIDS_VERSION`` at the tag: the
  ``bids_version`` the compiled schema itself declares (often
  ``<next>-dev`` for schemas released between BIDS releases).
- ``tag``, ``commit`` (full sha), ``date`` (committer date, UTC).

The output carries no timestamps of its own, so it only changes when the set
of tags does.
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from bids_schema.metadata.io import write_json_atomic

log = logging.getLogger(__name__)

BIDS_SPECIFICATION_URL = "https://github.com/bids-standard/bids-specification"
SCHEMA_TAG_PREFIX = "schema-"
BIDS_RELEASE_TAG_GLOB = "v[0-9]*.[0-9]*.[0-9]*"
BIDS_VERSION_PATH = "src/schema/BIDS_VERSION"
OUTPUT_PATH = Path("versions") / "schema_to_bids.json"
SCHEMA_VERSION = 1
# Fixed, rather than git's repository-size-dependent default, so the output
# does not depend on the clone it was generated from.
ABBREV = 9


class GitError(RuntimeError):
    """Raised when a git operation against the bids-specification clone fails."""


def _run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        raise GitError(
            f"git {' '.join(args)} failed (rc={result.returncode}): "
            f"{(result.stderr or result.stdout).strip()[:400]}"
        )
    return result.stdout


def _version_key(version: str) -> list:
    """Natural sort key: ``1.0.9 < 1.0.10``, ``0.11.3 < 0.11.3.post1``."""
    return [int(p) if p.isdigit() else p for p in re.split(r"(\d+)", version)]


def _utc(iso: str) -> str:
    return datetime.fromisoformat(iso).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def describe_bids_version(repo: Path, commit: str) -> str | None:
    """Return the BIDS version of ``commit`` relative to the preceding ``v*`` release."""
    try:
        release = _run_git(
            repo, "describe", "--tags", "--abbrev=0", f"--match={BIDS_RELEASE_TAG_GLOB}", commit,
        ).strip()
        distance = int(_run_git(repo, "rev-list", "--count", f"{release}..{commit}"))
    except GitError as e:
        log.warning("Cannot describe %s relative to a BIDS release: %s", commit[:10], e)
        return None
    version = release.removeprefix("v")
    return version if distance == 0 else f"{version}+{distance}-g{commit[:ABBREV]}"


def _schema_bids_version(repo: Path, commit: str) -> str | None:
    try:
        return _run_git(repo, "show", f"{commit}:{BIDS_VERSION_PATH}").strip() or None
    except GitError:
        return None


def build_mapping(repo: Path) -> dict:
    """Return the ``schema_to_bids.json`` content for the clone at ``repo``."""
    out = _run_git(
        repo, "for-each-ref",
        "--format=%(refname:strip=2)%09%(*objectname)%09%(objectname)",
        f"refs/tags/{SCHEMA_TAG_PREFIX}*",
    )
    schemas: dict[str, dict] = {}
    for line in out.splitlines():
        tag, peeled, obj = line.split("\t")
        # %(*objectname) (the tagged commit) is empty for lightweight tags
        commit = peeled or obj
        date = _run_git(repo, "log", "-1", "--format=%cI", commit).strip()
        schemas[tag.removeprefix(SCHEMA_TAG_PREFIX)] = {
            "bids_version": describe_bids_version(repo, commit),
            "schema_bids_version": _schema_bids_version(repo, commit),
            "tag": tag,
            "commit": commit,
            "date": _utc(date),
        }
    return {
        "_schema_version": SCHEMA_VERSION,
        "_source": {
            "repo": BIDS_SPECIFICATION_URL,
            "schema_tags": f"{SCHEMA_TAG_PREFIX}*",
            "bids_release_tags": BIDS_RELEASE_TAG_GLOB,
        },
        "schemas": {k: schemas[k] for k in sorted(schemas, key=_version_key)},
    }


def collect(skip_fetch: bool = False,
            base_dir: Path | None = None,
            bids_repo: Path | None = None) -> int:
    """Write ``versions/schema_to_bids.json`` from the ``bids-specification`` clone.

    Returns a process-exit code (0 = OK; non-zero = unrecoverable error).
    """
    logging.basicConfig(level=os.environ.get("BIDS_SCHEMA_LOGLEVEL", "INFO"),
                        format="%(asctime)s %(levelname)s %(message)s")
    root = base_dir or Path.cwd()
    repo = bids_repo or Path(os.environ.get("BIDS_REPO", str(root.parent / "bids-specification")))
    if not (repo / ".git").exists():
        log.error("No bids-specification clone at %s (set BIDS_REPO)", repo)
        return 2

    if not skip_fetch:
        try:
            _run_git(repo, "fetch", "--tags", "origin")
        except GitError as e:
            # Tags only ever get added; a stale clone just yields fewer entries.
            log.warning("git fetch --tags failed for %s: %s", repo, e)

    try:
        mapping = build_mapping(repo)
    except GitError as e:
        log.error("Failed to map schema tags: %s", e)
        return 2

    output = root / OUTPUT_PATH
    write_json_atomic(output, mapping)
    log.info("Wrote %d schema versions to %s", len(mapping["schemas"]), output)
    return 0
