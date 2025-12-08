# Application Update Workflow

**Workflow**: `application-update.yml`
**Purpose**: Unified configuration-driven orchestrator for updating FOLIO application module dependencies
**Type**: Reusable workflow (`workflow_call`)

## 🎯 Overview

This workflow provides a unified, configuration-driven solution for updating FOLIO application module dependencies across all branch types. The workflow orchestrates the complete update process including module updates, validation, notifications, and comprehensive summaries.

All branch-specific configuration (pre-release mode, build offsets, PR requirements) is read from the application's `update-config.yml` file, enabling consistent behavior across the FOLIO ecosystem. The same workflow handles snapshot branches (direct commits), release branches (PR-based updates), and custom branch configurations.

## 📋 Workflow Interface

### Inputs

| Input                     | Description                                          | Required | Type    | Default             |
|---------------------------|------------------------------------------------------|----------|---------|---------------------|
| `app_name`                | Application name                                     | Yes      | string  | -                   |
| `repo`                    | Application repository (org/repo format)             | Yes      | string  | -                   |
| `branch`                  | Branch to update                                     | Yes      | string  | -                   |
| `update_branch`           | Update branch name (for PRs)                         | No       | string  | `''`                |
| `need_pr`                 | Whether to create/update PR                          | No       | boolean | `false`             |
| `pre_release`             | Pre-release mode (true/false/only)                   | No       | string  | `'false'`           |
| `workflow_run_number`     | GitHub run number for display                        | Yes      | string  | -                   |
| `descriptor_build_offset` | Offset for application artifact version              | No       | string  | `'100100000000000'` |
| `rely_on_FAR`             | Whether to rely on FAR for dependencies              | No       | boolean | `false`             |
| `dry_run`                 | Perform dry run without making changes               | No       | boolean | `false`             |
| `use_github_app`          | Use GitHub App for authentication                    | No       | boolean | `false`             |
| `pr_reviewers`            | Comma-separated list of reviewers                    | No       | string  | `''`                |
| `pr_labels`               | Comma-separated list of PR labels                    | No       | string  | `''`                |
| `is_scheduled`            | Whether this is a scheduled run                      | No       | boolean | `false`             |

### Outputs

| Output                 | Description                                                  |
|------------------------|--------------------------------------------------------------|
| `update_result`        | Result of the update (success/failure/skipped)               |
| `updated`              | Whether modules were updated                                 |
| `new_version`          | New application version                                      |
| `previous_version`     | Previous application version                                 |
| `updated_cnt`          | Number of updated modules                                    |
| `updated_modules`      | List of updated modules                                      |
| `pr_created`           | Whether a PR was created (for need_pr mode)                  |
| `pr_url`               | URL of created/updated PR                                    |
| `commit_sha`           | Commit SHA of the update                                     |
| `failure_reason`       | Reason for failure (validation or publishing errors)         |
| `notification_outcome` | Outcome of the notification                                  |

### Permissions

| Permission        | Level  | Purpose                              |
|-------------------|--------|--------------------------------------|
| `contents`        | write  | Repository content and branch access |
| `pull-requests`   | write  | PR creation and management           |
| `issues`          | write  | Issue and PR interaction             |

## 🔄 Workflow Execution Flow

### 1. Update Execution
**Job**: `update`

Delegates to the core `application-update-flow.yml` workflow with all configuration:

**Process**:
- Passes all input parameters to flow workflow
- Handles both PR and direct commit modes
- Supports all pre-release modes (true/false/only)
- Manages platform descriptor requirements

### 2. Notification Management (Conditional)
**Job**: `notify`

**Execution Conditions**:
- Not in dry-run mode
- Either updates were made OR workflow failed
- Team and general Slack channels configured

**Notification Scenarios**:
- **Success**: Module updates with version details
- **Failure**: Error information with failure reasons
- **Skipped**: Gracefully handled without notification

**Channel Configuration**:
- `SLACK_NOTIF_CHANNEL`: Team-specific notifications
- `GENERAL_SLACK_NOTIF_CHANNEL`: Organization-wide announcements

### 3. Workflow Summary Generation
**Job**: `summarize`

**Always Executes**: Provides complete status report regardless of outcome

**Includes**:
- Update results and version information
- Module change details
- PR information (if applicable)
- Notification status
- Error details and diagnostics

## 🎯 Pre-Release Mode Configuration

The `pre_release` parameter controls module version filtering and supports three values:

### `pre_release: "only"` (Snapshot-Only Mode)
- **Registry Query**: `preRelease=only` and `npmSnapshot=only`
- **Module Filter**: ONLY snapshot/pre-release versions
- **Typical Use**: Snapshot branches tracking latest development
- **Example Versions**: `1.2.3-SNAPSHOT`, `2.0.0-alpha.1`

