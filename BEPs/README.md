# BIDS Extension Proposals (BEPs) Schemas

This directory contains automatically generated schemas for BIDS Extension Proposals.
Each BEP schema is linked to its corresponding Pull Request in the BIDS specification repository.

## Overview

BIDS Extension Proposals (BEPs) are community-driven extensions to the BIDS specification.
This directory provides compiled schemas for BEPs that have associated Pull Requests with schema changes.

Each subdirectory corresponds to a BEP number and contains:
- `schema/` - The raw schema files from the associated PR
- `schema.json` - The compiled BIDS schema
- `BEP_METADATA` - Metadata about the BEP and its PR association

## BEP Status Overview

**Status Summary:** 📝 Draft (0) | 👁️ Under Review (1) | ✅ Accepted (0) | 📦 Archived (0)

### BEPs Under Review

| BEP # | Title | Status | Associated PR | Google Doc | Schema Updated | Actions |
|-------|-------|--------|---------------|------------|----------------|---------|
| 032 | Microelectrode electrophysiology | 👁️ Review | [#1705](https://github.com/bids-standard/bids-specification/pull/1705) | [Doc](https://docs.google.com/document/d/1oG-C8T-dWPqfVzL2W8HO3elWK8NIh2cOCPssRGv23n0/) | 2025-09-17 | [Schema](./32/schema.json) |

## How to Use BEP Schemas

1. **Accessing a schema**: Navigate to `BEPs/{bep_number}/schema.json`
2. **Checking metadata**: View `BEPs/{bep_number}/BEP_METADATA` for BEP details
3. **Raw schema files**: Available in `BEPs/{bep_number}/schema/`
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

---

*Last generated: 2025-09-17 13:11:36 UTC*
