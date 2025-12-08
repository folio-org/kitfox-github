# Commit and Push Changes Workflow

**Workflow**: `commit-and-push-changes.yml`
**Purpose**: Generic Git operations for committing and pushing repository changes from artifacts
**Type**: Reusable workflow (`workflow_call`)

## 🎯 Overview

This is a generic, reusable workflow that handles Git operations for committing and pushing changes to any repository. It downloads files from a workflow artifact, commits them to a specified branch, and pushes to the remote repository. Perfect for automated update workflows, release preparation, or any scenario where changes need to be committed from CI/CD pipelines.

**Key Features**:
- Downloads changes from workflow artifacts
- Supports branch creation from source branches
- **File deletion support**: Clean up generated state files before commit
- Multiline commit message support
- GitHub App authentication for cross-repo operations
- Dry-run mode for testing
- Graceful handling of no-change scenarios

## 📋 Workflow Interface

### Inputs

| Input            | Description                                          | Required | Type    | Default      |
|------------------|------------------------------------------------------|----------|---------|--------------|
| `repo`           | Target repository (org/repo format)                  | Yes      | string  | -            |
| `branch`         | Target branch for changes                            | No       | string  | `'main'`     |
| `artifact_name`  | Name of artifact containing files to commit          | Yes      | string  | -            |
| `commit_message` | Full commit message (supports multiline)             | Yes      | string  | -            |
| `dry_run`        | Perform dry run without pushing changes              | No       | boolean | `false`      |
| `use_github_app` | Use GitHub App for authentication                    | No       | boolean | `false`      |
| `source_branch`  | Source branch to checkout from (for branch creation) | No       | string  | `''`         |
| `deleted_files`  | Files to delete before commit (multiline list)       | No       | string  | `''`         |

### Outputs

| Output            | Description                         |
|-------------------|-------------------------------------|
| `commit_sha`      | SHA of the created commit           |
| `branch_created`  | Whether a new branch was created    |
| `changes_made`    | Whether any changes were committed  |
| `failure_reason`  | Reason for failure if any           |

### Secrets

| Secret              | Description                          | Required     |
|---------------------|--------------------------------------|--------------|
| `EUREKA_CI_APP_ID`  | GitHub App ID (when use_github_app)  | Conditional  |
| `EUREKA_CI_APP_KEY` | GitHub App key (when use_github_app) | Conditional  |

## 🔄 Workflow Execution Flow

### 1. Extract Owner and Repository
- Parses `repo` input (org/repo format)
- Extracts owner and repository name for authentication

### 2. Authentication Setup
- **GitHub App Mode**: Generates app token when `use_github_app=true`
- **Standard Mode**: Uses default GitHub token
- Configures permissions for repository access

### 3. Repository Checkout
- Clones the target repository
- If `source_branch` provided: Checks out source branch
- If no source branch: Checks out target branch directly
- Fetches full history for branch operations

### 4. Download Artifact
- Retrieves files from specified artifact
- Downloads to repository root
- Supports any file types from the artifact

### 5. Delete Specified Files
- **Optional**: Runs only if `deleted_files` provided
- Deletes files line-by-line from multiline input
- Skips empty lines and trims whitespace
- Gracefully handles missing files (no error)
- Useful for cleaning up generated state files

### 6. Git Configuration
- Sets up bot identity based on authentication mode:
  - GitHub App: `eureka-ci[bot]`
  - Standard: `github-actions[bot]`
- Configures Git for automated commits

