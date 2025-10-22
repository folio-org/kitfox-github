# Generate Application Descriptor Action

A GitHub Action that generates FOLIO application descriptors from application state files (JSON format). This action validates the state file for placeholder values, generates the descriptor using Maven, and optionally uploads it as a build artifact.

## Features

- **Placeholder Validation**: Automatically checks for `<CHANGE_ME>` placeholders in module versions
- **Maven Integration**: Uses the FOLIO application generator Maven plugin
- **Artifact Upload**: Optionally uploads generated descriptors as GitHub artifacts
- **Error Handling**: Comprehensive validation and error reporting
- **Flexible Configuration**: Customizable state file paths and artifact settings

## Usage

### Basic Usage

```yaml
- name: Generate Application Descriptor
  uses: ./.github/actions/generate-application-descriptor
  with:
    app_name: 'my-folio-app'
    state_file: 'application-descriptor.json'
```

### With Custom Configuration

```yaml
- name: Generate Application Descriptor
  uses: ./.github/actions/generate-application-descriptor
  with:
    app_name: 'platform-complete'
    state_file: 'config/platform-state.json'
    upload_artifact: 'true'
    artifact_retention_days: '7'
```

### Skip Artifact Upload

```yaml
- name: Generate Application Descriptor
  uses: ./.github/actions/generate-application-descriptor
  with:
    app_name: 'my-app'
    state_file: 'app-state.json'
    upload_artifact: 'false'
```

## Inputs

| Input                     | Required  | Default                       | Description                                                     |
|---------------------------|-----------|-------------------------------|-----------------------------------------------------------------|
| `app_name`                | Yes       | -                             | Application name used for naming the generated descriptor file  |
| `state_file`              | No        | `application-descriptor.json` | Path to the application state file (JSON format)                |
| `upload_artifact`         | No        | `true`                        | Whether to upload the generated descriptor as a GitHub artifact |
| `artifact_retention_days` | No        | `1`                           | Number of days to retain the uploaded artifact                  |

## Outputs

| Output                 | Description                                                                       |
|------------------------|-----------------------------------------------------------------------------------|
| `generated`            | Whether the descriptor was generated successfully (`true`/`false`)                |
| `descriptor_file`      | Name of the generated descriptor file (e.g., `my-app-1.0.0.json`)                 |
| `descriptor_file_name` | Name of the descriptor file without extension (e.g., `my-app-1.0.0`)              |
| `has_placeholders`     | Whether the state file contains `<CHANGE_ME>` placeholder values (`true`/`false`) |

## Examples

### Complete Workflow Example

```yaml
name: Build Application Descriptor

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  generate-descriptor:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Java
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'

      - name: Generate Application Descriptor
        id: generate
        uses: ./.github/actions/generate-application-descriptor
        with:
          app_name: 'platform-complete'
          state_file: 'application-state.json'
          upload_artifact: 'true'
          artifact_retention_days: '30'

      - name: Check Generation Status
        run: |
          if [ "${{ steps.generate.outputs.generated }}" == "true" ]; then
            echo "✅ Descriptor generated: ${{ steps.generate.outputs.descriptor_file }}"
          else
            echo "❌ Descriptor generation failed"
            exit 1
          fi
```

### Conditional Processing Example

```yaml
- name: Generate Application Descriptor
  id: generate
  uses: ./.github/actions/generate-application-descriptor
  with:
    app_name: 'my-folio-app'
    state_file: 'config/app-state.json'

- name: Process Generated Descriptor
  if: steps.generate.outputs.generated == 'true' && steps.generate.outputs.has_placeholders == 'false'
  run: |
    echo "Processing descriptor: ${{ steps.generate.outputs.descriptor_file }}"
    # Additional processing steps here

- name: Handle Placeholders
  if: steps.generate.outputs.has_placeholders == 'true'
  run: |
    echo "⚠️ State file contains placeholders - descriptor generation skipped"
    echo "Please replace all <CHANGE_ME> values in the state file"
```

### Matrix Build Example

```yaml
strategy:
  matrix:
    platform:
      - name: 'platform-minimal'
        state_file: 'states/minimal.json'
      - name: 'platform-complete'
        state_file: 'states/complete.json'

steps:
  - name: Generate Descriptor for ${{ matrix.platform.name }}
    uses: ./.github/actions/generate-application-descriptor
    with:
      app_name: ${{ matrix.platform.name }}
      state_file: ${{ matrix.platform.state_file }}
      artifact_retention_days: '14'
```

## Behavior

### Placeholder Validation

The action first validates the state file for placeholder values:

