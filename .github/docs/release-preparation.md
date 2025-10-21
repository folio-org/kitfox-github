# Application Release Preparation Workflow

**Workflows**: `release-preparation.yml` (public) + `release-preparation-flow.yml` (core logic)
**Purpose**: Orchestrates release branch preparation for FOLIO applications
**Type**: Reusable workflows (`workflow_call`)

## 🎯 Overview

This workflow system orchestrates the preparation of FOLIO application repositories for release cycles using a **template-based approach**. It creates release branches with `^VERSION` placeholders in application templates, manages branch tracking configuration, and cleans up generated state files for CI regeneration.

**Key Concept**: Application templates are the source of truth. State files (like `application.lock.json`) are generated artifacts that should be recreated by CI, not committed.

## 🏗️ Architecture

The workflow system uses a **two-layer architecture** similar to snapshot updates:

### Layer 1: Public Workflow (`release-preparation.yml`)
```
prepare (calls flow) ──→ notify ──→ summarize
```

**Jobs**:
1. **`prepare`** - Calls `release-preparation-flow.yml` to execute core logic
2. **`notify`** - Sends Slack notifications (team and general channels)
3. **`summarize`** - Generates workflow summary with results

### Layer 2: Core Logic (`release-preparation-flow.yml`)
```
update-template ──────┐
                      ├──→ commit-release-branch ──→ commit-config ──→ upload_results
update-config ────────┘
```

**Jobs**:
1. **`update-template`** - Updates application.template.json and pom.xml with new version
2. **`update-config`** - Manages update-config.yml for branch tracking
3. **`commit-release-branch`** - Creates release branch with template changes
4. **`commit-config`** - Commits configuration to default branch
5. **`upload_results`** - Uploads result artifact for orchestrator collection

All commits use the reusable **`commit-and-push-changes.yml`** workflow for consistency.

**Why Two Layers?**
- **Separation of concerns**: Core logic vs notifications/summaries
- **Matrix compatibility**: Orchestrators can call `-flow.yml` directly in matrix
- **Artifact-based results**: Flow uploads results for orchestrator aggregation

## 📋 Workflow Interface

### Inputs

| Input                     | Description                                               | Required | Type    | Default   |
|---------------------------|-----------------------------------------------------------|----------|---------|-----------|
| `app_name`                | Application repository name (e.g., 'app-acquisitions')    | Yes      | string  | -         |
| `repo`                    | Application repository (org/repo format)                  | Yes      | string  | -         |
| `previous_release_branch` | Previous release branch (e.g., 'R1-2024')                 | Yes      | string  | -         |
| `new_release_branch`      | New release branch to create (e.g., 'R2-2025')            | Yes      | string  | -         |
| `use_snapshot_fallback`   | Use snapshot branch if previous branch not found          | No       | boolean | `false`   |
| `use_snapshot_version`    | Use snapshot version for new release                      | No       | boolean | `false`   |
| `need_pr`                 | Require PR for version updates on this branch             | No       | boolean | `true`    |
| `prerelease_mode`         | Module version constraints: `"false"`, `"true"`, `"only"` | No       | string  | `"false"` |
| `dry_run`                 | Perform dry run without making changes                    | No       | boolean | `false`   |

### Outputs

| Output                  | Description                                      |
|-------------------------|--------------------------------------------------|
| `preparation_result`    | Result of preparation (success/failure/skipped)  |
| `app_name`              | Application name (pass-through from input)       |
| `app_version`           | Determined application version for release       |
| `source_branch`         | Source branch used for release preparation       |
| `commit_sha`            | SHA of the commit on the new release branch      |
| `notification_outcome`  | Outcome of Slack notification (success/failure)  |

## 🔄 Workflow Execution Flow

### 1. Update Template Job

**Purpose**: Prepare application template and version information