### `pre_release: "true"` (Include Pre-Release Mode)
- **Registry Query**: `preRelease=true` and `npmSnapshot=true`
- **Module Filter**: BOTH release AND pre-release versions
- **Typical Use**: Development branches that may use either
- **Example Versions**: `1.2.3`, `2.0.0-SNAPSHOT`, `3.0.0-beta.1`

### `pre_release: "false"` (Release-Only Mode)
- **Registry Query**: `preRelease=false` and `npmSnapshot=false`
- **Module Filter**: ONLY stable release versions
- **Typical Use**: Release branches (R1-2025, R2-2025, etc.)
- **Example Versions**: `1.2.3`, `2.0.4` (excludes SNAPSHOT/beta/alpha)

## 📊 Usage Examples

### Configuration-Based Scheduling (Recommended)

**Application's `update-scheduler.yml`**:
```yaml
name: Application Update Scheduler

on:
  schedule:
    - cron: "*/20 * * * *"
  workflow_dispatch:
    inputs:
      dry_run:
        description: 'Perform dry run'
        type: boolean
        default: false

jobs:
  get-config:
    runs-on: ubuntu-latest
    outputs:
      branch_config: ${{ steps.get-update-config.outputs.branch_config }}
      branch_count: ${{ steps.get-update-config.outputs.branch_count }}
      pr_reviewers: ${{ steps.get-update-config.outputs.pr_reviewers }}
      pr_labels: ${{ steps.get-update-config.outputs.pr_labels }}
    steps:
      - uses: actions/checkout@v4
      - name: Get Update Configuration
        id: get-update-config
        uses: folio-org/kitfox-github/.github/actions/get-update-config@master
        with:
          repo: ${{ github.repository }}
          github_token: ${{ github.token }}

  update-branches:
    name: Update ${{ matrix.branch }}
    needs: get-config
    if: needs.get-config.outputs.branch_count > 0
    strategy:
      matrix:
        include: ${{ fromJson(needs.get-config.outputs.branch_config) }}
      fail-fast: false
      max-parallel: 3
    uses: folio-org/kitfox-github/.github/workflows/application-update.yml@master
    with:
      app_name: ${{ github.event.repository.name }}
      repo: ${{ github.repository }}
      branch: ${{ matrix.branch }}
      update_branch: ${{ matrix.update_branch }}
      need_pr: ${{ matrix.need_pr }}
      pre_release: ${{ matrix.pre_release }}
      workflow_run_number: ${{ github.run_number }}
      descriptor_build_offset: ${{ matrix.descriptor_build_offset }}
      rely_on_FAR: ${{ matrix.rely_on_FAR }}
      dry_run: ${{ github.event_name == 'workflow_dispatch' && inputs.dry_run || false }}
      pr_reviewers: ${{ needs.get-config.outputs.pr_reviewers }}
      pr_labels: ${{ needs.get-config.outputs.pr_labels }}
    secrets: inherit
```

**Application's `update-config.yml`**:
```yaml
update_config:
  enabled: true
  update_branch_format: version-update/{0}
  labels:
    - version-update
    - automated
  pr_reviewers:
    - folio-org/kitfox

branches:
  - snapshot:
      enabled: true
      need_pr: false
      pre_release: "only"
      descriptor_build_offset: "100100000000000"
      rely_on_FAR: false
  - R1-2025:
      enabled: true
      need_pr: true
      pre_release: "false"
      descriptor_build_offset: ""
      rely_on_FAR: false
  - R2-2025:
      enabled: true
      need_pr: true
      pre_release: "false"
      descriptor_build_offset: ""
      rely_on_FAR: false
```

### Manual Single Branch Update

```yaml
jobs:
  update-snapshot:
    uses: folio-org/kitfox-github/.github/workflows/application-update.yml@master
    with:
      app_name: ${{ github.event.repository.name }}
      repo: ${{ github.repository }}
      branch: 'snapshot'
      pre_release: 'only'
      workflow_run_number: ${{ github.run_number }}
      descriptor_build_offset: '100100000000000'
      dry_run: false
    secrets: inherit
```

### Release Branch with PR

```yaml
jobs:
  update-release:
    uses: folio-org/kitfox-github/.github/workflows/application-update.yml@master
    with:
      app_name: ${{ github.event.repository.name }}
      repo: ${{ github.repository }}
      branch: 'R1-2025'
      update_branch: 'version-update/R1-2025'
      need_pr: true
      pre_release: 'false'
      workflow_run_number: ${{ github.run_number }}
      pr_reviewers: 'platform-lead,senior-dev'
      pr_labels: 'release-update,automated'
      dry_run: false
    secrets: inherit
```

### Dry Run Testing

```yaml
jobs:
  test-update:
    uses: folio-org/kitfox-github/.github/workflows/application-update.yml@master
    with:
      app_name: ${{ github.event.repository.name }}
      repo: ${{ github.repository }}
      branch: 'snapshot'
      pre_release: 'only'
      workflow_run_number: ${{ github.run_number }}
      dry_run: true
    secrets: inherit
```

