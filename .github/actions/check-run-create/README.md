# Check Run Create Action

**Action**: `check-run-create`
**Purpose**: Creates a GitHub check run for non-update commits with unified messaging
**Type**: Composite action

## Overview

This action creates a GitHub check run for non-update commits (commits that don't modify `application.lock.json`). It provides immediate feedback based on protected file validation results:

- **No violations**: Creates a successful check run ("Non-Update Approved")
- **Violations found**: Creates a failed check run ("Protected File Violation")

This action is designed to work with the `check-protected-files` action output.

## Inputs

| Input            | Description                                  | Required  |
|------------------|----------------------------------------------|-----------|
| `repo_owner`     | Repository owner                             | Yes       |
| `repo_name`      | Repository name                              | Yes       |
| `head_sha`       | Commit SHA                                   | Yes       |
| `github_token`   | GitHub token with `checks:write` permission  | Yes       |
| `has_violations` | Whether protected file violations were found | Yes       |
| `violations`     | Violation messages (if any)                  | No        |
| `details_url`    | URL to workflow run                          | Yes       |

## Outputs

| Output        | Description          |
|---------------|----------------------|
| `check_run_id`| Created check run ID |

## Check Run States

### No Violations (`has_violations: 'false'`)

```yaml
name: eureka-ci / validate-application
status: completed
conclusion: success
title: Non-Update Approved
summary: This is not an update. Validation skipped, can proceed.
```

### Violations Found (`has_violations: 'true'`)

```yaml
name: eureka-ci / validate-application
status: completed
conclusion: failure
title: Protected File Violation
summary: |
  This commit modifies protected files:
  application.lock.json: lock file deletion not allowed
  application.template.json: template file deletion not allowed
```

## Usage

### Basic Usage

```yaml
- name: Create Check Run
  uses: folio-org/kitfox-github/.github/actions/check-run-create@master
  with:
    repo_owner: ${{ inputs.repo_owner }}
    repo_name: ${{ inputs.repo_name }}
    head_sha: ${{ inputs.head_sha }}
    github_token: ${{ steps.app-token.outputs.token }}
    has_violations: ${{ steps.check-protected.outputs.has_violations }}
    violations: ${{ steps.check-protected.outputs.violations }}
    details_url: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
```

### Combined with Protected Files Check

```yaml
- name: Check Protected Files
  id: check-protected
  uses: folio-org/kitfox-github/.github/actions/check-protected-files@master
  with:
    check_type: pr
    repo_owner: ${{ inputs.repo_owner }}
    repo_name: ${{ inputs.repo_name }}
    pr_number: ${{ inputs.pr_number }}
    github_token: ${{ steps.app-token.outputs.token }}

- name: Create Check Run
  uses: folio-org/kitfox-github/.github/actions/check-run-create@master
  with:
    repo_owner: ${{ inputs.repo_owner }}
    repo_name: ${{ inputs.repo_name }}
    head_sha: ${{ inputs.head_sha }}
    github_token: ${{ steps.app-token.outputs.token }}
    has_violations: ${{ steps.check-protected.outputs.has_violations }}
    violations: ${{ steps.check-protected.outputs.violations }}
    details_url: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
```

## Why This Action Exists

For non-update commits (commits that don't modify `application.lock.json`), running full application validation is unnecessary. This action provides:

1. **Fast feedback**: Immediate check run result without expensive validation
2. **Protected file enforcement**: Blocks commits that delete critical files
3. **Consistent UX**: Same `eureka-ci / validate-application` check name for all paths
4. **Clear messaging**: Distinct messages for non-update vs update commits

## Check Run Name

The check run is always named `eureka-ci / validate-application` to:
- Match the check required by branch rulesets
- Provide consistent status in GitHub UI
- Allow merge queue to proceed based on check result

## Prerequisites

- GitHub token must have `checks:write` permission
- Repository must allow external check runs
- Token must have access to target repository

## Related Documentation

- **[Check Protected Files Action](../check-protected-files/README.md)**: Provides violation data
- **[PR Check Workflow](../../docs/pr-check.md)**: Uses this action for non-update PRs
- **[Merge Queue Check Workflow](../../docs/merge-queue-check.md)**: Uses this action for non-update commits

---

**Last Updated**: December 2025
**Version**: 1.0
