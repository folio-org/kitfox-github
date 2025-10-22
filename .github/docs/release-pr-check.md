# Release PR Check Workflow

**Workflow**: `release-pr-check.yml`
**Purpose**: Automated validation of pull requests targeting release branches
**Type**: Reusable workflow (`workflow_dispatch`)

## 🎯 Overview

This workflow provides comprehensive automated validation for pull requests targeting configured release branches. It's designed to be triggered by a GitHub App webhook when PRs are opened or when check suites are requested. The workflow validates application descriptors, checks module interface integrity, verifies dependencies, and provides detailed feedback through GitHub Check Runs with interactive re-run capabilities.

## 📋 Workflow Interface

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

## 🔄 Workflow Execution Flow

### 1. Pre-Check Configuration
**Job**: `pre-check`

Validates the PR configuration and determines if validation should proceed.

**Steps**:
1. **Generate GitHub App Token**: Creates scoped token for repository access
2. **Get Pull Request Information**: Retrieves PR details (base/head branches, labels)
3. **Check Commit in PR**: Verifies the commit SHA exists in the PR
4. **Checkout Repository**: Checks out the repository at the head commit
5. **Get Release Configuration**: Reads `.github/release-config.yml` from the repository
6. **Validate Configuration**: Checks if validation should run based on:
   - Configuration file existence
   - Release scanning enabled
   - Target branch in configured release branches
   - Required PR labels (if configured)

**Outputs**:
- `validation_status`: `success`, `skipped`, or `failure`
- `validation_message`: Detailed message about the validation status
- `head_branch`: PR head branch name
- `base_branch`: PR base (target) branch name

**Skip Conditions**:
- Configuration file not found
- Release scanning disabled
- Target branch not in `release_branches`
- Missing required PR labels

### 2. Application Check
**Job**: `check`

Performs the actual validation of the application descriptor and dependencies.

**Steps**:

#### a. Generate GitHub App Token
Creates scoped token for repository and GitHub API access.

#### b. Checkout Repository
Checks out the repository at the specified commit SHA.

#### c. Create Check Run
Creates a GitHub Check Run named `eureka-ci/release-app-validation` with:
- Status: `in_progress`
- Initial summary indicating validation has started
- Link to the PR

#### d. Update Check Run - Generating Descriptor
Updates check run to indicate descriptor generation is in progress.

#### e. Generate Application Descriptor
Uses the `generate-application-descriptor` action to create the application descriptor from the repository's module information.

**Outputs**:
- `generated`: Whether generation succeeded
- `descriptor_file`: Path to generated descriptor
- `descriptor_file_name`: Name of descriptor file
- `artifact_name`: Name of uploaded artifact

#### f. Fetch Platform Descriptor
Attempts to fetch the platform descriptor from `platform-lsp` repository using the base branch name.

**HTTP Status Handling**:
- `200`: Platform descriptor found and downloaded
- `404`: Platform descriptor not found (expected for some branches) - validation continues without dependency checks
- Other: Real error (network issues, etc.) - fails the workflow

**Outputs**:
- `platform_found`: `true` if platform descriptor was fetched successfully
- `fetch_error`: `true` if there was a real error (not 404)

#### g. Upload Platform Descriptor
Uploads the platform descriptor as an artifact if it was found.

#### h. Update Check Run - Validating
Updates check run to indicate validation is in progress.

#### i. Validate Application
Uses the `validate-application` action to perform:
- **Module Interface Validation**: Validates all module interfaces against FAR API
- **Dependency Validation** (conditional): If platform descriptor was found, validates application dependencies across the platform

**Parameters**:
- `use_platform_descriptor`: Set based on whether platform descriptor was found
- `rely_on_FAR`: Set to `false` (uses local platform descriptor)

**Outputs**:
- `validation_passed`: `true` if all validations passed
- `failure_reason`: Detailed reason if validation failed

#### j. Finalize Check Run
Updates the check run with final status and detailed results.

**Conclusion States**:
- `failure`: If generation failed, fetch error occurred, or validation failed
- `success`: If all validations passed
- `neutral`: If checks couldn't complete (shouldn't normally happen)

**Re-run Button**:
Adds a "Re-run Validation" action button if:
- Platform descriptor fetch failed (for retry)
- Validation failed

**Output Format**:
```markdown
## Application Verification Results

**Branch:** `release-update/R2-2025`
**Commit:** `ee30528e060aa6f99e86ae2f1c54c3faecd65417`
**Pull Request:** [#97](link)

### Validation Status
- **Result:** success
- **Message:** Configuration validation passed

### Descriptor Generation
- **Generated:** true

### Application Verification
- **Passed:** true

### Workflow Run
- **Run ID:** 12345
- **Run Number:** 42
- **Run URL:** [link]
```

