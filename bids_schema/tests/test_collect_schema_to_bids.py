"""Tests for the ``schema-*`` tag → BIDS version mapper.

Builds a small fixture bids-specification clone with BIDS release tags
(``v*``) and schema release tags (``schema-*``), annotated and lightweight,
and verifies the records written to ``versions/schema_to_bids.json``.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from bids_schema.collect import schema_to_bids


def _git(cwd: Path, *args: str, date: str = "2024-01-01T00:00:00+0000") -> str:
    env = os.environ.copy()
    env.update(
        GIT_AUTHOR_NAME="Test", GIT_AUTHOR_EMAIL="test@example.org",
        GIT_COMMITTER_NAME="Test", GIT_COMMITTER_EMAIL="test@example.org",
        GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date,
    )
    return subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, check=True, env=env,
    ).stdout


def _commit(repo: Path, bids_version: str, schema_version: str, date: str) -> str:
    schema_dir = repo / "src" / "schema"
    schema_dir.mkdir(parents=True, exist_ok=True)
    (schema_dir / "BIDS_VERSION").write_text(bids_version + "\n")
    (schema_dir / "SCHEMA_VERSION").write_text(schema_version + "\n")
    _git(repo, "add", "src/schema")
    _git(repo, "commit", "-m", f"BIDS {bids_version}, schema {schema_version}", date=date)
    return _git(repo, "rev-parse", "HEAD").strip()


@pytest.fixture
def spec_repo(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    """History: v1.0.0 = schema-0.9.0 (annotated); one commit later
    schema-0.9.1 (lightweight); v1.1.0 = schema-0.10.0 (annotated)."""
    repo = tmp_path / "bids-specification"
    repo.mkdir()
    _git(repo, "init", "--initial-branch=master")
    commits = {}
    _commit(repo, "1.0.0-dev", "0.9.0-dev", "2023-01-01T00:00:00+0000")
    commits["0.9.0"] = _commit(repo, "1.0.0", "0.9.0", "2023-02-01T10:00:00+0200")
    _git(repo, "tag", "-a", "-m", "BIDS 1.0.0", "v1.0.0")
    _git(repo, "tag", "-a", "-m", "schema 0.9.0", "schema-0.9.0")
    commits["0.9.1"] = _commit(repo, "1.1.0-dev", "0.9.1", "2023-03-01T00:00:00+0000")
    _git(repo, "tag", "schema-0.9.1")
    commits["0.10.0"] = _commit(repo, "1.1.0", "0.10.0", "2023-04-01T00:00:00+0000")
    _git(repo, "tag", "-a", "-m", "BIDS 1.1.0", "v1.1.0")
    _git(repo, "tag", "-a", "-m", "schema 0.10.0", "schema-0.10.0")
    # Neither BIDS nor schema release, must not show up
    _git(repo, "tag", "-a", "-m", "other", "other-tag")
    return repo, commits


@pytest.mark.ai_generated
def test_build_mapping(spec_repo: tuple[Path, dict[str, str]]) -> None:
    repo, commits = spec_repo
    mapping = schema_to_bids.build_mapping(repo)

    assert mapping["_schema_version"] == 1
    # natural version order, not lexicographic (0.10.0 after 0.9.1)
    assert list(mapping["schemas"]) == ["0.9.0", "0.9.1", "0.10.0"]
    assert mapping["schemas"]["0.9.0"] == {
        "bids_version": "1.0.0",
        "schema_bids_version": "1.0.0",
        "tag": "schema-0.9.0",
        "commit": commits["0.9.0"],
        "date": "2023-02-01T08:00:00Z",
    }
    # lightweight tag between releases: describe-style version, declared -dev
    rec = mapping["schemas"]["0.9.1"]
    assert rec["bids_version"] == f"1.0.0+1-g{commits['0.9.1'][:9]}"
    assert rec["schema_bids_version"] == "1.1.0-dev"
    assert rec["commit"] == commits["0.9.1"]
    assert mapping["schemas"]["0.10.0"]["bids_version"] == "1.1.0"


@pytest.mark.ai_generated
def test_describe_without_preceding_release(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--initial-branch=master")
    commit = _commit(repo, "1.0.0-dev", "0.1.0", "2023-01-01T00:00:00+0000")
    _git(repo, "tag", "schema-0.1.0")
    assert schema_to_bids.describe_bids_version(repo, commit) is None
    assert schema_to_bids.build_mapping(repo)["schemas"]["0.1.0"]["bids_version"] is None


@pytest.mark.ai_generated
def test_collect_writes_file_idempotently(
    spec_repo: tuple[Path, dict[str, str]], tmp_path: Path
) -> None:
    repo, _ = spec_repo
    base = tmp_path / "bids-schema"
    assert schema_to_bids.collect(skip_fetch=True, base_dir=base, bids_repo=repo) == 0
    output = base / "versions" / "schema_to_bids.json"
    first = output.read_text()
    assert json.loads(first)["schemas"]["0.10.0"]["bids_version"] == "1.1.0"

    assert schema_to_bids.collect(skip_fetch=True, base_dir=base, bids_repo=repo) == 0
    assert output.read_text() == first


@pytest.mark.ai_generated
def test_collect_missing_repo(tmp_path: Path) -> None:
    assert schema_to_bids.collect(
        skip_fetch=True, base_dir=tmp_path, bids_repo=tmp_path / "nope"
    ) == 2
    assert not (tmp_path / "versions").exists()


@pytest.mark.ai_generated
def test_cli_uses_bids_repo_env(
    spec_repo: tuple[Path, dict[str, str]], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from click.testing import CliRunner

    from bids_schema.cli import main

    repo, _ = spec_repo
    base = tmp_path / "bids-schema"
    base.mkdir()
    monkeypatch.chdir(base)
    monkeypatch.setenv("BIDS_REPO", str(repo))
    result = CliRunner().invoke(main, ["collect", "schema-to-bids", "--skip-fetch"])
    assert result.exit_code == 0, result.output
    data = json.loads((base / "versions" / "schema_to_bids.json").read_text())
    assert list(data["schemas"]) == ["0.9.0", "0.9.1", "0.10.0"]
