# Merge Queue Check Workflow

**Workflow**: `merge-queue-check.yml`
**Purpose**: Validates commits in GitHub's merge queue before merging
**Type**: Reusable workflow (`workflow_dispatch`)

## Overview

This workflow validates commits that have entered GitHub's merge queue. It ensures that commits in the queue meet all requirements before being merged into release branches. The workflow supports two distinct validation paths:

1. **Update Commits**: Commits that modify `application.lock.json` undergo full application descriptor validation
2. **Non-Update Commits**: Other commits are checked only for protected file violations

The workflow integrates with GitHub Check Runs to provide merge queue status feedback.

## Workflow Interface

### Inputs

| Input         | Description                              | Required | Type   |
|---------------|------------------------------------------|----------|--------|
| `repo_owner`  | Repository owner (organization or user)  | Yes      | string |
| `repo_name`   | Repository name                          | Yes      | string |
| `head_sha`    | Head commit SHA to validate              | Yes      | string |
| `base_branch` | Target branch the commit will merge into | Yes      | string |

### Permissions

| Permission      | Level  | Purpose                           |
|-----------------|--------|-----------------------------------|
| `contents`      | read   | Read repository content           |
| `checks`        | write  | Create and update check runs      |
| `statuses`      | write  | Update commit statuses            |

### Secrets

| Secret                      | Description                       | Required |
|-----------------------------|-----------------------------------|----------|
| `EUREKA_CI_APP_KEY`         | GitHub App private key            | Yes      |
| `EUREKA_CI_SLACK_BOT_TOKEN` | Slack bot token for notifications | Yes      |

### Variables

| Variable                       | Description                          | Required |
|--------------------------------|--------------------------------------|----------|
| `EUREKA_CI_APP_ID`             | GitHub App ID                        | Yes      |
| `FAR_URL`                      | FOLIO Application Registry URL       | Yes      |
| `SLACK_NOTIF_CHANNEL`          | Team Slack notification channel      | No       |
| `GENERAL_SLACK_NOTIF_CHANNEL`  | General Slack notification channel   | No       |

## Workflow Execution Flow

### 1. Pre-Check Configuration
**Job**: `pre-check`

Validates the configuration and determines which validation path to use.

**Steps**:
1. Print Input Parameters
2. Generate GitHub App Token
3. Checkout Repository (with fetch-depth: 2 for diff comparison)
4. Get Update Configuration
5. Validate Configuration

**Validation Logic**:
- Skip if configuration file not found
- Skip if release scanning disabled
- Skip if target branch not in `release_branches`
- Skip if `need_pr=false` for the branch
- Determine if commit modifies `application.lock.json` (update vs non-update)

**Outputs**:
- `validation_status`: `success` or `skipped`
- `validation_message`: Detailed message about the validation status
- `is_update_commit`: Whether this commit modifies `application.lock.json`
- `base_branch`: Target branch

### 2. Non-Update Check
**Job**: `non-update-check`

Runs only for non-update commits. Validates that protected files are not deleted.

**Condition**: `validation_status == 'success' && is_update_commit == 'false'`

**Protected Files**:
- `application.lock.json` - deletion not allowed
- `application.template.json` - deletion not allowed

**Steps**:
1. Generate GitHub App Token
2. Checkout Repository (fetch-depth: 2)
3. Check Protected Files - uses `check-protected-files` action with `check_type: merge_queue`
4. Create Check Run - uses `check-run-create` action
5. Send Slack notifications if violations found

**Outputs**:
- `has_violations`: Whether protected file violations were found
- `violations`: Semicolon-separated violation messages

### 3. Update Commit Check
**Job**: `check`

Runs only for update commits. Performs full application descriptor validation.

**Condition**: `validation_status == 'success' && is_update_commit == 'true'`

**Steps**:
1. Generate GitHub App Token
2. Checkout Repository (fetch-depth: 2)
3. Check Commit - uses `check-commit` action with `check_type: merge_queue`

**Outputs**:
- `validation_passed`: Whether all validations passed
- `failure_reason`: Reason for failure if applicable

### 4. Send Notifications
**Job**: `notify`

Sends Slack notifications to configured channels about update commit validation results.

**Condition**: Runs for update commits regardless of check outcome

**Message Format**:
```
*app-acquisitions merge queue check passed/failed #42*

Target branch: R2-2025
Commit: ee30528...
```

### 5. Workflow Summary
**Job**: `summarize`

Generates a comprehensive workflow summary in the GitHub Actions UI.

**Summary Sections**:
1. Merge Queue Check Summary - repository, branch, and commit information
2. Pre-Check Status - configuration validation results
3. Application Check Status - validation results
4. Notification Status - Slack notification delivery status

## Features

### Update vs Non-Update Detection

The workflow determines commit type by checking if `application.lock.json` was modified:

```bash
git diff --name-only HEAD~1 HEAD | grep -q "application.lock.json"
```

- **Update Commit**: Modifies `application.lock.json` - full validation
- **Non-Update Commit**: Doesn't modify lock file - protected file check only

### Protected File Enforcement

For merge queue, uses `git diff` to detect protected file deletions:

```bash
git diff --name-status HEAD~1 HEAD
```

Files with status "D" (deleted) that match protected file names trigger violations.

### GitHub Check Run Integration

Creates `eureka-ci / validate-application` check run that:
- Blocks merge queue progression on failure
- Provides detailed validation results
- Includes re-run button for retries

## Usage Examples

### Triggered by GitHub App Webhook

This workflow is triggered when commits enter the merge queue:

**Merge Group Events**:
```yaml
event_type: merge_group
actions: [checks_requested]
```

### Configuration Requirements

The target repository must have `.github/update-config.yml`:

```yaml
release_scan:
  enabled: true
  release_branches:
    - name: R1-2025
      need_pr: true
      update_branch: version-update/R1-2025
```

## Error Handling

### Failure Scenarios

**Configuration Issues**:
- Configuration file missing - check skipped
- Branch not configured - check skipped
- `need_pr=false` for branch - check skipped

**Non-Update Commit Violations**:
- Protected file deletion detected
- Check run created with failure status
- Merge queue entry blocked

**Update Commit Validation Failures**:
- Descriptor not found
- Platform descriptor fetch failed
- Module interface validation failed
- Dependency validation failed

## Troubleshooting

### Common Issues

**Merge Queue Entry Blocked**:
1. Check the GitHub Check Run for failure details
2. Review workflow logs for specific error
3. Verify descriptor file exists and is valid

**Check Not Running**:
1. Verify webhook handler is configured for merge_group events
2. Check update-config.yml exists and is properly configured
3. Confirm branch has `need_pr: true` setting

**Protected File Violation**:
1. Review which files were deleted in the commit
2. Ensure `application.lock.json` and `application.template.json` are not deleted

### Debug Commands

**Test Workflow Manually**:
```bash
gh workflow run merge-queue-check.yml \
  -f repo_owner=folio-org \
  -f repo_name=app-acquisitions \
  -f head_sha=abc123 \
  -f base_branch=R1-2025
```

## Related Documentation

- **[PR Check](pr-check.md)**: Validation for pull requests
- **[Post-Merge Flow](post-merge-flow.md)**: Post-merge descriptor publishing
- **[Check Commit Action](../actions/check-commit/README.md)**: Full validation action
- **[Check Protected Files Action](../actions/check-protected-files/README.md)**: Protected file detection

---

**Last Updated**: December 2025
**Workflow Version**: 1.0
**Compatibility**: GitHub App webhook integration required, merge queue enabled