**Outputs**:
- `generated`: Whether descriptor was generated
- `descriptor_file`: Descriptor file path
- `descriptor_file_name`: Descriptor file name
- `validation_passed`: Whether validation passed
- `platform_found`: Whether platform descriptor was found
- `failure_reason`: Failure reason if applicable

### 3. Send Notifications
**Job**: `notify`

Sends Slack notifications to configured channels about the validation results.

**Conditions**:
- Only runs if pre-check validation status is `success`
- Always runs regardless of check job outcome (to report failures)

**Steps**:

#### a. Generate GitHub App Token
Creates token for accessing repository variables.

#### b. Get Repository Variables
Retrieves the `SLACK_NOTIF_CHANNEL` variable from the target repository.

#### c. Send to Team Channel
Sends notification to team-specific channel (if configured).

**Message Format**:
```
*app-acquisitions release update check passed #42*

Repository: folio-org/app-acquisitions
Release branch: R2-2025
Update branch: release-update/R2-2025
PR Number: #97
Commit: ee30528...
```

**Color Coding**:
- Green: Check passed and validation succeeded
- Red: Check failed or validation failed

#### d. Send to General Channel
Sends notification to organization-wide channel (if configured).

Uses the same message format as team channel.

**Outputs**:
- `team_channel`: Team channel that was notified

### 4. Workflow Summary
**Job**: `summarize`

Generates a comprehensive workflow summary in the GitHub Actions UI.

**Always Runs**: Regardless of previous job outcomes.

**Summary Sections**:
1. **Release PR Check Summary**: Repository, PR, and commit information
2. **Pre-Check Status**: Configuration validation results
3. **Application Check Status**: Descriptor generation and validation results
4. **Notification Status**: Slack notification delivery status

## 🔍 Features

### Intelligent Configuration Validation

The workflow respects repository-level configuration in `.github/release-config.yml`:

```yaml
release_scan:
  enabled: true
  release_branches:
    - R1-2025
    - R2-2025
  pr_labels:
    - release-update
```

**Benefits**:
- Repositories can opt-in/out of validation
- Validation only runs for configured release branches
- Can require specific PR labels before validation runs

### Platform Descriptor Handling

The workflow intelligently handles platform descriptor availability:

**404 (Not Found)**:
- Expected for some release branches
- Validation continues without dependency checks
- Warning logged but check doesn't fail

**Other Errors**:
- Network issues, API problems, etc.
- Check fails with retry option
- User can click "Re-run Validation" button

### Interactive Re-run Capability

The workflow adds a "Re-run Validation" action button via GitHub Check Runs API when:
- Platform descriptor fetch fails (temporary network issues)
- Validation fails (allows retry after fixes)

**How It Works**:
1. User clicks "Re-run Validation" button in the check run
2. GitHub sends `check_run.requested_action` webhook event
3. GitHub App webhook handler receives the event
4. Workflow is triggered again with same parameters
5. Validation runs fresh with current state

### Comprehensive Error Reporting

The workflow provides detailed error information at multiple levels:

**Check Run Output**:
- Clear title indicating failure type
- Detailed summary with actionable information
- Full breakdown of what succeeded and what failed

**Workflow Summary**:
- Visual indicators (✅❌⏭️) for each stage
- Detailed status for each job
- Links to relevant resources

**Slack Notifications**:
- Real-time alerts to team channels
- Failure reasons included in messages
- Links to PR and workflow run

### Proper Failure Blocking

The workflow correctly blocks PR merges when:
- Descriptor generation fails
- Platform descriptor fetch fails (real errors, not 404)
- Module interface validation fails
- Dependency validation fails

**Check Conclusion States**:
- `failure`: Blocks merge, indicates issues must be fixed
- `success`: Allows merge, all checks passed
- `neutral`: Not used (would not block merge)

## 📊 Usage Examples

### Triggered by GitHub App Webhook

This workflow is typically triggered by a GitHub App webhook handler when:

**Pull Request Events**:
```yaml
event_type: pull_request
actions: [opened, reopened]
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

The webhook handler invokes the workflow via `workflow_dispatch`:
```yaml
inputs:
  repo_owner: "folio-org"
  repo_name: "app-acquisitions"
  pr_number: "97"
  head_sha: "ee30528e060aa6f99e86ae2f1c54c3faecd65417"
