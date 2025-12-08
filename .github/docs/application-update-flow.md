# Application Update Flow Workflow

**Workflow**: `application-update-flow.yml`
**Purpose**: Core application update flow implementation for all branch types
**Type**: Reusable workflow (`workflow_call`)

## 🎯 Overview

This workflow implements the core update flow for FOLIO applications. It coordinates specialized workflows and actions to check for newer module versions, validate changes, and commit updates. The workflow supports both direct commit mode (for snapshot branches) and PR-based mode (for release branches), making it a unified solution for all branch types.

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

### Outputs

| Output           | Description                                          |
|------------------|------------------------------------------------------|
| `updated`        | Whether application was updated                      |
| `previous_version` | Previous application version                       |
| `new_version`    | New application version if updated                   |
| `updated_cnt`    | Number of updated modules                            |
| `updated_modules`| List of updated modules                              |
| `pr_created`     | Whether a PR was created                             |
| `pr_url`         | URL of created/updated PR                            |
| `failure_reason` | Reason for failure (validation or publishing errors) |
| `commit_sha`     | Commit SHA                                           |

### Permissions

| Permission        | Level  | Purpose                              |
|-------------------|--------|--------------------------------------|
| `contents`        | write  | Repository content and branch access |
| `pull-requests`   | write  | PR creation and management           |
| `issues`          | write  | Issue and PR interaction             |

## 🔄 Workflow Execution Flow

### 1. Prepare Context
**Job**: `prepare-context`

Determines the source branch and checks for existing PRs:

**Source Branch Logic**:
- For PR mode (`need_pr: true`):
  - If update branch exists: use update branch as source
  - If update branch doesn't exist: use main branch as source
- For direct commit mode (`need_pr: false`): use main branch

**PR Status Check**:
- Searches for existing PRs from update branch to main branch
- Records PR number and URL for reuse

### 2. Update Application
**Job**: `update-application`

Uses the `generate-application-descriptor` action with `generation_mode: update`:

**Process**:
- Resolves version constraints from `application.template.json` (^2.0.0 → 2.3.1)
- Full module synchronization (add/remove/upgrade/downgrade)
- Validates Docker images and NPM packages exist
- Updates `application.lock.json` with resolved versions
- Generates `update-result.json` with detailed change tracking
- Creates state files for downstream processing
- Generates artifacts for validation

### 3. Fetch Platform Descriptor (Conditional)
**Job**: `verify-application` (Step)

**Execution Condition**: Only if not relying on FAR

**Process**:
- Fetches platform descriptor from platform-lsp repository
- Uses `fetch-platform-descriptor` action
- Provides descriptor path to validation step
- Runs in same job workspace as validation

### 4. Validate Application (Conditional)
**Job**: `verify-application`

**Execution Condition**: Only when updates were found

**Process**:
- Downloads updated application descriptor artifact
- Validates module interface integrity via FAR API
- Validates application dependencies integrity (if platform descriptor available)
- Provides comprehensive error reporting

### 5. Publish Descriptor (Conditional)
**Job**: `publish-descriptor`

