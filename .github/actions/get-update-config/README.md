# Get Update Configuration Action

A GitHub Action that reads and parses update configuration from an `update-config.yml` file in a repository. This action validates configuration settings, checks for existing update branches, and provides structured outputs for update automation workflows.

## Features

- **Configuration File Discovery**: Automatically locates and reads `update-config.yml` files
- **Branch Validation**: Verifies that configured update branches actually exist in the repository
- **Flexible Configuration**: Supports custom config file paths and branch references
- **Structured Outputs**: Provides JSON arrays and maps for easy consumption by other workflow steps
- **Default Handling**: Gracefully handles missing configuration files with sensible defaults
- **Resilient API Calls**: Retries transient GitHub API failures (HTTP 429/5xx, network) with backoff. A genuine `404` is treated as "not found"; a transient failure that persists fails the step instead of silently assuming the resource is absent
- **Cross-Repository Support**: Can read configuration from any accessible repository

## Usage

### Basic Usage

```yaml
- name: Get Update Configuration
  uses: ./.github/actions/get-update-config
  with:
    repo: 'folio-org/platform-complete'
```

### With Custom Configuration

```yaml
- name: Get Update Configuration
  uses: ./.github/actions/get-update-config
  with:
    repo: 'my-org/my-repo'
    branch: 'develop'
    config_file: '.github/custom-release-config.yml'
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

### Cross-Repository Configuration

```yaml
- name: Get Update Configuration from Template Repo
  uses: ./.github/actions/get-update-config
  with:
    repo: 'folio-org/platform-template'
    branch: 'main'
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

## Inputs

| Input          | Required   | Default                                       | Description                                                     |
|----------------|------------|-----------------------------------------------|-----------------------------------------------------------------|
| `repo`         | Yes        | -                                             | Repository in `org/repo` format to read configuration from      |
| `branch`       | No         | `${{ github.base_ref \|\| github.ref_name }}` | Branch where the configuration file resides                     |
| `config_file`  | No         | `.github/update-config.yml`                   | Path to the configuration file within the repository            |
| `github_token` | No         | `${{ github.token }}`                         | GitHub token for API access (needs repository read permissions) |

## Outputs

| Output          | Description                                                                                       |
|-----------------|---------------------------------------------------------------------------------------------------|
| `enabled`       | Whether update scanning is enabled (`true`/`false`)                                              |
| `branches`      | JSON array of enabled branch names (e.g., `["snapshot", "R1-2025"]`)                             |
| `branch_count`  | Number of enabled branches (integer)                                                              |
| `pr_reviewers`  | Comma-separated list of PR reviewers                                                              |
| `pr_labels`     | Comma-separated list of PR labels                                                                 |
| `branch_config` | JSON array of branch configuration objects with all branch-specific settings                     |
| `config_exists` | Whether the configuration file exists in the repository (`true`/`false`)                          |

### `branch_config` Structure

The `branch_config` output provides a JSON array of objects, each containing:

```json
[
  {
    "branch": "snapshot",
    "update_branch": null,
    "need_pr": false,
    "pre_release": "only",
    "descriptor_build_offset": "100100000000000",
    "rely_on_FAR": false,
    "ruleset": {
      "enabled": false,
      "pattern": "{0}-eureka-ci",
      "required_checks": [{"context": "eureka-ci / validate-application", "integration_id": null}],
      "merge_queue": {
        "enabled": true,
        "check_response_timeout_minutes": 300,
        "grouping_strategy": "ALLGREEN",
        "max_entries_to_build": 1,
        "max_entries_to_merge": 1,
        "merge_method": "SQUASH",
        "min_entries_to_merge": 1,
        "min_entries_to_merge_wait_minutes": 5
      },
      "bypass_actors": [{"actor_id": null, "actor_type": "Integration", "bypass_mode": "always"}]
    }
  },
  {
    "branch": "R1-2025",
    "update_branch": "version-update/R1-2025",
    "need_pr": true,
    "pre_release": "false",
    "descriptor_build_offset": "",
    "rely_on_FAR": false,
    "ruleset": {
      "enabled": true,
      "pattern": "{0}-eureka-ci",
      "required_checks": [{"context": "eureka-ci / validate-application", "integration_id": null}],
      "merge_queue": {
        "enabled": true,
        "check_response_timeout_minutes": 60,
        "grouping_strategy": "ALLGREEN",
        "max_entries_to_build": 5,
        "max_entries_to_merge": 5,
        "merge_method": "SQUASH",
        "min_entries_to_merge": 1,
        "min_entries_to_merge_wait_minutes": 5
      },
      "bypass_actors": [{"actor_id": null, "actor_type": "Integration", "bypass_mode": "always"}]
    }
  }
]
```

