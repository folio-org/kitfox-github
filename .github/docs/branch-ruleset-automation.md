# Branch Ruleset Automation Workflow

**Workflow**: `branch-ruleset-automation.yml`
**Purpose**: Automatically configures branch protection rules and merge queue settings
**Type**: Reusable workflow (`workflow_dispatch`)

## Overview

This workflow automatically configures GitHub branch rulesets for release branches based on the repository's update configuration. It sets up:

1. Required status checks (eureka-ci / validate-application)
2. Merge queue configuration (SQUASH merge, ALLGREEN strategy)
3. PR approval requirements

The workflow is typically triggered when the update configuration file changes, ensuring branch protection stays synchronized with repository settings.

## Workflow Interface

### Inputs

| Input        | Description                                   | Required | Type   | Default |
|--------------|-----------------------------------------------|----------|--------|---------|
| `repo_owner` | Repository owner (organization or user)       | Yes      | string | -       |
| `repo_name`  | Repository name                               | Yes      | string | -       |
| `head_sha`   | Commit SHA that triggered the update          | No       | string | `''`    |

### Permissions

| Permission      | Level  | Purpose                           |
|-----------------|--------|-----------------------------------|
| `contents`      | read   | Read repository content           |

### Secrets

| Secret                      | Description                       | Required |
|-----------------------------|-----------------------------------|----------|
| `EUREKA_CI_APP_KEY`         | GitHub App private key            | Yes      |
| `EUREKA_CI_SLACK_BOT_TOKEN` | Slack bot token for notifications | Yes      |

### Variables

| Variable                       | Description                          | Required |
|--------------------------------|--------------------------------------|----------|
| `EUREKA_CI_APP_ID`             | GitHub App ID                        | Yes      |
| `SLACK_NOTIF_CHANNEL`          | Team Slack notification channel      | No       |
| `GENERAL_SLACK_NOTIF_CHANNEL`  | General Slack notification channel   | No       |

## Workflow Execution Flow

### 1. Update Branch Rulesets
**Job**: `update-rulesets`

Reads configuration and updates branch rulesets for each configured branch.

**Steps**:
1. Generate GitHub App Token
2. Get Update Configuration
3. Check Configuration - validates config exists, is enabled, and has branches
4. Update Branch Rulesets - uses `update-branch-rulesets` action

**Configuration Checks**:
- Configuration file must exist
- `enabled` must be `true`
- At least one branch must be configured

**Outputs**:
- `branches_updated`: List of branches where rulesets were created/updated
- `branches_skipped`: List of branches that were skipped
- `branches_failed`: List of branches where ruleset update failed

### 2. Send Notifications
**Job**: `notify`

Sends Slack notifications with ruleset update results.

**Message Format**:
```
*app-acquisitions branch ruleset update completed/failed #42*

Branches Updated: R1-2025 (created), R2-2025 (updated)
Config Change: <commit-link>
```

### 3. Workflow Summary
**Job**: `summarize`

Generates a comprehensive workflow summary showing:
1. Repository information
2. Ruleset configuration details
3. Results for each branch
4. Notification status

## Ruleset Configuration

Each configured branch (with `need_pr: true`) gets a ruleset with:

### Required Status Check

```yaml
context: eureka-ci / validate-application
integration_id: 1671958  # GitHub App ID
strict: false
```

### Merge Queue Settings

```yaml
check_response_timeout_minutes: 60
grouping_strategy: ALLGREEN
max_entries_to_build: 5
max_entries_to_merge: 5
merge_method: SQUASH
min_entries_to_merge: 1
min_entries_to_merge_wait_minutes: 5
```

### Bypass Actors

The Eureka CI GitHub App (ID: 1671958) is configured as a bypass actor with `always` mode, allowing the CI system to perform operations that would otherwise be blocked.

## Features

### Automatic Ruleset Creation

For each branch in `release_branches` with `need_pr: true`:
- Creates ruleset if it doesn't exist
- Updates existing ruleset if found

### Ruleset Naming Convention

Rulesets are named using the pattern `{branch}-eureka-ci`:
- `R1-2025-eureka-ci`
- `R2-2025-eureka-ci`

### Branch Existence Validation

Before creating/updating a ruleset, the workflow verifies the branch exists:
- Skips non-existent branches (logs as skipped)
- Continues with other branches

### Need PR Filtering

Only branches with `need_pr: true` get rulesets configured:
- Branches with `need_pr: false` are skipped
- Allows mixed strategies in single repository

## Usage Examples

### Triggered by GitHub App Webhook

This workflow can be triggered when update-config.yml changes:

**Push Events**:
```yaml
event_type: push
files_changed:
  - .github/update-config.yml
```

### Manual Trigger

```bash
gh workflow run branch-ruleset-automation.yml \
  -f repo_owner=folio-org \
  -f repo_name=app-acquisitions
```

### Configuration File Format

`.github/update-config.yml`:

```yaml
release_scan:
  enabled: true
  release_branches:
    - name: R1-2025
      need_pr: true
      update_branch: version-update/R1-2025
    - name: R2-2025
      need_pr: true
      update_branch: version-update/R2-2025
    - name: snapshot
      need_pr: false  # No ruleset created for this branch
```

## Error Handling

### Failure Scenarios

**Configuration Issues**:
- Config file not found - workflow skipped
- Scanning disabled - workflow skipped
- No branches configured - workflow skipped

**Branch Issues**:
- Branch doesn't exist - skipped (continues with others)
- API errors - recorded as failed

**Ruleset Errors**:
- Permission denied - recorded as failed
- API rate limits - recorded as failed

### Partial Success

The workflow supports partial success:
- Some branches may succeed while others fail
- Detailed report of each branch's status
- Notification includes failure details

## Troubleshooting

### Common Issues

**No Rulesets Created**:
1. Verify update-config.yml exists
2. Check `enabled: true` in config
3. Verify branches have `need_pr: true`
4. Confirm branches actually exist in repository

**Ruleset Update Failed**:
1. Check GitHub App has admin permissions
2. Verify repository allows rulesets
3. Review workflow logs for API errors

**Wrong Status Check**:
1. Verify check context matches workflow output
2. Check integration ID is correct

### Debug Commands

**View Existing Rulesets**:
```bash
gh api repos/folio-org/app-acquisitions/rulesets
```

**View Configuration**:
```bash
gh api repos/folio-org/app-acquisitions/contents/.github/update-config.yml \
  --jq '.content' | base64 -d
```

## Current Limitations

1. **Non-PR Branches**: Rulesets are only created for branches with `need_pr: true`. Support for non-PR branches is planned.

2. **Fixed Parameters**: Merge queue parameters (timeout, strategy, etc.) are currently hardcoded. Future versions will read these from config.

3. **Integration ID**: The GitHub App integration ID is hardcoded. This should be moved to a repository variable.

## Related Documentation

- **[PR Check](pr-check.md)**: Validation workflow that rulesets enforce
- **[Merge Queue Check](merge-queue-check.md)**: Merge queue validation
- **[Update Branch Rulesets Action](../actions/update-branch-rulesets/README.md)**: Ruleset update action

---

**Last Updated**: December 2025
**Workflow Version**: 1.0
**Compatibility**: Requires repository admin permissions
