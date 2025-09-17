# BIDS Specification PR Schemas

This directory contains automatically generated schemas from Pull Requests to the BIDS specification
that modify the schema files.

## Overview

Each subdirectory corresponds to a Pull Request (PR) number and contains:
- `schema/` - The raw schema files from the PR
- `schema.json` - The compiled BIDS schema
- `PR_METADATA` - Metadata about the PR and processing status

## Active PR Schemas

*No PR schemas currently available*


## How to Use PR Schemas

1. **Accessing a schema**: Navigate to `PRs/{pr_number}/schema.json`
2. **Checking metadata**: View `PRs/{pr_number}/PR_METADATA` for processing details
3. **Raw schema files**: Available in `PRs/{pr_number}/schema/`

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

*Last generated: 2025-09-17 12:54:00 UTC*
