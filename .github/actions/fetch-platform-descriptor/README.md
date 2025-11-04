# Fetch Platform Descriptor Action

**Action**: `fetch-platform-descriptor`
**Purpose**: Fetches platform descriptor from the platform-lsp repository for application validation
**Type**: Composite action

## 🎯 Overview

This action fetches the platform descriptor from the platform-lsp repository for a specific branch. The platform descriptor contains the list of applications and their versions required for a platform release, which is used to validate application dependencies during the update process.

The action can optionally upload the descriptor as an artifact for use in subsequent jobs or simply return the path to the fetched file for use within the same job.

## 📋 Action Interface

### Inputs

| Input             | Description                               | Required   | Default   |
|-------------------|-------------------------------------------|------------|-----------|
| `branch`          | Branch to fetch platform descriptor from  | Yes        | -         |
| `upload_artifact` | Whether to upload descriptor as artifact  | No         | `'false'` |

### Outputs

| Output             | Description                                             |
|--------------------|---------------------------------------------------------|
| `platform_found`   | Whether platform descriptor was found (`true`/`false`)  |
| `descriptor_path`  | Path to the fetched platform descriptor file            |

## 🔄 How It Works

### Fetching Process

1. **Creates temporary directory** using `mktemp -d`
2. **Fetches descriptor** from platform-lsp repository via GitHub raw content URL
3. **Validates response** by checking HTTP status code
4. **Sets outputs** with platform found status and file path
5. **Optionally uploads** as artifact if requested

### URL Structure

```
https://raw.githubusercontent.com/folio-org/platform-lsp/{branch}/platform-descriptor.json
```

## 📊 Usage Examples

### Within Same Job (Recommended)

```yaml
jobs:
  verify-application:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Fetch Platform Descriptor
        id: fetch-platform
        uses: folio-org/kitfox-github/.github/actions/fetch-platform-descriptor@master
        with:
          branch: 'snapshot'
          upload_artifact: 'false'

      - name: Validate Application
        if: steps.fetch-platform.outputs.platform_found == 'true'
        uses: folio-org/kitfox-github/.github/actions/validate-application@master
        with:
          app_name: ${{ github.event.repository.name }}
          app_descriptor_file: 'application-descriptor.json'
          platform_descriptor_path: ${{ steps.fetch-platform.outputs.descriptor_path }}
          far_url: ${{ vars.FAR_URL }}
```

### With Artifact Upload (Cross-Job)

```yaml
jobs:
  fetch-platform:
    runs-on: ubuntu-latest
    outputs:
      platform_found: ${{ steps.fetch.outputs.platform_found }}
    steps:
      - name: Fetch Platform Descriptor
        id: fetch
        uses: folio-org/kitfox-github/.github/actions/fetch-platform-descriptor@master
        with:
          branch: 'R1-2025'
          upload_artifact: 'true'

  validate:
    needs: fetch-platform
    if: needs.fetch-platform.outputs.platform_found == 'true'
    runs-on: ubuntu-latest
    steps:
      - name: Download Platform Descriptor
        uses: actions/download-artifact@v4
        with:
          name: platform-descriptor
          path: /tmp/platform-descriptor

      - name: Validate Application
        uses: folio-org/kitfox-github/.github/actions/validate-application@master
        with:
          app_name: ${{ github.event.repository.name }}
          app_descriptor_file: 'application-descriptor.json'
          far_url: ${{ vars.FAR_URL }}
```

### With Conditional Validation

```yaml
- name: Fetch Platform Descriptor
  id: fetch-platform
  uses: folio-org/kitfox-github/.github/actions/fetch-platform-descriptor@master
  with:
    branch: ${{ inputs.branch }}

- name: Validate with Platform
  if: steps.fetch-platform.outputs.platform_found == 'true'
  run: |
    echo "Platform descriptor found, performing full validation"
    # Use platform descriptor for comprehensive validation

- name: Validate without Platform
  if: steps.fetch-platform.outputs.platform_found != 'true'
  run: |
    echo "Platform descriptor not found, performing basic validation only"
    # Perform validation without platform context
```

## 🔍 Features

### Temporary File Management
- **Auto-cleanup**: Temporary files are cleaned up by the runner after job completion
- **Unique paths**: Each invocation gets a unique temporary directory
- **No conflicts**: Safe for parallel execution

### Workspace Compatibility
- **Same-job usage**: File path works within the same job
- **Artifact support**: Can upload for cross-job access
- **Flexible patterns**: Supports both local and distributed workflows

