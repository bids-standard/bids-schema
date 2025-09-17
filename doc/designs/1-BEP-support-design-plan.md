# BEP Support Implementation Design Plan

## Executive Summary

This document outlines the technical design for automating the generation and maintenance of BIDS schemas from Pull Requests (PRs) and BIDS Extension Proposals (BEPs). The system will automatically detect schema changes in PRs, generate corresponding schemas, and maintain a structured directory hierarchy for both PRs and BEPs.

## Current State Analysis

### Existing Infrastructure
- **tools/inject-schema-fully-auto**: Main orchestration script that clones bids-specification and processes releases
- **tools/inject-schema**: Core script that generates schema.json from a specific git reference
- **.github/workflows/inject.yml**: CI workflow running twice daily and on manual dispatch
- **versions/**: Directory containing versioned schemas (releases and master branch)

### Limitations
- Only processes tagged releases and master branch
- No support for PR-based schemas
- No BEP tracking or schema generation
- Manual intervention required for testing BEP schemas

## Design Goals

1. **Automatic PR Schema Detection**: Identify PRs that modify schema files
2. **Schema Generation for PRs**: Build and store schemas for relevant PRs
3. **BEP Integration**: Map BEPs to their corresponding PRs and maintain dedicated folders
4. **Lifecycle Management**: Clean up schemas for merged/closed PRs and completed BEPs
5. **Incremental Processing**: Only process changed PRs/BEPs to optimize CI time

## Proposed Architecture

### Directory Structure
```
versions/
├── 1.10.0/           # Existing release schemas
├── master/           # Existing master branch schema
├── latest/           # Symlink to latest release
PRs/                  # NEW: PR-based schemas
├── 518/
│   ├── schema/
│   ├── schema.json
│   └── PR_METADATA  # PR state, last update, etc.
├── 1234/
│   └── ...
BEPs/                 # NEW: BEP schemas (copies from PRs/)
├── 011/              # BEP number
│   ├── schema/
│   ├── schema.json
│   └── BEP_METADATA  # BEP info, linked PR, etc.
└── 025/
    └── ...
```

### Component Design

#### 1. Enhanced inject-schema Script
**File**: `tools/inject-schema`

**Changes Required**:
- Accept arbitrary git references (not just tags/branches)
- Handle PR refs format: `refs/pull/origin/*/merge`
- Add error handling for non-existent refs
- Support metadata generation for tracking

**New Parameters**:
- `--type`: Specify reference type (release|master|pr)
- `--metadata`: Generate metadata file with processing info

#### 2. PR Schema Processor
**File**: `tools/process-pr-schemas`

**Functionality**:
- Fetch all PR references from bids-specification
- Detect PRs with schema changes using git diff
- Generate schemas for new/updated PRs
- Remove schemas for merged/closed PRs
- Track PR state and last processed commit

**Implementation Steps**:
```bash
# Fetch PR references
git config --add remote.origin.fetch '+refs/pull/*:refs/pull/origin/*'
git fetch origin

# Check for schema changes
for ref in .git/refs/pull/origin/*/merge; do
    pr_number=$(basename $(dirname $ref))
    if git diff --stat origin/master...$ref -- src/schema | grep -q .; then
        # Process PR with schema changes
        process_pr_schema "$pr_number" "$ref"
    fi
done
```

#### 3. BEP Schema Manager
**File**: `tools/process-bep-schemas`

**Functionality**:
- Clone bids-website repository
- Parse `data/beps/beps.yml` for BEP definitions
- Map BEPs to their corresponding PRs
- Copy PR schemas to BEP folders
- Track BEP metadata and relationships

**Data Flow**:
1. Read BEP configuration from bids-website
2. For each BEP with a pull_request field:
   - Verify PR schema exists in PRs/
   - Copy/link PR schema to BEPs/{bep_number}
   - Generate BEP metadata file

#### 4. Enhanced Main Orchestrator
**File**: `tools/inject-schema-fully-auto`

**New Workflow**:
```
1. Process releases and master (existing)
2. Process PR schemas (new)
3. Process BEP schemas (new)
4. Commit changes with detailed messages
5. Generate summary report
```

**Commit Strategy**:
- One commit per PR schema update
- One commit per BEP schema update
- Informative commit messages with PR/BEP context

### State Management

#### PR State Tracking
**File**: `PRs/{pr_number}/PR_METADATA`
```json
{
  "pr_number": 518,
  "last_commit": "abc123...",
  "last_updated": "2024-01-15T10:00:00Z",
  "status": "open|merged|closed",
  "has_schema_changes": true,
  "title": "Add structural derivatives",
  "author": "username"
}
```

#### BEP State Tracking
**File**: `BEPs/{bep_number}/BEP_METADATA`
```json
{
  "bep_number": "011",
  "title": "Structural preprocessing derivatives",
  "pr_number": 518,
  "google_doc": "https://...",
  "last_synced": "2024-01-15T10:00:00Z",
  "status": "draft|review|accepted"
}
```

### GitHub Actions Workflow Updates

#### Enhanced inject.yml
```yaml
name: Inject

on:
  schedule:
    - cron: '0 */12 * * *'
  push:
    branches:
      - main
    paths:
      - '.github/workflows/inject.yml'
      - 'tools/**'
  workflow_dispatch:
    inputs:
      process_prs:
        description: 'Process PR schemas'
        required: false
        default: true
        type: boolean
      process_beps:
        description: 'Process BEP schemas'
        required: false
        default: true
        type: boolean

