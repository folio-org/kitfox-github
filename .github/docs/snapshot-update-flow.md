# Snapshot Update Flow Workflow

**Workflow**: `snapshot-update-flow.yml`
**Purpose**: Orchestrates automated module version updates and application descriptor management for FOLIO snapshot operations
**Type**: Reusable workflow (`workflow_call`)
**Related Ticket**: RANCHER-2571, Item #8

## 🎯 Overview

This workflow orchestrates the complete snapshot update flow for FOLIO applications. It coordinates specialized workflows and actions to check for newer module versions, validate changes, and commit updates.

## 🏗️ Refactored Architecture

The workflow has been refactored into modular components for better reusability and maintainability:

1. **`update-application.yml`** - Module version checking and descriptor generation
2. **`validate-application`** action - Application descriptor validation
3. **`publish-app-descriptor`** action - Publishing descriptors to FAR
4. **`commit-application-changes.yml`** - Git operations for committing changes

This orchestrator workflow coordinates these components and handles failure scenarios.

## 📋 Workflow Interface

### Inputs

| Input                     | Description                                                    | Required  | Type    | Default             |
|---------------------------|----------------------------------------------------------------|-----------|---------|---------------------|
| `app_name`                | Application name                                               | Yes       | string  | -                   |
| `repo`                    | Application repository name (org/repo format)                  | Yes       | string  | -                   |
| `branch`                  | Branch to update                                               | No        | string  | `'snapshot'`        |
| `workflow_run_number`     | GitHub run number for display                                  | Yes       | string  | -                   |
| `descriptor_build_offset` | Offset to apply to application artifact version                | No        | string  | `'100100000000000'` |
| `rely_on_FAR`             | Whether to rely on FAR for application descriptor dependencies | No        | boolean | `false`             |
| `mode`                    | Update mode: 'snapshot' or 'release'                           | No        | string  | `'snapshot'`        |
| `dry_run`                 | Perform dry run without making changes                         | No        | boolean | `false`             |
| `use_github_app`          | Use GitHub App for authentication                              | No        | boolean | `false`             |

### Outputs

| Output                     | Description                                                  |
|----------------------------|--------------------------------------------------------------|
| `app_name`                 | Application name (pass-through)                              |
| `skipped`                  | Whether workflow was skipped (e.g., branch does not exist)   |
| `updated`                  | Whether application was updated                              |
| `previous_version`         | Previous application version                                 |
| `new_version`              | New application version if updated                           |
| `updated_cnt`              | Number of updated modules                                    |
| `updated_modules`          | List of updated modules                                      |
| `failure_reason`           | Reason for failure (validation or publishing errors)         |
| `commit_sha`               | Commit SHA                                                   |
| `app_descriptor_url`       | URL of generated application descriptor                      |
| `app_descriptor_file_name` | Name of generated application descriptor file                |

### Secrets

| Secret         | Description                        | Required                      |
|----------------|------------------------------------|-------------------------------|
| `GH_APP_TOKEN` | GitHub token for repository access | No (fallback to GITHUB_TOKEN) |

## 🔄 Workflow Execution Flow

### 1. Check Branch Existence - *Resilience Gate*
- **Branch Validation**: Verifies target branch exists in the repository
- **Graceful Skipping**: If branch doesn't exist, workflow skips update without failing
- **Status Reporting**: Reports "skipped" status with clear reason
- **Resilience**: Prevents failures when new applications don't have snapshot branches yet

### 2. Update Application (`update-application.yml`) - *Conditional*
- **Runs only if**: Branch exists
- **Module Version Checking**: Queries FOLIO registry for latest module versions
- **Version Comparison**: Compares current vs. available versions
- **Descriptor Updates**: Updates application-descriptor.json with new module versions
- **POM Updates**: Updates pom.xml version when in release mode
- **Artifact Generation**: Creates state files for downstream processing

### 3. Validate Application (`validate-application` action) - *Conditional*
- **Runs only if**: Updates were found in step 2
- **Platform Integration**: Downloads platform descriptor for validation context
- **Interface Validation**: Validates module interface integrity via FAR API
- **Dependency Validation**: Validates application dependencies integrity (conditional based on platform descriptor availability)

### 4. Publish Descriptor (`publish-app-descriptor` action) - *Conditional*
- **Runs only if**: Validation passed and not in dry-run mode
- **Registry Upload**: Publishes application descriptor to FAR registry