```

### Manual Trigger (Testing)

For testing purposes, you can manually trigger the workflow:

```yaml
on:
  workflow_dispatch:
    inputs:
      repo_owner:
        description: 'Repository owner'
        required: true
      repo_name:
        description: 'Repository name'
        required: true
      pr_number:
        description: 'Pull request number'
        required: true
      head_sha:
        description: 'Head commit SHA'
        required: true
```

### Repository Configuration Example

`.github/release-config.yml` in target repository:

```yaml
# Enable release PR validation
release_scan:
  enabled: true

  # Only validate PRs targeting these branches
  release_branches:
    - R1-2025
    - R2-2025
    - R3-2025

  # Require these labels on PRs (optional)
  pr_labels:
    - release-update
    - automated
```

## 🛡️ Error Handling

### Failure Scenarios

**Pre-Check Failures**:
- **Cause**: PR not found, commit not in PR, configuration issues
- **Response**: Workflow skips validation, provides clear message
- **Recovery**: Verify PR exists and commit is part of it

**Configuration Validation Skips**:
- **Cause**: Scanning disabled, branch not configured, missing labels
- **Response**: Workflow exits early with skip status
- **Recovery**: Update configuration or add required labels

**Descriptor Generation Failure**:
- **Cause**: Invalid module dependencies, missing install.json
- **Response**: Check fails with clear error message
- **Recovery**: Fix module configuration in repository

**Platform Descriptor Fetch Failures**:
- **404 Not Found**: Warning logged, dependency validation skipped, check continues
- **Network/API Errors**: Check fails with retry button
- **Recovery**: Click "Re-run Validation" or investigate network issues

**Module Interface Validation Failure**:
- **Cause**: Invalid module interfaces, FAR API issues
- **Response**: Check fails with detailed error from FAR
- **Recovery**: Fix module interface definitions

**Dependency Validation Failure**:
- **Cause**: Missing dependencies, version conflicts
- **Response**: Check fails with dependency conflict details
- **Recovery**: Update dependencies or platform descriptor

### Graceful Degradation

**Platform Descriptor Not Found (404)**:
```
⚠️ Platform descriptor not found for branch R2-2025 (HTTP 404)
⚠️ Dependency validation will be skipped

✅ Application verification completed successfully
   (dependency validation skipped - platform descriptor not found)
```

**Validation proceeds without dependency checks but still validates**:
- Application descriptor structure
- Module interface integrity
- Required fields

## 🧪 Testing Strategy

### Test Scenarios

**Normal Flow - All Checks Pass**:
- PRs with valid descriptors
- Platform descriptor found
- All validations pass
- Check conclusion: `success`

**Platform Descriptor Not Found (404)**:
- PR targeting branch without platform descriptor
- Warning logged but check continues
- Dependency validation skipped
- Check conclusion: `success`

**Platform Fetch Failure (Network Error)**:
- Temporary network issues
- Check fails with retry button
- User can re-run validation
- Check conclusion: `failure`

**Validation Failure**:
- Invalid module interfaces
- Dependency conflicts
- Check fails with details
- Retry button available
- Check conclusion: `failure`

**Configuration Skips**:
- Scanning disabled
- Branch not in release_branches
- Missing required labels
- Check doesn't run, no status reported

**Re-run Button**:
- Click button in failed check
- Webhook triggers new run
- Validation runs fresh
- Check updates with new results

### Validation Checklist

- [ ] GitHub App configured with correct permissions
- [ ] Repository variables configured (app ID, FAR URL)
- [ ] Repository secrets configured (app key, Slack token)
- [ ] Release configuration file exists in target repo
- [ ] Release branches configured correctly
- [ ] PR labels configured (if required)
- [ ] Slack channels configured (if notifications desired)
- [ ] Webhook handler configured to trigger workflow
- [ ] Check run permissions enabled

## 📈 Performance Considerations

### Optimization Features

**Early Exit for Skips**:
- Pre-check validates configuration first
- Exits early if validation shouldn't run
- Saves compute resources

**Conditional Job Execution**:
- Check job only runs if pre-check succeeds
- Notification job only runs if needed
- Summary always runs for visibility

**Artifact Management**:
- Short retention (1 day) for descriptors
- Artifacts only uploaded if needed
- Minimal storage impact

**GitHub API Efficiency**:
- Scoped tokens for minimal permissions
- Single check run updated throughout
- Consolidated API calls

### Resource Management

**Check Run Updates**:
- Single check run created and updated
- Avoids creating multiple check runs
- Clean PR checks interface

**Token Scoping**:
- App tokens scoped to specific repository
- Minimal permission grants
- Security best practices

**Parallel Execution**:
- Independent steps within jobs run sequentially
- Jobs run in parallel where possible
- Optimal workflow execution time

## 🔄 Integration Patterns

### GitHub App Webhook Integration

The workflow is designed to be triggered by a GitHub App webhook handler. The webhook handler should:

1. **Listen for Events**:
   - `pull_request` (opened, reopened)
   - `check_suite` (requested, rerequested)
   - `check_run` (requested_action)

2. **Extract Information**:
   - Repository owner and name
   - PR number
   - Head commit SHA

3. **Trigger Workflow**:
   ```python
   workflow_trigger.trigger_workflow(
       owner='folio-org',
       repo='kitfox-github',
       workflow_file='release-pr-check.yml',
       ref='master',
       inputs={
           'repo_owner': repo_owner,
           'repo_name': repo_name,
           'pr_number': pr_number,
           'head_sha': head_sha
       }
   )
   ```

### Configuration File Integration

The workflow reads `.github/release-config.yml` from the target repository:

```yaml
# .github/release-config.yml
release_scan:
  enabled: true
  release_branches:
    - R1-2025
    - R2-2025
  pr_labels:
    - release-update
