# BIDS Extension Proposals (BEPs) Schemas

This directory contains automatically generated schemas for BIDS Extension Proposals.
Each BEP schema is linked to its corresponding Pull Request in the BIDS specification repository.

## Overview

BIDS Extension Proposals (BEPs) are community-driven extensions to the BIDS specification.
This directory provides compiled schemas for BEPs that have associated Pull Requests with schema changes.

Each subdirectory corresponds to a BEP number and contains:
- `schema.json` - The compiled BIDS schema (only file stored to save space)
- `BEP_METADATA.json` - Metadata about the BEP and its PR association

## Active BEP Schemas

| BEP # | Title | Google Doc | PR # | Authors | Build | Schema Updated | Last Commit | Actions |
|-------|-------|------------|------|---------|-------|----------------|-------------|---------|
| [012](https://bids.neuroimaging.io/bep012) | Functional preprocessing derivatives | N/A | [519](https://github.com/bids-standard/bids-specification/pull/519) | 3 | ✅ | 2025-10-01 | [bd52fd178a](https://github.com/bids-standard/bids-specification/commit/bd52fd178ae077a10e04858bccdc30a1cdcd25e4) | [Schema](./12/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/enh-prs-and-beps/BEPs/12/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/enh-prs-and-beps/BEPs/12/schema_pp.json) |
| [016](https://bids.neuroimaging.io/bep016) | Diffusion weighted imaging derivatives | N/A | [2211](https://github.com/bids-standard/bids-specification/pull/2211) | 9 | ✅ | 2025-12-25 | [29c197a6ca](https://github.com/bids-standard/bids-specification/commit/29c197a6ca843f2349e77a1774f247765b068aff) | [Schema](./16/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/enh-prs-and-beps/BEPs/16/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/enh-prs-and-beps/BEPs/16/schema_pp.json) |
| [020](https://bids.neuroimaging.io/bep020) | Eye Tracking including Gaze Position and Pupil Size | N/A | [1128](https://github.com/bids-standard/bids-specification/pull/1128) | 12 | ✅ | 2025-12-19 | [a9b26d0b84](https://github.com/bids-standard/bids-specification/commit/a9b26d0b842ad4e25ffae32eddb6b069b43040a1) | [Schema](./20/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/enh-prs-and-beps/BEPs/20/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/enh-prs-and-beps/BEPs/20/schema_pp.json) |
| [028](https://bids.neuroimaging.io/bep028) | Provenance | [Doc](https://docs.google.com/document/d/1vw3VNDof5cecv2PkFp7Lw_pNUTUo8-m8V4SIdtGJVKs/) | [2099](https://github.com/bids-standard/bids-specification/pull/2099) | 5 | ✅ | 2025-12-16 | [cdea944f0f](https://github.com/bids-standard/bids-specification/commit/cdea944f0f8eb3f683052a5462a7e0b17fa083c9) | [Schema](./28/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/enh-prs-and-beps/BEPs/28/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/enh-prs-and-beps/BEPs/28/schema_pp.json) |
| [032](https://bids.neuroimaging.io/bep032) | Microelectrode electrophysiology | [Doc](https://docs.google.com/document/d/1oG-C8T-dWPqfVzL2W8HO3elWK8NIh2cOCPssRGv23n0/) | [1705](https://github.com/bids-standard/bids-specification/pull/1705) | 12 | ✅ | 2025-12-26 | [1f6f8f938a](https://github.com/bids-standard/bids-specification/commit/1f6f8f938a3ac26d673474a05dd574121c297c84) | [Schema](./32/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/enh-prs-and-beps/BEPs/32/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/enh-prs-and-beps/BEPs/32/schema_pp.json) |
| [034](https://bids.neuroimaging.io/bep034) | Computational modeling | N/A | [967](https://github.com/bids-standard/bids-specification/pull/967) | 3 | ✅ | 2025-10-01 | [b4d0044a79](https://github.com/bids-standard/bids-specification/commit/b4d0044a797202df2fb1afa912f0a3def07a09e7) | [Schema](./34/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/enh-prs-and-beps/BEPs/34/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/enh-prs-and-beps/BEPs/34/schema_pp.json) |
| [044](https://bids.neuroimaging.io/bep044) | Stimuli | N/A | [2022](https://github.com/bids-standard/bids-specification/pull/2022) | 4 | ✅ | 2025-12-19 | [25dde94375](https://github.com/bids-standard/bids-specification/commit/25dde94375b0aae3b168ec138bb077321c61aafd) | [Schema](./44/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/enh-prs-and-beps/BEPs/44/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/enh-prs-and-beps/BEPs/44/schema_pp.json) |## How to Use BEP Schemas

1. **Accessing a schema**: Navigate to `BEPs/{bep_number}/schema.json`
2. **Checking metadata**: View `BEPs/{bep_number}/BEP_METADATA.json` for BEP details
3. **Raw schema files**: Not stored (only compiled schema.json saved to reduce repository size)
4. **Finding the source PR**: Check the "Associated PR" column in the tables above

## BEP Process

1. **Draft**: Initial proposal and discussion
2. **Under Review**: Active development and community feedback
3. **Accepted**: Approved for inclusion in BIDS
4. **Archived**: Historical BEPs no longer under active development

## Automation

[![Inject](https://github.com/bids-standard/bids-schema/actions/workflows/inject.yml/badge.svg)](https://github.com/bids-standard/bids-schema/actions/workflows/inject.yml)

BEP schemas are automatically synchronized with their associated PRs by the [Schema Injection GitHub workflow](https://github.com/bids-standard/bids-schema/actions/workflows/inject.yml). View [workflow runs](https://github.com/bids-standard/bids-schema/actions/workflows/inject.yml) to see the latest updates.

## Related Resources

- [PR Schemas](../PRs/) - All Pull Request schemas
- [Released Versions](../versions/) - Official BIDS schema releases
- [BIDS Website - BEPs](https://bids.neuroimaging.io/beps) - Official BEP documentation
- [BIDS Specification Repository](https://github.com/bids-standard/bids-specification)