### 7. Branch Management
- **If `source_branch` provided**:
  - Creates new branch from source (if doesn't exist)
  - Switches to target branch
  - Sets `branch_created` output
- **If no source branch**:
  - Works directly on target branch
- Handles existing branch scenarios gracefully

### 8. Commit Creation
- Reviews and stages all changes
- Validates changes exist before committing
- Creates commit with provided message via temporary file
- Supports multiline messages with special characters
- Sets `commit_sha` and `changes_made` outputs

### 9. Push Changes
- **If not dry-run**: Pushes changes to remote with `-u` flag
- **If dry-run**: Skips push, local commit only
- Handles both new and existing branches
- Provides clear error messages on failure

## 🔀 Branch Management Strategies

### Creating New Branch
```yaml
# For release preparation
with:
  branch: 'R1-2025'           # Target branch to create
  source_branch: 'R2-2024'    # Source to branch from
  commit_message: |
    Prepare app for R1-2025 release
    
    Based on R2-2024 branch
    Setting placeholder versions
```

### Updating Existing Branch
```yaml
# For snapshot updates
with:
  branch: 'snapshot'          # Existing branch
  # No source_branch - work directly on snapshot
  commit_message: |
    Update application to version 1.2.3-SNAPSHOT.100
    
    Updated modules: 5
    Previous version: 1.2.2-SNAPSHOT.99
```

### Feature Branch Creation
```yaml
# For feature development
with:
  branch: 'feature/new-modules'
  source_branch: 'master'
  commit_message: 'Add new modules for feature X'
```

## 🗑️ File Deletion Patterns

### State File Cleanup
```yaml
# Remove CI-generated files
with:
  deleted_files: |
    application.lock.json
    application-descriptor.json
```

### Multiple File Types
```yaml
# Clean up various generated files
with:
  deleted_files: |
    *.lock.json
    build/artifacts/**
    temp-*.json
```

**Note**: Currently supports simple file paths. Glob patterns are not expanded but can be listed explicitly.

### Empty Lines and Whitespace
```yaml
# Whitespace is handled gracefully
with:
  deleted_files: |
    file1.json

    file2.json
    file3.json
```

**Behavior**:
- Empty lines are skipped
- Leading/trailing whitespace is trimmed
- Missing files don't cause errors
- Successful deletions are logged

## 📊 Usage Examples

### Basic Commit and Push
```yaml
- uses: ./.github/workflows/commit-and-push-changes.yml
  with:
    repo: folio-org/my-application
    artifact_name: update-files
    commit_message: 'Update application modules'
```

### Application Update with Artifact
```yaml
- uses: ./.github/workflows/commit-and-push-changes.yml
  with:
    repo: ${{ inputs.repo }}
    branch: snapshot
    artifact_name: ${{ needs.update-job.outputs.artifact_name }}
    commit_message: |
      Update application to version ${{ needs.update-job.outputs.new_version }}

      Updated modules: ${{ needs.update-job.outputs.updated_cnt }}
      Previous version: ${{ needs.update-job.outputs.previous_version }}
```

### Release Branch Creation
```yaml
- uses: ./.github/workflows/commit-and-push-changes.yml
  with:
    repo: folio-org/my-app
    branch: R1-2025
    source_branch: R2-2024
    artifact_name: release-prep-files
    commit_message: |
      Prepare for R1-2025 release

      Based on R2-2024 branch
      Setting placeholder versions
```

### Release Branch with File Deletion
```yaml
- uses: ./.github/workflows/commit-and-push-changes.yml
  with:
    repo: folio-org/my-app
    branch: R1-2025
    source_branch: R2-2024
    artifact_name: release-prep-files
    commit_message: |
      Prepare for R1-2025 release

      Module versions set to ^VERSION placeholder.
      State files deleted for CI regeneration.
    deleted_files: |
      application.lock.json
      application-descriptor.json
```

### Dry Run Testing
```yaml
- uses: ./.github/workflows/commit-and-push-changes.yml
  with:
    repo: ${{ inputs.repo }}
    artifact_name: test-changes
    commit_message: 'Test update'
    dry_run: true  # No actual push
```

### GitHub App Authentication
```yaml
- uses: ./.github/workflows/commit-and-push-changes.yml
  with:
    repo: folio-org/my-app
    artifact_name: automated-updates
    commit_message: 'Automated update'
    use_github_app: true  # Use app token for cross-repo access
  secrets: inherit
```

## 🔐 Authentication Modes

### Standard Token
- Uses `GITHUB_TOKEN` from workflow
- Limited to repository scope
- Suitable for single-repo operations

### GitHub App Token
- Enhanced permissions across repositories
- Required for cross-repo operations
- Enables bot identity for commits
- Better audit trail

## 📝 Commit Message Formatting

### Multiline Support
The workflow handles multiline messages properly:
```yaml
commit_message: |
  Update application to version 2.0.0
  
  Changes:
  - Updated 15 backend modules
  - Updated 8 UI modules
  - Fixed dependency conflicts
  
  Previous version: 1.9.5
  Build number: 12345
```

### Special Characters
- Handles quotes, backticks, and special characters
- Preserves formatting and line breaks
- No escaping needed in YAML

## 🚨 Error Handling

### Common Scenarios

**No changes to commit**:
- Detected when no files are staged
- Returns gracefully without error
- Sets `changes_made=false` output

**Branch already exists**:
- Switches to existing branch
- Continues with commit operation
- No error if branch exists

**Permission denied**:
- Clear error message
- Suggests checking token permissions
- Fails fast for quick debugging

**Push conflicts**:
- Reports conflict details
- Suggests pull/merge strategy
- Never force-pushes without explicit config

## 🧪 Dry Run Behavior

When `dry_run: true`:
- ✅ Downloads and stages files
- ✅ Creates commit locally
- ❌ Skips push to remote
- ✅ Reports what would be done
- ✅ Returns commit SHA (local)

## 📈 Performance Considerations

- **Shallow clone**: When possible for faster checkout
- **Artifact caching**: Reuses downloaded files
- **Minimal operations**: Only required Git commands
- **Efficient staging**: Stages all changes at once

## 🔧 Troubleshooting

### Authentication Issues
```
Error: Permission denied to repository
Solution: 
- Check token permissions
- Verify repository access
- Consider using GitHub App token
```

### Branch Creation Failures
```
Error: Branch already exists
Solution:
- Workflow handles gracefully
- Switches to existing branch
- Continues with commit
```

### No Changes Detected
```
Notice: No changes to commit
Solution:
- Normal when files unchanged
- Check update workflow outputs
- Verify artifact download
```

### Push Rejected
```
Error: Updates were rejected
Solution:
- Pull latest changes
- Resolve conflicts
- Retry workflow
```

## 📚 Related Documentation

- **[Application Update Flow](application-update-flow.md)**: Core flow implementation
- **[Validate Application Action](../actions/validate-application/README.md)**: Application descriptor validation
- **[Publish Application Descriptor](../actions/publish-app-descriptor/README.md)**: Publish descriptors to FAR
- **[snapshot-update-flow.md](snapshot-update-flow.md)**: Orchestrator workflow
- **[Git Best Practices](https://docs.github.com/en/get-started/using-git)**: Git documentation

---

**Last Updated**: October 2025 (Added deleted_files parameter - RANCHER-2572)
**Workflow Version**: 1.1
**Compatibility**: All FOLIO application repositories
