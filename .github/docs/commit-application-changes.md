# Commit Application Changes Workflow

**Workflow**: `commit-application-changes.yml`  
**Purpose**: Git operations for committing and pushing application changes  
**Type**: Reusable workflow (`workflow_call`)

## 🎯 Overview

This workflow handles all Git operations for committing and pushing changes to application repositories. It supports branch creation, multiline commit messages, GitHub App authentication, and flexible branch management strategies.

## 📋 Workflow Interface

### Inputs

| Input            | Description                                          | Required | Type    | Default      |
|------------------|------------------------------------------------------|----------|---------|--------------|
| `app_name`       | Application name                                     | Yes      | string  | -            |
| `repo`           | Application repository name (org/repo format)        | Yes      | string  | -            |
| `branch`         | Target branch for changes                            | No       | string  | `'snapshot'` |
| `source_branch`  | Source branch to create new branch from              | No       | string  | `''`         |
| `commit_message` | Full commit message (supports multiline)             | Yes      | string  | -            |
| `dry_run`        | Perform dry run without making changes               | No       | boolean | `false`      |
| `use_github_app` | Use GitHub App for authentication                    | No       | boolean | `false`      |

### Outputs

| Output            | Description                        |
|-------------------|------------------------------------|
| `commit_sha`      | SHA of the created commit          |
| `branch_created`  | Whether a new branch was created   |
| `changes_made`    | Whether any changes were committed |

### Secrets

| Secret              | Description                          | Required     |
|---------------------|--------------------------------------|--------------|
| `EUREKA_CI_APP_ID`  | GitHub App ID (when use_github_app)  | Conditional  |
| `EUREKA_CI_APP_KEY` | GitHub App key (when use_github_app) | Conditional  |

## 🔄 Workflow Execution Flow

### 1. Authentication Setup
- **GitHub App Mode**: Generates app token when `use_github_app=true`
- **Standard Mode**: Uses default GitHub token
- Configures permissions for repository access

### 2. Repository Checkout
- Clones the target repository
- If `source_branch` provided: Checks out source branch
- If no source branch: Checks out target branch directly
- Fetches full history for branch operations

### 3. Download Updated Files
- Retrieves application update files from artifacts:
  - `application-descriptor.json`
  - `pom.xml`
- Places files in repository root

### 4. Git Configuration
- Sets up GitHub Actions bot identity:
  - Name: `github-actions[bot]`
  - Email: `41898282+github-actions[bot]@users.noreply.github.com`
- Configures Git for automated commits

### 5. Branch Management
- **If `source_branch` provided**:
  - Creates new branch from source
  - Switches to target branch
- **If no source branch**:
  - Works directly on target branch
- Handles existing branch scenarios gracefully

### 6. Commit Creation
- Stages all changes
- Creates commit with provided message
- Supports multiline messages via temporary file
- Validates changes exist before committing

### 7. Push Changes
- **If not dry-run**: Pushes changes to remote
- **If dry-run**: Skips push, reports what would be done
- Handles both new and existing branches
- Force-push protection for safety

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

## 📊 Usage Examples

### Basic Commit and Push
```yaml
- uses: ./.github/workflows/commit-application-changes.yml
  with:
    app_name: ${{ inputs.app_name }}
    repo: ${{ inputs.repo }}
    commit_message: 'Update application modules'
```

### Release Branch Creation
```yaml
- uses: ./.github/workflows/commit-application-changes.yml
  with:
    app_name: ${{ inputs.app_name }}
    repo: ${{ inputs.repo }}
    branch: ${{ inputs.new_release_branch }}
    source_branch: ${{ inputs.previous_release_branch }}
    commit_message: |
      Prepare ${{ inputs.app_name }} for release
      
      Previous release: ${{ inputs.previous_release_branch }}
      New release: ${{ inputs.new_release_branch }}
```

### Dry Run Testing
```yaml
- uses: ./.github/workflows/commit-application-changes.yml
  with:
    app_name: ${{ inputs.app_name }}
    repo: ${{ inputs.repo }}
    commit_message: 'Test update'
    dry_run: true  # No actual commit/push
```

### GitHub App Authentication
```yaml
- uses: ./.github/workflows/commit-application-changes.yml
  with:
    app_name: ${{ inputs.app_name }}
    repo: ${{ inputs.repo }}
    commit_message: 'Automated update'
    use_github_app: true  # Use app token
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

- **[update-application.md](update-application.md)**: Module update workflow
- **[Validate Application Action](../actions/validate-application/README.md)**: Application descriptor validation
- **[Publish Application Descriptor](../actions/publish-app-descriptor/README.md)**: Publish descriptors to FAR
- **[snapshot-update-flow.md](snapshot-update-flow.md)**: Orchestrator workflow
- **[Git Best Practices](https://docs.github.com/en/get-started/using-git)**: Git documentation

---

**Last Updated**: September 2025
**Workflow Version**: 1.0  
**Compatibility**: All FOLIO application repositories