## 🔍 Features

### Unified Workflow Logic
- **Single Entry Point**: One workflow for all branch types
- **Configuration-Driven**: Behavior controlled by inputs and config files
- **Consistent Behavior**: Same logic for all branches

### Flexible Authentication
- **GitHub App**: Enhanced permissions for cross-repo operations
- **Standard Token**: Fallback to repository token
- **Automatic Selection**: Based on `use_github_app` parameter

### Comprehensive Notifications
- **Multi-Channel Support**: Team and general Slack channels
- **Rich Content**: Detailed module update information
- **Status-Based Messaging**: Success, failure, and skip scenarios
- **Non-Blocking**: Notification failures don't fail workflow

### Professional Reporting
- **GitHub Summaries**: Rich markdown summaries in workflow UI
- **Progress Indicators**: Visual status for each component
- **Complete Details**: Module lists, PR links, versions
- **Troubleshooting Info**: Failure reasons and diagnostics

## 🛡️ Error Handling

### Failure Scenarios

**Update Failure**:
- **Cause**: Module discovery or version checking fails
- **Response**: Error notification with failure reason
- **Recovery**: Check module registry connectivity

**Validation Failure**:
- **Cause**: Application descriptor validation fails
- **Response**: Workflow fails with validation details
- **Recovery**: Review descriptor format and module compatibility

**PR Management Failure**:
- **Cause**: GitHub API issues or permission problems
- **Response**: Notification includes failure context
- **Recovery**: Verify repository permissions and GitHub API status

**Notification Failure**:
- **Cause**: Slack API issues or channel configuration
- **Response**: Workflow continues, status recorded
- **Recovery**: Verify Slack bot configuration and channels

### Graceful Degradation

- **Platform Descriptor**: Continues without platform validation if unavailable
- **Partial Updates**: Processes available module updates even if some fail
- **Notification Resilience**: Continues workflow if notifications fail
- **Dry-Run Safety**: All destructive operations skipped in dry-run mode

## 📈 Performance Considerations

### Optimization Features

- **Conditional Execution**: Skips unnecessary steps based on configuration
- **Parallel Processing**: Independent operations run concurrently
- **Artifact Efficiency**: Minimal artifact sizes and retention
- **API Efficiency**: Consolidated GitHub API calls

### Resource Management

- **Memory Usage**: Minimal state retention between jobs
- **Network Optimization**: Cached platform descriptors
- **Time Efficiency**: Smart job dependencies
- **Cost Efficiency**: Only runs necessary operations

## 🧪 Testing Strategy

### Test Scenarios

**Snapshot Branch (Direct Commit)**:
- **Configuration**: `need_pr: false`, `pre_release: "only"`
- **Expected**: Direct commits to snapshot branch
- **Validation**: Commits appear on branch, no PRs created

**Release Branch (PR Mode)**:
- **Configuration**: `need_pr: true`, `pre_release: "false"`
- **Expected**: PR created/updated with release modules only
- **Validation**: PR contains only stable release versions

**No Updates Available**:
- **Expected**: No commits, no PRs, workflow completes
- **Validation**: No repository changes made

**Dry Run Mode**:
- **Expected**: All analysis runs, no commits or PRs
- **Validation**: No side effects in repository

### Validation Checklist

- [ ] `update-config.yml` exists and is properly formatted
- [ ] Branch exists in repository
- [ ] Module registry is accessible
- [ ] Platform descriptor available (if not relying on FAR)
- [ ] Slack channels configured (for notifications)
- [ ] GitHub App credentials configured (if using)
- [ ] Reviewer names are valid (for PR mode)

## 📚 Related Documentation

- **[Application Update Flow](application-update-flow.md)**: Core flow implementation
- **[Generate Application Descriptor Action](../actions/generate-application-descriptor/README.md)**: Template-based descriptor generation and update
- **[Get Update Config Action](../actions/get-update-config/README.md)**: Configuration parsing
- **[Validate Application Action](../actions/validate-application/README.md)**: Descriptor validation
- **[Fetch Platform Descriptor Action](../actions/fetch-platform-descriptor/README.md)**: Platform descriptor fetching

## 🔍 Troubleshooting

### Common Issues

**Configuration Not Found**:
```
Error: update-config.yml not found
Solution: Create update-config.yml in .github/ directory
```

**Branch Not Enabled**:
```
Warning: Branch 'snapshot' is disabled in configuration
Solution: Set enabled: true in branch configuration
```

**No Branches to Update**:
```
Warning: No existing update branches found to scan
Solution: Verify branches exist and are enabled in configuration
```

**Module Version Resolution Failed**:
```
Error: Failed to fetch latest module versions
Solution: Check FOLIO registry connectivity and module availability
```

---

**Last Updated**: November 2025
**Workflow Version**: 2.0 (Unified)
**Compatibility**: All FOLIO application repositories