**Steps**:
1. **Branch Verification**
   - Ensures new release branch doesn't already exist
   - Confirms previous release branch exists (or uses snapshot fallback)
   - Detects default branch using GitHub API: `gh api repos/{repo} --jq .default_branch`

2. **Version Determination**
   - Collects version from source branch (previous release or snapshot)
   - Calculates new release version (typically major version increment)
   - Handles snapshot version logic if enabled

3. **Template Update**
   - Updates `application.template.json`:
     - Preserves version field (typically Maven placeholder like `${project.version}`)
     - Sets all module versions to `^VERSION` placeholder with `preRelease: "false"`
     - Sets all UI module versions to `^VERSION` placeholder with `preRelease: "false"`
     - Sets all dependency versions to `^VERSION` placeholder with `preRelease: "false"`
   - Example: `{"version": "${project.version}", "modules": [{"version": "^VERSION", "preRelease": "false"}]}`
   - **Note**: `preRelease` is a string enum with possible values: `"false"`, `"true"`, or `"only"`

4. **POM Update** (if present)
   - Updates Maven pom.xml with new version
   - Skips gracefully if pom.xml doesn't exist

5. **Artifact Upload**
   - Uploads `application.template.json` and `pom.xml` as artifact
   - Artifact name: `{app_name}-release-files`

### 2. Update Config Job

**Purpose**: Manage update-config.yml for branch tracking

**Steps**:
1. **Checkout Default Branch**
   - Checks out the repository's default branch (not source branch)

2. **Config File Management**
   - **If exists**: Adds new release branch to branches list
   - **If missing**: Creates from template, then adds branch
   - Template source: `kitfox-github/.github/templates/update-config.yml.template`

3. **Duplicate Check**
   - Skips update if branch already in configuration

4. **Branch Configuration Generation**
   - Dynamically builds branch configuration using jq:
     - `enabled: true` - Always enabled for new release branches
     - `need_pr: <input>` - From `need_pr` input parameter (default: `true`)
     - `preRelease: <input>` - From `prerelease_mode` input parameter (default: `"false"`)
   - Example configuration:
     ```json
     {
       "R2-2025": {
         "enabled": true,
         "need_pr": true,
         "preRelease": "false"
       }
     }
     ```

5. **Artifact Upload**
   - Uploads modified `.github/update-config.yml` as artifact
   - Artifact name: `{app_name}-config-file`
   - Uses `include-hidden-files: true` to preserve `.github/` directory structure

### 3. Commit Release Branch Job

**Purpose**: Create release branch with template changes

**Workflow**: Calls `commit-and-push-changes.yml`

**Key Parameters**:
- Downloads `{app_name}-release-files` artifact
- Creates branch from `source_branch`
- **Deletes**: `application.lock.json` (regenerated by CI)
- Commits `application.template.json` and `pom.xml`
- Commit message mentions `^VERSION` placeholders

### 4. Commit Config Job

**Purpose**: Update configuration on default branch

**Workflow**: Calls `commit-and-push-changes.yml`

**Conditions**:
- Only runs if config was updated
- Only runs if release branch commit succeeded
- Skipped in dry-run mode

**Key Parameters**:
- Downloads `{app_name}-config-file` artifact
- Targets default branch
- Commits `update-config.yml`
- Adds new release branch to tracked branches

## 📝 Understanding ^VERSION Placeholder

### What is ^VERSION?

After release preparation, `application.template.json` contains `^VERSION` placeholders for all module, uiModule, and dependency versions with `preRelease: "false"`:

```json
{
  "version": "${project.version}",
  "dependencies": [
    {"name": "app-platform-complete", "version": "^VERSION", "preRelease": "false"}
  ],
  "modules": [
    {"name": "mod-inventory", "version": "^VERSION", "preRelease": "false"}
  ],
  "uiModules": [
    {"name": "ui-users", "version": "^VERSION", "preRelease": "false"}
  ]
}
```

