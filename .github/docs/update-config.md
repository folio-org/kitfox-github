# Update Configuration Schema

**File**: `.github/update-config.yml`
**Purpose**: Configure automated module updates, PR settings, and branch rulesets

## Overview

The `update-config.yml` file controls how the Eureka CI/CD system handles module version updates for a repository. It specifies which branches to scan, how to create PRs, and how to configure branch protection rulesets.

## Complete Schema

```yaml
update_config:
  enabled: boolean                              # Enable/disable scanning
  update_branch_format: string                  # Template for update branch names
  labels: array                                 # Labels for update PRs
  pr_reviewers: array                           # Reviewers for update PRs
  ruleset: object                               # Global ruleset configuration (optional)

branches: array                                 # List of branch configurations
```

## Configuration Sections

### update_config (Global Settings)

| Field                   | Type    | Required | Default              | Description                           |
|-------------------------|---------|----------|----------------------|---------------------------------------|
| `enabled`               | boolean | Yes      | -                    | Enable scanning for this repository   |
| `update_branch_format`  | string  | No       | `version-update/{0}` | Template for update branch names      |
| `labels`                | array   | No       | `[]`                 | Labels to add to update PRs           |
| `pr_reviewers`          | array   | No       | `[]`                 | Teams/users to request review from    |
| `ruleset`               | object  | No       | See defaults         | Global branch ruleset configuration   |

### branches (Per-Branch Settings)

Each branch is defined as a single-key object:

```yaml
branches:
  - branch_name:
      enabled: boolean
      need_pr: boolean
      pre_release: string
      descriptor_build_offset: string
      rely_on_FAR: boolean
      skip_interface_validation: boolean
      skip_dependency_validation: string
      publish: boolean
      release: boolean
      ruleset: object  # Per-branch ruleset overrides
```

| Field                     | Type    | Required | Default | Description                                      |
|---------------------------|---------|----------|---------|--------------------------------------------------|
| `enabled`                 | boolean | Yes      | -       | Enable scanning for this branch                  |
| `need_pr`                 | boolean | Yes      | -       | Create PR for updates (vs direct push)           |
| `pre_release`             | string  | No       | `""`    | Filter: `"only"`, `"true"`, `"false"`            |
| `descriptor_build_offset` | string  | No       | `""`    | Build number offset for descriptors              |
| `rely_on_FAR`             | boolean | No       | `false` | Use FOLIO Application Registry for validation    |
| `skip_interface_validation` | boolean | No     | `false` | Skip module interface integrity validation       |
| `skip_dependency_validation`| string  | No     | `false` | Dependency validation mode: `false` / `true` / `bypass` |
| `publish`                 | boolean | No       | `true`  | Whether to publish descriptor to FAR after validation |
| `release`                 | boolean | No       | `true`  | Whether to create/update release PR (only with `need_pr: true`) |
| `ruleset`                 | object  | No       | -       | Branch-specific ruleset configuration overrides  |

## Ruleset Configuration

The `ruleset` section controls GitHub branch rulesets. It can be specified globally under `update_config.ruleset` and overridden per branch.

### Default Values

When no `ruleset` section is specified, the following defaults are used:

```yaml
ruleset:
  enabled: false
  pattern: "{0}-eureka-ci"
  required_checks:
    - context: "eureka-ci / validate-application"
  merge_queue:
    enabled: true
    check_response_timeout_minutes: 60
    grouping_strategy: "ALLGREEN"
    max_entries_to_build: 5
    max_entries_to_merge: 5
    merge_method: "SQUASH"
    min_entries_to_merge: 1
    min_entries_to_merge_wait_minutes: 5
  bypass_actors:
    - actor_type: "Integration"
      bypass_mode: "always"
```

### Ruleset Schema

| Field             | Type    | Default                                 | Description                              |
|-------------------|---------|-----------------------------------------|------------------------------------------|
| `enabled`         | boolean | `false`                                 | Enable ruleset for this branch (`false` disables existing) |
| `pattern`         | string  | `"{0}-eureka-ci"`                       | Ruleset naming pattern (`{0}` = branch)  |
| `required_checks` | array   | Single eureka-ci check                  | Required status checks                   |
| `merge_queue`     | object  | See below                               | Merge queue configuration                |
| `bypass_actors`   | array   | Single integration actor                | Actors that can bypass ruleset           |

### merge_queue Object

