"""Shared time helpers.

Kept apart from ``io.py`` so callers that only need a timestamp don't
pull in the file-writing machinery.
"""

from __future__ import annotations

from datetime import datetime, timezone


def now_utc_iso() -> str:
    """Return the current UTC time as an ISO-8601 ``Z``-suffixed string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
