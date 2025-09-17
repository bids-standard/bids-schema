# BIDS Specification PR Schemas

This directory contains automatically generated schemas from Pull Requests to the BIDS specification
that modify the schema files.

## Overview

Each subdirectory corresponds to a Pull Request (PR) number and contains:
- `schema.json` - The compiled BIDS schema (only file stored to save space)
- `PR_METADATA.json` - Metadata about the PR and processing status

## Active PR Schemas

**Status Summary:** 🟢 Open (8) | 🟣 Merged (0) | 🔴 Closed (0)

| PR # | Title | Author | Status | Schema Updated | Last Commit | Actions |
|------|-------|--------|--------|----------------|-------------|---------|
| 1261 | Unknown | Unknown | 🟢 Open | 2025-09-17 | 97825f5c27 | [View PR](https://github.com/bids-standard/bids-specification/pull/1261) \| [Schema](./1261/schema.json) |
| 1328 | Unknown | Unknown | 🟢 Open | 2025-09-17 | 79c7024e7a | [View PR](https://github.com/bids-standard/bids-specification/pull/1328) \| [Schema](./1328/schema.json) |
| 1331 | Unknown | Unknown | 🟢 Open | 2025-09-17 | 33a11f2944 | [View PR](https://github.com/bids-standard/bids-specification/pull/1331) \| [Schema](./1331/schema.json) |
| 1533 | Unknown | Unknown | 🟢 Open | 2025-09-17 | 7a84ff6c95 | [View PR](https://github.com/bids-standard/bids-specification/pull/1533) \| [Schema](./1533/schema.json) |
| 1567 | Unknown | Unknown | 🟢 Open | 2025-09-17 | eb040f59b0 | [View PR](https://github.com/bids-standard/bids-specification/pull/1567) \| [Schema](./1567/schema.json) |
| 1632 | Unknown | Unknown | 🟢 Open | 2025-09-17 | 7ad57fd96e | [View PR](https://github.com/bids-standard/bids-specification/pull/1632) \| [Schema](./1632/schema.json) |
| 1705 | Unknown | Unknown | 🟢 Open | 2025-09-17 | 70bddec095 | [View PR](https://github.com/bids-standard/bids-specification/pull/1705) \| [Schema](./1705/schema.json) |
| 2191 | Unknown | Unknown | 🟢 Open | 2025-09-17 | 2b87c982cf | [View PR](https://github.com/bids-standard/bids-specification/pull/2191) \| [Schema](./2191/schema.json) |

## How to Use PR Schemas

1. **Accessing a schema**: Navigate to `PRs/{pr_number}/schema.json`
2. **Checking metadata**: View `PRs/{pr_number}/PR_METADATA.json` for processing details
3. **Raw schema files**: Not stored (only compiled schema.json saved to reduce repository size)

## Update Frequency

PR schemas are automatically updated:
- Every 12 hours via scheduled GitHub Actions
- On manual workflow dispatch
- When changes are pushed to the main branch

## Related Resources

- [BEP Schemas](../BEPs/) - BIDS Extension Proposal schemas
- [Released Versions](../versions/) - Official BIDS schema releases
- [BIDS Specification Repository](https://github.com/bids-standard/bids-specification)

---

*Last generated: 2025-09-17 14:30:40 UTC*
