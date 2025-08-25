# Application Update Workflow

**Workflow**: `app-update.yml`  
**Purpose**: Automated module version updates and application descriptor management for FOLIO applications  
**Type**: Reusable workflow (`workflow_call`)

## 🎯 Overview

This workflow automates the continuous integration process for FOLIO applications by checking for newer module versions, updating application descriptors, generating artifacts, and publishing to the application registry. It's the core workflow powering FOLIO's snapshot CI system.

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
| `pre_release`             | Pre-release modules (only \| true \| false)                    | No        | string  | `'only'`            |
| `dry_run`                 | Perform dry run without making changes                         | No        | boolean | `false`             |

### Outputs

| Output                     | Description                                   |
|----------------------------|-----------------------------------------------|
| `app_name`                 | Application name (pass-through)               |
| `updated`                  | Whether application was updated               |
| `previous_version`         | Previous application version                  |
| `new_version`              | New application version if updated            |
| `updated_cnt`              | Number of updated modules                     |
| `updated_modules`          | List of updated modules                       |
| `failure_reason`           | Reason for failure                            |
| `commit_sha`               | Commit SHA                                    |
| `app_descriptor_url`       | URL of generated application descriptor       |
| `app_descriptor_file_name` | Name of generated application descriptor file |

### Secrets

| Secret         | Description                        | Required                      |
|----------------|------------------------------------|-------------------------------|
| `GH_APP_TOKEN` | GitHub token for repository access | No (fallback to GITHUB_TOKEN) |

## 🔄 Workflow Execution Flow

### 1. Update Application Descriptor
- **Version Collection**: Extracts current application version from Maven pom.xml
- **Module Version Checking**: Queries FOLIO registry for latest module versions
- **Version Comparison**: Compares current vs. available versions
- **Descriptor Updates**: Updates application-descriptor.json with new module versions
- **Version Calculation**: Calculates new application version based on updates

### 2. Generate Application Artifact
- **Maven Generation**: Uses folio-application-generator to create application descriptor
- **Artifact Validation**: Ensures generated descriptor is valid
- **File Management**: Handles artifact upload and storage

### 3. Verify and Publish Descriptor
- **Platform Integration**: Downloads platform descriptor for validation context
- **Interface Validation**: Validates module interface integrity via FAR API
- **Dependency Validation**: Validates application dependencies integrity
- **Registry Upload**: Publishes application descriptor to FAR registry

### 4. Commit State File
- **Git Configuration**: Sets up GitHub Actions bot identity
- **Change Staging**: Stages updated application-descriptor.json
- **Commit Creation**: Creates descriptive commit with update details
- **Branch Push**: Pushes changes to target branch
- **Rollback Handling**: Removes uploaded descriptor on commit failure

### 5. Results Upload
- **Result Aggregation**: Collects all workflow outputs
- **Artifact Creation**: Creates structured JSON result artifact
- **Status Reporting**: Provides comprehensive operation summary

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
    uses: folio-org/kitfox-github/.github/workflows/app-update.yml@master
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
    uses: folio-org/kitfox-github/.github/workflows/app-update.yml@master
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
    uses: folio-org/kitfox-github/.github/workflows/app-update.yml@master
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
    uses: folio-org/kitfox-github/.github/workflows/app-update.yml@master
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
    uses: folio-org/kitfox-github/.github/workflows/app-update.yml@master
```

### Notification Integration

```yaml
jobs:
  update-application:
    uses: folio-org/kitfox-github/.github/workflows/app-update.yml@master
    # ... configuration ...

  notify-results:
    needs: update-application
    if: always() && needs.update-application.outputs.updated == 'true'
    uses: folio-org/kitfox-github/.github/workflows/app-update-notification.yml@master
    with:
      app_name: ${{ github.event.repository.name }}
      repo: ${{ github.repository }}
      new_version: ${{ needs.update-application.outputs.new_version }}
      previous_version: ${{ needs.update-application.outputs.previous_version }}
      workflow_result: ${{ needs.update-application.result }}
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

- **[App Update Notification](app-update-notification.md)**: Slack notification workflow
- **[Platform LSP Integration](../../../platform-lsp/.github/docs/snapshot-flow.md)**: Platform-level coordination
- **[FAR Registry Documentation](https://folio-org.atlassian.net/wiki/spaces/FOLIJET/pages/1115029566/Application+registry+hosting+approach)**: Application registry details
- **[FOLIO Module Registry](https://folio-registry.dev.folio.org)**: Module version discovery

---

**Last Updated**: August 2025  
**Workflow Version**: 2.0  
**Compatibility**: All FOLIO application repositories