**Note**: The `preRelease` field is a string enum, not a boolean. Possible values:
- `"false"` - Include only release versions (no snapshots or pre-releases)
- `"true"` - Include all versions including pre-releases and snapshots
- `"only"` - Include only pre-release/snapshot versions

### Developer Responsibility

**CRITICAL**: Developers must replace `^VERSION` with actual version constraints before the CI can generate valid descriptors.

### Version Constraint Examples

```json
// Caret range (allow minor and patch updates) - Release versions only
{"name": "mod-inventory", "version": "^2.0.0", "preRelease": "false"}

// Tilde range (allow patch updates only) - Release versions only
{"name": "mod-users", "version": "~1.5.0", "preRelease": "false"}

// Range constraints - Release versions only
{"name": "mod-orders", "version": ">1.0.0 <=2.5.0", "preRelease": "false"}

// Exact version (not recommended for most cases) - Release versions only
{"name": "mod-circulation", "version": "3.1.0", "preRelease": "false"}

// Include pre-release/snapshot versions (for snapshot branches)
{"name": "mod-finance", "version": "^2.0.0", "preRelease": "true"}

// Only pre-release/snapshot versions
{"name": "mod-data-export", "version": "^1.0.0", "preRelease": "only"}
```

### File Lifecycle

| File                         | Status              | Purpose                          |
|------------------------------|---------------------|----------------------------------|
| `application.template.json`  | ✅ Committed        | Source of truth with constraints |
| `application.lock.json`      | ❌ Deleted/Generated| CI-generated resolved versions   |
| `application-descriptor.json`| ❌ Deleted/Generated| CI-generated descriptor          |
| `update-config.yml`          | ✅ Committed        | Branch tracking configuration    |
| `pom.xml`                    | ✅ Committed        | Maven project version            |

**Key Point**: Only commit templates and configuration. Let CI generate state files.

## 🛡️ Security Considerations

### Authorization Boundary

**CRITICAL**: This workflow contains **NO** authorization logic. Authorization must be handled by the calling repository.

```yaml
# ✅ CORRECT: Authorization in calling repository
jobs:
  authorize:
    steps:
      - uses: folio-org/kitfox-github/.github/actions/validate-team-membership@main
        with:
          username: ${{ github.actor }}
  
  prepare:
    needs: authorize
    if: needs.authorize.outputs.authorized == 'true'
    uses: folio-org/kitfox-github/.github/workflows/release-preparation.yml@main
```

### Token Requirements

- **Standard GitHub Token**: Workflow uses `secrets.GITHUB_TOKEN`
- **Repository Access**: Requires write access to target repository
- **Branch Permissions**: Must respect branch protection rules

## 📊 Usage Examples

### Basic Usage

```yaml
jobs:
  prepare-release:
    uses: folio-org/kitfox-github/.github/workflows/release-preparation.yml@main
    with:
      app_name: 'app-acquisitions'
      repo: 'folio-org/app-acquisitions'
      previous_release_branch: 'R1-2024'
      new_release_branch: 'R2-2025'
```

### With Fallback Options

```yaml
jobs:
  prepare-release:
    uses: folio-org/kitfox-github/.github/workflows/release-preparation.yml@main
    with:
      app_name: 'app-acquisitions'
      repo: 'folio-org/app-acquisitions'
      previous_release_branch: 'R1-2024'
      new_release_branch: 'R2-2025'
      use_snapshot_fallback: true
      use_snapshot_version: true
```

### Dry Run Testing

```yaml
jobs:
  test-preparation:
    uses: folio-org/kitfox-github/.github/workflows/release-preparation.yml@main
    with:
      app_name: 'app-acquisitions'
      repo: 'folio-org/app-acquisitions'
      previous_release_branch: 'R1-2024'
      new_release_branch: 'R2-2025'
      dry_run: true
```

## 🧪 Testing Strategy

### Dry Run Behavior

