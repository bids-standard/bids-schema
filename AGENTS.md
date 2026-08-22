# AGENTS.md — bids-schema

Guidance for AI agents working in this repository.
Human agents should also find this useful as a quick
orientation; the canonical user-facing README is `README.md`.

## Purpose of this repository

`bids-schema` is a **schema archive and staging area** for the
[BIDS specification](https://github.com/bids-standard/bids-specification):

- `versions/x.y.z/` — compiled schemas for every released BIDS version
- `versions/master/` — schema built from `bids-specification` master
- `versions/latest/` — copy of the most recent release
- `PRs/<N>/` — schema built from open PR #`<N>` against `bids-specification`
  (only PRs that touch `src/schema/`)
- `BEPs/<NN>/` — schema for BIDS Extension Proposal `NN`, tracked via the
  BEP's associated PR (from `bids-website`'s `data/beps/beps.yml`)
- `tools/` — the scripts that produce everything above

The live schema is developed in `bids-specification`; this repo is a
consumer that periodically compiles snapshots and publishes them as JSON
plus metadata.

## Repository layout

```
versions/           released schemas + master
  x.y.z/, master/, latest/
PRs/                one dir per open PR with schema changes
  <N>/schema.json, schema_pp.json, BIDS_VERSION, SCHEMA_VERSION,
      PR_METADATA.json, [bst-output.log on build failure]
  README.md         auto-generated status table
BEPs/               one dir per BEP with a linked PR
  <NN>/schema.json, schema_pp.json, BIDS_VERSION, SCHEMA_VERSION,
       BEP_METADATA.json
  README.md         auto-generated status table
tools/              orchestration and generation scripts (see below)
doc/                design docs (e.g. doc/designs/1-BEP-support-design-plan.md)
.github/workflows/  CI (inject.yml runs twice daily; shellcheck.yml)
```

## Tooling map

Bash scripts under `tools/` still own the schema-build side (git ref
extraction, `bst` invocation, `datalad run` orchestration). The Python
side has been consolidated into the `bids_schema` in-tree package —
one `click`-based CLI (`bids-schema`) is installed by `pip install -e .`
from the repo root.

| Command / script                            | Language | Role                                                                                                          |
| ------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------- |
| `tools/inject-schema-fully-auto`            | bash     | Top-level orchestrator (releases + master + PRs + BEPs + stats + READMEs). Run by CI and locally.             |
| `tools/inject-schema`                       | bash     | Build schema for a **release** git ref into `versions/<folder>/`.                                             |
| `tools/inject-schema-pr`                    | bash     | Generalised builder: any git ref, any output dir, optional `PR_METADATA.json` generation.                     |
| `tools/process-pr-schemas`                  | bash     | Enumerate `refs/pull/*/merge` in `bids-specification`, detect `src/schema/` diffs, invoke `inject-schema-pr`. |
| `tools/process-bep-schemas`                 | python   | Read `bids-website:data/beps/beps.yml`, copy each BEP's PR schema into `BEPs/<NN>/`, write `BEP_METADATA.json`. |
| `tools/prettify-schema`                     | bash     | Emit `schema_pp.json` (pretty-printed sibling).                                                               |
| `tools/version_component.sh`                | bash     | Helper: describe HEAD relative to schema-touching commits.                                                    |
| `bids-schema collect prs`                   | python   | Collect PR stats (reviews, comments, unresolved threads) via `gh api graphql`; merge into `PR_METADATA.json`. |
| `bids-schema collect beps`                  | python   | Compute `bep_registered` / `googledoc_registered` from `bids-website` git history; merge into `BEP_METADATA.json`. |
| `bids-schema render prs`                    | python   | Render `PRs/README.md` from on-disk metadata. No HTTP calls.                                                  |
| `bids-schema render beps`                   | python   | Render `BEPs/README.md`; joins sibling `PRs/<N>/PR_METADATA.json` at render time. No HTTP calls.              |
| `bids-schema metadata write-pr`             | python   | Canonical `PR_METADATA.json` emitter (called from `tools/inject-schema-pr`).                                  |
| `bids-schema metadata write-bep`            | python   | Canonical `BEP_METADATA.json` emitter (importable from `tools/process-bep-schemas` as `write_bep_metadata`).  |
| `bids-schema cycle`                         | python   | Composite: `collect prs && collect beps && render prs && render beps`.                                        |
| `bids-schema info`                          | python   | Print tool version / gh CLI location / auth status (CI debugging).                                            |

