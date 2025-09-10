# Application Release Preparation Workflow

**Workflow**: `release-preparation.yml`  
**Purpose**: Orchestrates release branch preparation for FOLIO applications  
**Type**: Reusable workflow (`workflow_call`)

## 🎯 Overview

This workflow orchestrates the preparation of FOLIO application repositories for release cycles. It coordinates the modular workflows to create release branches, set placeholder versions for team-managed modules, and update both application descriptors and pom.xml files.

## 🏗️ Refactored Architecture

The workflow leverages modular components for better reusability:

1. **`update-application.yml`** - Sets placeholder versions and updates pom.xml
2. **`commit-application-changes.yml`** - Creates branch and commits changes

This orchestrator coordinates these components for release preparation.

## 📋 Workflow Interface

### Inputs

| Input                     | Description                                            | Required  | Type    | Default |
|---------------------------|--------------------------------------------------------|-----------|---------|---------|
| `app_name`                | Application repository name (e.g., 'app-acquisitions') | Yes       | string  | -       |
| `previous_release_branch` | Previous release branch (e.g., 'R1-2024')              | Yes       | string  | -       |
| `new_release_branch`      | New release branch to create (e.g., 'R2-2025')         | Yes       | string  | -       |
| `use_snapshot_fallback`   | Use snapshot branch if previous branch not found       | No        | boolean | `false` |
| `use_snapshot_version`    | Use snapshot version for new release                   | No        | boolean | `false` |
| `dry_run`                 | Perform dry run without making changes                 | No        | boolean | `false` |

### Outputs

| Output          | Description                                |
|-----------------|--------------------------------------------|
| `app_name`      | Application name (pass-through)            |
| `app_version`   | Extracted application version from pom.xml |
| `source_branch` | Source branch used for release preparation |
| `target_branch` | Target release branch created              |

## 🔄 Workflow Execution Flow

### 1. Branch Verification
- **Check Target Branch**: Ensures new release branch doesn't already exist
- **Validate Source Branch**: Confirms previous release branch exists
- **Fallback Logic**: Uses snapshot branch if previous release branch missing (when enabled)
- **Determine Source**: Selects appropriate source branch for release preparation

### 2. Update Application (`update-application.yml`)
- **Mode**: Always runs in `release` mode
- **Version Setting**: Uses major version increment from source branch
- **Placeholder Modules**: Sets all module versions to `<CHANGE_ME>`
- **POM Update**: Updates pom.xml with new release version
- **Artifact Generation**: Creates updated state files

### 3. Commit and Create Branch (`commit-application-changes.yml`)
- **Branch Creation**: Creates new release branch from source
- **File Download**: Retrieves updated state files from artifacts
- **Commit Creation**: Commits with detailed release preparation message
- **Push Changes**: Pushes new branch to remote (unless dry-run)

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

- [ ] Source branch exists and is accessible
- [ ] Target branch does not already exist
- [ ] Maven pom.xml is present and readable
- [ ] Application descriptor template exists
- [ ] Git operations have proper permissions
- [ ] Branch protection rules are respected

## 🔍 Troubleshooting

### Common Issues

**Branch Already Exists**:
```
Error: Branch 'R2-2025' already exists
Solution: Use different branch name or delete existing branch
```

**Missing Source Branch**:
```
Error: Previous release branch 'R1-2024' not found
Solution: Use snapshot fallback or verify branch name
```

**Permission Denied**:
```
Error: Permission denied to repository
Solution: Verify token permissions and repository access
```

**Invalid POM**:
```
Error: Could not extract version from pom.xml
Solution: Verify Maven project structure and pom.xml validity
```

### Debug Information

The workflow provides comprehensive logging:
- Branch existence checks with detailed results
- Version extraction with validation
- File operation results and changes
- Git operation outcomes with commit hashes

## 🔄 Integration Patterns

### Matrix Processing

```yaml
strategy:
  matrix:
    application: ${{ fromJson(needs.setup.outputs.applications) }}
  fail-fast: false
  max-parallel: 5

steps:
  - name: 'Prepare Application Release'
    uses: folio-org/kitfox-github/.github/actions/orchestrate-external-workflow@main
    with:
      repository: 'folio-org/${{ matrix.application }}'
      workflow_file: 'release-preparation.yml'
      workflow_parameters: |
        previous_release_branch: ${{ inputs.previous_release_branch }}
        new_release_branch: ${{ inputs.new_release_branch }}
        dry_run: ${{ inputs.dry_run }}
```

### Result Aggregation

```yaml
collect-results:
  needs: [prepare-applications]
  if: always()
  steps:
    - name: 'Download Results'
      uses: actions/download-artifact@v4
      with:
        pattern: 'result-*'
        merge-multiple: true
    
    - name: 'Aggregate Results'
      run: |
        success_count=$(jq -s 'map(select(.success)) | length' result-*.json)
        echo "Successfully prepared: $success_count applications"
```

## 📚 Related Documentation

- **[App Notification Guide](app-notification.md)**: Slack notification patterns
- **[Distributed Orchestration](distributed-orchestration.md)**: Cross-repository coordination
- **[Security Implementation](security-implementation.md)**: Authorization patterns
- **[FOLIO Release Process](https://folio-org.atlassian.net/wiki/spaces/FOLIJET/pages/886178625/Release+preparation)**: Official documentation

---

**Last Updated**: September 2025  
**Workflow Version**: 2.5
**Compatibility**: All FOLIO application repositories
