# PR Check Workflow

**Workflow**: `pr-check.yml`
**Purpose**: Automated validation of pull requests targeting release branches
**Type**: Reusable workflow (`workflow_dispatch`)

## Overview

This workflow provides comprehensive automated validation for pull requests targeting configured release branches. It's designed to be triggered by a GitHub App webhook when PRs are opened or when check suites are requested.

The workflow validates application descriptors, checks module interface integrity, verifies dependencies, enforces protected file policies, and provides detailed feedback through GitHub Check Runs. For commits without an application descriptor, the check run completes with a "Non-Update Approved" success status.

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

**Outputs**:
- `validation_status`: `success`, `skipped`, or `failure`
- `validation_message`: Detailed message about the validation status
- `head_branch`: PR head branch name
- `base_branch`: PR base (target) branch name

### 2. PR Check
**Job**: `check`

Performs application validation using the `check-commit` action.

**Condition**: `validation_status == 'success'`

**Steps**:
1. Generate GitHub App Token
2. Checkout Repository
3. Check Commit - uses `check-commit` action which:
   - Creates GitHub Check Run
   - Checks protected files
   - Validates descriptor existence (non-update commits get "Non-Update Approved" success)
   - Fetches platform descriptor
   - Validates application via `validate-application` action (respects `skip_interface_validation` and `skip_dependency_validation` from branch config)
   - Finalizes check run with results

**Outputs**:
- `validation_passed`: Whether all validations passed
- `failure_reason`: Reason for failure if applicable
- `dependency_validation_bypassed`: Whether dependency validation failure was bypassed
- `bypass_warning`: Warning message with error details when bypassed

### 3. Send Notifications
**Job**: `notify`

Sends Slack notifications to configured channels about validation results.

**Condition**: Runs when pre-check passes, regardless of check outcome

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

### 4. Workflow Summary
**Job**: `summarize`

Generates a comprehensive workflow summary in the GitHub Actions UI.

**Always Runs**: Regardless of previous job outcomes.

**Summary Sections**:
1. PR Check Summary - repository, PR, and commit information
2. Pre-Check Status - configuration validation results
3. Application Check Status - descriptor generation and validation results
4. Notification Status - Slack notification delivery status

## Features

### Unified Validation Path

All PRs go through the same `check-commit` action which handles both scenarios:

- **Update PRs** (descriptor present): Full application descriptor validation, module interface integrity checks, dependency validation against platform descriptor
- **Non-update PRs** (no descriptor): Check run completes with "Non-Update Approved" success status
- **Protected file violations**: Detected for all PRs regardless of descriptor presence

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

The workflow adds a "Re-run Validation" action button in failed check runs:
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

**Protected File Violations**:
- Protected file deletion detected
- Check run created with failure status

**Validation Failures**:
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

---

**Last Updated**: December 2025
**Workflow Version**: 2.0
**Compatibility**: GitHub App webhook integration required
