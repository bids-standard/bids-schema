"""Schema-version constants + helpers.

The ``_schema_version`` key is bumped whenever the metadata layout gains
or removes fields in a way downstream consumers should notice. v1 files
predate this key entirely (missing key → treat as 1).
"""

from __future__ import annotations

CURRENT_PR_SCHEMA_VERSION = 2
CURRENT_BEP_SCHEMA_VERSION = 3


def detect_version(record: dict) -> int:
    """Return the ``_schema_version`` of a record, defaulting to 1."""
    return int(record.get("_schema_version", 1))
