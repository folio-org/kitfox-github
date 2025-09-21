# Release Preparation Slack Notification Workflow

**Workflow**: `release-preparation-notification.yml`
**Purpose**: Sends Slack notifications for release preparation workflow results
**Type**: Reusable workflow (`workflow_call`)

## 🎯 Overview

This workflow provides comprehensive Slack notification functionality for release preparation workflows. It sends contextual success or failure notifications to designated Slack channels, including detailed information about the release branch, version, commit details, and workflow outcomes. The workflow is designed to integrate seamlessly with release preparation processes and provides immediate feedback to development teams.

## 📋 Workflow Interface

### Inputs

| Input                  | Description                                    | Required | Type   | Default |
|------------------------|------------------------------------------------|----------|--------|---------|
| `app_name`             | Application repository name                    | Yes      | string | -       |
| `new_release_branch`   | New release branch name                        | Yes      | string | -       |
| `source_branch`        | Source branch used for release                 | Yes      | string | -       |
| `app_version`          | Application version                            | Yes      | string | -       |
| `commit_sha`           | Commit SHA of the release                      | Yes      | string | -       |
| `workflow_result`      | Result of the main workflow (success/failure)  | Yes      | string | -       |
| `workflow_run_id`      | GitHub run ID for linking                      | Yes      | string | -       |
| `workflow_run_number`  | GitHub run number for display                  | Yes      | string | -       |
| `slack_notif_channel`  | Slack notification channel                     | Yes      | string | -       |

### Outputs

| Output                | Description                                                 |
|-----------------------|-------------------------------------------------------------|
| `notification_outcome`| Outcome of the Slack notification (success/failure/skipped) |

### Secrets

| Secret                      | Description                    | Required |
|-----------------------------|--------------------------------|----------|
| `EUREKA_CI_SLACK_BOT_TOKEN` | Slack bot token for API access | Yes      |

## 🔄 Workflow Execution Flow

### 1. Success Notification (Conditional)
- **Triggers when**: `workflow_result == 'success'`
- **Channel Target**: Uses provided `slack_notif_channel`
- **Message Format**: Rich Slack blocks with attachment formatting
- **Content Includes**:
  - Success status with workflow run link
  - New release branch with repository link
  - Source branch with repository link
  - Application version
  - Commit SHA with commit link
  - Eureka CI/CD footer branding

### 2. Failure Notification (Conditional)
- **Triggers when**: `workflow_result == 'failure'`
- **Channel Target**: Uses provided `slack_notif_channel`
- **Message Format**: Rich Slack blocks with danger-colored attachment
- **Content Includes**:
  - Failure status with workflow run link
  - New release branch with repository link
  - Source branch with repository link
  - Eureka CI/CD footer branding

### 3. Error Handling
- **Continue on Error**: Both notification steps use `continue-on-error: true`
- **Graceful Degradation**: Workflow continues even if Slack API fails
- **Outcome Tracking**: Records success/failure of notification attempts

## 📧 Notification Format

### Success Notification

**Header**:
```
*{app_name} Application Release Preparation SUCCESS #{workflow_run_number}*
```

**Attachment Fields**:
- **New Release**: Linked release branch name
- **Source Branch**: Linked source branch name
- **New Version**: Application version string
- **Commit**: Linked commit SHA

**Visual Indicators**:
- **Color**: Green (good)
- **Status**: SUCCESS

### Failure Notification

**Header**:
```
*{app_name} Application Release Preparation FAILED #{workflow_run_number}*
```

**Attachment Fields**:
- **New Release**: Linked release branch name
- **Source Branch**: Linked source branch name

**Visual Indicators**:
- **Color**: Red (danger)
- **Status**: FAILED

## 📊 Usage Examples

### Basic Release Preparation Integration

```yaml
jobs:
  prepare-release:
    # Release preparation logic here
    outputs:
      result: ${{ job.status }}
      new_branch: ${{ steps.create-branch.outputs.branch_name }}
      version: ${{ steps.get-version.outputs.version }}
      commit_sha: ${{ steps.commit.outputs.sha }}

  notify-result:
    needs: prepare-release
    if: always()
    uses: folio-org/kitfox-github/.github/workflows/release-preparation-notification.yml@master
    with:
      app_name: ${{ github.event.repository.name }}
      new_release_branch: ${{ needs.prepare-release.outputs.new_branch }}
      source_branch: 'snapshot'
      app_version: ${{ needs.prepare-release.outputs.version }}
      commit_sha: ${{ needs.prepare-release.outputs.commit_sha }}
      workflow_result: ${{ needs.prepare-release.result }}
      workflow_run_id: ${{ github.run_id }}
      workflow_run_number: ${{ github.run_number }}
      slack_notif_channel: '#releases'
    secrets: inherit
```

