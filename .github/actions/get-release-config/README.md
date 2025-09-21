# Get Release Configuration Action

A GitHub Action that reads and parses release configuration from a `release-config.yml` file in a repository. This action validates configuration settings, checks for existing release branches, and provides structured outputs for release automation workflows.

## Features

- **Configuration File Discovery**: Automatically locates and reads `release-config.yml` files
- **Branch Validation**: Verifies that configured release branches actually exist in the repository
- **Flexible Configuration**: Supports custom config file paths and branch references
- **Structured Outputs**: Provides JSON arrays and maps for easy consumption by other workflow steps
- **Default Handling**: Gracefully handles missing configuration files with sensible defaults
- **Cross-Repository Support**: Can read configuration from any accessible repository

## Usage

### Basic Usage

```yaml
- name: Get Release Configuration
  uses: ./.github/actions/get-release-config
  with:
    repo: 'folio-org/platform-complete'
```

### With Custom Configuration

```yaml
- name: Get Release Configuration
  uses: ./.github/actions/get-release-config
  with:
    repo: 'my-org/my-repo'
    branch: 'develop'
    config_file: '.github/custom-release-config.yml'
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

### Cross-Repository Configuration

```yaml
- name: Get Release Configuration from Template Repo
  uses: ./.github/actions/get-release-config
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
| `config_file`  | No         | `.github/release-config.yml`                  | Path to the configuration file within the repository            |
| `github_token` | No         | `${{ github.token }}`                         | GitHub token for API access (needs repository read permissions) |

## Outputs

| Output                | Description                                                              |
|-----------------------|--------------------------------------------------------------------------|
| `enabled`             | Whether release scanning is enabled (`true`/`false`)                     |
| `release_branches`    | JSON array of existing release branches (e.g., `["r1.0", "r2.0"]`)       |
| `branch_count`        | Number of existing release branches (integer)                            |
| `pr_reviewers`        | Comma-separated list of PR reviewers                                     |
| `pr_labels`           | Comma-separated list of PR labels                                        |
| `update_branches_map` | JSON map of release branches to their corresponding update branches      |
| `config_exists`       | Whether the configuration file exists in the repository (`true`/`false`) |

## Configuration File Format

The `release-config.yml` file should follow this structure:

```yaml
# Release scanning configuration
scan_config:
  enabled: true
  pr_reviewers:
    - "reviewer1"
    - "reviewer2"
  labels:
    - "release-update"
    - "automated"
  update_branch_format: "release-update/{0}"

# List of release branches to monitor
release_branches:
  - "r1.0"
  - "r2.0"
  - "r3.0"
```

### Configuration Options

#### `scan_config` Section

- **`enabled`**: Boolean flag to enable/disable release scanning
- **`pr_reviewers`**: Array of GitHub usernames to assign as PR reviewers
- **`labels`**: Array of labels to apply to generated PRs
- **`update_branch_format`**: Template for update branch names (use `{0}` as placeholder for release branch name)

#### `release_branches` Section

- Array of release branch names to monitor and process
- Only existing branches will be included in the outputs
- Non-existent branches are logged as warnings but don't cause failures

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

      - name: Get Release Configuration
        id: config
        uses: ./.github/actions/get-release-config
        with:
          repo: ${{ github.repository }}
          branch: ${{ github.ref_name }}

      - name: Process Release Branches
        if: steps.config.outputs.enabled == 'true' && steps.config.outputs.branch_count > 0
        env:
          RELEASE_BRANCHES: ${{ steps.config.outputs.release_branches }}
          UPDATE_BRANCHES_MAP: ${{ steps.config.outputs.update_branches_map }}
        run: |
          echo "Found ${{ steps.config.outputs.branch_count }} release branches to process"
          echo "Release branches: $RELEASE_BRANCHES"
          echo "Update branches mapping: $UPDATE_BRANCHES_MAP"

          # Process each release branch
          for branch in $(echo '${{ steps.config.outputs.release_branches }}' | jq -r '.[]'); do
            echo "Processing release branch: $branch"
            # Add your release processing logic here
          done

      - name: Handle Disabled or Missing Configuration
        if: steps.config.outputs.enabled != 'true'
        run: |
          if [ "${{ steps.config.outputs.config_exists }}" == "false" ]; then
            echo "No release configuration found - using defaults"
          else
            echo "Release scanning is disabled in configuration"
          fi
```

### Matrix Strategy Example

```yaml
strategy:
  matrix:
    include: ${{ fromJson(steps.config.outputs.release_branches) }}

steps:
  - name: Get Release Configuration
    id: config
    uses: ./.github/actions/get-release-config
    with:
      repo: ${{ github.repository }}

  - name: Process Branch
    env:
      RELEASE_BRANCH: ${{ matrix }}
      UPDATE_BRANCHES_MAP: ${{ steps.config.outputs.update_branches_map }}
    run: |
      update_branch=$(echo '${{ steps.config.outputs.update_branches_map }}' | jq -r '.["${{ matrix }}"]')
      echo "Processing: $RELEASE_BRANCH -> $update_branch"
