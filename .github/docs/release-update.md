# Release Update Workflow

**Workflow**: `release-update.yml`
**Purpose**: Orchestrates automated module updates for release branches with integrated notifications
**Type**: Reusable workflow (`workflow_call`)

## 🎯 Overview

This workflow provides a comprehensive solution for maintaining FOLIO release branches by automatically scanning for module updates, creating or updating pull requests, and sending notifications to relevant teams. It serves as the main entry point for release branch maintenance, orchestrating the complete flow from module discovery to team notification. The workflow is designed to handle both successful updates and failure scenarios with appropriate messaging.

## 📋 Workflow Interface

### Inputs

| Input            | Description                           | Required | Type    | Default |
|------------------|---------------------------------------|----------|---------|---------|
| `release_branch` | Release branch to scan                | Yes      | string  | -       |
| `update_branch`  | Update branch name for this release   | Yes      | string  | -       |
| `dry_run`        | Perform dry run without creating PRs  | No       | boolean | `false` |
| `pr_reviewers`   | Comma-separated list of reviewers     | No       | string  | `''`    |
| `pr_labels`      | Comma-separated list of labels        | No       | string  | `''`    |

### Outputs

| Output            | Description                                   |
|-------------------|-----------------------------------------------|
| `scan_result`     | Result of the scan (success/failure/skipped)  |
| `updated`         | Whether updates were found                    |
| `pr_created`      | Whether a PR was created                      |
| `pr_url`          | URL of the created PR                         |
| `workflow_status` | Overall workflow status                       |
| `failure_reason`  | Reason for workflow failure if any            |

### Permissions

| Permission        | Level  | Purpose                    |
|-------------------|--------|----------------------------|
| `contents`        | write  | Repository content access  |
| `pull-requests`   | write  | PR creation and management |
| `issues`          | write  | Issue and PR interaction   |

### Secrets

| Secret                      | Description                       | Required  |
|-----------------------------|-----------------------------------|-----------|
| `EUREKA_CI_SLACK_BOT_TOKEN` | Slack bot token for notifications | Yes       |

## 🔄 Workflow Execution Flow

### 1. Release Branch Scanning
- **Workflow Delegation**: Calls `release-update-flow.yml` for main processing
- **Parameter Passing**: Forwards all input parameters to the flow workflow
- **Repository Context**: Provides application name and repository information
- **Secret Inheritance**: Passes all secrets to the child workflow

### 2. Notification Management (Conditional)
- **Trigger Conditions**: Runs when updates are found and not in dry-run mode
- **Multi-Channel Support**: Sends notifications to both team and general channels
- **Status-Based Messaging**: Different message formats for success vs failure
- **Rich Content**: Includes detailed update information and links

### 3. Workflow Summary Generation
- **Always Executes**: Runs regardless of previous job outcomes
- **Comprehensive Reporting**: Generates detailed markdown summaries
- **GitHub Integration**: Uses GitHub step summary for visibility
- **Progress Tracking**: Shows notification status and outcomes

## 📧 Notification System

### Channel Configuration

**Team Channel** (`SLACK_NOTIF_CHANNEL` variable):
- **Purpose**: Team-specific notifications
- **Content**: Detailed technical information
- **Audience**: Development team members

**General Channel** (`GENERAL_SLACK_NOTIF_CHANNEL` variable):
- **Purpose**: Organization-wide announcements
- **Content**: High-level status information
- **Audience**: Broader stakeholder group

### Message Format

**Success Notifications**:
```
*{app_name} {release_branch} release updated #{run_number}*

Release Branch: [R1-2025](link)
New Version: 1.2.3-SNAPSHOT.456
Updated: 5 modules
Pull Request: [#123](pr_link)

Updated Modules:
mod-users: 18.0.1 → 18.0.2
mod-orders: 12.0.5 → 12.0.6
...

Reviewers: user1, user2
```

**Failure Notifications**:
```
*{app_name} {release_branch} release failed #{run_number}*

Release Branch: [R1-2025](link)
Failure Reason: Failed to update application modules
```

## 📊 Usage Examples

### Basic Release Update

```yaml
jobs:
  update-release:
    uses: folio-org/kitfox-github/.github/workflows/release-update.yml@master
    with:
      release_branch: 'R1-2025'
      update_branch: 'R1-2025-update'
    secrets: inherit
```

