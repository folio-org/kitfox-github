# Update Configuration Schema

**File**: `.github/update-config.yml`
**Purpose**: Configure automated module updates, PR settings, and branch rulesets

## Overview

The `update-config.yml` file controls how the Eureka CI/CD system handles module version updates for a repository. It specifies which branches to scan, how to create PRs, and how to configure branch protection rulesets.

The schema applies to every `folio-org/app-*` repository and to `folio-org/platform-lsp`. Both are wired to
`branch-ruleset-automation.yml` through the `push` event mapping in the GitHub App webhook listener.

One value is repository-specific: the required check context. Application repositories publish
`eureka-ci / validate-application` (the default), while platform-lsp publishes
`eureka-ci/release-platform-validation` and overrides `required_checks` globally. Note the differing spacing
around the slash in the two conventions — the ruleset matches on the exact string.

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
      yarn_lock_update: string
      rely_on_FAR: boolean
      skip_interface_validation: boolean
      skip_dependency_validation: string
      publish: boolean
      release: boolean
      name: string
      description: string
      ruleset: object  # Per-branch ruleset overrides
```

| Field                     | Type    | Required | Default | Description                                      |
|---------------------------|---------|----------|---------|--------------------------------------------------|
| `enabled`                 | boolean | Yes      | -       | Enable scanning for this branch                  |
| `need_pr`                 | boolean | Yes      | -       | Create PR for updates (vs direct push)           |
| `pre_release`             | string  | No       | `""`    | Filter: `"only"`, `"true"`, `"false"`            |
| `descriptor_build_offset` | string  | No       | `""`    | Build number offset for descriptors              |
| `yarn_lock_update`        | string  | No       | `"always"` | Platform `yarn.lock` policy: `"always"` (delete before `yarn install`, ranges re-resolve), `"on_package_change"` (keep; follows `package.json` pins), `"never"` |
| `rely_on_FAR`             | boolean | No       | `false` | Use FOLIO Application Registry for validation    |
| `skip_interface_validation` | boolean | No     | `false` | Skip module interface integrity validation       |
| `skip_dependency_validation`| string  | No     | `false` | Dependency validation mode: `false` / `true` / `bypass` |
| `publish`                 | boolean | No       | `true`  | Whether to publish descriptor to FAR after validation |
| `release`                 | boolean | No       | `true`  | Whether to create GitHub release after PR merge (tags, release notes) |
| `name`                    | string  | No       | `""`    | Human-readable branch name (platform repositories) |
| `description`             | string  | No       | `""`    | Human-readable branch description (platform repositories) |
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
      integration_id: null                      # resolved to EUREKA_CI_APP_ID
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
    - actor_id: null                            # resolved to EUREKA_CI_APP_ID
      actor_type: "Integration"
      bypass_mode: "always"
```

The `integration_id` and `actor_id` nulls are part of the defaults, not omissions. `branch-ruleset-management`
resolves each one to the `integration_id` input, which the flow supplies from `vars.EUREKA_CI_APP_ID`.

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

### A merge queue is incompatible with `need_pr: false`

The `merge_queue` rule requires every change to reach the branch through the queue, so it rejects the direct
push that a `need_pr: false` branch depends on. Unless the pushing identity is listed in `bypass_actors`, an
active ruleset carrying a merge queue silently breaks the update cadence for that branch.

Note that `bypass_actors` resolves to the Eureka CI App. A workflow that pushes with the default
`GITHUB_TOKEN` acts as the GitHub Actions app instead, which is *not* the bypass actor.

The two safe shapes are:

- `need_pr: false` with `ruleset.enabled: false` — direct-commit branch, no ruleset.
- `need_pr: true` with `ruleset.enabled: true` — PR-based branch, ruleset and optional queue.

Flipping a branch from one to the other means changing both keys in the same commit. `need_pr: true` without
a ruleset leaves the update PR with nothing to merge it; a ruleset without `need_pr: true` blocks the direct
commit.

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
      yarn_lock_update: "always"
      ruleset:
        enabled: false
  - R1-2025:
      enabled: true
      need_pr: true
      pre_release: "false"
      yarn_lock_update: "on_package_change"
  - R2-2025:
      enabled: true
      need_pr: true
      pre_release: "false"
      ruleset:
        required_checks:
          - context: "eureka-ci / validate-application"   # restated: the array replaces, not appends
          - context: "eureka-ci / release-validation"
        merge_queue:
          check_response_timeout_minutes: 120             # other merge_queue keys inherited
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
          - context: "eureka-ci / validate-application"   # restated: the array replaces, not appends
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

The ruleset applied to a branch is resolved in three layers, each deep-merged over the previous one:

```
RULESET_DEFAULTS  ->  update_config.ruleset  ->  branches[].ruleset
```

**Objects merge key by key; arrays are replaced wholesale.** This distinction matters and is easy to get wrong:

- `merge_queue` is an object, so a branch may override a few keys and inherit the rest. A branch that sets only
  `check_response_timeout_minutes` keeps the global `merge_method`, `grouping_strategy` and everything else.
- `required_checks` and `bypass_actors` are arrays, so any branch-level list **discards** the inherited one
  entirely. To add one check to the global set, restate every check you want to keep.

Because each layer merges over the one before it, a global block only needs the keys that differ from the
defaults, and a branch block only the keys that differ from the global block.

### Partial merge_queue override

```yaml
update_config:
  ruleset:
    enabled: true
    merge_queue:
      enabled: false                            # release branches: checks only, no queue
      merge_method: "SQUASH"
      grouping_strategy: "ALLGREEN"
      check_response_timeout_minutes: 60
      max_entries_to_build: 5
      max_entries_to_merge: 5
      min_entries_to_merge: 1
      min_entries_to_merge_wait_minutes: 5

branches:
  - snapshot:
      enabled: true
      ruleset:
        merge_queue:
          enabled: true                         # re-enable the queue for this branch only
          check_response_timeout_minutes: 300   # long-running deployment gate
          max_entries_to_build: 1               # strictly serial
          max_entries_to_merge: 1
```

`snapshot` resolves to a merge queue with `merge_method: SQUASH`, `grouping_strategy: ALLGREEN` and
`min_entries_to_merge_wait_minutes: 5` inherited from the global block, and the four overridden values applied
on top. It does not restate `required_checks`, so it inherits the global list unchanged — which is the point:
a required check is a context name, and the same name may be published by different workflows on different
events (`pull_request` and `merge_group`).

## Related Documentation

- **[Branch Ruleset Automation](branch-ruleset-automation.md)**: Workflow that applies rulesets
- **[Branch Ruleset Management Action](../actions/branch-ruleset-management/README.md)**: Action for ruleset operations

---

**Last Updated**: September 2026
**Schema Version**: 3.1
