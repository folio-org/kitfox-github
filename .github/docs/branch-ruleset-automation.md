# Branch Ruleset Automation Workflow

**Workflows**: `branch-ruleset-automation.yml` (orchestrator) + `branch-ruleset-automation-flow.yml` (per-branch flow)
**Purpose**: Automatically configures branch protection rules and merge queue settings
**Type**: `workflow_dispatch` orchestrator calling a reusable `workflow_call` flow

## Overview

This workflow automatically configures GitHub branch rulesets for release branches based on the repository's update configuration. It uses a **two-workflow architecture**: an orchestrator builds a matrix from config and dispatches a per-branch flow that handles the update, notifications, and summary.

Features:
1. **Configurable ruleset parameters** via `update-config.yml`
2. **Matrix-based execution** - one flow job per branch for parallel processing
3. **Enforcement control** - `enabled: true` activates rulesets, `enabled: false` disables existing ones
4. **Per-branch notifications** - each branch gets its own Slack notification and summary
5. **Configurable merge queue** settings per branch

## Workflow Interface

### Inputs

| Input        | Description                                   | Required | Type   | Default |
|--------------|-----------------------------------------------|----------|--------|---------|
| `repo_owner` | Repository owner (organization or user)       | Yes      | string | -       |
| `repo_name`  | Repository name                               | Yes      | string | -       |
| `head_sha`   | Commit SHA that triggered the update          | No       | string | `''`    |

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
| `EUREKA_CI_APP_ID`             | GitHub App ID for bypass actors      | Yes      |
| `SLACK_NOTIF_CHANNEL`          | Team Slack notification channel      | No       |
| `GENERAL_SLACK_NOTIF_CHANNEL`  | General Slack notification channel   | No       |

## Workflow Execution Flow

### 1. Prepare Branch Configurations
**Job**: `prepare`

Reads configuration and builds a matrix of branches to process.

**Steps**:
1. Generate GitHub App Token
2. Get Update Configuration (including ruleset config)
3. Check Configuration - validates config exists, is enabled, and has branches
4. Build Matrix - creates one entry per branch with resolved ruleset config

**Outputs**:
- `matrix`: JSON matrix for parallel job execution (includes `enforcement` per branch)
- `has_branches`: Whether any branches need processing

### 2. Update Rulesets (Matrix)
**Job**: `update-rulesets`

Calls `branch-ruleset-automation-flow.yml` for each branch using matrix strategy.

**Strategy**:
- `fail-fast: false` - continue processing other branches if one fails
- `max-parallel: 5` - limit concurrent jobs

Each matrix entry includes `enforcement: active` or `enforcement: disabled` based on `ruleset.enabled` in config.

### 3. Per-Branch Flow (`branch-ruleset-automation-flow.yml`)

Each flow execution contains three jobs:

1. **Update Ruleset** - Calls `branch-ruleset-management` action with enforcement level
2. **Send Notifications** - Slack notifications (skipped when outcome is `skipped`)
3. **Workflow Summary** - Per-branch step summary with notification status

### 4. Workflow Summary (Orchestrator)
**Job**: `summarize`

Generates an aggregated summary across all branches.

## Ruleset Configuration

Ruleset parameters are now **fully configurable** via `update-config.yml`. See [update-config.md](update-config.md#ruleset-configuration) for complete schema.

### Basic Configuration

```yaml
update_config:
  enabled: true
  ruleset:
    enabled: true
    pattern: "{0}-eureka-ci"
    required_checks:
      - context: "eureka-ci / validate-application"
        integration_id: null  # Uses EUREKA_CI_APP_ID variable
    merge_queue:
      enabled: true
      merge_method: "SQUASH"
      grouping_strategy: "ALLGREEN"
    bypass_actors:
      - actor_id: null  # Uses EUREKA_CI_APP_ID variable
        actor_type: "Integration"
        bypass_mode: "always"

branches:
  - R1-2025:
      enabled: true
      need_pr: true
      # Inherits global ruleset config
  - snapshot:
      enabled: true
      need_pr: false
      ruleset:
        enabled: true  # Override: create ruleset for non-PR branch
        merge_queue:
          enabled: false  # Override: no merge queue for snapshot
```

### Per-Branch Overrides

Each branch can override any global ruleset setting:

```yaml
branches:
  - R1-2025:
      enabled: true
      need_pr: true
      ruleset:
        required_checks:
          - context: "eureka-ci / validate-application"
          - context: "eureka-ci / release-validation"  # Additional check
        merge_queue:
          check_response_timeout_minutes: 120  # Longer timeout
```

## Enforcement Behavior

The `ruleset.enabled` setting maps to ruleset enforcement:

| `ruleset.enabled` | Ruleset exists? | Action                          |
|--------------------|-----------------|--------------------------------------|
| `true`             | No              | Creates new active ruleset           |
| `true`             | Yes             | Updates existing ruleset (active)    |
| `false`            | No              | Skips (nothing to disable)           |
| `false`            | Yes             | Sets enforcement to `disabled`       |

## Usage Examples

### Manual Trigger

```bash
gh workflow run branch-ruleset-automation.yml \
  -f repo_owner=folio-org \
  -f repo_name=app-acquisitions
```

### Triggered by GitHub App Webhook

This workflow can be triggered when update-config.yml changes:

```yaml
event_type: push
files_changed:
  - .github/update-config.yml
```

## Troubleshooting

### Common Issues

**No Rulesets Created**:
1. Verify update-config.yml exists
2. Check `enabled: true` in config
3. For non-PR branches, verify `ruleset.enabled: true` is set
4. Confirm branches actually exist in repository

**Ruleset Update Failed**:
1. Check GitHub App has admin permissions
2. Verify EUREKA_CI_APP_ID variable is set
3. Review workflow logs for API errors

**Matrix Job Failures**:
- Check individual matrix job logs
- Other branches continue processing even if one fails

### Debug Commands

**View Existing Rulesets**:
```bash
gh api repos/folio-org/app-acquisitions/rulesets
```

**View Configuration**:
```bash
gh api repos/folio-org/app-acquisitions/contents/.github/update-config.yml \
  --jq '.content' | base64 -d
```

## Related Documentation

- **[Update Config Schema](update-config.md)**: Complete configuration schema including ruleset settings
- **[Merge Queue Check](merge-queue-check.md)**: Merge queue validation
- **[Branch Ruleset Management Action](../actions/branch-ruleset-management/README.md)**: Ruleset management action

---

**Last Updated**: February 2026
**Workflow Version**: 2.0
**Compatibility**: Requires repository admin permissions and EUREKA_CI_APP_ID variable