```

### Conditional PR Creation Example

```yaml
- name: Get Release Configuration
  id: config
  uses: ./.github/actions/get-release-config
  with:
    repo: ${{ github.repository }}

- name: Create Release Update PR
  if: steps.config.outputs.enabled == 'true' && steps.config.outputs.branch_count > 0
  uses: ./.github/actions/create-pr
  with:
    source_branch: 'release-updates'
    target_branch: ${{ github.ref_name }}
    pr_title: 'Release Updates for Multiple Branches'
    pr_body: |
      ## Automated Release Updates

      This PR contains updates for the following release branches:
      ${{ steps.config.outputs.release_branches }}

      **Configuration Details:**
      - Total branches: ${{ steps.config.outputs.branch_count }}
      - Auto-reviewers: ${{ steps.config.outputs.pr_reviewers }}
      - Labels: ${{ steps.config.outputs.pr_labels }}
    pr_reviewers: ${{ steps.config.outputs.pr_reviewers }}
    pr_labels: ${{ steps.config.outputs.pr_labels }}
```

## Behavior

### Configuration File Discovery

1. **Attempts to fetch** the configuration file from the specified repository and branch
2. **If file exists**: Downloads and parses the YAML content
3. **If file missing**: Uses default values and sets `config_exists=false`
4. **Validates YAML**: Ensures proper structure and data types

### Branch Existence Validation

1. **Reads configured branches** from the `release_branches` array
2. **Validates each branch** by checking if it exists in the repository via GitHub API
3. **Filters results** to include only existing branches in outputs
4. **Logs warnings** for non-existent branches without failing the action

### Output Generation

1. **Processes boolean values** (converts to lowercase strings for consistent comparison)
2. **Generates JSON arrays** for branch lists and structured data
3. **Creates mapping objects** for branch-to-update-branch relationships
4. **Handles empty states** gracefully with appropriate default values

## Default Values

When no configuration file exists or values are missing:

- `enabled`: `false`
- `release_branches`: `[]` (empty array)
- `branch_count`: `0`
- `pr_reviewers`: `""` (empty string)
- `pr_labels`: `""` (empty string)
- `update_branches_map`: `{}` (empty object)

## Requirements

### Permissions

The GitHub token must have the following permissions:

- **Repository read access**: To fetch the configuration file
- **Contents read**: To access file contents via the GitHub API
- **Metadata read**: To check branch existence

### Repository Structure

- **Configuration file**: Must be valid YAML format
- **Branch references**: Release branches should exist in the repository
- **File location**: Configuration file must be accessible at the specified path

## Troubleshooting

### Common Issues

#### Configuration File Not Found
```
::warning::Configuration file not found: .github/release-config.yml on branch main
```
**Solutions**:
- Verify the configuration file exists at the specified path
- Check that the branch name is correct
- Ensure the GitHub token has repository read permissions
- Verify the repository name format is correct (`org/repo`)

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
::warning::No existing release branches found to scan
```
**Solutions**:
- Verify that the configured branches actually exist
- Check the `release_branches` array in your configuration
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
scan_config:
  enabled: true
  pr_reviewers:
    - "user1"
    - "user2"
  labels:
    - "release"
    - "automated"

release_branches:
  - "r1.0"
  - "r2.0"

# ❌ Incorrect format
scan_config:
  enabled: yes  # Should be true/false
  pr_reviewers: "user1,user2"  # Should be array
  labels: release  # Should be array

release_branches: "r1.0,r2.0"  # Should be array
```

## Related Actions

- **[create-pr](../create-pr/README.md)**: Create pull requests using the configuration outputs
- **[update-pr](../update-pr/README.md)**: Update PRs with reviewers and labels from configuration
- **[generate-application-descriptor](../generate-application-descriptor/README.md)**: Generate descriptors for release branches

## Integration Examples

### With Release Automation

```yaml
- name: Get Release Configuration
  id: config
  uses: ./.github/actions/get-release-config
  with:
    repo: ${{ github.repository }}

- name: Generate Matrix
  id: matrix
  if: steps.config.outputs.enabled == 'true'
  run: |
    echo "matrix=$(echo '${{ steps.config.outputs.release_branches }}' | jq -c '{branch: .}')" >> "$GITHUB_OUTPUT"

  # Use in a matrix strategy
strategy:
  matrix: ${{ fromJson(steps.matrix.outputs.matrix) }}
```

### With Multi-Repository Workflows

```yaml
- name: Get Template Configuration
  uses: ./.github/actions/get-release-config
  with:
    repo: 'folio-org/platform-template'
    branch: 'main'
    config_file: '.github/shared-release-config.yml'
    github_token: ${{ secrets.GITHUB_TOKEN }}
```