The `ruleset` object is always fully resolved: every key is present even when the config file sets none of
them. `integration_id` and `actor_id` stay `null` here and are resolved downstream by
`branch-ruleset-management` from its `integration_id` input.

The `snapshot` entry above illustrates the two independent switches. `ruleset.enabled: false` means no
ruleset is applied to the branch, while the `merge_queue` block is fully resolved regardless — it carries
per-branch overrides (`check_response_timeout_minutes`, `max_entries_to_build`, `max_entries_to_merge`)
merged over the global block, ready for the day the branch is switched on.

## Configuration File Format

The `update-config.yml` file should follow this structure:

```yaml
# Application version update configuration
update_config:
  enabled: true
  pr_reviewers:
    - "org/team-name"
    - "username"
  labels:
    - "version-update"
    - "automated"
  update_branch_format: "version-update/{0}"
  ruleset:
    enabled: true
    pattern: "{0}-eureka-ci"
    required_checks:
      - context: "eureka-ci / validate-application"
    merge_queue:
      enabled: true
    bypass_actors:
      - actor_type: "Integration"
        bypass_mode: "always"

# List of branches to monitor with branch-specific settings
branches:
  - snapshot:
      enabled: true
      need_pr: false
      pre_release: "only"
      descriptor_build_offset: "100100000000000"
      rely_on_FAR: false
      ruleset:
        enabled: false
  - R1-2025:
      enabled: true
      need_pr: true
      pre_release: "false"
      descriptor_build_offset: ""
      rely_on_FAR: false
  - R2-2025:
      enabled: false
      need_pr: true
      pre_release: "false"
```

### Configuration Options

#### `update_config` Section

- **`enabled`**: Boolean flag to enable/disable version update scanning
- **`pr_reviewers`**: Array of GitHub usernames or teams to assign as PR reviewers
- **`labels`**: Array of labels to apply to generated PRs
- **`update_branch_format`**: Template for update branch names (use `{0}` as placeholder for branch name)
- **`ruleset`**: Global branch ruleset configuration. Rulesets are opt-in: the built-in default is `enabled: false`, so a repository with no `ruleset` section gets none. A global block may set `enabled: true` and a branch may still override it back to `false`. See [update-config.md](../../docs/update-config.md) for full schema

#### `branches` Section

- Array of branch objects with per-branch configuration
- Each branch object has a single key (branch name) with metadata:
  - **`enabled`**: Whether to scan this branch (default: `true`)
  - **`need_pr`**: Whether to create a PR or update directly (default: `true`)
    - When `true`: Creates update branch and PR
    - When `false`: Commits directly to the branch (no PR)
  - **`pre_release`**: Module version filter mode (default: `"false"`)
    - `"only"`: Snapshot-only modules (e.g., `1.2.3-SNAPSHOT`)
    - `"true"`: Both release and snapshot modules
    - `"false"`: Release-only modules (e.g., `1.2.3`)
  - **`descriptor_build_offset`**: Offset for application artifact version (default: `""`)
  - **`rely_on_FAR`**: Whether to rely on FAR for validation dependencies (default: `false`)
  - **`skip_interface_validation`**: Skip module interface integrity validation (default: `false`)
  - **`skip_dependency_validation`**: Dependency validation mode: `false` / `true` / `bypass` (default: `false`)
  - **`publish`**: Publish the descriptor to FAR after validation (default: `true`)
  - **`release`**: Create a GitHub release after the PR merges (default: `true`)
  - **`name`** / **`description`**: Human-readable branch metadata (platform repositories)
  - **`ruleset`**: Per-branch ruleset overrides. Resolution is three layers deep-merged in order —
    built-in defaults, then `update_config.ruleset`, then this block. Objects merge key by key; **arrays
    (`required_checks`, `bypass_actors`) are replaced wholesale**, so a branch-level list discards the
    inherited one
- Only existing and enabled branches will be included in outputs
- Disabled or non-existent branches are logged as warnings. A disabled branch is skipped before its ruleset
  is resolved, so any existing ruleset is left untouched rather than disabled

## Examples

### Complete Workflow Example