### Multi-Channel Notification

```yaml
jobs:
  prepare-release:
    # Release preparation logic

  notify-team:
    needs: prepare-release
    if: always()
    uses: folio-org/kitfox-github/.github/workflows/release-preparation-notification.yml@master
    with:
      app_name: ${{ github.event.repository.name }}
      new_release_branch: ${{ needs.prepare-release.outputs.new_branch }}
      source_branch: 'snapshot'
      app_version: ${{ needs.prepare-release.outputs.version }}
      commit_sha: ${{ needs.prepare-release.outputs.commit_sha }}
      workflow_result: ${{ needs.prepare-release.result }}
      workflow_run_id: ${{ github.run_id }}
      workflow_run_number: ${{ github.run_number }}
      slack_notif_channel: '#dev-team'
    secrets: inherit

  notify-management:
    needs: prepare-release
    if: always() && needs.prepare-release.result == 'success'
    uses: folio-org/kitfox-github/.github/workflows/release-preparation-notification.yml@master
    with:
      app_name: ${{ github.event.repository.name }}
      new_release_branch: ${{ needs.prepare-release.outputs.new_branch }}
      source_branch: 'snapshot'
      app_version: ${{ needs.prepare-release.outputs.version }}
      commit_sha: ${{ needs.prepare-release.outputs.commit_sha }}
      workflow_result: ${{ needs.prepare-release.result }}
      workflow_run_id: ${{ github.run_id }}
      workflow_run_number: ${{ github.run_number }}
      slack_notif_channel: '#release-announcements'
    secrets: inherit
```

### Conditional Notification with Custom Logic

```yaml
jobs:
  prepare-release:
    # Release preparation steps

  determine-notification:
    needs: prepare-release
    runs-on: ubuntu-latest
    outputs:
      should_notify: ${{ steps.check.outputs.notify }}
      channel: ${{ steps.check.outputs.channel }}
    steps:
      - name: Determine notification requirements
        id: check
        run: |
          if [[ "${{ needs.prepare-release.result }}" == "success" ]]; then
            echo "notify=true" >> "$GITHUB_OUTPUT"
            echo "channel=#releases" >> "$GITHUB_OUTPUT"
          elif [[ "${{ needs.prepare-release.result }}" == "failure" ]]; then
            echo "notify=true" >> "$GITHUB_OUTPUT"
            echo "channel=#alerts" >> "$GITHUB_OUTPUT"
          else
            echo "notify=false" >> "$GITHUB_OUTPUT"
          fi

  notify:
    needs: [prepare-release, determine-notification]
    if: needs.determine-notification.outputs.should_notify == 'true'
    uses: folio-org/kitfox-github/.github/workflows/release-preparation-notification.yml@master
    with:
      app_name: ${{ github.event.repository.name }}
      new_release_branch: ${{ needs.prepare-release.outputs.new_branch }}
      source_branch: 'snapshot'
      app_version: ${{ needs.prepare-release.outputs.version }}
      commit_sha: ${{ needs.prepare-release.outputs.commit_sha }}
      workflow_result: ${{ needs.prepare-release.result }}
      workflow_run_id: ${{ github.run_id }}
      workflow_run_number: ${{ github.run_number }}
      slack_notif_channel: ${{ needs.determine-notification.outputs.channel }}
    secrets: inherit
```

## 🔍 Features

### Rich Slack Integration
- **Slack Blocks**: Uses modern Slack block formatting
- **Clickable Links**: All repository and commit references are linked
- **Color Coding**: Visual distinction between success and failure
- **Contextual Information**: Comprehensive release details

### Robust Error Handling
- **API Resilience**: Continues on Slack API failures
- **Token Validation**: Uses secure token management
- **Graceful Degradation**: Workflow success not dependent on notifications

### Comprehensive Information
- **Release Context**: Branch names, versions, and commit details
- **Workflow Linking**: Direct links to GitHub workflow runs
- **Repository Integration**: Links to branches and commits
- **Professional Branding**: Consistent Eureka CI/CD footer

## 🛡️ Error Handling

### Common Issues

