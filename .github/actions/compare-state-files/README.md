# Compare State Files Action

A composite GitHub Action for comparing application state files from different sources (artifacts or branches).

## Description

This action compares two application state files (typically `application-descriptor.json`) to detect module version changes. It supports comparing:
- Branch vs Branch
- Branch vs Artifact
- Artifact vs Branch
- Artifact vs Artifact

The action identifies added, removed, and updated modules between the two states.

## Inputs

| Name                | Description                                           | Required | Default                          |
|---------------------|-------------------------------------------------------|----------|----------------------------------|
| `repo`              | Repository name in org/repo format                    | **Yes**  | -                                |
| `base-source-type`  | Type of base source: "artifact" or "branch"           | **Yes**  | -                                |
| `base-source`       | Base source: artifact name or branch name             | **Yes**  | -                                |
| `head-source-type`  | Type of head source: "artifact" or "branch"           | **Yes**  | -                                |
| `head-source`       | Head source: artifact name or branch name             | **Yes**  | -                                |
| `state-file`        | Name of the state file (application descriptor)       | No       | `application-descriptor.json`    |
| `github-token`      | GitHub token for API access                           | **Yes**  | -                                |

## Outputs

| Name              | Description                                          |
|-------------------|------------------------------------------------------|
| `updated-modules` | List of updated modules (multiline string)           |
| `updates-cnt`     | Number of module updates                             |
| `new-version`     | New version of the application from head state       |
| `has-changes`     | Whether there are changes between versions (boolean) |

## Prerequisites

This action downloads files automatically using GitHub API and artifacts, so no repository checkout is required. For artifact comparisons, the artifact must be uploaded in a previous workflow step using `actions/upload-artifact`.

## Usage

### Compare Two Branches

```yaml
steps:
  - name: Compare Branches
    id: compare
    uses: folio-org/kitfox-github/.github/actions/compare-state-files@master
    with:
      repo: ${{ github.repository }}
      base-source-type: 'branch'
      base-source: 'R1-2024'
      head-source-type: 'branch'
      head-source: 'R2-2024'
      github-token: ${{ github.token }}

  - name: Check Results
    run: |
      echo "Has changes: ${{ steps.compare.outputs.has-changes }}"
      echo "Updates count: ${{ steps.compare.outputs.updates-cnt }}"
      echo "New version: ${{ steps.compare.outputs.new-version }}"
```

### Compare Branch vs Artifact

```yaml
steps:
  - name: Compare Branch with Artifact
    id: compare
    uses: folio-org/kitfox-github/.github/actions/compare-state-files@master
    with:
      repo: ${{ github.repository }}
      base-source-type: 'branch'
      base-source: 'R1-2024'
      head-source-type: 'artifact'
      head-source: 'app-descriptor-artifact'
      github-token: ${{ github.token }}

  - name: Display Updated Modules
    if: steps.compare.outputs.has-changes == 'true'
    run: |
      echo "Module updates:"
      echo "${{ steps.compare.outputs.updated-modules }}"
```

### Compare Two Artifacts

```yaml
steps:
  - name: Compare Artifacts
    id: compare
    uses: folio-org/kitfox-github/.github/actions/compare-state-files@master
    with:
      repo: ${{ github.repository }}
      base-source-type: 'artifact'
      base-source: 'base-app-descriptor'
      head-source-type: 'artifact'
      head-source: 'head-app-descriptor'
      github-token: ${{ github.token }}
```

### Compare Artifact vs Branch

```yaml
steps:
  - name: Compare Artifact with Branch
    id: compare
    uses: folio-org/kitfox-github/.github/actions/compare-state-files@master
    with:
      repo: ${{ github.repository }}
      base-source-type: 'artifact'
      base-source: 'snapshot-descriptor'
      head-source-type: 'branch'
      head-source: 'R1-2025'
      github-token: ${{ github.token }}
```

### Custom State File

```yaml
steps:
  - name: Compare Custom State Files
    id: compare
    uses: folio-org/kitfox-github/.github/actions/compare-state-files@master
    with:
      repo: ${{ github.repository }}
      base-source-type: 'branch'
      base-source: 'main'
      head-source-type: 'branch'
      head-source: 'develop'
      state-file: 'custom-descriptor.json'
      github-token: ${{ github.token }}
```

## Output Format

### updated-modules

A multiline string with the following format:
```
module-name: 1.0.0 → 1.1.0
+ new-module: 2.0.0 (new)
- removed-module: 1.5.0 (removed)
```

### Module Change Types

- **Updated**: `module-name: old-version → new-version`
- **Added**: `+ module-name: version (new)`
- **Removed**: `- module-name: version (removed)`

## State File Structure

The action expects JSON files with the following structure:

```json
{
  "version": "1.0.0",
  "modules": [
    {
      "name": "mod-users",
      "version": "15.3.0"
    }
  ],
  "uiModules": [
    {
      "name": "@folio/users",
      "version": "2.5.0"
    }
  ]
}
```

## Error Handling

The action will fail if:
- State file is not found in the specified branch
- State file is not found in the specified artifact
- JSON parsing fails for state files
- Git operations fail (for branch comparisons)

All errors are reported using GitHub Actions error annotations.

## Example Workflow

```yaml
name: Compare Release Branches

on:
  workflow_dispatch:
    inputs:
      base_branch:
        description: 'Base release branch'
        required: true
      head_branch:
        description: 'Head release branch'
        required: true

jobs:
  compare:
    runs-on: ubuntu-latest
    steps:
      - name: Compare Release Branches
        id: compare
        uses: folio-org/kitfox-github/.github/actions/compare-state-files@master
        with:
          repo: ${{ github.repository }}
          base-source-type: 'branch'
          base-source: ${{ inputs.base_branch }}
          head-source-type: 'branch'
          head-source: ${{ inputs.head_branch }}
          github-token: ${{ github.token }}

      - name: Create Summary
        run: |
          echo "# Comparison Results" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "**Base Branch**: ${{ inputs.base_branch }}" >> $GITHUB_STEP_SUMMARY
          echo "**Head Branch**: ${{ inputs.head_branch }}" >> $GITHUB_STEP_SUMMARY
          echo "**New Version**: ${{ steps.compare.outputs.new-version }}" >> $GITHUB_STEP_SUMMARY
          echo "**Has Changes**: ${{ steps.compare.outputs.has-changes }}" >> $GITHUB_STEP_SUMMARY
          echo "**Module Updates**: ${{ steps.compare.outputs.updates-cnt }}" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY

          if [ "${{ steps.compare.outputs.has-changes }}" = "true" ]; then
            echo "## Updated Modules" >> $GITHUB_STEP_SUMMARY
            echo '```' >> $GITHUB_STEP_SUMMARY
            echo "${{ steps.compare.outputs.updated-modules }}" >> $GITHUB_STEP_SUMMARY
            echo '```' >> $GITHUB_STEP_SUMMARY
          fi
```

## License

This action is part of the FOLIO project and follows the project's licensing terms.