### Scheduled Release Maintenance

```yaml
on:
  schedule:
    - cron: '0 8 * * MON-FRI'  # Weekday mornings

jobs:
  maintain-releases:
    strategy:
      matrix:
        branch:
          - { release: 'R1-2025', update: 'R1-2025-update' }
          - { release: 'R2-2025', update: 'R2-2025-update' }
    uses: folio-org/kitfox-github/.github/workflows/release-update.yml@master
    with:
      release_branch: ${{ matrix.branch.release }}
      update_branch: ${{ matrix.branch.update }}
      pr_reviewers: 'team-lead,senior-dev'
      pr_labels: 'release-update,automated'
    secrets: inherit
```

### Dry Run Testing

```yaml
jobs:
  test-release-update:
    uses: folio-org/kitfox-github/.github/workflows/release-update.yml@master
    with:
      release_branch: 'R1-2025'
      update_branch: 'R1-2025-test-update'
      dry_run: true
      pr_reviewers: 'test-team'
    secrets: inherit
```

### Multi-Branch Release Management

```yaml
jobs:
  get-release-branches:
    runs-on: ubuntu-latest
    outputs:
      branches: ${{ steps.get-branches.outputs.branches }}
    steps:
      - uses: actions/checkout@v4
      - name: Get release branches
        id: get-branches
        run: |
          branches=$(git branch -r | grep -E 'origin/R[0-9]+-[0-9]+$' | sed 's/origin\///' | jq -R -s -c 'split("\n")[:-1]')
          echo "branches=$branches" >> "$GITHUB_OUTPUT"

  update-all-releases:
    needs: get-release-branches
    strategy:
      matrix:
        branch: ${{ fromJson(needs.get-release-branches.outputs.branches) }}
    uses: folio-org/kitfox-github/.github/workflows/release-update.yml@master
    with:
      release_branch: ${{ matrix.branch }}
      update_branch: '${{ matrix.branch }}-update'
      pr_reviewers: 'release-team'
      pr_labels: 'automated,release-maintenance'
    secrets: inherit
```

## 🔍 Features

### Comprehensive Orchestration
- **Flow Management**: Coordinates complex multi-step release update process
- **Error Handling**: Graceful handling of failures at each stage
- **Status Tracking**: Detailed outcome reporting for each component
- **Dependency Management**: Proper job dependency configuration

### Intelligent Notification System
- **Conditional Execution**: Only notifies when updates are found
- **Multi-Channel Support**: Configurable team and general channels
- **Rich Content**: Detailed module update information
- **Status Awareness**: Different messages for success and failure scenarios

### Professional Reporting
- **GitHub Summaries**: Rich markdown summaries in workflow UI
- **Progress Indicators**: Visual status indicators for each component
- **Comprehensive Details**: Module lists, PR links, reviewer information
- **Troubleshooting Info**: Failure reasons and diagnostic information

### Flexible Configuration
- **Reviewer Management**: Support for both users and teams
- **Label Assignment**: Configurable PR labels
- **Branch Naming**: Flexible branch naming conventions
- **Dry Run Support**: Testing without side effects

## 🛡️ Error Handling

### Failure Scenarios

**Scan Failure**:
- **Cause**: Module discovery or version checking fails
- **Response**: Error notification with failure reason
- **Recovery**: Manual investigation of module registry connectivity

**PR Management Failure**:
- **Cause**: GitHub API issues or permission problems
- **Response**: Notification includes failure context
- **Recovery**: Check repository permissions and GitHub API status

**Notification Failure**:
- **Cause**: Slack API issues or channel configuration problems
- **Response**: Workflow continues, notification status recorded
- **Recovery**: Verify Slack bot configuration and channel access

### Debug Configuration

```yaml
jobs:
  debug-release-update:
    uses: folio-org/kitfox-github/.github/workflows/release-update.yml@master
    with:
      release_branch: 'R1-2025'
      update_branch: 'R1-2025-debug'
      dry_run: true  # Safe debugging
    secrets: inherit
```

## 🧪 Testing Strategy

### Test Scenarios

**No Updates Available**:
- Expected: No PR created, no notifications sent
- Validation: Check workflow summary shows "No updates needed"

