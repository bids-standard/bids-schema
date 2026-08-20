"""Atomic read-modify-write helpers for JSON metadata files.

The write path is deliberately atomic: write to ``<path>.tmp``, ``os.replace``
onto ``<path>``. A crashed / killed collector never leaves partially-written
JSON on disk.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from pathlib import Path


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
