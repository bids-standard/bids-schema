# BIDS Extension Proposals (BEPs) Schemas

This directory contains automatically generated schemas for BIDS Extension Proposals.
Each BEP schema is linked to the Pull Request in `bids-specification` that owns it.

## Overview

BIDS Extension Proposals (BEPs) are community-driven extensions to the BIDS specification.
This directory provides compiled schemas for BEPs whose associated PR modifies the schema.

Each subdirectory corresponds to a BEP number and contains:
- `schema.json` — the compiled BIDS schema (pretty-printed alongside as `schema_pp.json`)
- `BEP_METADATA.json` — BEP-layer metadata: title, `google_doc` URL, PR linkage, and
  (schema v2+) registration timestamps (`bep_registered`, `googledoc_registered`).
  PR-derived facts (author count, build status, review counts, …) are joined at
  render time from the sibling `PRs/<N>/PR_METADATA.json` — never re-collected.

## Active BEP Schemas

| BEP # | Title | Google Doc | PR # | Authors | Build | Reviews | Comments | Unresolved | BEP registered | Doc registered | Actions |
| ----- | ----- | ---------- | ---- | ------- | ----- | ------- | -------- | ---------- | -------------- | -------------- | ------- |
| [011](https://bids.neuroimaging.io/bep011) | Structural preprocessing derivatives | [Doc](https://docs.google.com/document/d/1YG2g4UkEio4t_STIBOqYOwneLEs1emHIXbGKynx7V0Y/) | [518](https://github.com/bids-standard/bids-specification/pull/518) | 2 | ✅ ⚠ | — | — | — | 2024-06-15 | 2024-11-15 | [Schema](./11/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/main/BEPs/11/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/main/BEPs/11/schema_pp.json) |
| [012](https://bids.neuroimaging.io/bep012) | Functional preprocessing derivatives | — | [519](https://github.com/bids-standard/bids-specification/pull/519) | 3 | ✅ ⚠ | — | — | — | 2024-06-15 | — | [Schema](./12/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/main/BEPs/12/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/main/BEPs/12/schema_pp.json) |
| [016](https://bids.neuroimaging.io/bep016) | Diffusion weighted imaging derivatives | — | [2258](https://github.com/bids-standard/bids-specification/pull/2258) | 2 | ✅ ⚠ | — | — | — | 2024-06-15 | — | [Schema](./16/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/main/BEPs/16/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/main/BEPs/16/schema_pp.json) |
| [017](https://bids.neuroimaging.io/bep017) | Generic BIDS connectivity data schema | [Doc](https://docs.google.com/document/d/1ugBdUF6dhElXdj3u9vw0iWjE6f_Bibsro3ah7sRV0GA/) | [1902](https://github.com/bids-standard/bids-specification/pull/1902) | 2 | ✅ ⚠ | — | — | — | 2024-06-15 | 2024-11-15 | [Schema](./17/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/main/BEPs/17/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/main/BEPs/17/schema_pp.json) |
| [023](https://bids.neuroimaging.io/bep023) | PET Preprocessing derivatives | [Doc](https://docs.google.com/document/d/1yzsd1J9GT-aA0DWhdlgNr5LCu6_gvbjLyfvYq2FuxlY/) | [2339](https://github.com/bids-standard/bids-specification/pull/2339) | 4 | ✅ ⚠ | — | — | — | 2024-06-15 | 2024-11-15 | [Schema](./23/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/main/BEPs/23/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/main/BEPs/23/schema_pp.json) |
| [028](https://bids.neuroimaging.io/bep028) | Provenance | [Doc](https://docs.google.com/document/d/1vw3VNDof5cecv2PkFp7Lw_pNUTUo8-m8V4SIdtGJVKs/) | [2099](https://github.com/bids-standard/bids-specification/pull/2099) | 6 | ✅ ⚠ | — | — | — | 2024-06-15 | 2024-11-15 | [Schema](./28/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/main/BEPs/28/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/main/BEPs/28/schema_pp.json) |
| [032](https://bids.neuroimaging.io/bep032) | Microelectrode electrophysiology | [Doc](https://docs.google.com/document/d/1oG-C8T-dWPqfVzL2W8HO3elWK8NIh2cOCPssRGv23n0/) | [2307](https://github.com/bids-standard/bids-specification/pull/2307) | 2 | ✅ ⚠ | — | — | — | 2024-06-15 | 2024-11-15 | [Schema](./32/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/main/BEPs/32/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/main/BEPs/32/schema_pp.json) |
| [034](https://bids.neuroimaging.io/bep034) | Computational modeling | — | [967](https://github.com/bids-standard/bids-specification/pull/967) | 3 | ✅ ⚠ | — | — | — | 2024-06-15 | — | [Schema](./34/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/main/BEPs/34/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/main/BEPs/34/schema_pp.json) |
| [036](https://bids.neuroimaging.io/bep036) | Phenotypic Data Guidelines | [Doc](https://docs.google.com/document/d/1WTkfES8L0vItZVyyR68fc-9cO03jS-kCnMnw6602pbc/) | [2123](https://github.com/bids-standard/bids-specification/pull/2123) | 5 | ✅ ⚠ | — | — | — | 2024-06-15 | 2024-11-15 | [Schema](./36/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/main/BEPs/36/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/main/BEPs/36/schema_pp.json) |
| [044](https://bids.neuroimaging.io/bep044) | Stimuli | — | [2022](https://github.com/bids-standard/bids-specification/pull/2022) | 4 | ✅ ⚠ | — | — | — | 2024-09-05 | 2024-11-15 | [Schema](./44/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/main/BEPs/44/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/main/BEPs/44/schema_pp.json) |
| [045](https://bids.neuroimaging.io/bep045) | Peripheral Physiological Recordings | [Doc](https://docs.google.com/document/d/1oTfjzY5ZnLIYd0kPPWhR81sBmMuy_jC5YYIaqj6OhSA/edit) | [2267](https://github.com/bids-standard/bids-specification/pull/2267) | 4 | ✅ ⚠ | — | — | — | 2025-03-19 | 2025-03-19 | [Schema](./45/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/main/BEPs/45/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/main/BEPs/45/schema_pp.json) |
| [046](https://bids.neuroimaging.io/bep046) | Diffusion Tractography | [Doc](https://docs.google.com/document/d/1ubDQ2RhgjnfGqoeukzEkPV9YEHhfYMERrj7-3b0c2HI/edit) | [2333](https://github.com/bids-standard/bids-specification/pull/2333) | 2 | ✅ ⚠ | — | — | — | 2025-06-03 | 2025-06-03 | [Schema](./46/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/main/BEPs/46/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/main/BEPs/46/schema_pp.json) |
| [047](https://bids.neuroimaging.io/bep047) | Audio/video recordings for behavioral experiments | — | [2231](https://github.com/bids-standard/bids-specification/pull/2231) | 3 | ✅ ⚠ | — | — | — | 2026-02-08 | — | [Schema](./47/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/main/BEPs/47/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/main/BEPs/47/schema_pp.json) |

Column legend: **Reviews** = `approved✅ / changes_requested❌ / commented💬`; **Unresolved** = count of unresolved inline review threads (bolded if > 0); **BEP registered** = date the BEP entry was first added to `bids-website:data/beps/beps.yml`; **Doc registered** = date a `google_doc` URL was first attached to that entry.

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
