# Update Branch Rulesets Action

**Action**: `update-branch-rulesets`
**Purpose**: Creates or updates branch rulesets with merge queue and required status checks
**Type**: Composite action

## Overview

This action configures GitHub branch rulesets for release branches. For each configured branch (with `need_pr: true`), it sets up:

1. Required status checks (eureka-ci / validate-application)
2. Merge queue configuration
3. Bypass actors for CI systems

## Inputs

| Input                  | Description                                            | Required | Default                              |
|------------------------|--------------------------------------------------------|----------|--------------------------------------|
| `repository`           | Repository in `owner/repo` format                      | Yes      | -                                    |
| `branches`             | JSON array of branch names to configure                | Yes      | -                                    |
| `ruleset_pattern`      | Pattern for ruleset names (`{0}` = branch placeholder) | No       | `{0}-eureka-ci`                      |
| `required_check`       | Required status check context name                     | No       | `eureka-ci / validate-application`   |
| `check_integration_id` | Integration ID for the status check (GitHub App ID)    | No       | `1671958`                            |
| `branch_config`        | JSON array of branch configs with `need_pr` flag       | No       | `[]`                                 |
| `github_token`         | GitHub token with admin permissions                    | Yes      | -                                    |

## Outputs

| Output             | Description                                    |
|--------------------|------------------------------------------------|
| `branches_updated` | Comma-separated list of branches updated       |
| `branches_skipped` | Comma-separated list of branches skipped       |
| `branches_failed`  | Comma-separated list of branches that failed   |

## Ruleset Configuration

Each ruleset created includes:

### Required Status Checks Rule

```yaml
type: required_status_checks
parameters:
  required_status_checks:
    - context: eureka-ci / validate-application
      integration_id: 1671958
  strict_required_status_checks_policy: false
```

### Merge Queue Rule (when `need_pr: true`)

```yaml
type: merge_queue
parameters:
  check_response_timeout_minutes: 60
  grouping_strategy: ALLGREEN
  max_entries_to_build: 5
  max_entries_to_merge: 5
  merge_method: SQUASH
  min_entries_to_merge: 1
  min_entries_to_merge_wait_minutes: 5
```

### Bypass Actors

```yaml
bypass_actors:
  - actor_id: 1671958
    actor_type: Integration
    bypass_mode: always
```

The Eureka CI GitHub App is configured as a bypass actor, allowing CI operations that would otherwise be blocked.

## Usage

### Basic Usage

```yaml
- name: Update Branch Rulesets
  uses: folio-org/kitfox-github/.github/actions/update-branch-rulesets@master
  with:
    repository: folio-org/app-acquisitions
    branches: '["R1-2025", "R2-2025"]'
    github_token: ${{ steps.app-token.outputs.token }}
```

### With Branch Configuration

```yaml
- name: Update Branch Rulesets
  uses: folio-org/kitfox-github/.github/actions/update-branch-rulesets@master
  with:
    repository: ${{ inputs.repo_owner }}/${{ inputs.repo_name }}
    branches: ${{ steps.get-config.outputs.branches }}
    branch_config: ${{ steps.get-config.outputs.branch_config }}
    github_token: ${{ steps.app-token.outputs.token }}
```

### Custom Ruleset Pattern

```yaml
- name: Update Branch Rulesets
  uses: folio-org/kitfox-github/.github/actions/update-branch-rulesets@master
  with:
    repository: folio-org/app-acquisitions
    branches: '["R1-2025"]'
    ruleset_pattern: 'eureka-ci-{0}'  # Results in "eureka-ci-R1-2025"
    github_token: ${{ steps.app-token.outputs.token }}
```

## Branch Processing Logic

For each branch in the `branches` array:

1. **Check branch existence**: Skip if branch doesn't exist (404)
2. **Check branch config**: Skip if `need_pr != true`
3. **Find existing ruleset**: Search by ruleset name
4. **Create or update**: Create new ruleset or update existing one

### Output Examples

```yaml
branches_updated: "R1-2025 (created), R2-2025 (updated)"
branches_skipped: "snapshot (no PR required), hotfix (not found)"
branches_failed: "R3-2025: permission denied"
```

## Prerequisites

### GitHub Token Permissions

The token must have admin permissions on the repository:
- Create/update repository rulesets
- Read repository branches

### GitHub App Permissions

If using a GitHub App token, the app must have:
- `administration: write` permission
- Access to the target repository

## Current Limitations

1. **Non-PR Branches**: Rulesets are only created for branches with `need_pr: true`. Branches with `need_pr: false` are skipped.

2. **Fixed Parameters**: Merge queue parameters (timeout, strategy, etc.) are hardcoded. Future versions will read these from configuration.

3. **Integration ID**: The bypass actor integration ID is hardcoded to `1671958`.

## Error Handling

The action continues processing even if some branches fail:
- Failed branches are recorded in `branches_failed` output
- Action fails at the end if any branches failed
- Detailed error messages included in output

## Related Documentation

- **[Branch Ruleset Automation Workflow](../../docs/branch-ruleset-automation.md)**: Uses this action
- **[PR Check Workflow](../../docs/pr-check.md)**: Check that rulesets enforce
- **[Merge Queue Check Workflow](../../docs/merge-queue-check.md)**: Merge queue validation

---

**Last Updated**: December 2025
**Version**: 1.0
