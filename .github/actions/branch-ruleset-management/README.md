# Branch Ruleset Management Action

Creates or updates GitHub branch rulesets. Accepts individual configuration parameters and handles all processing internally, including computing ruleset names, resolving integration IDs, and building rules.

## Usage

```yaml
- uses: folio-org/kitfox-github/.github/actions/branch-ruleset-management@master
  with:
    repository: owner/repo
    branch: R1-2025
    ruleset_pattern: '{0}-eureka-ci'
    required_checks: |
      [{"context": "eureka-ci / validate-application", "integration_id": null}]
    merge_queue: |
      {
        "enabled": true,
        "check_response_timeout_minutes": 60,
        "grouping_strategy": "ALLGREEN",
        "max_entries_to_build": 5,
        "max_entries_to_merge": 5,
        "merge_method": "SQUASH",
        "min_entries_to_merge": 1,
        "min_entries_to_merge_wait_minutes": 5
      }
    bypass_actors: |
      [{"actor_id": null, "actor_type": "Integration", "bypass_mode": "always"}]
    integration_id: ${{ vars.EUREKA_CI_APP_ID }}
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

## Inputs

| Input             | Required  | Default         | Description                                                        |
|-------------------|-----------|-----------------|--------------------------------------------------------------------|
| `repository`      | Yes       | -               | Repository in `owner/repo` format                                  |
| `branch`          | Yes       | -               | Target branch name                                                 |
| `ruleset_pattern` | No        | `{0}-eureka-ci` | Naming pattern for ruleset (`{0}` = branch name)                   |
| `required_checks` | No        | `[]`            | JSON array of required status checks                               |
| `merge_queue`     | No        | `{}`            | JSON object with merge queue configuration                         |
| `bypass_actors`   | No        | `[]`            | JSON array of bypass actors                                        |
| `integration_id`  | Yes       | -               | Default integration ID for null `actor_id`/`integration_id` values |
| `github_token`    | Yes       | -               | GitHub token with admin permissions                                |

## Outputs

| Output       | Description                                                 |
|--------------|-------------------------------------------------------------|
| `result`     | Operation result: `created`, `updated`, `skipped`, `failed` |
| `ruleset_id` | Ruleset ID (if created or updated)                          |
| `message`    | Human-readable result message                               |

## Configuration Details

### Required Checks

JSON array of status check objects:
```json
[
  {"context": "eureka-ci / validate-application", "integration_id": null}
]
```
Use `null` for `integration_id` to use the default from `integration_id` input.

### Merge Queue

JSON object with merge queue settings:
```json
{
  "enabled": true,
  "check_response_timeout_minutes": 60,
  "grouping_strategy": "ALLGREEN",
  "max_entries_to_build": 5,
  "max_entries_to_merge": 5,
  "merge_method": "SQUASH",
  "min_entries_to_merge": 1,
  "min_entries_to_merge_wait_minutes": 5
}
```

### Bypass Actors

JSON array of bypass actor objects:
```json
[
  {"actor_id": null, "actor_type": "Integration", "bypass_mode": "always"}
]
```
Use `null` for `actor_id` to use the default from `integration_id` input.

**Actor Types:** `Integration`, `User`, `Team`, `DeployKey`

## Example

### With Matrix (from branch_config)

```yaml
- name: Update Branch Ruleset
  uses: folio-org/kitfox-github/.github/actions/branch-ruleset-management@master
  with:
    repository: ${{ inputs.repo_owner }}/${{ inputs.repo_name }}
    branch: ${{ matrix.branch }}
    ruleset_pattern: ${{ matrix.ruleset.pattern }}
    required_checks: ${{ toJson(matrix.ruleset.required_checks) }}
    merge_queue: ${{ toJson(matrix.ruleset.merge_queue) }}
    bypass_actors: ${{ toJson(matrix.ruleset.bypass_actors) }}
    integration_id: ${{ vars.EUREKA_CI_APP_ID }}
    github_token: ${{ steps.app-token.outputs.token }}
```

## Processing

The action handles internally:
1. **Ruleset name** - Computed from pattern + branch (`{0}` → branch name)
2. **Integration ID resolution** - Replaces `null` values with the default
3. **Rules array construction** - Builds `required_status_checks` and `merge_queue` rules
4. **Branch existence check** - Skips if branch doesn't exist
5. **Create/update logic** - Creates new or updates existing ruleset