### 5. Commit Changes (`commit-application-changes.yml`) - *Conditional*
- **Runs only if**: Updates were found and validation passed
- **Git Configuration**: Sets up GitHub Actions bot identity
- **File Download**: Retrieves updated state files from artifacts
- **Commit Creation**: Creates descriptive commit with update details
- **Branch Push**: Pushes changes to target branch (unless dry-run)

### 6. Cleanup on Failure - *Conditional*
- **Runs only if**: Commit failed after registry upload
- **Registry Cleanup**: Removes uploaded descriptor from FAR registry
- **Error Reporting**: Provides failure context for troubleshooting

### 7. Upload Results
- **Always runs**: Regardless of success or failure
- **Result Aggregation**: Collects all workflow outputs
- **Artifact Creation**: Creates structured JSON result artifact
- **Status Reporting**: Provides comprehensive operation summary for aggregation

## 🔍 Module Version Discovery

### Registry Integration

The workflow uses multiple sources for module version discovery:

**FOLIO Registry** (Primary):
- **Endpoint**: `https://folio-registry.dev.folio.org/_/proxy/modules`
- **Backend Modules**: Queries with `preRelease=only/true/false`
- **UI Modules**: Queries with `npmSnapshot=only/true/false`
- **Version Filtering**: Processes latest versions with artifact validation

**Artifact Validation**:
- **Docker Registry**: Validates backend module artifacts
- **NPM Registry**: Validates UI module artifacts
- **Existence Checking**: Ensures versions are actually available

### Version Processing Logic

```bash
# Backend modules: Docker Hub validation
artifact_path="$DOCKER_REGISTRY/$repository/$module_name/tags/$version"

# UI modules: NPM repository validation  
artifact_path="$NPM_REGISTRY/$repository/$module_name"
```

## 🏗️ Application Descriptor Management

### State File Processing

**application-descriptor.json** serves as the state file:
- **Current Versions**: Tracks current module versions
- **Update Detection**: Enables "Is new version available?" logic
- **Baseline Tracking**: Maintains version history for CI decisions

### Version Calculation

**SNAPSHOT Versions**:
```bash
BUILD_NUMBER=$((DESCRIPTOR_BUILD_OFFSET + RUN_NUMBER))
NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}-SNAPSHOT.${BUILD_NUMBER}"
```

**Release Versions**:
```bash
NEW_PATCH=$((PATCH + 1))
NEW_VERSION="${MAJOR}.${MINOR}.${NEW_PATCH}"
```

## 🛡️ Validation and Quality Assurance

### Interface Integrity Validation

**FAR API Validation**:
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  --data-binary @descriptor.json \
  "$FAR_API_URL/validate"
```

### Dependency Integrity Validation

**Multi-Descriptor Validation**:
```bash
find /tmp/app-descriptors -name '*.json' -print0 \
  | xargs -0 cat \
  | jq -s '{applicationDescriptors: .}' \
  | curl -X POST "$FAR_API_URL/validate-descriptors"
```

## 📊 Usage Examples

### Basic Snapshot Update

```yaml
jobs:
  update-application:
    uses: folio-org/kitfox-github/.github/workflows/snapshot-update-flow.yml@master
    with:
      app_name: ${{ github.event.repository.name }}
      repo: ${{ github.repository }}
      workflow_run_number: ${{ github.run_number }}
    secrets: inherit
```

### Custom Configuration

```yaml
jobs:
  update-application:
    uses: folio-org/kitfox-github/.github/workflows/snapshot-update-flow.yml@master
    with:
      app_name: ${{ github.event.repository.name }}
      repo: ${{ github.repository }}
      branch: 'development'
      workflow_run_number: ${{ github.run_number }}
      descriptor_build_offset: '200000000000000'
      rely_on_FAR: true
      pre_release: 'true'
      dry_run: false
    secrets: inherit
```

### Dry Run Testing

```yaml
jobs:
  test-update:
    uses: folio-org/kitfox-github/.github/workflows/snapshot-update-flow.yml@master
    with:
      app_name: ${{ github.event.repository.name }}
      repo: ${{ github.repository }}
      workflow_run_number: ${{ github.run_number }}
      dry_run: true
    secrets: inherit
