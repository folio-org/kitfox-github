# Application Release Notification Workflow

**Workflow**: `release-preparation-notification.yml`  
**Purpose**: Standardized Slack notifications for FOLIO application operations  
**Type**: Reusable workflow (`workflow_call`)

## 🎯 Overview

This workflow provides standardized Slack notifications for FOLIO application operations, particularly release preparation activities. It delivers rich, contextual notifications with consistent formatting across the entire FOLIO ecosystem.

## 📋 Workflow Interface

### Inputs

| Input | Description | Required | Type | Default |
|-------|-------------|----------|------|---------|
| `app_name` | Application name for notification context | Yes | string | - |
| `operation_status` | Operation result ('success', 'failure', 'cancelled') | Yes | string | - |
| `operation_type` | Type of operation performed | No | string | `'Release Preparation'` |
| `additional_info` | Additional context information | No | string | `''` |
| `dry_run` | Indicates if operation was a dry run | No | boolean | `false` |

### Secrets

| Secret | Description | Required |
|--------|-------------|----------|
| `slack_bot_token` | Slack Bot Token for API access | Yes |

### Outputs

| Output | Description |
|--------|-------------|
| `notification_sent` | Boolean indicating if notification was sent successfully |
| `message_timestamp` | Slack message timestamp for reference |

## 🔄 Workflow Execution Flow

### 1. Context Preparation
- **Operation Analysis**: Determines notification type based on operation status
- **Message Formatting**: Prepares Slack message with appropriate formatting
- **Dry Run Handling**: Adds dry run indicators when applicable

### 2. Slack Integration
- **Token Validation**: Verifies Slack bot token availability
- **Channel Targeting**: Uses configured channel from repository variables
- **Message Delivery**: Sends formatted message via Slack API

### 3. Result Reporting
- **Success Tracking**: Reports notification delivery status
- **Error Handling**: Logs failures with actionable error messages
- **Timestamp Capture**: Records message timestamp for audit trail

## 📢 Message Templates

### Success Notification

```
✅ Release Preparation - SUCCESS

Application: app-acquisitions
Operation: Release Preparation
Status: Completed Successfully
Time: 2025-08-07 10:30:45 UTC

Details: Release branch R2-2025 created successfully
```

### Failure Notification

```
❌ Release Preparation - FAILURE

Application: app-acquisitions  
Operation: Release Preparation
Status: Failed
Time: 2025-08-07 10:30:45 UTC

Error: Branch R2-2025 already exists
```

### Dry Run Notification

```
🧪 Release Preparation - DRY RUN SUCCESS

Application: app-acquisitions
Operation: Release Preparation (Dry Run)
Status: Validation Completed
Time: 2025-08-07 10:30:45 UTC

Details: All validation checks passed - ready for actual execution
```

## 🛡️ Security Considerations

### Token Management

```yaml
# ✅ CORRECT: Token passed from calling repository
secrets:
  slack_bot_token: ${{ secrets.SLACK_BOT_TOKEN }}
```

**Security Principles**:
- **No Token Storage**: Workflow doesn't store or expose tokens
- **Scoped Access**: Token only used for message sending
- **Error Isolation**: Token validation errors don't expose sensitive data

### Channel Configuration

**Channel Targeting**:
- Uses repository-level variables: `vars.GENERAL_SLACK_NOTIF_CHANNEL`
- Fallback to default channels if variable not configured
- No hardcoded channel references in workflow

## 📊 Usage Examples

### Basic Notification

```yaml
jobs:
  notify-completion:
    uses: folio-org/kitfox-github/.github/workflows/release-preparation-notification.yml@main
    with:
      app_name: 'app-acquisitions'
      operation_status: 'success'
    secrets:
      slack_bot_token: ${{ secrets.SLACK_BOT_TOKEN }}
```

### Detailed Notification

```yaml
jobs:
  notify-with-context:
    uses: folio-org/kitfox-github/.github/workflows/release-preparation-notification.yml@main
    with:
      app_name: 'app-acquisitions'
      operation_status: 'success'
      operation_type: 'Release Branch Creation'
      additional_info: 'Created branch R2-2025 from R1-2024'
      dry_run: false
    secrets:
      slack_bot_token: ${{ secrets.SLACK_BOT_TOKEN }}
```