When `dry_run: true`:
- **Branch Verification**: Executes normally
- **Version Extraction**: Processes actual version
- **File Updates**: Simulated (changes logged but not applied)
- **Git Operations**: Simulated (no actual commits or pushes)
- **Outputs**: Generated normally for testing pipeline integration

### Validation Checklist

#### Pre-Execution
- [ ] Source branch exists and is accessible
- [ ] Target branch does not already exist
- [ ] `application.template.json` exists in source branch
- [ ] Maven pom.xml is present (optional but recommended)
- [ ] Git operations have proper permissions
- [ ] Branch protection rules are respected

#### Post-Execution
- [ ] New release branch created with correct source
- [ ] `application.template.json` version field preserved (not overwritten)
- [ ] All module versions set to `^VERSION` with `preRelease: "false"`
- [ ] All uiModule versions set to `^VERSION` with `preRelease: "false"`
- [ ] All dependency versions set to `^VERSION` with `preRelease: "false"`
- [ ] `application.lock.json` deleted from release branch
- [ ] `update-config.yml` created/updated on default branch
- [ ] pom.xml updated with release version (if applicable)

## 🔍 Troubleshooting

### Common Issues

**Branch Already Exists**:
```
Error: New release branch 'R2-2025' already exists
Solution: Use different branch name or delete existing branch
```

**Missing Source Branch**:
```
Error: Previous release branch 'R1-2024' not found
Solution: Enable use_snapshot_fallback or verify branch name
```

**Missing Template File**:
```
Error: application.template.json not found
Solution: Ensure application.template.json exists in source branch
```

**Template Not Found**:
```
Error: Template not found at /tmp/kitfox-github/.github/templates/update-config.yml.template
Solution: Verify kitfox-github repository contains the template file
```

**Default Branch Detection Failed**:
```
Error: Could not determine default branch for repository
Solution: Verify repository exists and GitHub API is accessible
```

**Permission Denied**:
```
Error: Permission denied to repository
Solution: Verify token permissions and repository access
```

**Invalid POM**:
```
Error: Could not extract version from pom.xml
Solution: Verify Maven project structure and pom.xml validity (or remove pom.xml if not needed)
```

### Debug Information

The workflow provides comprehensive logging:
- Branch verification with default branch detection
- Version determination with calculation logic
- Template update operations with jq transformations
- Config file management (create vs update)
- File deletion operations
- Artifact upload/download status
- Git operation outcomes with commit hashes
- Grouped output for template and config content

## 🔄 Integration Patterns

### Two-Stage Orchestration

**CRITICAL**: Release preparation uses a two-stage approach to prevent difficult cleanup scenarios:

```yaml
check-applications:
  name: Check ${{ matrix.application }} Application
  strategy:
    matrix:
      application: ${{ fromJson(needs.setup.outputs.applications) }}
    fail-fast: false
    max-parallel: 5
  uses: folio-org/kitfox-github/.github/workflows/release-preparation-flow.yml@master
  with:
    app_name: ${{ matrix.application }}
    repo: folio-org/${{ matrix.application }}
    previous_release_branch: ${{ inputs.previous_release_branch }}
    new_release_branch: ${{ inputs.new_release_branch }}
    use_snapshot_fallback: ${{ inputs.use_snapshot_fallback }}
    use_snapshot_version: ${{ inputs.use_snapshot_version }}
    dry_run: true  # Always dry run for pre-check
  secrets: inherit

prepare-applications:
  name: Prepare ${{ matrix.application }} Application
  needs: [check-applications]
  if: needs.check-applications.result == 'success' && inputs.dry_run != true
  strategy:
    matrix:
      application: ${{ fromJson(needs.setup.outputs.applications) }}
    fail-fast: false
    max-parallel: 5
  uses: folio-org/kitfox-github/.github/workflows/release-preparation-flow.yml@master
  with:
    app_name: ${{ matrix.application }}
    repo: folio-org/${{ matrix.application }}
    previous_release_branch: ${{ inputs.previous_release_branch }}
    new_release_branch: ${{ inputs.new_release_branch }}
    use_snapshot_fallback: ${{ inputs.use_snapshot_fallback }}
    use_snapshot_version: ${{ inputs.use_snapshot_version }}
    dry_run: ${{ inputs.dry_run }}  # Actual dry_run value
  secrets: inherit
```