**Slack Bot Token Missing**:
```
Error: Token not provided
Solution: Ensure EUREKA_CI_SLACK_BOT_TOKEN secret is configured
```

**Invalid Channel**:
```
Error: channel_not_found
Solution: Verify channel name and bot permissions
```

**API Rate Limiting**:
```
Error: rate_limited
Solution: Notifications will be retried automatically
```

**Bot Permissions**:
```
Error: not_in_channel
Solution: Invite bot to the target channel
```

### Debug Configuration

```yaml
- name: Debug Slack notification
  env:
    ACTIONS_STEP_DEBUG: true
  uses: folio-org/kitfox-github/.github/workflows/release-preparation-notification.yml@master
  # ... other configuration
```

## 🧪 Testing Strategy

### Test Scenarios

**Success Notification**:
- Test with `workflow_result: 'success'`
- Verify green attachment color
- Confirm all links are functional

**Failure Notification**:
- Test with `workflow_result: 'failure'`
- Verify red attachment color
- Confirm error information is displayed

**Channel Variations**:
- Test different channel formats (#channel, @user)
- Verify bot permissions in target channels

### Validation Checklist

- [ ] Slack bot token is configured
- [ ] Bot has access to target channels
- [ ] Channel names are correctly formatted
- [ ] Repository links are accessible
- [ ] Commit SHAs are valid
- [ ] Workflow run IDs are correct

## 📈 Performance Considerations

### Optimization Features
- **Minimal Processing**: Simple message formatting
- **Conditional Execution**: Only runs when needed
- **Error Tolerance**: Non-blocking notification failures
- **Efficient API Usage**: Single API call per notification

### Resource Usage
- **Memory**: Minimal - simple message construction
- **Network**: Single Slack API call
- **Time**: < 5 seconds typical execution

## 🔄 Integration Patterns

### Release Pipeline Integration

```yaml
jobs:
  create-release-branch:
    # Branch creation logic

  prepare-application:
    needs: create-release-branch
    # Application preparation

  validate-release:
    needs: prepare-application
    # Release validation

  notify-preparation:
    needs: [create-release-branch, prepare-application, validate-release]
    if: always()
    uses: ./.github/workflows/release-preparation-notification.yml
    with:
      app_name: ${{ github.event.repository.name }}
      new_release_branch: ${{ needs.create-release-branch.outputs.branch }}
      source_branch: 'snapshot'
      app_version: ${{ needs.prepare-application.outputs.version }}
      commit_sha: ${{ needs.validate-release.outputs.commit }}
      workflow_result: ${{ contains(needs.*.result, 'failure') && 'failure' || 'success' }}
      workflow_run_id: ${{ github.run_id }}
      workflow_run_number: ${{ github.run_number }}
      slack_notif_channel: '#releases'
```

### Automated Release Workflow

```yaml
on:
  schedule:
    - cron: '0 10 * * MON'  # Weekly release preparation

jobs:
  prepare-weekly-release:
    # Automated release preparation

  notify-teams:
    needs: prepare-weekly-release
    if: always()
    strategy:
      matrix:
        channel: ['#dev-team', '#qa-team', '#release-management']
    uses: ./.github/workflows/release-preparation-notification.yml
    with:
      slack_notif_channel: ${{ matrix.channel }}
      # ... other inputs
```

## 🔍 Troubleshooting

### Common Resolution Steps

1. **Verify Bot Setup**: Ensure Slack bot is properly configured
2. **Check Permissions**: Confirm bot can post to target channels
3. **Validate Tokens**: Ensure EUREKA_CI_SLACK_BOT_TOKEN is current
4. **Test Channel Names**: Verify channel names include proper formatting
5. **Monitor Rate Limits**: Check for API rate limiting issues

### Manual Testing

```bash
# Test Slack API connectivity
curl -X POST -H 'Authorization: Bearer $SLACK_BOT_TOKEN' \
  -H 'Content-type: application/json' \
  --data '{"channel":"#test","text":"Test message"}' \
  https://slack.com/api/chat.postMessage
```

## 📚 Related Documentation

- **[Release Preparation](release-preparation.md)**: Main release preparation workflow
- **[App Notification](app-notification.md)**: General application notification patterns
- **[Slack API Documentation](https://api.slack.com/methods/chat.postMessage)**: Slack API reference

---

**Last Updated**: September 2025
**Workflow Version**: 1.0
**Compatibility**: All FOLIO release preparation workflows