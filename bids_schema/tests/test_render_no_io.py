"""Invariant #2 (collection ⟂ rendering) — rendering must never perform
HTTP calls or git operations. We enforce this by monkey-patching
``subprocess.run`` to raise, then asserting the renderers complete
successfully.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bids_schema.render import bep_readme, pr_readme


class _NoSubprocess(RuntimeError):
    pass


def _explode(*args, **kwargs):
    raise _NoSubprocess("render must not shell out")


@pytest.mark.ai_generated
def test_render_prs_makes_no_subprocess_calls(base_dir: Path, make_pr, monkeypatch) -> None:
    make_pr(518)
    make_pr(750, build_status="failed", error_log="bst-output.log")

    import subprocess
    monkeypatch.setattr(subprocess, "run", _explode)
    monkeypatch.setattr(subprocess, "Popen", _explode)

    out = pr_readme.render_to_disk(base_dir=base_dir)
    assert out.exists()


@pytest.mark.ai_generated
def test_render_beps_makes_no_subprocess_calls(base_dir: Path, make_pr, make_bep, monkeypatch) -> None:
    make_pr(518)
    make_bep(11, pr_number=518)

    import subprocess
    monkeypatch.setattr(subprocess, "run", _explode)
    monkeypatch.setattr(subprocess, "Popen", _explode)

    out = bep_readme.render_to_disk(base_dir=base_dir)
    assert out.exists()
