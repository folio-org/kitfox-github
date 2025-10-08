# Snapshot Update Workflow

## Overview

The **Snapshot Update** workflow provides a complete, integrated solution for updating FOLIO application snapshot versions with the latest module dependencies. It orchestrates the entire update process including platform descriptor fetching, module updates, notifications, and comprehensive summaries.

## Workflow File

[`../.github/workflows/snapshot-update.yml`](../.github/workflows/snapshot-update.yml)

## Purpose

This high-level orchestrator workflow:
- Updates application snapshots with latest module versions
- Manages platform descriptor dependencies
- Sends notifications to Slack channels
- Generates comprehensive workflow summaries
- Supports both scheduled and manual triggers

## Workflow Type

- **Type**: Reusable workflow
- **Trigger**: `workflow_call`
- **Level**: High-level orchestrator

## Inputs

| Input                     | Required  | Type    | Default           | Description                                                    |
|---------------------------|-----------|---------|-------------------|----------------------------------------------------------------|
| `app_name`                | Yes       | string  | -                 | Application name                                               |
| `repo`                    | Yes       | string  | -                 | Application repository (org/repo format)                       |
| `descriptor_build_offset` | No        | string  | '100100000000000' | Offset to apply to application artifact version                |
| `rely_on_FAR`             | No        | boolean | false             | Whether to rely on FAR for application descriptor dependencies |
| `dry_run`                 | No        | boolean | false             | Perform dry run without making changes                         |
| `is_scheduled`            | No        | boolean | false             | Whether this is a scheduled run                                |

## Outputs

| Output                 | Description                                    |
|------------------------|------------------------------------------------|
| `update_result`        | Result of the update (success/failure/skipped) |
| `updated`              | Whether modules were updated                   |
| `new_version`          | New application version                        |
| `previous_version`     | Previous application version                   |
| `updated_cnt`          | Number of updated modules                      |
| `updated_modules`      | List of updated modules                        |
| `commit_sha`           | Commit SHA of the update                       |
| `failure_reason`       | Reason for failure if any                      |
| `notification_outcome` | Outcome of the notification                    |

## Workflow Jobs

### 1. fetch-descriptor
- **Purpose**: Fetches platform descriptor from platform-lsp repository
- **Condition**: Skipped if `rely_on_FAR` is true
- **Uploads**: Platform descriptor as artifact

### 2. update
- **Purpose**: Core application update logic
- **Calls**: `snapshot-update-flow.yml` workflow
- **Passes**: All inputs and platform descriptor

### 3. notify
- **Purpose**: Sends Slack notifications
- **Condition**: Runs on failures or when updates are made
- **Channels**: Team and general Slack channels
- **Features**:
  - Rich message formatting
  - Success/failure templates
  - Non-blocking failures

### 4. summarize
- **Purpose**: Generates GitHub Actions summary
- **Always runs**: Provides complete status report
- **Includes**:
  - Update results
  - Module changes
  - Notification status
  - Error details (if any)

## Usage Example

### In Application Repository

```yaml
name: Snapshot update

on:
  schedule:
    - cron: "*/20 * * * *"
  workflow_dispatch:
    inputs:
      dry_run:
        description: 'Perform dry run'
        type: boolean
        default: false

jobs:
  update-snapshot:
    uses: folio-org/kitfox-github/.github/workflows/snapshot-update.yml@master
    with:
      app_name: ${{ github.event.repository.name }}
      repo: ${{ github.repository }}
      dry_run: ${{ inputs.dry_run || false }}
      is_scheduled: ${{ github.event_name == 'schedule' }}
    secrets: inherit
```

## Notification Format

### Success Notification

```
📦 app-agreements snapshot updated #123

New Version: 1.2.3-SNAPSHOT.456
Previous Version: 1.2.3-SNAPSHOT.455
Updated Modules: 5
Commit: abc123

Updated Modules:
- mod-agreements: 2.0.0 → 2.1.0
- mod-licenses: 1.5.0 → 1.6.0
```

### Failure Notification

```
❌ app-agreements snapshot failed #123

Failure Reason: Unable to resolve module versions
Check workflow logs for details
```

## Features

### Integrated Notifications
- Sends to both team and general Slack channels
- Non-blocking notification failures
- Status tracking in workflow summary

### Platform Descriptor Management
- Automatically fetches latest platform descriptor
- Optional FAR registry support
- Artifact caching for efficiency

### Comprehensive Summaries
- Detailed GitHub Actions summary
- Module-level change tracking
- Notification status reporting
- Error diagnostics

### Flexible Triggers
- Scheduled updates (cron)
- Manual triggers with parameters
- Dry-run support for testing

## Error Handling

- **Graceful Failures**: Notification failures don't fail the workflow
- **Detailed Logging**: Comprehensive error messages
- **Status Tracking**: All job outcomes tracked and reported
- **Rollback Support**: Through underlying snapshot-update-flow workflow

## Dependencies

### Called Workflows
- `snapshot-update-flow.yml`: Core update orchestration

### Required Secrets
- `EUREKA_CI_SLACK_BOT_TOKEN`: For Slack notifications
- Inherited secrets for registry access

### Required Variables
- `SLACK_NOTIF_CHANNEL`: Team notification channel
- `GENERAL_SLACK_NOTIF_CHANNEL`: General notification channel

## Best Practices

1. **Scheduled Updates**: Use conservative cron schedules to avoid overwhelming the registry
2. **Dry Runs**: Always test with dry_run before production changes
3. **Monitoring**: Set up Slack channels for notifications
4. **Version Offsets**: Use appropriate descriptor_build_offset values

## Troubleshooting

### Common Issues

1. **No Updates Found**
   - Check if modules have new versions available
   - Verify platform descriptor is current

2. **Notification Failures**
   - Verify Slack bot token is valid
   - Check channel variables are set

3. **Platform Descriptor Issues**
   - Ensure platform-lsp repository is accessible
   - Check snapshot branch exists

### Debug Steps

1. Enable debug logging in GitHub Actions
2. Check workflow summary for detailed status
3. Review individual job logs
4. Verify secrets and variables are configured

## Related Documentation

- [Snapshot Update Flow Workflow](snapshot-update-flow.md)
- [Update Application Workflow](update-application.md)
- [Platform LSP Documentation](https://github.com/folio-org/platform-lsp)