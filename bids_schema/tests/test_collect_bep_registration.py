"""Tests for the BEP-registration git-walker.

Builds a small fixture git repo in a tmpdir with successive edits to
``data/beps/beps.yml`` and verifies the collector derives the expected
per-BEP `bep_registered` and `googledoc_registered` timestamps.
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

from bids_schema.collect import bep_registration


def _run(cwd: Path, *args: str, env: dict | None = None) -> str:
    result = subprocess.run(
        list(args), cwd=str(cwd), capture_output=True, text=True, check=True,
        env=env,
    )
    return result.stdout


def _git(cwd: Path, *args: str, date: str | None = None) -> str:
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = "Test"
    env["GIT_AUTHOR_EMAIL"] = "test@example.org"
    env["GIT_COMMITTER_NAME"] = "Test"
    env["GIT_COMMITTER_EMAIL"] = "test@example.org"
    if date:
        env["GIT_AUTHOR_DATE"] = date
        env["GIT_COMMITTER_DATE"] = date
    return _run(cwd, "git", *args, env=env)


@pytest.fixture
def website_repo(tmp_path: Path) -> Path:
    """A minimal fixture bids-website clone with three successive edits
    to ``data/beps/beps.yml``.

    Commit 1 (2018-05-12): adds BEP 11 (no google_doc) and BEP 12 (with google_doc).
    Commit 2 (2019-11-02): adds a google_doc URL to BEP 11.
    Commit 3 (2020-01-01): adds BEP 42 (no google_doc).
    """
    repo = tmp_path / "bids-website"
    repo.mkdir()
    _git(repo, "init", "--initial-branch=main")

    beps_dir = repo / "data" / "beps"
    beps_dir.mkdir(parents=True)
    beps_yml = beps_dir / "beps.yml"

    # commit 1
    revision_1 = [
        {"number": "11", "title": "Structural preprocessing"},
        {"number": "12", "title": "Functional preprocessing", "google_doc": "https://docs.google.com/document/d/AAA/"},
    ]
    beps_yml.write_text(yaml.safe_dump(revision_1))
    _git(repo, "add", "data/beps/beps.yml")
    _git(repo, "commit", "-m", "Add BEPs 11 and 12", date="2018-05-12T14:03:11+0000")

    # commit 2: attach google_doc to BEP 11
    revision_2 = [
        {"number": "11", "title": "Structural preprocessing", "google_doc": "https://docs.google.com/document/d/BBB/"},
        {"number": "12", "title": "Functional preprocessing", "google_doc": "https://docs.google.com/document/d/AAA/"},
    ]
    beps_yml.write_text(yaml.safe_dump(revision_2))
    _git(repo, "add", "data/beps/beps.yml")
    _git(repo, "commit", "-m", "Attach google_doc to BEP 11", date="2019-11-02T08:30:00+0000")

    # commit 3: add BEP 42
    revision_3 = revision_2 + [{"number": "42", "title": "Answer BEP"}]
    beps_yml.write_text(yaml.safe_dump(revision_3))
    _git(repo, "add", "data/beps/beps.yml")
    _git(repo, "commit", "-m", "Add BEP 42", date="2020-01-01T00:00:00+0000")

    return repo


@pytest.mark.ai_generated
def test_walk_history_derives_correct_timestamps(website_repo: Path) -> None:
    bep_registered, googledoc_registered = bep_registration.walk_history(website_repo)

    assert bep_registered["11"] == "2018-05-12T14:03:11Z"
    assert bep_registered["12"] == "2018-05-12T14:03:11Z"
    assert bep_registered["42"] == "2020-01-01T00:00:00Z"

    # BEP 11: google_doc added in commit 2 → 2019-11-02
    assert googledoc_registered["11"] == "2019-11-02T08:30:00Z"
    # BEP 12: google_doc from commit 1 → same as bep_registered
    assert googledoc_registered["12"] == "2018-05-12T14:03:11Z"
    # BEP 42: never had a google_doc
    assert "42" not in googledoc_registered


@pytest.mark.ai_generated
def test_walk_history_skips_malformed_yaml(website_repo: Path) -> None:
    # Corrupt intermediate revision then restore
    beps_yml = website_repo / "data" / "beps" / "beps.yml"
    original = beps_yml.read_text()
    beps_yml.write_text("--- : broken:\n:not valid:\n\t- bad tab")
    _git(website_repo, "add", "data/beps/beps.yml")
    _git(website_repo, "commit", "-m", "Break yaml", date="2020-06-01T00:00:00+0000")
    beps_yml.write_text(original)
    _git(website_repo, "add", "data/beps/beps.yml")
    _git(website_repo, "commit", "-m", "Restore yaml", date="2020-06-02T00:00:00+0000")

    # Walk should still succeed and return original timestamps
    bep_registered, _ = bep_registration.walk_history(website_repo)
    assert bep_registered["11"] == "2018-05-12T14:03:11Z"


@pytest.mark.ai_generated
def test_collect_writes_records(website_repo: Path, base_dir: Path, make_bep) -> None:
    make_bep(11, title="Structural preprocessing", pr_number=518,
             google_doc="https://docs.google.com/document/d/BBB/")
    make_bep(12, title="Functional preprocessing", pr_number=519,
             google_doc="https://docs.google.com/document/d/AAA/")

    rc = bep_registration.collect(
        base_dir=base_dir, website_repo=website_repo, skip_fetch=True,
    )
    assert rc == 0

    rec_11 = json.loads((base_dir / "BEPs" / "11" / "BEP_METADATA.json").read_text())
    assert rec_11["_schema_version"] == 3
    assert rec_11["bep_registered"] == "2018-05-12T14:03:11Z"
    assert rec_11["googledoc_registered"] == "2019-11-02T08:30:00Z"
    assert rec_11["_registration_source"]["path"] == "data/beps/beps.yml"
    assert rec_11["_registration_source"]["repo"] == "bids-standard/bids-website"
    # walked_ref = HEAD sha (40-char hex)
    assert len(rec_11["_registration_source"]["walked_ref"]) == 40


@pytest.mark.ai_generated
def test_collect_leading_zero_normalisation(website_repo: Path, base_dir: Path, make_bep) -> None:
    # Fixture writes BEP as "011" in the YAML? No — number is stored as "11".
    # But the on-disk folder can be either — we normalise by stripping leading zeros.
    make_bep("011", pr_number=518)  # folder BEPs/011/

    rc = bep_registration.collect(
        base_dir=base_dir, website_repo=website_repo, skip_fetch=True,
    )
    assert rc == 0
    rec = json.loads((base_dir / "BEPs" / "011" / "BEP_METADATA.json").read_text())
    assert rec["bep_registered"] == "2018-05-12T14:03:11Z"


@pytest.mark.ai_generated
def test_freshness_gate_skips_when_walked_ref_matches(website_repo: Path,
                                                     base_dir: Path, make_bep,
                                                     caplog) -> None:
    make_bep(11, pr_number=518)
    # First run populates records
    bep_registration.collect(base_dir=base_dir, website_repo=website_repo, skip_fetch=True)

    # Second run — HEAD hasn't moved, all records reference walked_ref, should skip.
    import logging
    caplog.set_level(logging.INFO, logger="bids_schema.collect.bep_registration")
    bep_registration.collect(base_dir=base_dir, website_repo=website_repo, skip_fetch=True)
    assert any("skipping" in rec.message for rec in caplog.records)


@pytest.mark.ai_generated
def test_only_filter_restricts_scope(website_repo: Path, base_dir: Path, make_bep) -> None:
    make_bep(11, pr_number=518)
    make_bep(12, pr_number=519)

    bep_registration.collect(
        base_dir=base_dir, website_repo=website_repo, skip_fetch=True,
        only=["11"],
    )
    rec_11 = json.loads((base_dir / "BEPs" / "11" / "BEP_METADATA.json").read_text())
    rec_12 = json.loads((base_dir / "BEPs" / "12" / "BEP_METADATA.json").read_text())
    assert rec_11.get("bep_registered") == "2018-05-12T14:03:11Z"
    # BEP 12 was not in --only, so its record is untouched (no bep_registered)
    assert "bep_registered" not in rec_12


@pytest.mark.ai_generated
def test_normalise_iso_various_offsets() -> None:
    # +0000 → Z
    assert bep_registration._normalise_iso("2018-05-12T14:03:11+00:00") == "2018-05-12T14:03:11Z"
    # +05:00 → converted to UTC
    assert bep_registration._normalise_iso("2018-05-12T14:03:11+05:00") == "2018-05-12T09:03:11Z"
    # Malformed passes through
    assert bep_registration._normalise_iso("not a date") == "not a date"