| Field                              | Type    | Default      | Description                              |
|------------------------------------|---------|--------------|------------------------------------------|
| `enabled`                          | boolean | `true`       | Enable merge queue for this branch       |
| `check_response_timeout_minutes`   | integer | `60`         | Timeout waiting for status checks        |
| `grouping_strategy`                | string  | `"ALLGREEN"` | How to group entries: `ALLGREEN`, `HEADGREEN` |
| `max_entries_to_build`             | integer | `5`          | Max concurrent builds                    |
| `max_entries_to_merge`             | integer | `5`          | Max concurrent merges                    |
| `merge_method`                     | string  | `"SQUASH"`   | Merge method: `SQUASH`, `MERGE`, `REBASE` |
| `min_entries_to_merge`             | integer | `1`          | Min entries required to merge            |
| `min_entries_to_merge_wait_minutes`| integer | `5`          | Wait time before merging single entry    |

### required_checks Array Item

| Field            | Type    | Required | Description                              |
|------------------|---------|----------|------------------------------------------|
| `context`        | string  | Yes      | Status check context name                |
| `integration_id` | integer | No       | GitHub App ID (null = use EUREKA_CI_APP_ID) |

### bypass_actors Array Item

| Field        | Type    | Required | Description                              |
|--------------|---------|----------|------------------------------------------|
| `actor_id`   | integer | No       | Actor ID (null = use EUREKA_CI_APP_ID)   |
| `actor_type` | string  | Yes      | Type: `Integration`, `User`, `Team`, `DeployKey` |
| `bypass_mode`| string  | Yes      | Mode: `always`, `pull_request`           |

## Opt-in Behavior

Rulesets are **opt-in** — no rulesets are created unless explicitly enabled. Setting `ruleset.enabled: false` will disable any existing ruleset (set enforcement to `disabled`). If no ruleset exists, the branch is skipped.

To enable rulesets for a branch, set `ruleset.enabled: true` either globally or per branch:

```yaml
update_config:
  enabled: true
  ruleset:
    enabled: true              # Enable rulesets globally

branches:
  - snapshot:
      enabled: true
      need_pr: false
      ruleset:
        enabled: false         # Explicitly disable for snapshot
  - R1-2025:
      enabled: true
      need_pr: true
      # Inherits global ruleset (enabled: true)
```

## Example Configurations

### Minimal Configuration

```yaml
update_config:
  enabled: true

branches:
  - snapshot:
      enabled: true
      need_pr: false
      pre_release: "only"
  - R1-2025:
      enabled: true
      need_pr: true
      pre_release: "false"
```

### Full Configuration with Ruleset

```yaml
update_config:
  enabled: true
  update_branch_format: version-update/{0}
  labels:
    - version-update
  pr_reviewers:
    - folio-org/kitfox
    - folio-org/acquisitions
  ruleset:
    enabled: true
    pattern: "{0}-eureka-ci"
    required_checks:
      - context: "eureka-ci / validate-application"
    merge_queue:
      enabled: true
      check_response_timeout_minutes: 60
      grouping_strategy: "ALLGREEN"
      merge_method: "SQUASH"
    bypass_actors:
      - actor_type: "Integration"
        bypass_mode: "always"

branches:
  - snapshot:
      enabled: true
      need_pr: false
      pre_release: "only"
      descriptor_build_offset: "100200000000000"
      ruleset:
        enabled: false
  - R1-2025:
      enabled: true
      need_pr: true
      pre_release: "false"
  - R2-2025:
      enabled: true
      need_pr: true
      pre_release: "false"
      ruleset:
        required_checks:
          - context: "eureka-ci / validate-application"
          - context: "eureka-ci / release-validation"
        merge_queue:
          check_response_timeout_minutes: 120
```

### Custom Status Checks Per Branch

```yaml
update_config:
  enabled: true
  ruleset:
    required_checks:
      - context: "eureka-ci / validate-application"

branches:
  - main:
      enabled: true
      need_pr: true
      ruleset:
        required_checks:
          - context: "eureka-ci / validate-application"
          - context: "build / compile"
          - context: "test / unit-tests"
```

### Disable Merge Queue for Specific Branch

```yaml
branches:
  - hotfix:
      enabled: true
      need_pr: true
      ruleset:
        merge_queue:
          enabled: false  # Allow direct merges without queue
```

## Configuration Inheritance

Global `update_config.ruleset` settings are merged with per-branch `ruleset` overrides. Per-branch values take precedence over global values.

## Related Documentation

- **[Branch Ruleset Automation](branch-ruleset-automation.md)**: Workflow that applies rulesets
- **[Branch Ruleset Management Action](../actions/branch-ruleset-management/README.md)**: Action for ruleset operations

---

**Last Updated**: March 2026
**Schema Version**: 3.0
