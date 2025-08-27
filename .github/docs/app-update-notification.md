# Application Update Notification Workflow

**Workflow**: `app-update-notification.yml`  
**Purpose**: Standardized Slack notifications for FOLIO application update operations  
**Type**: Reusable workflow (`workflow_call`)

## 🎯 Overview

This workflow provides rich Slack notifications for FOLIO application update operations, particularly snapshot CI updates. It delivers contextual notifications with comprehensive update details, module information, and direct links to commits and descriptors.

## 📋 Workflow Interface

### Inputs

| Input                      | Description                                   | Required  | Type   | Default  |
|----------------------------|-----------------------------------------------|-----------|--------|----------|
| `app_name`                 | Application name                              | Yes       | string | -        |
| `repo`                     | Application repository name (org/repo format) | Yes       | string | -        |
| `new_version`              | Application new version                       | Yes       | string | -        |
| `previous_version`         | Application previous version                  | Yes       | string | -        |
| `updated_cnt`              | Number of updated modules                     | No        | string | `''`     |
| `updated_modules`          | List of updated modules                       | No        | string | `''`     |
| `failure_reason`           | Reason for failure if applicable              | No        | string | `''`     |
| `commit_sha`               | Commit SHA of the update                      | Yes       | string | -        |
| `app_descriptor_file_name` | Name of generated application descriptor file | Yes       | string | -        |
| `app_descriptor_url`       | Application descriptor URL                    | Yes       | string | -        |
| `workflow_result`          | Result of the main workflow (success/failure) | Yes       | string | -        |
| `workflow_run_id`          | GitHub run ID for linking                     | Yes       | string | -        |
| `workflow_run_number`      | GitHub run number for display                 | Yes       | string | -        |
| `slack_notif_channel`      | Slack notification channel                    | Yes       | string | -        |

### Secrets

| Secret                      | Description                                 | Required  |
|-----------------------------|---------------------------------------------|-----------|
| `EUREKA_CI_SLACK_BOT_TOKEN` | Slack Bot Token for Eureka CI notifications | Yes       |

## 🔄 Workflow Execution Flow

### 1. Success Notification Processing
- **Module Info Formatting**: Processes updated modules list for display
- **Rich Message Creation**: Builds comprehensive success notification
- **Context Integration**: Includes version changes, commit links, and descriptor URLs

### 2. Failure Notification Processing
- **Error Context**: Captures failure reason and workflow context
- **Simplified Message**: Focuses on failure details and troubleshooting links

### 3. Slack Integration
- **Channel Targeting**: Uses provided channel configuration
- **Message Delivery**: Sends formatted message via Slack API
- **Error Handling**: Manages API failures gracefully

## 📢 Message Templates

### Success Notification

```
✅ app-acquisitions Application Update SUCCESS #1234

┌─────────────────────────────────────────────────────────────┐
│ New Version: 1.2.3-SNAPSHOT.100100001234                    │
│ Previous Version: 1.2.2-SNAPSHOT.100100001200               │
│ Updated: 3 modules                                          │
│ Commit: a1b2c3d4                                            │
│ Descriptor: app-acquisitions-1.2.3-SNAPSHOT.100100001234    │
└─────────────────────────────────────────────────────────────┘

Updated Modules:
mod-inventory 2.1.0 -> 2.1.1-SNAPSHOT
ui-inventory 3.0.0 -> 3.0.1-SNAPSHOT  
mod-circulation 1.5.0 -> 1.5.2-SNAPSHOT

Eureka CI/CD
```

### Failure Notification

```
❌ app-acquisitions Application Update FAILED #1234

┌─────────────────────────────────────────────────────────────┐
│ Reason: Failed to fetch latest module versions from         │
│         registry for mod-inventory                          │
└─────────────────────────────────────────────────────────────┘

Eureka CI/CD
```

## 🎨 Message Formatting

### Slack Block Structure

**Success Messages**:
- **Header Block**: Application name, status, and workflow link
- **Attachment Fields**: Version details, update count, commit, descriptor
- **Module Details**: Formatted list of updated modules with version changes
- **Footer**: Eureka CI/CD branding

