# BIDS Extension Proposals (BEPs) Schemas

This directory contains automatically generated schemas for BIDS Extension Proposals.
Each BEP schema is linked to the Pull Request in `bids-specification` that owns it.

## Overview

BIDS Extension Proposals (BEPs) are community-driven extensions to the BIDS specification.
This directory provides compiled schemas for BEPs whose associated PR modifies the schema.

Each subdirectory corresponds to a BEP number and contains:
- `schema.json` — the compiled BIDS schema (pretty-printed alongside as `schema_pp.json`)
- `BEP_METADATA.json` — BEP-layer metadata: title, `google_doc` URL, PR linkage,
  registration timestamps (`bep_registered`, `googledoc_registered`), and
  (schema v3+) `doc_activity` — how recently the Google Doc itself was edited,
  fetched via the Google Drive API (see `bids_schema.collect.bep_doc_activity`).
  PR-derived facts (author count, build status, review counts, …) are joined at
  render time from the sibling `PRs/<N>/PR_METADATA.json` — never re-collected.

## Active BEP Schemas

| BEP # | Title | Doc Activity | PR # | # Authors | # Commenters | Build | Reviews | Unresolved | Comments | First comment | Last comment | BEP registered | Doc registered | Actions |
| ----- | ----- | ------------ | ---- | --------- | ------------ | ----- | ------- | ---------- | -------- | ------------- | ------------ | -------------- | -------------- | ------- |
| [011](https://bids.neuroimaging.io/bep011) | Structural preprocessing derivatives | ⚪ Not checked yet | [518](https://github.com/bids-standard/bids-specification/pull/518) | 2 | 3 | ✅ | 5💬 | **3** | 9 | 2020-06-30 | 2023-02-13 | 2024-06-15 | 2024-11-15 | [Schema](./11/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/claude/bids-schema-pr-display-ds2fna/BEPs/11/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/claude/bids-schema-pr-display-ds2fna/BEPs/11/schema_pp.json) |
| [012](https://bids.neuroimaging.io/bep012) | Functional preprocessing derivatives | — | [519](https://github.com/bids-standard/bids-specification/pull/519) | 3 | 8 | ✅ | 30💬 | **6** | 36 | 2020-07-07 | 2024-08-01 | 2024-06-15 | — | [Schema](./12/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/claude/bids-schema-pr-display-ds2fna/BEPs/12/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/claude/bids-schema-pr-display-ds2fna/BEPs/12/schema_pp.json) |
| [016](https://bids.neuroimaging.io/bep016) | Diffusion weighted imaging derivatives | — | [2258](https://github.com/bids-standard/bids-specification/pull/2258) | 2 | 6 | ✅ | 1💬 | **1** | 8 | 2025-11-13 | 2026-07-06 | 2024-06-15 | — | [Schema](./16/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/claude/bids-schema-pr-display-ds2fna/BEPs/16/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/claude/bids-schema-pr-display-ds2fna/BEPs/16/schema_pp.json) |
| [017](https://bids.neuroimaging.io/bep017) | Generic BIDS connectivity data schema | ⚪ Not checked yet | [1902](https://github.com/bids-standard/bids-specification/pull/1902) | 2 | 1 | ✅ | 0 | 0 | 1 | 2024-08-22 | 2024-08-22 | 2024-06-15 | 2024-11-15 | [Schema](./17/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/claude/bids-schema-pr-display-ds2fna/BEPs/17/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/claude/bids-schema-pr-display-ds2fna/BEPs/17/schema_pp.json) |
| [023](https://bids.neuroimaging.io/bep023) | PET Preprocessing derivatives | ⚪ Not checked yet | [2339](https://github.com/bids-standard/bids-specification/pull/2339) | 4 | 0 | ✅ | 0 | 0 | 0 | — | — | 2024-06-15 | 2024-11-15 | [Schema](./23/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/claude/bids-schema-pr-display-ds2fna/BEPs/23/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/claude/bids-schema-pr-display-ds2fna/BEPs/23/schema_pp.json) |
| [028](https://bids.neuroimaging.io/bep028) | Provenance | ⚪ Not checked yet | [2099](https://github.com/bids-standard/bids-specification/pull/2099) | 6 | 8 | ✅ | 1✅/3❌/195💬 | **21** | 393 | 2025-05-23 | 2026-04-22 | 2024-06-15 | 2024-11-15 | [Schema](./28/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/claude/bids-schema-pr-display-ds2fna/BEPs/28/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/claude/bids-schema-pr-display-ds2fna/BEPs/28/schema_pp.json) |
| [032](https://bids.neuroimaging.io/bep032) | Microelectrode electrophysiology | ⚪ Not checked yet | [2307](https://github.com/bids-standard/bids-specification/pull/2307) | 2 | 9 | ✅ | 16💬 | **10** | 63 | 2026-01-15 | 2026-07-29 | 2024-06-15 | 2024-11-15 | [Schema](./32/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/claude/bids-schema-pr-display-ds2fna/BEPs/32/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/claude/bids-schema-pr-display-ds2fna/BEPs/32/schema_pp.json) |
| [034](https://bids.neuroimaging.io/bep034) | Computational modeling | — | [967](https://github.com/bids-standard/bids-specification/pull/967) | 3 | 2 | ✅ | 0 | 0 | 2 | 2022-07-25 | 2023-02-13 | 2024-06-15 | — | [Schema](./34/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/claude/bids-schema-pr-display-ds2fna/BEPs/34/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/claude/bids-schema-pr-display-ds2fna/BEPs/34/schema_pp.json) |
| [036](https://bids.neuroimaging.io/bep036) | Phenotypic Data Guidelines | ⚪ Not checked yet | [2123](https://github.com/bids-standard/bids-specification/pull/2123) | 5 | 15 | ✅ | 1❌/125💬 | **31** | 245 | 2025-05-30 | 2026-09-03 | 2024-06-15 | 2024-11-15 | [Schema](./36/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/claude/bids-schema-pr-display-ds2fna/BEPs/36/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/claude/bids-schema-pr-display-ds2fna/BEPs/36/schema_pp.json) |
| [044](https://bids.neuroimaging.io/bep044) | Stimuli | — | [2022](https://github.com/bids-standard/bids-specification/pull/2022) | 4 | 6 | ✅ | 4✅/2❌/38💬 | **16** | 104 | 2024-12-31 | 2026-09-02 | 2024-09-05 | 2024-11-15 | [Schema](./44/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/claude/bids-schema-pr-display-ds2fna/BEPs/44/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/claude/bids-schema-pr-display-ds2fna/BEPs/44/schema_pp.json) |
| [045](https://bids.neuroimaging.io/bep045) | Peripheral Physiological Recordings | ⚪ Not checked yet | [2267](https://github.com/bids-standard/bids-specification/pull/2267) | 4 | 4 | ✅ | 3💬 | **6** | 13 | 2025-12-01 | 2026-07-01 | 2025-03-19 | 2025-03-19 | [Schema](./45/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/claude/bids-schema-pr-display-ds2fna/BEPs/45/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/claude/bids-schema-pr-display-ds2fna/BEPs/45/schema_pp.json) |
| [046](https://bids.neuroimaging.io/bep046) | Diffusion Tractography | ⚪ Not checked yet | [2333](https://github.com/bids-standard/bids-specification/pull/2333) | 2 | 6 | ✅ | 2✅/28💬 | **7** | 45 | 2026-01-31 | 2026-07-03 | 2025-06-03 | 2025-06-03 | [Schema](./46/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/claude/bids-schema-pr-display-ds2fna/BEPs/46/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/claude/bids-schema-pr-display-ds2fna/BEPs/46/schema_pp.json) |
| [047](https://bids.neuroimaging.io/bep047) | Audio/video recordings for behavioral experiments | — | [2231](https://github.com/bids-standard/bids-specification/pull/2231) | 3 | 12 | ✅ | 2✅/55💬 | **2** | 94 | 2025-10-25 | 2026-09-03 | 2026-02-08 | — | [Schema](./47/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/claude/bids-schema-pr-display-ds2fna/BEPs/47/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/claude/bids-schema-pr-display-ds2fna/BEPs/47/schema_pp.json) |

Column legend: **Doc Activity** = 🟢 edited in the last 30 days / 🟡 edited in the last 6 months / 🔴 not edited in over 6 months / ⚪ unknown (not checked yet, or the doc isn't publicly viewable), linking to the Google Doc itself; **# Authors** = distinct people behind the linked PR’s commits, counting both the author and the committer of each commit and keyed on GitHub account rather than on name; **# Commenters** = distinct accounts that commented on that PR. **Reviews** = submitted reviews as `approved✅ / changes_requested❌ / commented💬`, zero-valued components omitted (so `1✅/27💬`, not `1✅/0❌/27💬`); **Unresolved** = count of unresolved inline review threads (bolded if > 0); **Comments** / **First comment** / **Last comment** = issue comments plus review threads on the linked PR, count and dates split so each can be sorted independently; **BEP registered** = date the BEP entry was first added to `bids-website:data/beps/beps.yml`; **Doc registered** = date a `google_doc` URL was first attached to that entry. See [`PRs/README.md`](../PRs/) for the full per-PR commit statistics.

> ⚠ **Note on `BEPs/<NN>/PR_METADATA.json`.** These files are copied unchanged from the sibling `PRs/<N>/PR_METADATA.json` and are scheduled for removal in a future cron cycle. Downstream consumers should read PR-derived facts from `PRs/<N>/PR_METADATA.json` directly.

## How to Use BEP Schemas

1. **Accessing a schema**: navigate to `BEPs/<bep_number>/schema.json`.
2. **Checking metadata**: view `BEPs/<bep_number>/BEP_METADATA.json`.
3. **Finding the source PR**: follow the PR link in the table above.

## BEP Process

1. **Draft** — initial proposal and discussion
2. **Under Review** — active development and community feedback
3. **Accepted** — approved for inclusion in BIDS
4. **Archived** — historical BEPs no longer under active development

## Automation

[![Inject](https://github.com/bids-standard/bids-schema/actions/workflows/inject.yml/badge.svg)](https://github.com/bids-standard/bids-schema/actions/workflows/inject.yml)

BEP schemas are synchronised with their PRs by the [Schema Injection workflow](https://github.com/bids-standard/bids-schema/actions/workflows/inject.yml).

## Related Resources

- [PR Schemas](../PRs/) — all Pull Request schemas
- [Released Versions](../versions/) — official BIDS schema releases
- [BIDS Website — BEPs](https://bids.neuroimaging.io/beps) — official BEP documentation
- [BIDS Specification Repository](https://github.com/bids-standard/bids-specification)
