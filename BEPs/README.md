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
| [028](https://bids.neuroimaging.io/bep028) | Provenance | [Doc](https://docs.google.com/document/d/1vw3VNDof5cecv2PkFp7Lw_pNUTUo8-m8V4SIdtGJVKs/) | [2099](https://github.com/bids-standard/bids-specification/pull/2099) | 6 | ✅ | 2026-02-13 | [fd17184178](https://github.com/bids-standard/bids-specification/commit/fd17184178f58df00cfb2ccfc17241fb029e46ca) | [Schema](./28/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/enh-prs-and-beps/BEPs/28/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/enh-prs-and-beps/BEPs/28/schema_pp.json) |
| [032](https://bids.neuroimaging.io/bep032) | Microelectrode electrophysiology | [Doc](https://docs.google.com/document/d/1oG-C8T-dWPqfVzL2W8HO3elWK8NIh2cOCPssRGv23n0/) | [2307](https://github.com/bids-standard/bids-specification/pull/2307) | 1 | ✅ | 2026-02-05 | [0d80830ca1](https://github.com/bids-standard/bids-specification/commit/0d80830ca16aad1fd84f00224243ac26cbd19618) | [Schema](./32/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/enh-prs-and-beps/BEPs/32/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/enh-prs-and-beps/BEPs/32/schema_pp.json) |
| [034](https://bids.neuroimaging.io/bep034) | Computational modeling | N/A | [967](https://github.com/bids-standard/bids-specification/pull/967) | 3 | ✅ | 2025-10-01 | [b4d0044a79](https://github.com/bids-standard/bids-specification/commit/b4d0044a797202df2fb1afa912f0a3def07a09e7) | [Schema](./34/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/enh-prs-and-beps/BEPs/34/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/enh-prs-and-beps/BEPs/34/schema_pp.json) |
| [044](https://bids.neuroimaging.io/bep044) | Stimuli | N/A | [2022](https://github.com/bids-standard/bids-specification/pull/2022) | 4 | ✅ | 2026-01-02 | [ed0e3a7ffa](https://github.com/bids-standard/bids-specification/commit/ed0e3a7ffa567342fa6316e4ef77a964569b2626) | [Schema](./44/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/enh-prs-and-beps/BEPs/44/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/enh-prs-and-beps/BEPs/44/schema_pp.json) |
| [045](https://bids.neuroimaging.io/bep045) | Peripheral Physiological Recordings | [Doc](https://docs.google.com/document/d/1oTfjzY5ZnLIYd0kPPWhR81sBmMuy_jC5YYIaqj6OhSA/edit) | [2267](https://github.com/bids-standard/bids-specification/pull/2267) | 3 | ✅ | 2026-01-16 | [97da2a8697](https://github.com/bids-standard/bids-specification/commit/97da2a86974ab0e785c0d87b52bfa99ba9b7bda8) | [Schema](./45/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/enh-prs-and-beps/BEPs/45/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/enh-prs-and-beps/BEPs/45/schema_pp.json) |
| [047](https://bids.neuroimaging.io/bep047) | Audio/video recordings for behavioral experiments | N/A | [2231](https://github.com/bids-standard/bids-specification/pull/2231) | 3 | ✅ | 2026-02-10 | [ca047ef677](https://github.com/bids-standard/bids-specification/commit/ca047ef677826e6b05fd373d8c3457626cf27d29) | [Schema](./47/schema.json) \| [Raw](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/enh-prs-and-beps/BEPs/47/schema.json) \| [Pretty](https://raw.githubusercontent.com/bids-standard/bids-schema/refs/heads/enh-prs-and-beps/BEPs/47/schema_pp.json) |## How to Use BEP Schemas

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

