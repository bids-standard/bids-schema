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

| Script                              | Language | Role                                                                                                         |
| ----------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------ |
| `tools/inject-schema-fully-auto`    | bash     | Top-level orchestrator (releases + master + PRs + BEPs + READMEs). Run by CI and locally.                    |
| `tools/inject-schema`               | bash     | Build schema for a **release** git ref into `versions/<folder>/`.                                            |
| `tools/inject-schema-pr`            | bash     | Generalised builder: any git ref, any output dir, optional `PR_METADATA.json` generation.                    |
| `tools/process-pr-schemas`          | bash     | Enumerate `refs/pull/*/merge` in `bids-specification`, detect `src/schema/` diffs, invoke `inject-schema-pr`. |
| `tools/process-bep-schemas`         | python   | Read `bids-website:data/beps/beps.yml`, copy each BEP's PR schema into `BEPs/<NN>/`, write `BEP_METADATA.json`. |
| `tools/generate-pr-readme`          | python   | Render `PRs/README.md` status table from `PR_METADATA.json` files.                                           |
| `tools/generate-bep-readme`         | python   | Render `BEPs/README.md` status table (joins `BEP_METADATA.json` with sibling `PR_METADATA.json`).            |
| `tools/prettify-schema`             | bash     | Emit `schema_pp.json` (pretty-printed sibling).                                                              |
| `tools/version_component.sh`        | bash     | Helper: describe HEAD relative to schema-touching commits.                                                   |

Every mutating step is wrapped in `datalad run` so history contains a
reproducible provenance record. Commits are of the form
`[DATALAD RUNCMD] ...`.

## Metadata contracts

`PRs/<N>/PR_METADATA.json` — current fields:

- `pr_number`, `git_ref`, `last_commit`, `last_updated` (build time, UTC)
- `has_schema_changes`, `build_status` (`success` | `failed`)
- `authors_count` (unique commit authors from `merge_base..PR_HEAD`)
- On failure: `error_message`, `error_log`

`BEPs/<NN>/BEP_METADATA.json` — current fields:

- `bep_number`, `title`, `pr_number`, `pull_request` (URL),
  `google_doc` (URL, may be empty), `status`, `authors_count`

The BEP row in `BEPs/README.md` **reuses** the sibling PR's build /
commit / date info by loading `PRs/<pr_number>/PR_METADATA.json` at
render time. That reuse pattern is the one to preserve when extending
statistics: BEP metadata should not re-collect PR-derived facts.

## External dependencies

- `bst` from `bidsschematools` (installed via `requirements.txt`,
  pointing at `bids-specification` master)
- `datalad` for provenance
- `git` (with `+refs/pull/*:refs/pull/origin/*` fetch spec added on first
  run of `process-pr-schemas`)
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
   hand-edited — change the generator instead.
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

## Related docs

- `README.md` — user-facing overview
- `doc/designs/1-BEP-support.md` — original problem statement
- `doc/designs/1-BEP-support-design-plan.md` — implementation design
  behind the current `PRs/` + `BEPs/` layout
- `PRs/README.md`, `BEPs/README.md` — generated status pages