Every mutating step is wrapped in `datalad run` so history contains a
reproducible provenance record. Commits are of the form
`[DATALAD RUNCMD] ...`. The orchestrator uses a `datalad_run_retry`
helper (defined inline in `tools/inject-schema-fully-auto`) that
catches the "clean dataset required" failure mode by making an
intermediate commit and retrying once — mirrors the pattern already
established in `tools/process-bep-schemas`.

### `bids_schema` package layout

```
bids_schema/
  __init__.py
  __main__.py                # `python -m bids_schema`
  cli.py                     # `click` group: `bids-schema` entry point
  collect/
    __init__.py
    github.py                # GraphQL PR stats collector (PR #1)
    bep_registration.py      # git-log walker for BEP registration timestamps
  render/
    __init__.py
    formatters.py            # shared cell formatters + record loaders
    pr_readme.py             # `bids-schema render prs`
    bep_readme.py            # `bids-schema render beps`
  metadata/
    __init__.py
    io.py                    # atomic read-modify-write + write_pr_metadata / write_bep_metadata
    schema.py                # _schema_version constants
    time.py                  # now_utc_iso helper
  tests/                     # pytest
```

Install with `pip install -e '.[test]'` (or `.[ci]` in workflows).
The CLI is registered via `[project.scripts]` in `pyproject.toml`.

## Metadata contracts

`PRs/<N>/PR_METADATA.json` — fields (schema v2):

- `_schema_version` — currently `2`. Files written by pre-v2 tooling
  lack this key; the renderer treats missing `_schema_version` as v1
  and leaves the new stats columns as `—`.
- `pr_number`, `git_ref`, `last_commit`, `last_updated` (build time, UTC)
- `has_schema_changes`, `build_status` (`success` | `failed`)
- `authors_count` (unique commit authors from `merge_base..PR_HEAD`)
- On failure: `error_message`, `error_log`
- **`stats`** (v2 nested block, populated by `bids-schema collect prs`):
  `_source_head_sha`, `_collected_at`, `_complete`, `_error`;
  `pr_state`, `pr_created_at`, `pr_updated_at`, `review_decision`;
  `commits.{count, first_at, last_at}`;
  `reviews.{approved, changes_requested, commented, dismissed, pending, total, by_author{...}}`;
  `comments.{issue_count, review_thread_count, total, first_at, last_at, by_author{...}}`;
  `review_threads.{total, unresolved, unresolved_active, unresolved_outdated, unresolved_by_author{...}}`.