### Error Handling
- **Graceful degradation**: Returns `platform_found=false` instead of failing
- **HTTP validation**: Checks response codes before processing
- **Clear status**: Boolean output makes conditional logic simple

## 🛡️ Error Scenarios

### Platform Descriptor Not Found

**Scenario**: Branch doesn't have platform-descriptor.json

**Behavior**:
```yaml
outputs:
  platform_found: 'false'
  descriptor_path: ''
```

**Usage**:
```yaml
- name: Validate
  if: steps.fetch.outputs.platform_found == 'true'
  # Only runs if platform was found
```

### Network Issues

**Scenario**: GitHub raw content unavailable

**Behavior**: HTTP error code captured, `platform_found=false`

**Recovery**: Workflow continues without platform validation

### Invalid JSON

**Scenario**: Platform descriptor exists but is malformed

**Behavior**: File is fetched, validation happens downstream

**Handling**: validate-application action will catch JSON errors

## 📈 Performance Considerations

### Optimizations

- **Direct fetch**: No git clone needed
- **Small file**: Platform descriptors are typically < 100KB
- **Cached**: GitHub serves raw content efficiently
- **Temporary storage**: No repository pollution

### Resource Usage

- **Network**: Single HTTP request
- **Storage**: Temporary directory (auto-cleaned)
- **Time**: Typically < 2 seconds
- **Cost**: Negligible (free tier compatible)

## 🧪 Branch Support

### Snapshot Branch
```yaml
- uses: folio-org/kitfox-github/.github/actions/fetch-platform-descriptor@master
  with:
    branch: 'snapshot'
```

### Release Branches
```yaml
- uses: folio-org/kitfox-github/.github/actions/fetch-platform-descriptor@master
  with:
    branch: 'R1-2025'
```

### Custom Branches
```yaml
- uses: folio-org/kitfox-github/.github/actions/fetch-platform-descriptor@master
  with:
    branch: ${{ inputs.platform_branch }}
```

## 🔗 Integration Points

### With Validate Application Action

The primary use case is providing platform context to validation:

```yaml
- name: Fetch Platform Descriptor
  id: fetch-platform
  uses: folio-org/kitfox-github/.github/actions/fetch-platform-descriptor@master
  with:
    branch: ${{ inputs.branch }}

- name: Validate Application
  uses: folio-org/kitfox-github/.github/actions/validate-application@master
  with:
    app_name: ${{ inputs.app_name }}
    app_descriptor_file: 'application-descriptor.json'
    platform_descriptor_path: ${{ steps.fetch-platform.outputs.descriptor_path }}
    far_url: ${{ vars.FAR_URL }}
```

### With Application Update Flow

Integrated into the update flow for dependency validation:

```yaml
jobs:
  verify-application:
    runs-on: ubuntu-latest
    steps:
      - name: Fetch Platform Descriptor
        id: fetch-platform
        if: ${{ !inputs.rely_on_FAR }}
        uses: folio-org/kitfox-github/.github/actions/fetch-platform-descriptor@master
        with:
          branch: ${{ inputs.branch }}
          upload_artifact: 'false'

      - name: Validate Application
        uses: folio-org/kitfox-github/.github/actions/validate-application@master
        with:
          platform_descriptor_path: ${{ steps.fetch-platform.outputs.descriptor_path }}
          rely_on_FAR: ${{ inputs.rely_on_FAR }}
          # ... other inputs
```

## 📚 Related Actions

- **[validate-application](../validate-application/README.md)**: Uses platform descriptor for validation
- **[get-update-config](../get-update-config/README.md)**: Provides branch configuration
- **[publish-app-descriptor](../publish-app-descriptor/README.md)**: Publishes validated descriptors

## 🔍 Troubleshooting

### Platform Not Found

```
Output: platform_found=false
```

**Possible Causes**:
- Branch doesn't exist in platform-lsp repository
- Branch doesn't have platform-descriptor.json file
- Typo in branch name

**Solutions**:
- Verify branch exists: `https://github.com/folio-org/platform-lsp/tree/{branch}`
- Check for platform-descriptor.json in branch
- Ensure branch name matches exactly (case-sensitive)

### Path Not Accessible

```
Error: File not found at {descriptor_path}
```

**Cause**: Trying to use path in different job

**Solution**: Either use within same job or set `upload_artifact: 'true'` and download in subsequent job

### Empty Descriptor Path

```
Output: descriptor_path=""
```

**Cause**: Platform not found (normal behavior)

**Solution**: Check `platform_found` output before using path

---

**Last Updated**: November 2025
**Action Version**: 1.0
**Compatibility**: All FOLIO application repositories