**Execution Conditions**:
- Validation passed
- Not in dry-run mode
- Not in PR mode (PRs don't publish to FAR)

**Process**:
- Publishes application descriptor to FAR registry
- Uses `publish-app-descriptor` action

### 6. Commit Changes (Conditional)
**Job**: `commit-changes`

**Execution Conditions**:
- Updates were found
- Validation passed
- Not in PR mode

**Process**:
- Downloads updated state files from artifacts
- Creates descriptive commit with module details
- Pushes changes to branch (unless dry-run)
- Uses GitHub App or standard token

### 7. Manage PR (Conditional)
**Job**: `manage-pr`

**Execution Conditions**:
- PR mode enabled (`need_pr: true`)
- Not in dry-run mode

**PR Creation Logic**:
- Creates PR if it doesn't exist and updates are available
- Uses update branch as head, main branch as base

**PR Update Logic**:
- Updates existing PR if new updates are found
- Adds/updates reviewers and labels

**Commit Generation**:
- Commits to update branch (creates if needed)
- Uses source branch determined in prepare-context

### 8. Cleanup on Failure (Conditional)
**Job**: `cleanup-on-failure`

**Execution Condition**: Commit failed after registry upload

**Process**:
- Removes uploaded descriptor from FAR registry
- Uses `unpublish-app-descriptor` action
- Provides failure context for troubleshooting

## 🔍 Module Version Discovery

### Template-Driven Version Resolution

The workflow uses the `folio-application-generator` Maven plugin for version resolution:

**Template File** (`application.template.json`):
- Contains version constraints (e.g., `^2.0.0`, `~1.2.3`, `>=1.0.0`)
- Supports semver constraint resolution
- Defines module list and pre-release preferences per module

**Version Resolution**:
- **Constraint Resolution**: `^2.0.0` resolves to latest compatible version (e.g., `2.3.1`)
- **Pre-release Filtering**: Respects `preRelease` setting per module
- **Module Synchronization**: Adds new modules, removes unlisted modules

**Artifact Validation** (default registries):
- **Docker Registry**: DockerHub `folioorg` (release), `folioci` (pre-release)
- **NPM Registry**: `npm-folio` (release), `npm-folioci` (pre-release)
- **Existence Checking**: Validates Docker images and NPM packages exist before resolution

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

### Direct Commit Mode (Snapshot Branch)

```yaml
jobs:
  update-snapshot:
    uses: folio-org/kitfox-github/.github/workflows/application-update-flow.yml@master
    with:
      app_name: ${{ github.event.repository.name }}
      repo: ${{ github.repository }}
      branch: 'snapshot'
      need_pr: false
      pre_release: 'only'
      workflow_run_number: ${{ github.run_number }}
      descriptor_build_offset: '100100000000000'
    secrets: inherit
```

### PR Mode (Release Branch)

```yaml
jobs:
  update-release:
    uses: folio-org/kitfox-github/.github/workflows/application-update-flow.yml@master
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
    secrets: inherit
```

### With GitHub App Authentication

```yaml
jobs:
  update-application:
    uses: folio-org/kitfox-github/.github/workflows/application-update-flow.yml@master
    with:
      app_name: ${{ github.event.repository.name }}
      repo: ${{ github.repository }}
      branch: 'snapshot'
      pre_release: 'only'
      workflow_run_number: ${{ github.run_number }}
      use_github_app: true
    secrets: inherit
```

### Dry Run Testing

```yaml
jobs:
  test-update:
    uses: folio-org/kitfox-github/.github/workflows/application-update-flow.yml@master
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

### Dual-Mode Operation
- **Direct Commit**: Commits directly to branch (snapshot workflow)
- **PR-Based**: Creates/updates PRs (release workflow)
- **Mode Detection**: Automatically adjusts behavior based on `need_pr`

### Comprehensive Validation
- **Interface Integrity**: Validates module interfaces via FAR
- **Dependency Integrity**: Validates all dependencies together
- **Platform Integration**: Uses platform descriptor for context
- **Error Reporting**: Detailed failure reasons

### Intelligent PR Management
- **PR Reuse**: Updates existing PRs instead of creating duplicates
- **Branch Management**: Creates update branches as needed
- **Reviewer Assignment**: Supports users and teams
- **Label Management**: Applies configured labels

### Rollback Capability
- **Cleanup on Failure**: Removes published descriptors if commit fails
- **Validation Gates**: Prevents invalid updates from being published
- **Dry-Run Safety**: No permanent changes in dry-run mode

## 🛡️ Error Handling

### Failure Scenarios

**Update Failure**:
- **Cause**: Module discovery or version checking fails
- **Response**: Workflow fails, no commits or PRs created
- **Recovery**: Check module registry connectivity

**Validation Failure**:
- **Cause**: Application descriptor validation fails
- **Response**: Workflow fails, descriptor not published
- **Recovery**: Review descriptor format and module compatibility

**Publishing Failure**:
- **Cause**: FAR API issues or descriptor problems
- **Response**: Workflow fails, no commits made
- **Recovery**: Check FAR API status and descriptor content

**Commit Failure**:
- **Cause**: Git conflicts or permission issues
- **Response**: Published descriptor is removed (cleanup)
- **Recovery**: Resolve conflicts manually or check permissions

**PR Management Failure**:
- **Cause**: GitHub API issues or reviewer problems
- **Response**: Error logged with specific failure details
- **Recovery**: Check GitHub API status and reviewer validity

### Graceful Degradation

- **Platform Descriptor**: Continues without platform validation if unavailable
- **Partial Updates**: Processes available module updates even if some fail
- **PR Reuse**: Handles existing PRs gracefully
- **Dry-Run Safety**: All destructive operations skipped in dry-run mode

## 📈 Performance Considerations

### Optimization Features

- **Conditional Execution**: Skips unnecessary steps when no updates found
- **Parallel Processing**: Independent validation steps run efficiently
- **Artifact Management**: Minimal artifact sizes and retention
- **API Efficiency**: Consolidated GitHub and FAR API calls

### Resource Management

- **Memory Efficiency**: Minimal state retention between jobs
- **Network Optimization**: Platform descriptor cached within job
- **Time Efficiency**: Smart job dependencies prevent unnecessary waiting
- **Cost Efficiency**: Only runs expensive operations when needed

## 🧪 Testing Strategy

### Dry Run Behavior

When `dry_run: true`:
- **Module Checking**: Executes normally
- **Version Updates**: Applied to state file
- **Artifact Generation**: Creates descriptors normally
- **Validation**: Performs all validation checks
- **Registry Upload**: **Skipped** (no actual publication)
- **Git Operations**: **Skipped** (no commits or pushes)
- **PR Management**: **Skipped** (no PRs created/updated)
- **Results**: Generated normally for pipeline testing

### Validation Checklist

- [ ] application-descriptor.json exists and is valid
- [ ] Maven pom.xml is present and readable (if applicable)
- [ ] FOLIO registry is accessible
- [ ] Docker/NPM registries are accessible
- [ ] FAR API is responsive
- [ ] Git operations have proper permissions
- [ ] GitHub App credentials configured (if using)

## 📚 Related Documentation

- **[Application Update](application-update.md)**: High-level orchestrator
- **[Generate Application Descriptor Action](../actions/generate-application-descriptor/README.md)**: Template-based descriptor generation and update
- **[Commit and Push Changes](commit-and-push-changes.md)**: Git operations workflow
- **[Validate Application Action](../actions/validate-application/README.md)**: Descriptor validation
- **[Fetch Platform Descriptor Action](../actions/fetch-platform-descriptor/README.md)**: Platform descriptor fetching
- **[Create PR Action](../actions/create-pr/README.md)**: PR creation
- **[Update PR Action](../actions/update-pr/README.md)**: PR updates

## 🔍 Troubleshooting

### Common Issues

**No Updates Found**:
```
Info: All modules are up to date
Behavior: Workflow completes successfully, no changes made
Solution: This is expected behavior when modules are current
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
Behavior: Workflow fails, no commit is made
Solution: Check the error message for specific module/interface issues
```

**Git Permission Denied**:
```
Error: Permission denied to repository
Solution: Verify GitHub App or token permissions
```

**PR Creation Failed**:
```
Error: Failed to create pull request
Solution: Check repository permissions and GitHub API status
```

---

**Last Updated**: November 2025
**Workflow Version**: 2.0 (Unified)
**Compatibility**: All FOLIO application repositories