Per-author records under `reviews.by_author` also carry `last_state`
(the reviewer's most recent submission state) and `effective_state`
(the state of their most recent non-COMMENTED, non-DISMISSED
submission — matches GitHub's reviewers-sidebar heuristic).

`BEPs/<NN>/BEP_METADATA.json` — current fields:

- `_schema_version` — currently `2`. Files written by pre-v2 tooling
  lack this key; the renderer treats missing `_schema_version` as v1
  and leaves `bep_registered` / `googledoc_registered` columns as `—`.
- `bep_number`, `title`, `pr_number`, `pull_request` (URL),
  `google_doc` (URL, may be empty), `status`, `authors_count`
- `bep_registered` — commit date when the BEP entry was first
  added to `bids-website:data/beps/beps.yml` (ISO-8601 UTC).
- `googledoc_registered` — commit date when a non-empty `google_doc`
  URL was first attached to the entry (`null` if never).
- `_registration_source` — `{repo, path, walked_at, walked_ref}`
  identifying the `bids-website` HEAD sha the walk was run against.
  May include `_fetch_error` when the collector's own `git fetch`
  failed and the walk fell back to stale local history.

The BEP row in `BEPs/README.md` **reuses** the sibling PR's build /
commit / date / stats info by loading `PRs/<pr_number>/PR_METADATA.json`
at render time via `bids_schema.render.formatters.load_pr_record`.
That read-through join is the invariant to preserve when extending
statistics: BEP metadata never re-collects PR-derived facts.

## External dependencies

- `bst` from `bidsschematools` (installed via `requirements.txt`,
  pointing at `bids-specification` master)
- `datalad` for provenance
- `git` (with `+refs/pull/*:refs/pull/origin/*` fetch spec added on first
  run of `process-pr-schemas`)
- **`gh` CLI** on `$PATH`, authenticated (`GITHUB_TOKEN` in CI /
  `gh auth login` locally). Consumed by `bids-schema collect prs`
  to hit the GitHub GraphQL API; missing / unauthenticated `gh`
  degrades gracefully — the collector logs a warning and sets
  `stats._error` on affected records rather than failing the run.
- **`bids_schema` package**: `pip install -e '.[ci]'` in CI,
  `pip install -e '.[test]'` locally. Registers the `bids-schema`
  entry-point script and pulls in `click` + `PyYAML`.
- Two sibling clones — location overridable:
  - `bids-specification` at `$BIDS_REPO` (defaults to `../bids-specification`)
  - `bids-website` at `$BIDS_WEBSITE_REPO` (defaults to `../bids-website`)

## CI

`.github/workflows/inject.yml` runs `tools/inject-schema-fully-auto` on
cron (twice daily) and on `workflow_dispatch`, then `git push`es. Any
new commits appear on branch `main` under the `bids-maintenance` bot.

The active feature branch for the PR/BEP work is `enh-prs-and-beps`
(URLs in generated READMEs point at raw files on that branch).

## Conventions for agents

1. **Do not duplicate PR-derived facts into `BEP_METADATA.json`.** BEPs
   join to their PR at read time. When extending metadata, add fields
   in the layer they belong to (PR-layer vs BEP-layer) and never both.
2. **All schema/README changes are executed via `datalad run`** so the
   commit message documents the command. Preserve this when adding
   scripts that write into `PRs/`, `BEPs/`, or their `README.md`.
3. **Auto-generated files** (`PRs/README.md`, `BEPs/README.md`,
   `versions/*/schema.json`, all `*_METADATA.json`) must not be
   hand-edited — change the generator instead. Notably, `PR_METADATA.json`
   and `BEP_METADATA.json` are always written through
   `bids_schema.metadata.io.write_pr_metadata` /
   `write_bep_metadata` — never via bash heredocs — so the schema
   layout has one source of truth.
4. **The `schema.json` under `PRs/<N>/`** on build failure contains an
   `error` object rather than a real schema. Downstream tools should
   check `PR_METADATA.json:build_status` before consuming it.
5. **Adding new metadata fields** — update the emitter (bash or python
   script that writes the JSON), update the renderer
   (`generate-*-readme`), and keep both README tables aligned per the
   Markdown-alignment rule in the user's global instructions.
6. **Testing locally** — you need `BIDS_REPO` and `BIDS_WEBSITE_REPO`
   pointed at fresh clones with PR refs fetched. Set
   `BIDS_SCHEMA_KEEPTMP=1` to preserve tempdirs when debugging
   `inject-schema-fully-auto`.
7. **Environment variables** consumed by the CLI:
   - `BIDS_SCHEMA_RAW_BRANCH` — branch name embedded in README raw-file
     URLs. Defaults to `main`. Override when rendering from an
     unmerged feature branch to keep `Raw` / `Pretty` links resolving.
   - `PR_STATS_MAX_AGE` — freshness floor in seconds for the PR stats
     collector (defaults to 21600 = 6h). `PR_STATS_MAX_AGE_SECONDS`
     accepted as a fallback name.
   - `PR_STATS_PREFLIGHT_BATCH` — PRs per aliased preflight GraphQL
     query (defaults to 50).
   - `PR_STATS_MAX_INNER_QUERIES` — cap on per-thread comment
     pagination round trips (defaults to 10).

## Related docs

- `README.md` — user-facing overview
- `doc/designs/1-BEP-support.md` — original problem statement
- `doc/designs/1-BEP-support-design-plan.md` — implementation design
  behind the current `PRs/` + `BEPs/` layout
- `doc/designs/2-extended-stats-plan.md` — the PR & BEP stats plan,
  including the `bids_schema` package refactor and the rollout PR list
- `PRs/README.md`, `BEPs/README.md` — generated status pages