**Failure Messages**:
- **Header Block**: Application name, failure status, and workflow link  
- **Attachment Fields**: Failure reason with context
- **Footer**: Eureka CI/CD branding

### Visual Elements

**Status Indicators**:
- ✅ Success operations
- ❌ Failed operations
- 📊 Update statistics
- 🔗 Clickable links

**Information Hierarchy**:
1. **Primary**: Application name and status
2. **Secondary**: Version changes and update count
3. **Tertiary**: Module-level details
4. **Links**: Commit, descriptor, workflow run

## 🛡️ Security Considerations

### Token Management

```yaml
env:
  SLACK_BOT_TOKEN: ${{ secrets.EUREKA_CI_SLACK_BOT_TOKEN }}
```

**Security Principles**:
- **Dedicated Token**: Uses Eureka CI-specific Slack bot token
- **Scoped Access**: Token only used for message posting
- **No Token Exposure**: Token never logged or exposed in outputs

### Channel Configuration

**Dynamic Channel Targeting**:
- Channel specified via workflow input parameter
- No hardcoded channel references
- Supports different channels per application/environment

## 📊 Usage Examples

### Basic Update Notification

```yaml
jobs:
  update-application:
    uses: folio-org/kitfox-github/.github/workflows/app-update.yml@master
    # ... update configuration ...

  notify-success:
    needs: update-application
    if: needs.update-application.outputs.updated == 'true'
    uses: folio-org/kitfox-github/.github/workflows/app-update-notification.yml@master
    with:
      app_name: ${{ github.event.repository.name }}
      repo: ${{ github.repository }}
      new_version: ${{ needs.update-application.outputs.new_version }}
      previous_version: ${{ needs.update-application.outputs.previous_version }}
      updated_cnt: ${{ needs.update-application.outputs.updated_cnt }}
      updated_modules: ${{ needs.update-application.outputs.updated_modules }}
      commit_sha: ${{ needs.update-application.outputs.commit_sha }}
      app_descriptor_file_name: ${{ needs.update-application.outputs.app_descriptor_file_name }}
      app_descriptor_url: ${{ needs.update-application.outputs.app_descriptor_url }}
      workflow_result: ${{ needs.update-application.result }}
      workflow_run_id: ${{ github.run_id }}
      workflow_run_number: ${{ github.run_number }}
      slack_notif_channel: ${{ vars.SLACK_NOTIF_CHANNEL }}
    secrets: inherit
```

### Conditional Notifications

```yaml
jobs:
  notify-results:
    needs: update-application
    if: always() && !(github.event_name == 'workflow_dispatch' && inputs.dry_run) &&
      (needs.update-application.result != 'success' || 
        needs.update-application.result == 'success' && needs.update-application.outputs.updated == 'true') && 
      vars.SLACK_NOTIF_CHANNEL != ''
    uses: folio-org/kitfox-github/.github/workflows/app-update-notification.yml@master
    with:
      # ... notification parameters ...
      failure_reason: ${{ needs.update-application.outputs.failure_reason }}
      workflow_result: ${{ needs.update-application.result }}
```

### Scheduled Update Notifications

```yaml
on:
  schedule:
    - cron: "*/20 * * * *"

jobs:
  update-application:
    uses: folio-org/kitfox-github/.github/workflows/app-update.yml@master
    # ... configuration ...

  slack_notification:
    needs: update-application
    if: always() && 
      (needs.update-application.result != 'success' || 
        needs.update-application.outputs.updated == 'true') && 
      vars.SLACK_NOTIF_CHANNEL != ''
    uses: folio-org/kitfox-github/.github/workflows/app-update-notification.yml@master
```

## 🧪 Testing Strategy

### Notification Testing

