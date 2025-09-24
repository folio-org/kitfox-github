# Verify Application Action

A composite GitHub Action for validating FOLIO application descriptors and uploading them to the FOLIO Application Registry (FAR).

## Description

This action performs comprehensive validation of application descriptors including:
- Module interface integrity checks
- Application dependency validation
- Cross-application compatibility verification
- Optional upload to FAR for distribution

## Inputs

| Name                                | Description                                                                | Required  | Default               |
|-------------------------------------|----------------------------------------------------------------------------|-----------|-----------------------|
| `app_name`                          | Application name                                                           | **Yes**   | -                     |
| `app_descriptor_file`               | Application descriptor file name                                           | **Yes**   | -                     |
| `app_descriptor_artifact_name`      | Application descriptor artifact name (defaults to `{app_name}-descriptor`) | No        | -                     |
| `platform_descriptor_artifact_name` | Name of the platform descriptor artifact to download                       | No        | `platform-descriptor` |
| `rely_on_FAR`                       | Whether to rely on FAR for application descriptor dependencies             | No        | `false`               |
| `skip_upload`                       | Skip uploading to registry (for PR validation flows)                       | No        | `false`               |
| `far_url`                           | FAR API URL base (falls back to `vars.FAR_URL` if not provided)            | **Yes**   | -                     |

## Outputs

| Name                   | Description                                                   |
|------------------------|---------------------------------------------------------------|
| `validation_passed`    | Whether all validations passed (`true` or `false`)            |
| `failure_reason`       | Detailed reason for failure if validation failed              |
| `uploaded_to_registry` | Whether the application was successfully uploaded to registry |

## Usage

### Basic Usage

```yaml
steps:
  - name: Verify Application
    uses: folio-org/kitfox-github/.github/actions/verify-application@main
    with:
      app_name: ${{ github.event.repository.name }}
      app_descriptor_file: ${{ needs.generate.outputs.descriptor_file }}
      app_descriptor_artifact_name: ${{ needs.generate.outputs.descriptor_artifact_name }}
      far_url: ${{ vars.FAR_URL }}
```

### Validation Only (Skip Upload)

```yaml
steps:
  - name: Validate Application
    uses: folio-org/kitfox-github/.github/actions/verify-application@main
    with:
      app_name: my-application
      app_descriptor_file: app-descriptor.json
      app_descriptor_artifact_name: my-app-descriptor
      skip_upload: 'true'
      far_url: ${{ vars.FAR_URL }}
```

### With Custom Platform Descriptor

```yaml
steps:
  - name: Verify with Custom Platform
    uses: folio-org/kitfox-github/.github/actions/verify-application@main
    with:
      app_name: my-application
      app_descriptor_file: app-descriptor.json
      app_descriptor_artifact_name: my-app-descriptor
      platform_descriptor_artifact_name: custom-platform-descriptor
      far_url: ${{ vars.FAR_URL }}
```

### Using FAR for Dependencies

```yaml
steps:
  - name: Verify with FAR Dependencies
    uses: folio-org/kitfox-github/.github/actions/verify-application@main
    with:
      app_name: my-application
      app_descriptor_file: app-descriptor.json
      app_descriptor_artifact_name: my-app-descriptor
      rely_on_FAR: 'true'
      far_url: ${{ vars.FAR_URL }}
```

## Prerequisites

This action expects the following artifacts to be available:
1. **Application descriptor artifact** - Named according to `app_descriptor_artifact_name` (or `{app_name}-descriptor` if not specified)
2. **Platform descriptor artifact** (optional) - Named according to `platform_descriptor_artifact_name` (or `platform-descriptor` if not specified)

These artifacts should be uploaded in previous workflow steps using `actions/upload-artifact`.

## Validation Process

1. **Download Artifacts**: Retrieves application and platform descriptor artifacts
2. **Fetch FAR Descriptors**: If not relying on FAR, fetches all application descriptors from FAR for validation
3. **Module Interface Validation**: Validates module interfaces against FAR API
4. **Dependency Validation**: Validates application dependencies using all available descriptors
5. **Upload to Registry**: Uploads validated descriptor to FAR (unless `skip_upload` is true)

## Error Handling

The action will fail if:
- Required artifacts are not found
- Descriptor validation fails (invalid JSON, missing fields, etc.)
- Module interface validation fails
- Dependency validation fails
- FAR upload fails (when not skipped)

All errors are reported through the `failure_reason` output and in the action logs.

## Example Workflow

```yaml
name: Verify Application
on:
  workflow_dispatch:

jobs:
  generate:
    runs-on: ubuntu-latest
    outputs:
      descriptor_file: ${{ steps.generate.outputs.descriptor_file }}
      descriptor_file_name: ${{ steps.generate.outputs.descriptor_file_name }}
    steps:
      - name: Generate Descriptor
        id: generate
        # ... generate application descriptor ...

      - name: Upload Descriptor Artifact
        uses: actions/upload-artifact@v4
        with:
          name: ${{ steps.generate.outputs.descriptor_file_name }}
          path: ${{ steps.generate.outputs.descriptor_file }}

  verify:
    needs: generate
    runs-on: ubuntu-latest
    steps:
      - name: Verify Application
        id: verify
        uses: folio-org/kitfox-github/.github/actions/verify-application@main
        with:
          app_name: ${{ github.event.repository.name }}
          app_descriptor_file: ${{ needs.generate.outputs.descriptor_file }}
          app_descriptor_artifact_name: ${{ needs.generate.outputs.descriptor_artifact_name }}
          far_url: ${{ vars.FAR_URL }}

      - name: Check Results
        if: always()
        run: |
          echo "Validation passed: ${{ steps.verify.outputs.validation_passed }}"
          echo "Failure reason: ${{ steps.verify.outputs.failure_reason }}"
          echo "Uploaded: ${{ steps.verify.outputs.uploaded_to_registry }}"
```

## License

This action is part of the FOLIO project and follows the project's licensing terms.