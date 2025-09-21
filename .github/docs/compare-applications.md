# Compare Application Versions Workflow

**Workflow**: `compare-applications.yml`
**Purpose**: Compares application descriptors between different branches or artifacts to identify module version differences
**Type**: Reusable workflow (`workflow_call`)

## 🎯 Overview

This workflow provides a sophisticated comparison mechanism for FOLIO application descriptors. It can compare versions between different git branches or between a branch and an artifact, making it essential for understanding what changes would be introduced by application updates. The workflow generates detailed reports of module version differences, new modules, removed modules, and overall change detection.

## 📋 Workflow Interface

### Inputs

| Input          | Description                                                | Required  | Type   | Default                         |
|----------------|------------------------------------------------------------|-----------|--------|---------------------------------|
| `repo`         | Repository (org/repo format)                               | Yes       | string | -                               |
| `base_branch`  | Base branch to compare against                             | Yes       | string | -                               |
| `head_branch`  | Head branch to compare (optional if using artifact)        | No        | string | `''`                            |
| `artifact_name`| Artifact name containing application descriptor (optional) | No        | string | `''`                            |
| `state_file`   | Name of the state file (application descriptor)            | No        | string | `'application-descriptor.json'` |

### Outputs

| Output           | Description                                |
|------------------|--------------------------------------------|
| `updated_modules`| List of updated modules with version info  |
| `updates_cnt`    | Number of module updates                   |
| `new_version`    | New version of the application             |
| `has_changes`    | Whether there are changes between versions |

## 🔄 Workflow Execution Flow

### 1. Repository Checkout and Base State Extraction
- **Base Branch Checkout**: Checks out the specified base branch
- **Base State Retrieval**: Extracts application descriptor from base branch
- **Version Recording**: Records base application version for comparison
- **State File Validation**: Ensures the state file exists and is valid JSON

### 2. Head State Acquisition (Dual Mode)
The workflow supports two methods for obtaining the head state:

**Artifact Mode** (when `artifact_name` is provided):
- **Artifact Download**: Downloads the specified artifact containing updated descriptor
- **State Extraction**: Extracts application descriptor from downloaded artifact
- **Validation**: Ensures the descriptor exists in the artifact

**Branch Mode** (when `head_branch` is provided):
- **Branch Fetch**: Fetches the specified head branch
- **File Checkout**: Checks out the state file from the head branch
- **State Copy**: Copies the head state for comparison

### 3. Version Comparison and Analysis
- **Module Discovery**: Identifies all modules present in either version
- **Version Extraction**: Extracts versions for each module from both states
- **Change Detection**: Compares versions and identifies differences
- **Classification**: Categorizes changes as updates, new modules, or removals

### 4. Report Generation
- **Update Formatting**: Formats module changes in human-readable format
- **Counting**: Tallies the number of changes
- **Change Detection**: Determines if any changes exist
- **Output Generation**: Creates structured outputs for downstream workflows

## 🔍 Module Comparison Logic

### Module Type Support
The workflow handles both backend and UI modules:
- **Backend Modules**: Located in `.modules[]` array
- **UI Modules**: Located in `.uiModules[]` array

### Change Detection Algorithm

```bash
# Module discovery across both states
all_modules=$(jq -r '(.modules[]?.name, .uiModules[]?.name) // empty' base_state.json head_state.json | sort -u)

# Version comparison for each module
for module in $all_modules; do
  base_ver=$(jq -r "(.modules[]? | select(.name == \"$module\") | .version) // (.uiModules[]? | select(.name == \"$module\") | .version) // \"not present\"" base_state.json)
  head_ver=$(jq -r "(.modules[]? | select(.name == \"$module\") | .version) // (.uiModules[]? | select(.name == \"$module\") | .version) // \"not present\"" head_state.json)

  # Generate change description
  if [ "$base_ver" != "$head_ver" ]; then
    # Format based on change type
  fi
done
```

### Change Format Examples

**Version Updates**:
```
mod-users: 18.0.1-SNAPSHOT.501 → 18.0.1-SNAPSHOT.525
```

**New Modules**:
```
+ mod-organizations: 1.6.3-SNAPSHOT.245 (new)
```

**Removed Modules**:
```
- mod-deprecated: 1.0.0-SNAPSHOT.100 (removed)
```

## 📊 Usage Examples

### Basic Branch Comparison

```yaml
jobs:
  compare-versions:
    uses: folio-org/kitfox-github/.github/workflows/compare-applications.yml@master
    with:
      repo: ${{ github.repository }}
      base_branch: 'master'
      head_branch: 'update-branch'
```

### Artifact vs Branch Comparison

```yaml
jobs:
  compare-with-artifact:
    uses: folio-org/kitfox-github/.github/workflows/compare-applications.yml@master
    with:
      repo: ${{ github.repository }}
      base_branch: 'R1-2025'
      artifact_name: 'updated-application-descriptor'
```

### Custom State File

```yaml
jobs:
  compare-custom:
    uses: folio-org/kitfox-github/.github/workflows/compare-applications.yml@master
    with:
      repo: ${{ github.repository }}
      base_branch: 'main'
      head_branch: 'development'
      state_file: 'app-descriptor.json'
```

### Release Preparation Workflow Integration