**Updates Available**:
- Expected: PR created/updated, success notifications sent
- Validation: Verify PR content and notification delivery

**Dry Run Mode**:
- Expected: Updates detected but no PR created
- Validation: Check that scan completes but no side effects occur

**Failure Handling**:
- Expected: Appropriate error notifications
- Validation: Verify failure reasons are clearly communicated

### Validation Checklist

- [ ] Release branch exists and is accessible
- [ ] Update branch naming is consistent
- [ ] Slack channels are configured correctly
- [ ] Bot tokens have appropriate permissions
- [ ] Repository permissions allow PR creation
- [ ] Module registry is accessible

## 📈 Performance Considerations

### Optimization Features
- **Concurrency Control**: Prevents conflicts with concurrent group settings
- **Efficient Delegation**: Minimal overhead for workflow orchestration
- **Conditional Execution**: Skips unnecessary steps when no updates found
- **Resource Isolation**: Each job runs independently for optimal resource usage

### Resource Management
- **Memory Usage**: Minimal overhead for orchestration layer
- **Network Efficiency**: Consolidated API calls through child workflows
- **Time Optimization**: Parallel execution where possible
- **Cost Efficiency**: Only runs expensive operations when needed

## 🔄 Integration Patterns

### Continuous Release Management

```yaml
on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours

jobs:
  update-active-releases:
    strategy:
      matrix:
        include:
          - release: 'R1-2025'
            update: 'R1-2025-update'
            reviewers: 'release-team'
          - release: 'R2-2025'
            update: 'R2-2025-update'
            reviewers: 'dev-team'
    uses: ./.github/workflows/release-update.yml
    with:
      release_branch: ${{ matrix.release }}
      update_branch: ${{ matrix.update }}
      pr_reviewers: ${{ matrix.reviewers }}
      pr_labels: 'automated,release-maintenance'
```

### Release Pipeline Integration

```yaml
jobs:
  prepare-release:
    # Release preparation steps

  update-release-modules:
    needs: prepare-release
    uses: ./.github/workflows/release-update.yml
    with:
      release_branch: ${{ needs.prepare-release.outputs.branch }}
      update_branch: '${{ needs.prepare-release.outputs.branch }}-initial-update'
      pr_reviewers: 'release-manager'

  validate-release:
    needs: update-release-modules
    if: needs.update-release-modules.outputs.pr_created == 'true'
    # Validation steps for updated release
```

### Custom Notification Integration

```yaml
jobs:
  release-update:
    uses: ./.github/workflows/release-update.yml
    with:
      release_branch: 'R1-2025'
      update_branch: 'R1-2025-update'

  custom-notifications:
    needs: release-update
    if: always() && needs.release-update.outputs.updated == 'true'
    runs-on: ubuntu-latest
    steps:
      - name: Send custom notifications
        # Custom notification logic
```

## 🔍 Troubleshooting

### Common Issues

**No Notifications Received**:
1. Check Slack channel configuration variables
2. Verify bot token validity
3. Confirm bot channel permissions
4. Review notification job logs

**PR Not Created**:
1. Verify repository permissions
2. Check branch naming consistency
3. Review release-update-flow.yml logs
4. Confirm update branch doesn't exist with conflicts

**Workflow Failures**:
1. Check individual job outcomes in summary
2. Review failure reasons in outputs
3. Verify input parameter correctness
4. Check repository and API connectivity

### Manual Verification

```bash
# Check release branch existence
gh api repos/:owner/:repo/branches/R1-2025

# Verify Slack channel configuration
echo "Team channel: ${{ vars.SLACK_NOTIF_CHANNEL }}"
echo "General channel: ${{ vars.GENERAL_SLACK_NOTIF_CHANNEL }}"

# Test bot permissions
curl -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  https://slack.com/api/conversations.info?channel=C1234567890
```

## 📚 Related Documentation

- **[Release Update Flow](release-update-flow.md)**: Detailed flow implementation
- **[Compare Applications](compare-applications.md)**: Version comparison workflow
- **[App Notification](app-notification.md)**: Notification patterns and best practices
- **[Update Application](update-application.md)**: Module update mechanics

---

**Last Updated**: September 2025
**Workflow Version**: 1.0
**Compatibility**: All FOLIO release branch maintenance workflows