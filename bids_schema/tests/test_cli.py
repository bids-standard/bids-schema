"""Tests for bids_schema.cli — currently just the `cycle` composite command."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from bids_schema import cli
from bids_schema.collect import bep_doc_activity, bep_registration, github
from bids_schema.render import bep_readme, pr_readme


@pytest.mark.ai_generated
def test_cycle_still_renders_after_bep_doc_activity_key_error(monkeypatch) -> None:
    """A missing/rejected GOOGLE_API_KEY must not skip the README renders.

    Regression test: `cycle()` used to re-raise `GoogleApiKeyError` as a
    `ClickException`, aborting before `pr_readme.render_to_disk()` /
    `bep_readme.render_to_disk()` ran — contradicting the comment
    directly above it that says a non-zero exit from one collector
    shouldn't skip subsequent phases.
    """
    calls: list[str] = []

    monkeypatch.setattr(github, "collect", lambda: calls.append("github"))
    monkeypatch.setattr(bep_registration, "collect", lambda: calls.append("bep_registration"))

    def _raise_key_error() -> None:
        calls.append("bep_doc_activity")
        raise bep_doc_activity.GoogleApiKeyError("GOOGLE_API_KEY is not set")

    monkeypatch.setattr(bep_doc_activity, "collect", _raise_key_error)
    monkeypatch.setattr(pr_readme, "render_to_disk", lambda: calls.append("pr_readme"))
    monkeypatch.setattr(bep_readme, "render_to_disk", lambda: calls.append("bep_readme"))

    result = CliRunner().invoke(cli.main, ["cycle"])

    assert result.exit_code == 0, result.output
    assert calls == ["github", "bep_registration", "bep_doc_activity", "pr_readme", "bep_readme"]
    assert "GOOGLE_API_KEY" in result.output
