"""Map ``schema-*`` tags of bids-specification to BIDS versions.

Adds every ``schema-*`` tag not yet in ``versions/schema_to_bids.json``,
describing it relative to the BIDS release tags (``git describe --match
"v*"``): ``bids_version_released`` is the preceding BIDS release and
``bids_version_exact`` the full description, with ``+`` for its first ``-``
(e.g. ``1.11.1+22-ge37e21053``). See bids-standard/bids-schema#20.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from bids_schema.metadata.io import load_json, write_json_atomic

OUTPUT_PATH = Path("versions") / "schema_to_bids.json"


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True)


def collect(base_dir: Path | None = None, bids_repo: Path | None = None) -> dict:
    """Add new ``schema-*`` tags to ``versions/schema_to_bids.json``; return the mapping."""
    root = base_dir or Path.cwd()
    repo = bids_repo or Path(os.environ.get("BIDS_REPO") or root.parent / "bids-specification")
    output = root / OUTPUT_PATH
    mapping = load_json(output)
    for tag in _git(repo, "tag", "--list", "schema-*").split():
        schema_version = tag.removeprefix("schema-")
        if schema_version not in mapping:
            # fixed --abbrev, so that it does not depend on the clone
            described = _git(repo, "describe", "--match", "v*", "--abbrev=9", tag).strip()
            mapping[schema_version] = {
                "bids_version_released": described.split("-")[0].removeprefix("v"),
                "bids_version_exact": described.removeprefix("v").replace("-", "+", 1),
            }
    mapping = dict(sorted(mapping.items()))
    write_json_atomic(output, mapping)
    return mapping