```

This allows each repository to control:
- Whether validation runs
- Which branches are validated
- Required PR labels

### Slack Notification Integration

Notifications are sent to two types of channels:

**Team Channel** (Repository Variable):
- Defined in target repository's `SLACK_NOTIF_CHANNEL` variable
- Team-specific notifications
- More detailed information

**General Channel** (Organization Variable):
- Defined in organization's `GENERAL_SLACK_NOTIF_CHANNEL` variable
- Organization-wide announcements
- High-level status

## 🔍 Troubleshooting

### Common Issues

**Check Run Not Created**:
1. Verify GitHub App has `checks:write` permission
2. Check workflow permissions
3. Review workflow logs for errors
4. Confirm app token generation succeeded

**Pre-Check Skips Validation**:
1. Check if release configuration file exists
2. Verify `enabled: true` in configuration
3. Confirm target branch in `release_branches`
4. Check PR has required labels (if configured)

**Platform Descriptor Always Fails**:
1. Verify platform-lsp repository exists
2. Check branch naming matches base branch
3. Confirm descriptor file exists in platform-lsp
4. Test URL manually: `https://raw.githubusercontent.com/folio-org/platform-lsp/{branch}/platform-descriptor.json`

**Re-run Button Doesn't Work**:
1. Verify webhook handler configured for `check_run.requested_action`
2. Check webhook delivery logs in GitHub App settings
3. Confirm Lambda/handler is processing events
4. Verify workflow is triggered via workflow_dispatch

**Notifications Not Sent**:
1. Check Slack bot token is valid
2. Verify channel configuration variables
3. Confirm bot has access to channels
4. Review notification job logs
5. Check `continue-on-error` isn't masking failures

### Debug Configuration

**Enable Detailed Logging**:
```yaml
env:
  ACTIONS_STEP_DEBUG: true
  ACTIONS_RUNNER_DEBUG: true
```

**Test Manually**:
```bash
# Trigger workflow manually for testing
gh workflow run release-pr-check.yml \
  -f repo_owner=folio-org \
  -f repo_name=app-acquisitions \
  -f pr_number=97 \
  -f head_sha=ee30528e060aa6f99e86ae2f1c54c3faecd65417
```

**Verify Configuration**:
```bash
# Check release configuration
gh api repos/folio-org/app-acquisitions/contents/.github/release-config.yml \
  --jq '.content' | base64 -d

# Check repository variables
gh api repos/folio-org/app-acquisitions/actions/variables/SLACK_NOTIF_CHANNEL
```

**Test Platform Descriptor Fetch**:
```bash
# Test platform descriptor availability
curl -I https://raw.githubusercontent.com/folio-org/platform-lsp/R2-2025/platform-descriptor.json
```

## 📚 Related Documentation

- **[Validate Application Action](../actions/validate-application/README.md)**: Core validation action
- **[Generate Application Descriptor Action](../actions/generate-application-descriptor/README.md)**: Descriptor generation
- **[Get PR Info Action](../actions/get-pr-info/README.md)**: PR information retrieval
- **[Is Commit in PR Action](../actions/is-commit-in-pr/README.md)**: Commit verification
- **[Get Update Config Action](../actions/get-update-config/README.md)**: Configuration loading

---

**Last Updated**: October 2025
**Workflow Version**: 1.0
**Compatibility**: GitHub App webhook integration required
