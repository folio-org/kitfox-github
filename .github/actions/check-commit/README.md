# Check Commit Action

**Action**: `check-commit`
**Purpose**: Comprehensive validation action for application commit validation with check run management
**Type**: Composite action

## Overview

This action orchestrates the complete application commit validation process. It creates and manages GitHub check runs, validates application descriptors, checks protected files, fetches platform descriptors, and executes application validation.

The action supports two contexts:
- **PR context**: Validation for pull request commits
- **Merge queue context**: Validation for commits in GitHub's merge queue

## Inputs

| Input              | Description                                      | Required  | Default  |
|--------------------|--------------------------------------------------|-----------|----------|
| `repo_owner`       | Repository owner                                 | Yes       | -        |
| `repo_name`        | Repository name                                  | Yes       | -        |
| `head_sha`         | Commit SHA to validate                           | Yes       | -        |
| `base_branch`      | Target branch for platform descriptor            | Yes       | -        |
| `github_token`     | GitHub token with `checks:write` permission      | Yes       | -        |
| `check_type`       | Check type for messaging (`pr` or `merge_queue`) | No        | `pr`     |
| `pr_number`        | PR number (for PR context messaging)             | No        | `''`     |
| `head_branch`      | Head branch name (for PR context messaging)      | No        | `''`     |
| `far_url`          | FAR API URL base                                 | Yes       | -        |
| `workflow_run_url` | URL to the workflow run for details link         | Yes       | -        |

## Outputs

| Output                      | Description                                    |
|-----------------------------|------------------------------------------------|
| `validation_passed`         | Whether validation passed (`true`/`false`)     |
| `failure_reason`            | Reason for failure                             |
| `check_run_id`              | Created check run ID                           |
| `descriptor_exists`         | Whether descriptor file exists (`true`/`false`)|
| `platform_found`            | Whether platform descriptor was found          |
| `protected_file_violation`  | Whether protected files were violated          |

## Execution Flow

### 1. Create Check Run

Creates a GitHub check run named `eureka-ci / validate-application`:
- Status: `in_progress`
- Links to PR (for PR context) or workflow run (for merge queue)

### 2. Check Existing Descriptor

Validates that `application.lock.json` exists:
- If missing, check run fails with "Descriptor Not Found"
- Subsequent steps are skipped

### 3. Check Protected Files

Validates that protected files are not deleted:
- **PR context**: Uses GitHub API to check file status
- **Merge queue context**: Uses `git diff HEAD~1 HEAD`

Protected violation if `application.template.json` is deleted.

### 4. Fetch Platform Descriptor

Fetches `platform-descriptor.json` from `platform-lsp` repository:
- Uses base branch to find matching platform descriptor
- **HTTP 200**: Platform found, dependency validation enabled
- **HTTP 404**: Platform not found, dependency validation skipped
- **Other errors**: Check fails with "Platform Descriptor Fetch Failed"

### 5. Update Check Run - Validating

Updates check run status to indicate validation in progress.

### 6. Validate Application

Uses the `validate-application` action:
- Module interface validation via FAR API
- Dependency validation if platform descriptor found
- Sets `rely_on_FAR: false`

### 7. Finalize Check Run

Updates check run with final results:

**Conclusion States**:
- `success`: All validations passed
- `failure`: Descriptor missing, fetch error, protected violation, or validation failed
- `neutral`: Checks couldn't complete (rare)

**Output Includes**:
- Context information (PR or merge queue)
- Descriptor status
- Verification results
- Workflow run link
- Re-run button on failure

## Usage

### In PR Check Workflow

```yaml
- name: Check Commit
  uses: folio-org/kitfox-github/.github/actions/check-commit@master
  with:
    repo_owner: ${{ inputs.repo_owner }}
    repo_name: ${{ inputs.repo_name }}
    head_sha: ${{ inputs.head_sha }}
    base_branch: ${{ needs.pre-check.outputs.base_branch }}
    github_token: ${{ steps.app-token.outputs.token }}
    check_type: pr
    pr_number: ${{ inputs.pr_number }}
    head_branch: ${{ needs.pre-check.outputs.head_branch }}
    far_url: ${{ vars.FAR_URL }}
    workflow_run_url: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
```

### In Merge Queue Check Workflow

```yaml
- name: Check Commit
  uses: folio-org/kitfox-github/.github/actions/check-commit@master
  with:
    repo_owner: ${{ inputs.repo_owner }}
    repo_name: ${{ inputs.repo_name }}
    head_sha: ${{ inputs.head_sha }}
    base_branch: ${{ inputs.base_branch }}
    github_token: ${{ steps.app-token.outputs.token }}
    check_type: merge_queue
    far_url: ${{ vars.FAR_URL }}
    workflow_run_url: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
```

## Check Run Output Format

The finalized check run includes detailed markdown:

```markdown
## Application Verification Results

**Pull Request:** [#97](link)
**Branch:** `version-update/R1-2025`
**Commit:** `abc123def`

### Descriptor Status
- **Found:** true

### Application Verification
- **Passed:** true

### Workflow Run
- **URL:** <workflow-link>
```

## Error Scenarios

### Descriptor Not Found

```
Title: Descriptor Not Found
Summary: Application descriptor file not found: application.lock.json
Conclusion: failure
```

### Platform Fetch Failed

```
Title: Platform Descriptor Fetch Failed
Summary: Failed to fetch platform descriptor from branch R1-2025. This might be a temporary issue. Please retry.
Conclusion: failure
```

### Protected File Violation

```
Title: Protected File Violation
Summary: application.template.json: template file deletion not allowed
Conclusion: failure
```

### Validation Failed

```
Title: Verification Failed
Summary: <detailed failure reason from validate-application>
Conclusion: failure
```

## Related Documentation

- **[PR Check Workflow](../../docs/pr-check.md)**: Uses this action
- **[Merge Queue Check Workflow](../../docs/merge-queue-check.md)**: Uses this action
- **[Validate Application Action](../validate-application/README.md)**: Validation logic

---

**Last Updated**: December 2025
**Version**: 1.0
