# BIDS Extension Proposals (BEPs) Schemas

This directory contains automatically generated schemas for BIDS Extension Proposals.
Each BEP schema is linked to its corresponding Pull Request in the BIDS specification repository.

## Overview

BIDS Extension Proposals (BEPs) are community-driven extensions to the BIDS specification.
This directory provides compiled schemas for BEPs that have associated Pull Requests with schema changes.

Each subdirectory corresponds to a BEP number and contains:
- `schema.json` - The compiled BIDS schema (only file stored to save space)
- `BEP_METADATA.json` - Metadata about the BEP and its PR association

## BEP Status Overview

**Status Summary:** 📝 Draft (0) | 👁️ Under Review (7) | ✅ Accepted (0) | 📦 Archived (0)

### BEPs Under Review

| BEP # | Title | Status | Associated PR | Google Doc | Schema Updated | Actions |
|-------|-------|--------|---------------|------------|----------------|---------|
| 012 | Functional preprocessing derivatives | 👁️ Review | [#519](https://github.com/bids-standard/bids-specification/pull/519) | N/A | 2025-09-17 | [Schema](./12/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/enh-prs-and-beps/BEPs/12/schema.json) |
| 020 | Eye Tracking including Gaze Position and Pupil Size | 👁️ Review | [#1128](https://github.com/bids-standard/bids-specification/pull/1128) | N/A | 2025-09-17 | [Schema](./20/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/enh-prs-and-beps/BEPs/20/schema.json) |
| 028 | Provenance | 👁️ Review | [#2099](https://github.com/bids-standard/bids-specification/pull/2099) | [Doc](https://docs.google.com/document/d/1vw3VNDof5cecv2PkFp7Lw_pNUTUo8-m8V4SIdtGJVKs/) | 2025-09-17 | [Schema](./28/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/enh-prs-and-beps/BEPs/28/schema.json) |
| 032 | Microelectrode electrophysiology | 👁️ Review | [#1705](https://github.com/bids-standard/bids-specification/pull/1705) | [Doc](https://docs.google.com/document/d/1oG-C8T-dWPqfVzL2W8HO3elWK8NIh2cOCPssRGv23n0/) | 2025-09-17 | [Schema](./32/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/enh-prs-and-beps/BEPs/32/schema.json) |
| 034 | Computational modeling | 👁️ Review | [#967](https://github.com/bids-standard/bids-specification/pull/967) | N/A | 2025-09-17 | [Schema](./34/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/enh-prs-and-beps/BEPs/34/schema.json) |
| 042 | Electromyography | 👁️ Review | [#1998](https://github.com/bids-standard/bids-specification/pull/1998) | N/A | 2025-09-17 | [Schema](./42/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/enh-prs-and-beps/BEPs/42/schema.json) |
| 044 | Stimuli | 👁️ Review | [#2022](https://github.com/bids-standard/bids-specification/pull/2022) | N/A | 2025-09-17 | [Schema](./44/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/enh-prs-and-beps/BEPs/44/schema.json) |

## How to Use BEP Schemas

1. **Accessing a schema**: Navigate to `BEPs/{bep_number}/schema.json`
2. **Checking metadata**: View `BEPs/{bep_number}/BEP_METADATA.json` for BEP details
3. **Raw schema files**: Not stored (only compiled schema.json saved to reduce repository size)
4. **Finding the source PR**: Check the "Associated PR" column in the tables above

## BEP Process

1. **Draft**: Initial proposal and discussion
2. **Under Review**: Active development and community feedback
3. **Accepted**: Approved for inclusion in BIDS
4. **Archived**: Historical BEPs no longer under active development

## Update Frequency

BEP schemas are automatically synchronized with their associated PRs:
- Every 12 hours via scheduled GitHub Actions
- On manual workflow dispatch
- When PR schemas are updated

## Related Resources

- [PR Schemas](../PRs/) - All Pull Request schemas
- [Released Versions](../versions/) - Official BIDS schema releases
- [BIDS Website - BEPs](https://bids.neuroimaging.io/beps) - Official BEP documentation
- [BIDS Specification Repository](https://github.com/bids-standard/bids-specification)

## Legend

- 📝 **Draft**: Proposal under initial development
- 👁️ **Under Review**: Actively being reviewed by the community
- ✅ **Accepted**: Approved and merged into BIDS
- 📦 **Archived**: No longer under active development
