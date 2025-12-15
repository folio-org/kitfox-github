# PR Check Workflow

**Workflow**: `pr-check.yml`
**Purpose**: Automated validation of pull requests targeting release branches
**Type**: Reusable workflow (`workflow_dispatch`)

## Overview

This workflow provides comprehensive automated validation for pull requests targeting configured release branches. It's designed to be triggered by a GitHub App webhook when PRs are opened or when check suites are requested. The workflow supports two distinct validation paths:

1. **Update PRs**: PRs from the configured update branch undergo full application descriptor validation
2. **Non-Update PRs**: Other PRs are checked only for protected file violations

The workflow validates application descriptors, checks module interface integrity, verifies dependencies, enforces protected file policies, and provides detailed feedback through GitHub Check Runs.

## Workflow Interface

### Inputs

| Input        | Description                                    | Required | Type   |
|--------------|------------------------------------------------|----------|--------|
| `repo_owner` | Repository owner (organization or user)        | Yes      | string |
| `repo_name`  | Repository name                                | Yes      | string |
| `pr_number`  | Pull request number to validate                | Yes      | string |
| `head_sha`   | Head commit SHA that triggered the check suite | Yes      | string |

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

Validates the PR configuration and determines if validation should proceed, and which validation path to use.

**Steps**:
1. Generate GitHub App Token
2. Get Pull Request Information (base/head branches, labels)
3. Check Commit in PR - verifies the commit SHA exists in the PR
4. Checkout Repository
5. Get Update Configuration - reads `.github/update-config.yml`
6. Validate Configuration

**Validation Logic**:
- Skip if configuration file not found
- Skip if release scanning disabled
- Skip if target branch not in `release_branches`
- Skip if `need_pr=false` for the branch
- Determine if PR is from update branch (update PR) or other branch (non-update PR)
- Check for required PR labels (if configured)

**Outputs**:
- `validation_status`: `success`, `skipped`, or `failure`
- `validation_message`: Detailed message about the validation status
- `is_update_pr`: Whether this is an update PR (from configured update branch)
- `head_branch`: PR head branch name
- `base_branch`: PR base (target) branch name

### 2. Non-Update PR Check
**Job**: `non-update-check`

Runs only for non-update PRs. Validates that protected files are not deleted.

**Condition**: `validation_status == 'success' && is_update_pr == 'false'`

**Protected Files**:
- `application.lock.json` - deletion not allowed
- `application.template.json` - deletion not allowed

**Steps**:
1. Generate GitHub App Token
2. Check Protected Files - uses `check-protected-files` action
3. Create Check Run - uses `check-run-create` action
4. Send Slack notifications if violations found

**Outputs**:
- `has_violations`: Whether protected file violations were found
- `violations`: Semicolon-separated violation messages

### 3. Update PR Check
**Job**: `check`

Runs only for update PRs. Performs full application descriptor validation.

**Condition**: `validation_status == 'success' && is_update_pr == 'true'`

**Steps**:
1. Generate GitHub App Token
2. Checkout Repository
3. Check Commit - uses `check-commit` action which:
   - Creates GitHub Check Run
   - Validates descriptor existence
   - Checks protected files
   - Fetches platform descriptor
   - Validates application via `validate-application` action
   - Finalizes check run with results

**Outputs**:
- `validation_passed`: Whether all validations passed
- `failure_reason`: Reason for failure if applicable

### 4. Send Notifications
**Job**: `notify`

Sends Slack notifications to configured channels about update PR validation results.

**Condition**: Runs for update PRs regardless of check outcome

**Message Format**:
```
*app-acquisitions release update check passed/failed #42*

Repository: folio-org/app-acquisitions
Release branch: R2-2025
Update branch: release-update/R2-2025
PR Number: #97
Commit: ee30528...
```

**Color Coding**:
- Green: Check passed and validation succeeded
- Red: Check failed or validation failed

### 5. Workflow Summary
**Job**: `summarize`

Generates a comprehensive workflow summary in the GitHub Actions UI.

**Always Runs**: Regardless of previous job outcomes.

**Summary Sections**:
1. PR Check Summary - repository, PR, and commit information
2. Pre-Check Status - configuration validation results
3. Application Check Status - descriptor generation and validation results
4. Notification Status - Slack notification delivery status