```

## 🧪 Testing Strategy

### Dry Run Behavior

When `dry_run: true`:
- **Module Checking**: Executes normally
- **Version Updates**: Applied to state file
- **Artifact Generation**: Creates descriptors normally
- **Validation**: Performs all validation checks
- **Registry Upload**: **Skipped** (no actual publication)
- **Git Operations**: **Skipped** (no commits or pushes)
- **Results**: Generated normally for pipeline testing

### Validation Checklist

- [ ] application-descriptor.json exists and is valid
- [ ] Maven pom.xml is present and readable
- [ ] FOLIO registry is accessible
- [ ] Docker/NPM registries are accessible
- [ ] FAR API is responsive
- [ ] Git operations have proper permissions

## 🔍 Troubleshooting

### Common Issues

**Branch Does Not Exist**:
```
Warning: Branch 'snapshot' does not exist in repository 'folio-org/app-example'
Status: Skipped (not failed)
Solution: Workflow gracefully skips update. Create the branch when ready or this is expected for new applications.
```

**State File Missing**:
```
Error: application-descriptor.json not found
Solution: Ensure state file exists in repository root
```

**Registry Connection Failed**:
```
Error: Failed to fetch latest module versions from registry
Solution: Check FOLIO registry availability and network connectivity
```

**Artifact Validation Failed**:
```
Error: Failed to fetch module artifacts from repository
Solution: Verify module versions exist in Docker Hub/NPM registry
```

**FAR Validation Failed**:
```
Error: Module interface integrity validation request failed (HTTP 400)
Solution: Check application descriptor format and module compatibility
```

**FAR Publishing Failed**:
```
Error: Failed to publish application descriptor to FAR (HTTP 400)
Behavior: Workflow fails, no commit is made, notification is sent with failure details
Common Causes:
  - Duplicate interface declarations (same interface marked as both REQUIRED and OPTIONAL)
  - Malformed module descriptors in upstream modules
  - Invalid descriptor format
Solution: Check the error message for specific module/interface issues. May require fixing upstream module descriptors.
```

**Git Permission Denied**:
```
Error: Permission denied to repository
Solution: Verify GH_APP_TOKEN permissions or use repository token
```

### Debug Information

The workflow provides comprehensive logging:
- **Module Discovery**: Detailed version checking with registry responses
- **Validation Steps**: API request/response logging
- **Git Operations**: Commit details and push results
- **Error Context**: Specific failure reasons with actionable guidance

## 🔄 Integration Patterns

### Scheduled Updates

```yaml
on:
  schedule:
    - cron: "*/20 * * * *"  # Every 20 minutes

jobs:
  update-application:
    uses: folio-org/kitfox-github/.github/workflows/snapshot-update-flow.yml@master
    with:
      app_name: ${{ github.event.repository.name }}
      repo: ${{ github.repository }}
      workflow_run_number: ${{ github.run_number }}
```

### Platform Integration

```yaml
jobs:
  fetch-platform-descriptor:
    steps:
      - uses: actions/checkout@v4
        with:
          repository: folio-org/platform-lsp
          ref: snapshot
      - uses: actions/upload-artifact@v4
        with:
          name: platform-descriptor
          path: platform-descriptor.json

  update-application:
    needs: fetch-platform-descriptor
    uses: folio-org/kitfox-github/.github/workflows/snapshot-update-flow.yml@master
```


## 📈 Performance Considerations

### Registry Optimization

- **Concurrent Requests**: Module version checks run in parallel
- **Caching Strategy**: Registry responses cached within workflow run
- **Timeout Handling**: Reasonable timeouts for external API calls
- **Retry Logic**: Built-in retry for transient failures

### Artifact Management

- **Retention Policy**: Artifacts retained for 1 day
- **Size Optimization**: Only essential files uploaded
- **Cleanup Strategy**: Failed uploads automatically cleaned up

## 📚 Related Documentation

- **[Snapshot Update](snapshot-update.md)**: Complete snapshot update workflow with integrated notifications
- **[Release Update](release-update.md)**: Release branch update orchestration with notifications
- **[Platform LSP Integration](../../../platform-lsp/.github/docs/snapshot-flow.md)**: Platform-level coordination
- **[FAR Registry Documentation](https://folio-org.atlassian.net/wiki/spaces/FOLIJET/pages/1115029566/Application+registry+hosting+approach)**: Application registry details
- **[FOLIO Module Registry](https://folio-registry.dev.folio.org)**: Module version discovery

---

**Last Updated**: September 2025  
**Workflow Version**: 3.0  
**Compatibility**: All FOLIO application repositories
