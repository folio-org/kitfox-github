# Branch Ruleset Automation Workflow

**Workflows**: `branch-ruleset-automation.yml` (orchestrator) + `branch-ruleset-automation-flow.yml` (per-branch flow)
**Purpose**: Automatically configures branch protection rules and merge queue settings
**Type**: `workflow_dispatch` orchestrator calling a reusable `workflow_call` flow

## Overview

This workflow automatically configures GitHub branch rulesets from a repository's update configuration. It uses a **two-workflow architecture**: an orchestrator builds a matrix from config and dispatches a per-branch flow that handles the update, notifications, and summary.

It serves every `folio-org/app-*` repository and `folio-org/platform-lsp`. It is repository-agnostic: everything specific to a repository comes from that repository's `update-config.yml`.

It runs over every enabled branch, not only release branches — a branch may appear in the matrix in order to have its ruleset *disabled*.

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
        enabled: false  # direct-commit branch: no ruleset
```

A `need_pr: false` branch takes direct commits, and the `merge_queue` rule rejects direct pushes. Enabling a
ruleset on such a branch stops its update cadence unless the pushing identity is a bypass actor — and a
workflow pushing with the default `GITHUB_TOKEN` is not, since `bypass_actors` resolves to the Eureka CI App.
Keep `ruleset.enabled` and `need_pr` in step, and flip both in the same commit.

### Per-Branch Overrides

Each branch can override any global ruleset setting. Objects merge key by key; **arrays are replaced
wholesale**, so a branch-level `required_checks` or `bypass_actors` discards the inherited list entirely:

```yaml
branches:
  - R1-2025:
      enabled: true
      need_pr: true
      ruleset:
        required_checks:
          - context: "eureka-ci / validate-application"  # restated: the array replaces, not appends
          - context: "eureka-ci / release-validation"
        merge_queue:
          check_response_timeout_minutes: 120  # other merge_queue keys inherited
```

A branch that needs the same checks as everyone else should omit `required_checks` entirely and inherit it.
A required check is a context name, not a workflow: the same name can be published by one workflow on
`pull_request` and another on `merge_group`.

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

gh workflow run branch-ruleset-automation.yml \
  -f repo_owner=folio-org \
  -f repo_name=platform-lsp
```

### Triggered by GitHub App Webhook

The GitHub App webhook listener dispatches this workflow on a `push` that touches `update-config.yml`. The
mapping lives in `gh-app-webhook-listener/terraform/environments/github_events_config.json`, with one
`repository_patterns` entry per repository family:

```json
{
  "event_type": "push",
  "repository_patterns": [
    {
      "owner": "folio-org",
      "repository": "app-*",
      "branches": "master",
      "file_patterns": [".github/update-config.yml"],
      "workflows": [
        {
          "owner": "folio-org",
          "repository": "kitfox-github",
          "workflow_file": "branch-ruleset-automation.yml",
          "ref": "master",
          "inputs": {
            "repo_owner": "{owner}",
            "repo_name": "{repository}",
            "head_sha": "{head_sha}"
          }
        }
      ]
    },
    { "owner": "folio-org", "repository": "platform-lsp", "...": "same shape" }
  ]
}
```

Both `folio-org/app-*` and `folio-org/platform-lsp` are wired. The `repository` field is a single fnmatch
pattern, not a list, so each family needs its own entry.

Two constraints are easy to miss:

- `branches: "master"` — a push touching `update-config.yml` on any other branch does not dispatch.
- `file_patterns` is matched against the union of `added`, `modified` and `removed` across the push's
  `commits`. A push that carries an empty `commits` array, such as a force-push or a branch creation, matches
  nothing and does not dispatch.

## Troubleshooting

### Common Issues

**No Rulesets Created**:
1. Verify update-config.yml exists
2. Check `enabled: true` in config
3. Verify `ruleset.enabled: true` for the branch, globally or per branch
4. Confirm branches actually exist in repository
5. A branch whose own `enabled` is not `true` is skipped before the ruleset is resolved, so its existing
   ruleset is left untouched rather than disabled

**Required Check Never Satisfied** (PR stuck on "Expected — waiting for status to be reported"):
The `required_checks` context must match the published check run by name **and** by publishing app.
`integration_id` resolves to `EUREKA_CI_APP_ID`, so a check run created with the default `GITHUB_TOKEN` is
published by the GitHub Actions app and will not satisfy the rule. Publish it with an Eureka CI App token.

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

**Last Updated**: September 2026
**Workflow Version**: 2.1
**Compatibility**: Requires repository admin permissions and EUREKA_CI_APP_ID variable
