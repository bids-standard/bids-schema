"""Tests for the ``schema-*`` tag → BIDS version mapper."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from bids_schema.collect import schema_to_bids


def _git(cwd: Path, *args: str) -> str:
    env = os.environ.copy()
    env.update(
        GIT_AUTHOR_NAME="Test", GIT_AUTHOR_EMAIL="test@example.org",
        GIT_COMMITTER_NAME="Test", GIT_COMMITTER_EMAIL="test@example.org",
    )
    return subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, check=True, env=env,
    ).stdout


def _commit(repo: Path) -> str:
    _git(repo, "commit", "--allow-empty", "-m", "change")
    return _git(repo, "rev-parse", "HEAD").strip()


@pytest.fixture
def spec_repo(tmp_path: Path) -> Path:
    """v1.0.0 = schema-0.9.0; schema-0.9.1 one commit later (lightweight tag);
    v1.1.0 = schema-0.10.0."""
    repo = tmp_path / "bids-specification"
    repo.mkdir()
    _git(repo, "init", "--initial-branch=master")
    _commit(repo)
    _git(repo, "tag", "-a", "-m", "BIDS 1.0.0", "v1.0.0")
    _git(repo, "tag", "-a", "-m", "schema 0.9.0", "schema-0.9.0")
    _commit(repo)
    _git(repo, "tag", "schema-0.9.1")
    _commit(repo)
    _git(repo, "tag", "-a", "-m", "BIDS 1.1.0", "v1.1.0")
    _git(repo, "tag", "-a", "-m", "schema 0.10.0", "schema-0.10.0")
    return repo


@pytest.mark.ai_generated
def test_collect(spec_repo: Path, tmp_path: Path) -> None:
    base = tmp_path / "bids-schema"
    mapping = schema_to_bids.collect(base_dir=base, bids_repo=spec_repo)
    sha = _git(spec_repo, "rev-parse", "schema-0.9.1").strip()
    assert mapping == {
        "0.10.0": {"bids_version_released": "1.1.0", "bids_version_exact": "1.1.0"},
        "0.9.0": {"bids_version_released": "1.0.0", "bids_version_exact": "1.0.0"},
        "0.9.1": {
            "bids_version_released": "1.0.0",
            "bids_version_exact": f"1.0.0+1-g{sha[:9]}",
        },
    }
    assert json.loads((base / "versions" / "schema_to_bids.json").read_text()) == mapping


@pytest.mark.ai_generated
def test_collect_adds_only_new_tags(spec_repo: Path, tmp_path: Path) -> None:
    base = tmp_path / "bids-schema"
    output = base / "versions" / "schema_to_bids.json"
    output.parent.mkdir(parents=True)
    known = {"bids_version_released": "kept", "bids_version_exact": "kept"}
    output.write_text(json.dumps({"0.9.0": known, "0.1.0": known}))

    mapping = schema_to_bids.collect(base_dir=base, bids_repo=spec_repo)
    assert mapping["0.9.0"] == known  # not described again
    assert mapping["0.1.0"] == known  # kept although not tagged in this clone
    assert mapping["0.10.0"]["bids_version_released"] == "1.1.0"
    assert list(json.loads(output.read_text())) == ["0.1.0", "0.10.0", "0.9.0", "0.9.1"]


@pytest.mark.ai_generated
def test_cli_uses_bids_repo_env(
    spec_repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from click.testing import CliRunner

    from bids_schema.cli import main

    base = tmp_path / "bids-schema"
    base.mkdir()
    monkeypatch.chdir(base)
    monkeypatch.setenv("BIDS_REPO", str(spec_repo))
    result = CliRunner().invoke(main, ["collect", "schema-to-bids"])
    assert result.exit_code == 0, result.output
    data = json.loads((base / "versions" / "schema_to_bids.json").read_text())
    assert set(data) == {"0.9.0", "0.9.1", "0.10.0"}