```yaml
jobs:
  update-application:
    uses: ./.github/workflows/update-application.yml
    with:
      app_name: ${{ github.event.repository.name }}
      repo: ${{ github.repository }}
      branch: 'update-branch'

  compare-changes:
    needs: update-application
    uses: ./.github/workflows/compare-applications.yml
    with:
      repo: ${{ github.repository }}
      base_branch: 'R1-2025'
      artifact_name: '${{ github.event.repository.name }}-update-files'

  create-pr:
    needs: [update-application, compare-changes]
    if: needs.compare-changes.outputs.has_changes == 'true'
    # Create PR with comparison results
```

## 🔍 Features

### Comprehensive Module Tracking
- **Full Coverage**: Tracks both backend modules and UI modules
- **Version History**: Maintains complete version change history
- **Change Attribution**: Clearly identifies what changed and how

### Flexible Input Sources
- **Branch Comparison**: Direct comparison between git branches
- **Artifact Integration**: Compare against workflow artifacts
- **State File Flexibility**: Configurable state file names

### Detailed Output Format
- **Human Readable**: Formatted change descriptions
- **Machine Parsable**: Structured JSON outputs
- **Change Metrics**: Quantitative change information

### Error Handling
- **State File Validation**: Ensures valid JSON and required fields
- **Branch Existence**: Validates branch availability
- **Artifact Validation**: Confirms artifact contents
- **Graceful Failures**: Clear error messages for troubleshooting

## 🛡️ Error Handling

### Common Issues

**State File Not Found**:
```
Error: State file not found in base branch
Solution: Ensure application-descriptor.json exists in the base branch
```

**Invalid JSON**:
```
Error: Invalid JSON in state file
Solution: Validate JSON syntax in application descriptor
```

**Artifact Missing**:
```
Error: State file not found in artifact
Solution: Ensure the artifact contains the expected state file
```

**Branch Access**:
```
Error: Branch not found
Solution: Verify branch name and repository access permissions
```

## 🧪 Testing Strategy

### Test Scenarios

**No Changes**:
- Base and head versions are identical
- Expected: `has_changes: false`, `updates_cnt: 0`

**Version Updates**:
- Modules have different versions between base and head
- Expected: Detailed update list with version transitions

**Module Addition**:
- New modules present in head but not in base
- Expected: Addition markers in output

**Module Removal**:
- Modules present in base but not in head
- Expected: Removal markers in output

### Validation Checklist

- [ ] State file exists in base branch
- [ ] State file is valid JSON
- [ ] Head source (branch or artifact) is accessible
- [ ] Module arrays are properly structured
- [ ] Version fields are present and valid

## 📈 Performance Considerations

### Optimization Features
- **Efficient Module Discovery**: Single pass through both states
- **Minimal Checkouts**: Only retrieves necessary files
- **Memory Efficient**: Streams large descriptor files
- **Fast Comparison**: Optimized jq queries for version extraction

### Resource Usage
- **Checkout Overhead**: Minimal - only state files
- **Memory Usage**: Low - processes one module at a time
- **Network Calls**: Minimal - only for branch/artifact retrieval

## 🔄 Integration Patterns

### Release Workflow Integration

```yaml
jobs:
  scan-for-updates:
    uses: ./.github/workflows/update-application.yml
    # ... update configuration

  compare-with-release:
    needs: scan-for-updates
    if: needs.scan-for-updates.outputs.updated == 'true'
    uses: ./.github/workflows/compare-applications.yml
    with:
      repo: ${{ github.repository }}
      base_branch: 'R1-2025'
      artifact_name: 'updated-descriptor'

  manage-pr:
    needs: [scan-for-updates, compare-with-release]
    # Use comparison results for PR management
```

### Continuous Integration

```yaml
on:
  pull_request:
    branches: ['R*-*']

jobs:
  validate-changes:
    uses: ./.github/workflows/compare-applications.yml
    with:
      repo: ${{ github.repository }}
      base_branch: ${{ github.base_ref }}
      head_branch: ${{ github.head_ref }}

  report-changes:
    needs: validate-changes
    if: needs.validate-changes.outputs.has_changes == 'true'
    # Post PR comment with change summary
```

## 🔍 Troubleshooting

### Debug Information

**Enable Verbose Logging**:
```yaml
- name: Compare with debug
  env:
    ACTIONS_STEP_DEBUG: true
  uses: ./.github/workflows/compare-applications.yml
```

**Manual Validation**:
```bash
# Check state file manually
jq '.' application-descriptor.json

# Validate module structure
jq '.modules[].name, .uiModules[].name' application-descriptor.json
```

### Common Resolution Steps

1. **Verify Repository Access**: Ensure workflow has read access to repository
2. **Check Branch Names**: Confirm branch names are spelled correctly
3. **Validate State File**: Ensure JSON syntax and required structure
4. **Artifact Contents**: Verify artifact contains expected files
5. **Permissions**: Confirm workflow has necessary repository permissions

## 📚 Related Documentation

- **[Release Update Flow](release-update-flow.md)**: Comprehensive release update workflow
- **[Application Update](app-update.md)**: Main application update workflow
- **[Commit Application Changes](commit-application-changes.md)**: Change commitment workflow

---

**Last Updated**: September 2025
**Workflow Version**: 1.0
**Compatibility**: All FOLIO application repositories