```yaml
name: Release Branch Scanning

on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM
  workflow_dispatch:

jobs:
  scan-releases:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Get Update Configuration
        id: config
        uses: ./.github/actions/get-update-config
        with:
          repo: ${{ github.repository }}
          branch: ${{ github.ref_name }}

      - name: Process Branches
        if: steps.config.outputs.enabled == 'true' && steps.config.outputs.branch_count > 0
        env:
          BRANCHES: ${{ steps.config.outputs.branches }}
          BRANCH_CONFIG: ${{ steps.config.outputs.branch_config }}
        run: |
          echo "Found ${{ steps.config.outputs.branch_count }} branches to process"
          echo "Branches: $BRANCHES"
          echo "Branch configuration: $BRANCH_CONFIG"

          # Process each branch with its configuration
          echo "$BRANCH_CONFIG" | jq -c '.[]' | while read -r branch_cfg; do
            branch=$(echo "$branch_cfg" | jq -r '.branch')
            pre_release=$(echo "$branch_cfg" | jq -r '.pre_release')
            echo "Processing branch: $branch (pre_release=$pre_release)"
            # Add your processing logic here
          done

      - name: Handle Disabled or Missing Configuration
        if: steps.config.outputs.enabled != 'true'
        run: |
          if [ "${{ steps.config.outputs.config_exists }}" == "false" ]; then
            echo "No update configuration found - using defaults"
          else
            echo "Update scanning is disabled in configuration"
          fi
```

### Matrix Strategy Example

```yaml
jobs:
  get-config:
    runs-on: ubuntu-latest
    outputs:
      branch_config: ${{ steps.config.outputs.branch_config }}
      branch_count: ${{ steps.config.outputs.branch_count }}
      pr_reviewers: ${{ steps.config.outputs.pr_reviewers }}
      pr_labels: ${{ steps.config.outputs.pr_labels }}
    steps:
      - name: Get Update Configuration
        id: config
        uses: ./.github/actions/get-update-config
        with:
          repo: ${{ github.repository }}

  update-branches:
    needs: get-config
    if: needs.get-config.outputs.branch_count > 0
    strategy:
      matrix:
        include: ${{ fromJson(needs.get-config.outputs.branch_config) }}
      fail-fast: false
      max-parallel: 3
    runs-on: ubuntu-latest
    steps:
      - name: Process Branch
        run: |
          echo "Branch: ${{ matrix.branch }}"
          echo "Pre-release: ${{ matrix.pre_release }}"
          echo "Need PR: ${{ matrix.need_pr }}"
          echo "Update branch: ${{ matrix.update_branch }}"
```

## Behavior

### Configuration File Discovery

1. **Attempts to fetch** the configuration file from the specified repository and branch, retrying transient GitHub API failures (HTTP 429/5xx, network errors) with backoff
2. **If file exists (HTTP 200)**: Downloads and parses the YAML content
3. **If file is genuinely missing (HTTP 404)**: Uses default values and sets `config_exists=false`
4. **If the API keeps failing (non-404) after retries**: Fails the step with an `::error::` so the run can be retried, instead of silently assuming the file is absent
5. **Validates YAML**: Ensures proper structure and data types

### Branch Existence Validation

1. **Reads configured branches** from the `branches` array
2. **Validates each branch** by checking if it exists in the repository via GitHub API, retrying transient failures with backoff
3. **Filters results** to include only existing branches (HTTP 200) in outputs
4. **Logs warnings** for genuinely non-existent branches (HTTP 404) without failing the action
5. **Fails the step** if a branch check keeps failing (non-404) after retries, instead of silently dropping the branch

### Output Generation

1. **Processes boolean values** (converts to lowercase strings for consistent comparison)
2. **Generates JSON arrays** for branch lists and structured data
3. **Creates mapping objects** for branch-to-update-branch relationships
4. **Handles empty states** gracefully with appropriate default values

## Default Values

When no configuration file exists or values are missing:

- `enabled`: `false`
- `branches`: `[]` (empty array)
- `branch_count`: `0`
- `pr_reviewers`: `""` (empty string)
- `pr_labels`: `""` (empty string)
- `branch_config`: `[]` (empty array)

## Requirements

### Permissions

The GitHub token must have the following permissions:

- **Repository read access**: To fetch the configuration file
- **Contents read**: To access file contents via the GitHub API
- **Metadata read**: To check branch existence

### Repository Structure

- **Configuration file**: Must be valid YAML format
- **Branch references**: Update branches should exist in the repository
- **File location**: Configuration file must be accessible at the specified path

## Troubleshooting

### Common Issues

#### Configuration File Not Found
```
::warning::Configuration file not found: .github/update-config.yml on branch main
```
**Solutions**:
- Verify the configuration file exists at the specified path
- Check that the branch name is correct
- Ensure the GitHub token has repository read permissions
- Verify the repository name format is correct (`org/repo`)

> **Note**: This warning is emitted only for a genuine `404` (the file truly does not exist).
> A transient GitHub API failure no longer produces this warning — see *Transient GitHub API Failure* below.

#### Transient GitHub API Failure (Step Failed)
```
::error::gh api repos/ORG/REPO/contents/.github/update-config.yml?ref=BRANCH failed after 3 attempts (non-404): ...
```
The action **fails** (red run) rather than silently treating a config or branch check as "not found"
when the GitHub API returns a transient error (HTTP 429/5xx or a network error) that persists after
retries. This prevents a release from being silently skipped on a false negative.