**Why Two Stages?**
- **Safety**: If validation fails in check stage, no branches are created
- **Cleanup**: Release branches are hard to clean up (multiple repos, config files)
- **Confidence**: Pre-check ensures all apps can be prepared before committing

### Result Aggregation

```yaml
collect-results:
  name: Collect Application Results
  needs: [prepare-applications]
  runs-on: ubuntu-latest
  if: always() && needs.prepare-applications.result != 'skipped'
  outputs:
    failed_apps: ${{ steps.gather-failures.outputs.failed_apps }}
    success_count: ${{ steps.gather-failures.outputs.success_count }}
    failure_count: ${{ steps.gather-failures.outputs.failure_count }}
  steps:
    - name: Download All Application Results
      uses: actions/download-artifact@v4
      with:
        pattern: "result-*"
        path: /tmp/all-results
        merge-multiple: true

    - name: Gather Application Results
      id: gather-failures
      run: |
        all=$(jq -s '.' /tmp/all-results/*.json)

        success_count=$(jq '[.[] | select(.status=="success")] | length' <<<"$all")
        failure_count=$(jq '[.[] | select(.status!="success")] | length' <<<"$all")
        failed_apps=$(jq -r '[.[] | select(.status!="success") | .application] | join(", ")' <<<"$all")

        echo "failed_apps=$failed_apps" >> "$GITHUB_OUTPUT"
        echo "success_count=$success_count" >> "$GITHUB_OUTPUT"
        echo "failure_count=$failure_count" >> "$GITHUB_OUTPUT"
```

## 🔧 Maintainer Notes

### Environment Variables

The workflow uses centralized environment variables for file names, making it easy to update naming conventions in a single location:

```yaml
env:
  APPLICATION_TEMPLATE_FILE: 'application.template.json'
  UPDATE_CONFIG_FILE: '.github/update-config.yml'
  UPDATE_CONFIG_TEMPLATE_PATH: '.github/templates/update-config.yml.template'
  APPLICATION_STATE_FILE: 'application.lock.json'
```

**Purpose**: Single source of truth for all file name references throughout the workflow.

**Usage in Workflow**:
- Bash scripts: `if [ ! -f "$APPLICATION_TEMPLATE_FILE" ]`
- Artifact paths: `path: ${{ env.APPLICATION_TEMPLATE_FILE }}`
- Multiline parameters: `deleted_files: | ${{ env.APPLICATION_STATE_FILE }}`

**Benefits**:
- Easy to update if file naming conventions change
- No duplication across multiple jobs and steps
- Workflow-level scope (available to all jobs automatically)
- Clear documentation of which files the workflow manages

**Changing File Names**: To change any file name, update the environment variable at the workflow level. All references will automatically use the new value.

## 📚 Related Documentation

- **[Release Preparation Flow](release-preparation-flow.md)**: Core logic workflow (called by this wrapper)
- **[App Notification Guide](app-notification.md)**: Slack notification patterns
- **[Distributed Orchestration](distributed-orchestration.md)**: Cross-repository coordination
- **[Commit and Push Changes](commit-and-push-changes.md)**: Reusable commit workflow
- **[Security Implementation](security-implementation.md)**: Authorization patterns
- **[FOLIO Release Process](https://folio-org.atlassian.net/wiki/spaces/FOLIJET/pages/886178625/Release+preparation)**: Official documentation

---

**Last Updated**: October 2025 (RANCHER-2572)
**Workflow Version**: 3.0 (Template-based approach)
**Compatibility**: All FOLIO application repositories with application.template.json