jobs:
  inject:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout this repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 1

      - name: Configure git
        run: |
          git config --global user.name bids-maintenance
          git config --global user.email bids.maintenance@gmail.com

      - name: Run schema injection
        run: |
          tools/inject-schema-fully-auto
        env:
          PROCESS_PRS: ${{ inputs.process_prs }}
          PROCESS_BEPS: ${{ inputs.process_beps }}

      - name: Push results
        run: git push
```

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1)
1. Enhance `inject-schema` to handle arbitrary refs
2. Create directory structure for PRs/ and BEPs/
3. Implement basic PR detection logic

### Phase 2: PR Processing (Week 2)
1. Implement `process-pr-schemas` script
2. Add PR state tracking
3. Test with sample PRs

### Phase 3: BEP Integration (Week 3)
1. Implement `process-bep-schemas` script
2. Add BEP-to-PR mapping
3. Test with existing BEPs

### Phase 4: Orchestration (Week 4)
1. Update `inject-schema-fully-auto`
2. Enhance GitHub Actions workflow
3. Add comprehensive logging and error handling

### Phase 5: Testing & Deployment (Week 5)
1. End-to-end testing
2. Performance optimization
3. Documentation updates
4. Production deployment

## Performance Considerations

### Optimization Strategies
1. **Incremental Processing**: Only process PRs/BEPs with changes
2. **Parallel Execution**: Process multiple PRs concurrently where possible
3. **Caching**: Cache PR metadata to avoid redundant API calls
4. **Selective Fetching**: Only fetch necessary git refs

### Expected Performance
- Initial full scan: ~10-15 minutes (all open PRs)
- Incremental updates: ~2-3 minutes (changed PRs only)
- BEP processing: ~1-2 minutes

## Error Handling

### Failure Scenarios
1. **Network Failures**: Retry with exponential backoff
2. **Invalid PR Refs**: Log and skip, continue with next
3. **Schema Build Failures**: Store error state in metadata
4. **Concurrent Modifications**: Use file locking for critical sections

### Monitoring & Alerts
- Log all PR/BEP processing activities
- Generate summary reports
- Alert on repeated failures

## Testing Strategy

### Unit Tests
- Test PR detection logic
- Test schema generation for different ref types
- Test metadata parsing and generation

### Integration Tests
- Test full PR processing pipeline
- Test BEP-to-PR mapping
- Test cleanup of merged/closed PRs

### End-to-End Tests
- Simulate full workflow with test PRs
- Verify correct directory structure
- Validate generated schemas

## Security Considerations

1. **Input Validation**: Sanitize PR numbers and refs
2. **File System Security**: Validate paths to prevent directory traversal
3. **Git Security**: Use safe git operations, avoid arbitrary command execution
4. **API Rate Limiting**: Respect GitHub API limits

## Migration Plan

1. **Backup Current State**: Archive existing versions/ directory
2. **Test in Staging**: Run new system in parallel temporarily
3. **Gradual Rollout**: Enable PR processing first, then BEPs
4. **Monitoring Period**: Watch for issues over 1-2 weeks
5. **Full Deployment**: Switch to new system completely

## Future Enhancements

1. **Web Interface**: Dashboard showing PR/BEP schema status
2. **Validation Reports**: Automated schema validation for PRs
3. **Diff Visualization**: Show schema changes between versions
4. **API Endpoints**: Provide programmatic access to PR/BEP schemas
5. **Notification System**: Alert PR authors about schema build status

## Dependencies

### External Dependencies
- bids-specification repository
- bids-website repository (for BEP data)
- bidsschematools Python package
- GitHub API (for PR metadata)

### Internal Dependencies
- Existing inject-schema infrastructure
- GitHub Actions environment
- Git command-line tools

## Risks and Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Large number of PRs overwhelming CI | High | Medium | Implement batching and rate limiting |
| Schema build failures blocking pipeline | Medium | Low | Continue processing other PRs on failure |
| Disk space consumption | Medium | Low | Implement retention policy for old PR schemas |
| GitHub API rate limits | Low | Medium | Cache API responses, use conditional requests |

## Success Metrics

1. **Coverage**: >95% of PRs with schema changes have generated schemas
2. **Freshness**: Schemas updated within 12 hours of PR changes
3. **Reliability**: <1% failure rate in schema generation
4. **Performance**: <5 minute average processing time for updates

## Documentation Requirements

1. **User Documentation**: How to access PR/BEP schemas
2. **Developer Documentation**: How to maintain and extend the system
3. **API Documentation**: Schema access patterns and formats
4. **Troubleshooting Guide**: Common issues and solutions

## Approval and Sign-off

- [ ] Technical Lead Review
- [ ] Security Review
- [ ] Performance Review
- [ ] Documentation Review
- [ ] Final Approval

---

*This design plan is subject to revision based on implementation discoveries and stakeholder feedback.*