**Solutions**:
- Re-run the job — transient GitHub API errors usually clear on retry
- Check the [GitHub status page](https://www.githubstatus.com/) for an ongoing incident
- Inspect the `::error::` detail for the HTTP status returned by the API

#### Invalid YAML Format
```
Error parsing configuration file
```
**Solutions**:
- Validate the YAML syntax using a YAML validator
- Check for proper indentation and structure
- Ensure boolean values are `true`/`false` (not `yes`/`no`)
- Verify array syntax uses proper YAML formatting

#### Branch Not Found Warnings
```
::warning::  ✗ Branch not found: r1.0
```
**Solutions**:
- Check that the branch exists in the repository
- Verify branch names match exactly (case-sensitive)
- Ensure branches are not protected or hidden
- Consider if branches were renamed or deleted

#### Empty Results
```
::warning::No existing update branches found to scan
```
**Solutions**:
- Verify that the configured branches actually exist
- Check the `branches` array in your configuration
- Ensure branches are pushed to the remote repository
- Review the GitHub API response for authentication issues

### Debug Information

The action provides comprehensive logging:

- **Configuration Discovery**: Shows whether the config file was found
- **Branch Validation**: Lists each branch check with success/failure status
- **Parsed Values**: Displays all parsed configuration values
- **API Responses**: Shows GitHub API responses for debugging
- **Final Outputs**: Summarizes all output values

### Configuration Validation

Validate your configuration file structure:

```yaml
# ✅ Correct format
update_config:
  enabled: true
  pr_reviewers:
    - "user1"
    - "user2"
  labels:
    - "label1"
    - "label2"
  update_branch_format: "update/{0}"

branches:
  - branch1:
      enabled: true
      need_pr: true
  - branch2:
      enabled: false
      need_pr: false

# ❌ Incorrect format
update_config:
  enabled: yes  # Should be true/false
  pr_reviewers: "user1,user2"  # Should be array
  labels: label1  # Should be array

branches:
  - "branch1"  # Should be object with metadata
  - branch2: true  # Should have enabled/need_pr properties
```

## Related Actions

- **[create-pr](../create-pr/README.md)**: Create pull requests using the configuration outputs
- **[update-pr](../update-pr/README.md)**: Update PRs with reviewers and labels from configuration
- **[generate-application-descriptor](../generate-application-descriptor/README.md)**: Generate descriptors for update branches

## Integration Examples

### With Unified Application Update Workflow

```yaml
jobs:
  get-config:
    runs-on: ubuntu-latest
    outputs:
      branch_config: ${{ steps.get-update-config.outputs.branch_config }}
      branch_count: ${{ steps.get-update-config.outputs.branch_count }}
      pr_reviewers: ${{ steps.get-update-config.outputs.pr_reviewers }}
      pr_labels: ${{ steps.get-update-config.outputs.pr_labels }}
    steps:
      - uses: actions/checkout@v4
      - name: Get Update Configuration
        id: get-update-config
        uses: folio-org/kitfox-github/.github/actions/get-update-config@master
        with:
          repo: ${{ github.repository }}
          github_token: ${{ github.token }}

  update-branches:
    name: Update ${{ matrix.branch }}
    needs: get-config
    if: needs.get-config.outputs.branch_count > 0
    strategy:
      matrix:
        include: ${{ fromJson(needs.get-config.outputs.branch_config) }}
      fail-fast: false
      max-parallel: 3
    uses: folio-org/kitfox-github/.github/workflows/application-update.yml@master
    with:
      app_name: ${{ github.event.repository.name }}
      repo: ${{ github.repository }}
      branch: ${{ matrix.branch }}
      update_branch: ${{ matrix.update_branch }}
      need_pr: ${{ matrix.need_pr }}
      pre_release: ${{ matrix.pre_release }}
      workflow_run_number: ${{ github.run_number }}
      descriptor_build_offset: ${{ matrix.descriptor_build_offset }}
      rely_on_FAR: ${{ matrix.rely_on_FAR }}
      pr_reviewers: ${{ needs.get-config.outputs.pr_reviewers }}
      pr_labels: ${{ needs.get-config.outputs.pr_labels }}
    secrets: inherit
```

### With Multi-Repository Workflows

```yaml
- name: Get Template Configuration
  uses: folio-org/kitfox-github/.github/actions/get-update-config@master
  with:
    repo: 'folio-org/platform-template'
    branch: 'main'
    config_file: '.github/shared-release-config.yml'
    github_token: ${{ secrets.GITHUB_TOKEN }}
```