```yaml
jobs:
  test-notifications:
    strategy:
      matrix:
        result: [success, failure]
        updated: [true, false]
    steps:
      - name: 'Test Update Notification'
        uses: folio-org/kitfox-github/.github/workflows/app-update-notification.yml@master
        with:
          app_name: 'test-app'
          repo: 'folio-org/test-app'
          new_version: '1.0.1-SNAPSHOT.100100001234'
          previous_version: '1.0.0-SNAPSHOT.100100001200'
          updated_cnt: '2'
          updated_modules: 'mod-test 1.0.0 -> 1.0.1\nui-test 2.0.0 -> 2.0.1'
          commit_sha: 'abc123def456'
          app_descriptor_file_name: 'test-app-1.0.1-SNAPSHOT.100100001234'
          app_descriptor_url: 'https://far.ci.folio.org/applications/test-app-1.0.1-SNAPSHOT.100100001234?full=true'
          workflow_result: ${{ matrix.result }}
          workflow_run_id: ${{ github.run_id }}
          workflow_run_number: ${{ github.run_number }}
          slack_notif_channel: '#test-channel'
```

### Channel Validation

**Prerequisites**:
- Eureka CI Slack bot token with `chat:write` permissions
- Target channel exists and bot is member
- Repository variables configured correctly

**Validation Steps**:
1. Verify bot permissions in Slack workspace
2. Confirm bot membership in notification channel
3. Test message delivery with various scenarios
4. Validate message formatting and link functionality

## 🔍 Troubleshooting

### Common Issues

**Token Permission Error**:
```
Error: The token used is not granted the required scopes: chat:write
Solution: Update Eureka CI bot token permissions in Slack app configuration
```

**Channel Not Found**:
```
Error: Channel not found
Solution: Verify channel exists and Eureka CI bot is invited to channel
```

**Message Formatting Issues**:
```
Error: Invalid block format
Solution: Check updated_modules format and special character escaping
```

**Missing Repository Variables**:
```
Error: vars.SLACK_NOTIF_CHANNEL is empty
Solution: Configure SLACK_NOTIF_CHANNEL repository variable
```

### Debug Information

The workflow provides detailed logging:
- **Input Validation**: Parameter presence and format checking
- **Message Construction**: Block building and formatting steps
- **API Interaction**: Slack API request/response details
- **Error Context**: Specific failure reasons with resolution guidance

## 🔄 Integration Patterns

### Multi-Application Notifications

```yaml
collect-and-notify:
  needs: [matrix-updates]
  if: always()
  steps:
    - name: 'Aggregate Update Results'
      id: aggregate
      run: |
        # Process matrix results
        success_count=$(echo '${{ toJSON(needs.matrix-updates.outputs) }}' | jq '[.[] | select(.updated == "true")] | length')
        echo "summary=$success_count applications updated successfully" >> "$GITHUB_OUTPUT"
    
    - name: 'Send Summary Notification'
      uses: folio-org/kitfox-github/.github/workflows/app-update-notification.yml@master
      with:
        app_name: 'platform-summary'
        repo: 'folio-org/platform-lsp'
        new_version: 'batch-update'
        previous_version: 'various'
        updated_cnt: ${{ steps.aggregate.outputs.success_count }}
        updated_modules: ${{ steps.aggregate.outputs.summary }}
        workflow_result: 'success'
        # ... other parameters ...
```

### Environment-Specific Channels

```yaml
jobs:
  notify-snapshot:
    if: github.ref == 'refs/heads/snapshot'
    uses: folio-org/kitfox-github/.github/workflows/app-update-notification.yml@master
    with:
      # ... parameters ...
      slack_notif_channel: '#snapshot-updates'

  notify-release:
    if: startsWith(github.ref, 'refs/heads/R')
    uses: folio-org/kitfox-github/.github/workflows/app-update-notification.yml@master
    with:
      # ... parameters ...
      slack_notif_channel: '#release-updates'
```

## 📚 Related Documentation

- **[App Update Workflow](app-update.md)**: Main application update workflow
- **[Platform Snapshot Flow](../../../platform-lsp/.github/docs/snapshot-flow.md)**: Platform-level update coordination
- **[Slack API Documentation](https://api.slack.com/messaging/composing)**: Official Slack formatting guide
- **[FOLIO Communication Guidelines](https://folio-org.atlassian.net/)**: Team communication standards

---

**Last Updated**: August 2025  
**Workflow Version**: 1.0  
**Slack API Version**: v2.1.1