## Features

### Dual Validation Paths

The workflow intelligently routes PRs through different validation paths:

**Update PRs** (from configured update branch):
- Full application descriptor validation
- Module interface integrity checks
- Dependency validation against platform descriptor
- GitHub Check Run with detailed results

**Non-Update PRs** (from other branches):
- Protected file deletion detection
- Quick validation without expensive checks
- Immediate check run result

### Protected File Enforcement

Prevents deletion of critical application files:
- `application.lock.json` - tracks deployed module versions
- `application.template.json` - application configuration template

### Configuration-Driven Behavior

Respects repository-level configuration in `.github/update-config.yml`:

```yaml
release_scan:
  enabled: true
  release_branches:
    - name: R1-2025
      need_pr: true
      update_branch: version-update/R1-2025
  pr_labels:
    - release-update
```

### Interactive Re-run Capability

For update PRs, the workflow adds a "Re-run Validation" action button in failed check runs:
1. User clicks "Re-run Validation" button
2. GitHub sends `check_run.requested_action` webhook event
3. GitHub App webhook handler receives the event
4. Workflow is triggered again with same parameters

## Usage Examples

### Triggered by GitHub App Webhook

This workflow is typically triggered by a GitHub App webhook handler:

**Pull Request Events**:
```yaml
event_type: pull_request
actions: [opened, reopened, synchronize]
```

**Check Suite Events**:
```yaml
event_type: check_suite
actions: [requested, rerequested]
```

**Check Run Events** (Re-run button):
```yaml
event_type: check_run
actions: [requested_action]
```

### Repository Configuration Example

`.github/update-config.yml` in target repository:

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
  pr_labels:
    - release-update
```

## Error Handling

### Failure Scenarios

**Pre-Check Failures**:
- PR not found or commit not in PR
- Configuration file missing
- Target branch not configured
- Missing required PR labels

**Non-Update PR Violations**:
- Protected file deletion detected
- Check run created with failure status
- Slack notification sent

**Update PR Validation Failures**:
- Descriptor not found
- Platform descriptor fetch failed
- Module interface validation failed
- Dependency validation failed

### Graceful Degradation

**Platform Descriptor Not Found (404)**:
- Warning logged but check continues
- Dependency validation skipped
- Module interface validation still performed

## Troubleshooting

### Common Issues

**Check Run Not Created**:
1. Verify GitHub App has `checks:write` permission
2. Check workflow permissions
3. Review workflow logs for errors

**Pre-Check Skips Validation**:
1. Check if update-config.yml exists
2. Verify `enabled: true` in configuration
3. Confirm target branch in `release_branches`
4. Verify `need_pr: true` for the branch
5. Check PR has required labels (if configured)

**Non-Update PR Blocked**:
1. Review which protected files were modified
2. Ensure PR doesn't delete `application.lock.json` or `application.template.json`

**Re-run Button Doesn't Work**:
1. Verify webhook handler configured for `check_run.requested_action`
2. Check webhook delivery logs in GitHub App settings
3. Confirm Lambda/handler is processing events

### Debug Configuration

**Test Manually**:
```bash
gh workflow run pr-check.yml \
  -f repo_owner=folio-org \
  -f repo_name=app-acquisitions \
  -f pr_number=97 \
  -f head_sha=ee30528e060aa6f99e86ae2f1c54c3faecd65417
```

**Verify Configuration**:
```bash
gh api repos/folio-org/app-acquisitions/contents/.github/update-config.yml \
  --jq '.content' | base64 -d
```

## Related Documentation

- **[Merge Queue Check](merge-queue-check.md)**: Validation for merge queue commits
- **[Post-Merge Flow](post-merge-flow.md)**: Post-merge descriptor publishing
- **[Check Commit Action](../actions/check-commit/README.md)**: Full validation action
- **[Check Protected Files Action](../actions/check-protected-files/README.md)**: Protected file detection
- **[Check Run Create Action](../actions/check-run-create/README.md)**: Check run creation

---

**Last Updated**: December 2025
**Workflow Version**: 2.0
**Compatibility**: GitHub App webhook integration required