### Failure Notification

```yaml
jobs:
  notify-failure:
    if: failure()
    uses: folio-org/kitfox-github/.github/workflows/release-preparation-notification.yml@main
    with:
      app_name: 'app-acquisitions'
      operation_status: 'failure'
      additional_info: ${{ steps.operation.outputs.error_message }}
    secrets:
      slack_bot_token: ${{ secrets.SLACK_BOT_TOKEN }}
```

## 🎨 Message Formatting

### Slack mrkdwn Format

The workflow uses Slack's `mrkdwn` format for rich text:

```markdown
*Bold Text*: Important information
`Code Text`: Technical details
> Quoted Text: Additional context
```

### Status Icons

- ✅ Success operations
- ❌ Failed operations  
- ⚠️ Warning/cancelled operations
- 🧪 Dry run operations
- ℹ️ Informational messages

### Contextual Information

**Always Included**:
- Application name
- Operation type
- Status result
- Timestamp (UTC)

**Conditionally Included**:
- Dry run indicators
- Additional context information
- Error details (for failures)
- Links to workflow runs (when available)

## 🧪 Testing Strategy

### Notification Testing

```yaml
jobs:
  test-notifications:
    strategy:
      matrix:
        status: [success, failure, cancelled]
    steps:
      - name: 'Test Notification'
        uses: folio-org/kitfox-github/.github/workflows/release-preparation-notification.yml@main
        with:
          app_name: 'test-app'
          operation_status: ${{ matrix.status }}
          dry_run: true
```

### Channel Validation

**Prerequisites**:
- Slack bot token with appropriate permissions
- Channel exists and bot is member
- Repository variables configured correctly

**Validation Steps**:
1. Verify token permissions in Slack workspace
2. Confirm bot membership in target channel
3. Test message delivery with dry run
4. Validate message formatting and content

## 🔍 Troubleshooting

### Common Issues

**Token Permission Error**:
```
Error: The token used is not granted the required scopes: chat:write
Solution: Update bot token permissions in Slack app configuration
```

**Channel Not Found**:
```
Error: Channel not found
Solution: Verify channel exists and bot is invited to channel
```

**Message Too Long**:
```
Error: Message text exceeds character limit
Solution: Reduce additional_info content or split into multiple messages
```

### Debug Information

The workflow provides detailed logging:
- Token validation (without exposing token)
- Channel resolution and targeting
- Message formatting and content
- API response status and details

## 🔄 Integration Patterns

### Conditional Notifications

```yaml
jobs:
  operation:
    # ... operation steps ...
    
  notify-success:
    needs: operation
    if: success()
    uses: folio-org/kitfox-github/.github/workflows/release-preparation-notification.yml@main
    with:
      app_name: ${{ inputs.app_name }}
      operation_status: 'success'
    
  notify-failure:
    needs: operation
    if: failure()
    uses: folio-org/kitfox-github/.github/workflows/release-preparation-notification.yml@main
    with:
      app_name: ${{ inputs.app_name }}
      operation_status: 'failure'
      additional_info: 'Check workflow logs for details'
```

### Matrix Result Notifications

```yaml
collect-and-notify:
  needs: [matrix-operations]
  if: always()
  steps:
    - name: 'Aggregate Results'
      id: results
      run: |
        # Process matrix results
        echo "summary=5 successful, 2 failed" >> "$GITHUB_OUTPUT"
    
    - name: 'Send Summary Notification'
      uses: folio-org/kitfox-github/.github/workflows/release-preparation-notification.yml@main
      with:
        app_name: 'multiple-applications'
        operation_status: ${{ steps.results.outputs.overall_status }}
        operation_type: 'Batch Release Preparation'
        additional_info: ${{ steps.results.outputs.summary }}
```

## 📚 Related Documentation

- **[App Release Preparation](release-preparation.md)**: Main workflow that uses this notification
- **[Distributed Orchestration](distributed-orchestration.md)**: Cross-repository coordination patterns
- **[Slack API Documentation](https://api.slack.com/messaging/composing)**: Official Slack formatting guide
- **[FOLIO Communication Guidelines](https://folio-org.atlassian.net/)**: Team communication standards

---

**Last Updated**: August 2025  
**Workflow Version**: 1.2  
**Slack API Version**: v2.1.1
