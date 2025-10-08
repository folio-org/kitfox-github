# Unpublish Application Descriptor

Removes an application descriptor from the FOLIO Artifact Registry (FAR).

## Description

This composite action unpublishes a FOLIO application descriptor from the FAR registry using the descriptor ID (typically in `name-version` format).

## Inputs

| Input            | Description                                            | Required | Default |
|------------------|--------------------------------------------------------|----------|---------|
| `descriptor-id`  | Descriptor ID (name-version format) to unpublish from FAR | Yes      | -       |
| `far-url`        | FAR registry URL                                       | Yes      | -       |

## Outputs

| Output              | Description                                        |
|---------------------|----------------------------------------------------|
| `unpublish-status`  | Success/failure status (`success` or `failure`)    |
| `http-code`         | HTTP response code from the unpublish request      |

## Usage

### Example 1: Unpublish descriptor with explicit ID

```yaml
- name: Unpublish Application Descriptor
  uses: folio-org/kitfox-github/.github/actions/unpublish-app-descriptor@master
  with:
    descriptor-id: app-acquisitions-1.0.0
    far-url: ${{ vars.FAR_URL }}
```

### Example 2: Unpublish with dynamic descriptor ID from previous step

```yaml
- name: Unpublish Application Descriptor
  id: unpublish
  uses: folio-org/kitfox-github/.github/actions/unpublish-app-descriptor@master
  with:
    descriptor-id: ${{ steps.update-app.outputs.app_descriptor_file_name }}
    far-url: ${{ vars.FAR_URL }}

- name: Check Unpublish Status
  if: steps.unpublish.outputs.unpublish-status == 'success'
  run: echo "Descriptor unpublished successfully"
```

### Example 3: Cleanup on failure

```yaml
- name: Cleanup on Failure
  if: failure()
  uses: folio-org/kitfox-github/.github/actions/unpublish-app-descriptor@master
  with:
    descriptor-id: ${{ needs.update-application.outputs.app_descriptor_file_name }}
    far-url: ${{ vars.FAR_URL }}
```

## Notes

- The descriptor ID typically follows the format `{app-name}-{version}` (e.g., `app-acquisitions-1.0.0`)
- Unpublish failures will cause the action to exit with status code 1
- Response body is logged to stderr on failures for debugging
- This action is commonly used in cleanup jobs when other workflow steps fail