1. **Checks for `<CHANGE_ME>` values** in `modules[].version` and `uiModules[].version` fields
2. **If placeholders found**: Skips descriptor generation and sets `has_placeholders=true`
3. **If no placeholders**: Proceeds with descriptor generation

### Maven Descriptor Generation

When no placeholders are detected:

1. **Validates Prerequisites**: Checks for `pom.xml` and state file existence
2. **Executes Maven Command**: Runs `folio-application-generator:generateFromJson`
3. **Locates Generated File**: Finds the generated descriptor in the `target/` directory
4. **Sets Outputs**: Provides file names and success status

### Artifact Upload

When `upload_artifact` is enabled:

1. **Uploads Generated Descriptor**: Uses `actions/upload-artifact@v4`
2. **Names Artifact**: Uses format `{app_name}-descriptor`
3. **Includes All Matching Files**: Uploads all `target/{app_name}*.json` files
4. **Applies Retention**: Respects the configured retention period

## Requirements

### Repository Structure

- **Maven Project**: Must contain a valid `pom.xml` file in the repository root
- **State File**: Application state file must be in valid JSON format
- **Build Environment**: Java and Maven must be available in the runner

### State File Format

The state file should follow the FOLIO application descriptor format:

```json
{
  "modules": [
    {
      "name": "mod-example",
      "version": "1.0.0"
    }
  ],
  "uiModules": [
    {
      "name": "ui-example",
      "version": "1.0.0"
    }
  ]
}
```

**Important**: All version fields must contain actual version numbers, not `<CHANGE_ME>` placeholders.

### Maven Configuration

Your `pom.xml` should include the FOLIO application generator plugin:

```xml
<plugin>
  <groupId>org.folio</groupId>
  <artifactId>folio-application-generator</artifactId>
  <version><!-- latest version --></version>
</plugin>
```

## Troubleshooting

### Common Issues

#### Descriptor Generation Failed
```
::error::Generated application descriptor not found
```
**Solutions**:
- Verify the state file format is valid JSON
- Check that all module versions are properly specified
- Ensure Maven can resolve the FOLIO application generator plugin
- Verify the application name matches the expected output pattern

#### State File Not Found
```
::error::State file not found: application-descriptor.json
```
**Solutions**:
- Check the `state_file` input path is correct
- Ensure the file exists in the repository
- Verify the file is committed and available in the workflow

#### Placeholder Values Detected
```
::warning::Found <CHANGE_ME> placeholders in module versions. Skipping descriptor generation.
```
**Solutions**:
- Replace all `<CHANGE_ME>` values with actual version numbers
- Use the `has_placeholders` output to conditionally handle this case
- Implement a separate workflow step to update placeholder values

#### Maven Build Failure
```
::error::pom.xml not found
```
**Solutions**:
- Ensure the repository contains a valid `pom.xml` file
- Verify Maven and Java are properly set up in the workflow
- Check that the FOLIO application generator plugin is configured

### Debug Information

The action provides detailed logging:

- **Placeholder Check**: Shows which fields contain placeholders
- **Maven Command**: Displays the full Maven command being executed
- **Target Directory**: Lists contents of the target directory for debugging
- **File Discovery**: Shows the process of locating generated files

## Related Actions

- **[create-pr](../create-pr/README.md)**: Create pull requests with generated descriptors
- **[update-pr](../update-pr/README.md)**: Update existing pull requests with new descriptors
- **[get-release-config](../get-update-config/README.md)**: Get configuration for release workflows

## Integration Examples

### With Release Workflows

```yaml
- name: Generate Descriptor
  id: generate
  uses: ./.github/actions/generate-application-descriptor
  with:
    app_name: ${{ matrix.platform }}
    state_file: 'states/${{ matrix.platform }}.json'

- name: Create Release PR
  if: steps.generate.outputs.generated == 'true'
  uses: ./.github/actions/create-pr
  with:
    source_branch: ${{ github.ref_name }}
    target_branch: 'main'
    pr_title: 'Release: ${{ steps.generate.outputs.descriptor_file_name }}'
    pr_body: |
      ## Generated Application Descriptor

      - **Application**: ${{ matrix.platform }}
      - **Descriptor**: ${{ steps.generate.outputs.descriptor_file }}
      - **Generated**: ${{ steps.generate.outputs.generated }}
```

### With Artifact Processing

```yaml
- name: Generate Descriptor
  id: generate
  uses: ./.github/actions/generate-application-descriptor
  with:
    app_name: 'platform'
    upload_artifact: 'true'
    artifact_retention_days: '90'

- name: Download and Process
  if: steps.generate.outputs.generated == 'true'
  run: |
    # Download the artifact in a subsequent job
    # Process the descriptor file
    # Deploy or publish as needed
```