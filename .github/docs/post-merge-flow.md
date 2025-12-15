# Post-Merge Flow Workflow

**Workflow**: `post-merge-flow.yml`
**Purpose**: Executes after PR merge to publish descriptor to FAR and cleanup update branch
**Type**: Reusable workflow (`workflow_dispatch`)

## Overview

This workflow handles post-merge operations for update PRs. When a PR from the configured update branch is merged into a release branch, this workflow:

1. Publishes the merged application descriptor to FOLIO Application Registry (FAR)
2. Deletes the update branch to keep the repository clean

The workflow validates that the merge was successful and that the PR originated from the correct update branch before proceeding.

## Workflow Interface

### Inputs

| Input         | Description                                      | Required | Type   | Default   |
|---------------|--------------------------------------------------|----------|--------|-----------|
| `repo_owner`  | Repository owner (organization or user)          | Yes      | string | -         |
| `repo_name`   | Repository name                                  | Yes      | string | -         |
| `pr_number`   | Pull request number                              | Yes      | string | -         |
| `head_sha`    | Head commit SHA that was merged                  | Yes      | string | -         |
| `base_branch` | Base branch the PR was merged into               | No       | string | `''`      |
| `merged`      | Whether the PR was merged (true/false)           | No       | string | `'false'` |

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
| `FAR_URL`                      | FOLIO Application Registry URL       | Yes      |
| `SLACK_NOTIF_CHANNEL`          | Team Slack notification channel      | No       |
| `GENERAL_SLACK_NOTIF_CHANNEL`  | General Slack notification channel   | No       |

## Workflow Execution Flow

### 1. Pre-Check Merge Status
**Job**: `pre-check`

Validates merge status and configuration before proceeding.

**Steps**:
1. Check Merge Status - verify PR was actually merged
2. Generate GitHub App Token
3. Get Pull Request Information
4. Get Update Configuration
5. Validate Configuration

**Validation Logic**:
- Skip if PR was closed without merging (`merged != 'true'`)
- Skip if configuration file not found
- Skip if release scanning disabled
- Skip if target branch not in `release_branches`
- Skip if `need_pr=false` for the branch
- Skip if PR head branch doesn't match configured `update_branch`

**Outputs**:
- `should_process`: Whether to proceed with post-merge operations
- `skip_reason`: Reason for skipping if applicable
- `base_branch`: Target branch the PR was merged into
- `head_branch`: PR head branch (update branch)
- `update_branch`: Configured update branch name

### 2. Publish to FAR
**Job**: `publish`

Publishes the merged application descriptor to FOLIO Application Registry.

**Condition**: `should_process == 'true'`

**Steps**:
1. Generate GitHub App Token
2. Checkout Repository at base branch (post-merge state)
3. Check Existing Descriptor - verify `application.lock.json` exists
4. Get Descriptor ID - extract ID from descriptor file
5. Publish Application Descriptor to FAR - uses `publish-app-descriptor` action

**Outputs**:
- `publish_status`: `success` or `failure`
- `descriptor_url`: URL to published descriptor in FAR
- `descriptor_id`: Application descriptor ID
- `descriptor_exists`: Whether descriptor file was found
- `failure_reason`: Reason for failure if applicable

### 3. Cleanup Update Branch
**Job**: `cleanup-branch`

Deletes the merged update branch.

**Condition**: Runs after publish regardless of outcome (if `should_process == 'true'`)

**Steps**:
1. Generate GitHub App Token
2. Delete Update Branch via GitHub API

**Outputs**:
- `branch_deleted`: `true`, `false`, or `skipped`
- `failure_reason`: Reason if deletion failed

### 4. Send Notifications
**Job**: `notify`

Sends Slack notifications with post-merge results.

**Condition**: Runs if `should_process == 'true'`

**Message Format**:
```
*app-acquisitions post-merge completed/failed #42*

Release branch: R2-2025
PR Number: #97
Descriptor ID: app-acquisitions-2.0.5
Commit: ee30528...
Branch Cleanup: Deleted
Descriptor URL: <link>
```

**Color Coding**:
- Green: Publish succeeded and branch cleanup succeeded
- Red: Any operation failed

### 5. Workflow Summary
**Job**: `summarize`

Generates a comprehensive workflow summary in the GitHub Actions UI.

**Summary Sections**:
1. Descriptor Publish Summary - repository, PR, commit, merge status
2. Pre-Check Status - configuration validation results
3. Publication Status - descriptor and FAR publishing results
4. Notification Status - Slack notification delivery status

## Features

### Automatic Branch Cleanup

After successful merge, the update branch is automatically deleted:
- Keeps repository clean
- Prevents stale branches from accumulating
- Handles cleanup failures gracefully

### FAR Publishing

Publishes the merged descriptor to FOLIO Application Registry:
- Extracts descriptor ID from `application.lock.json`
- Uses `publish-app-descriptor` action
- Provides direct link to published descriptor

### Merge Validation

Ensures only properly merged PRs trigger post-merge operations:
- Checks `merged` input parameter
- Validates PR was from configured update branch
- Skips if PR was closed without merging

## Usage Examples

### Triggered by GitHub App Webhook

This workflow is triggered when PRs are closed:

**Pull Request Events**:
```yaml
event_type: pull_request
actions: [closed]
```

The webhook handler passes the `merged` status from the event payload.

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

**Pre-Check Skips**:
- PR not merged - workflow exits early
- Configuration issues - workflow skipped with reason
- Wrong source branch - workflow skipped

**Publish Failures**:
- Descriptor file not found
- FAR API errors
- Network issues

**Cleanup Failures**:
- Branch already deleted
- Permission issues
- API errors

### Graceful Degradation

- Branch cleanup runs even if publishing fails
- Notifications sent regardless of operation outcomes
- Each failure includes detailed reason

## Troubleshooting

### Common Issues

**Descriptor Not Published**:
1. Verify `application.lock.json` exists on target branch
2. Check FAR_URL variable is configured
3. Review publish job logs for API errors

**Branch Not Deleted**:
1. Check if branch was already deleted
2. Verify GitHub App has delete permissions
3. Review cleanup job logs

**Workflow Skipped**:
1. Verify PR was actually merged (not just closed)
2. Check head branch matches configured `update_branch`
3. Verify update-config.yml exists and is valid

### Debug Commands

**Test Workflow Manually**:
```bash
gh workflow run post-merge-flow.yml \
  -f repo_owner=folio-org \
  -f repo_name=app-acquisitions \
  -f pr_number=97 \
  -f head_sha=abc123 \
  -f base_branch=R1-2025 \
  -f merged=true
```

**Check Descriptor**:
```bash
gh api repos/folio-org/app-acquisitions/contents/application.lock.json \
  --jq '.content' | base64 -d | jq '.id'
```

## Related Documentation

- **[PR Check](pr-check.md)**: Validation for pull requests
- **[Merge Queue Check](merge-queue-check.md)**: Validation for merge queue commits
- **[Publish App Descriptor Action](../actions/publish-app-descriptor/README.md)**: FAR publishing

---

**Last Updated**: December 2025
**Workflow Version**: 1.0
**Compatibility**: GitHub App webhook integration required
