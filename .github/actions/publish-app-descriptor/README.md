# Publish Application Descriptor

Publishes an application descriptor to the FOLIO Artifact Registry (FAR).

## Description

This composite action publishes a FOLIO application descriptor JSON file to the FAR registry. It supports two input modes:
1. Direct file path - provide a path to a descriptor file on the filesystem
2. Artifact download - download a descriptor from a workflow artifact and publish it

## Inputs

| Input                      | Description                                                                              | Required   | Default  |
|----------------------------|------------------------------------------------------------------------------------------|------------|----------|
| `descriptor-path`          | Path to application descriptor file (mutually exclusive with `descriptor-artifact-name`) | No         | -        |
| `descriptor-artifact-name` | Name of artifact containing the descriptor (mutually exclusive with `descriptor-path`)   | No         | -        |
| `descriptor-file-name`     | File name within the artifact (required if `descriptor-artifact-name` is provided)       | No         | -        |
| `far-url`                  | FAR registry URL                                                                         | Yes        | -        |

## Outputs

| Output           | Description                                      |
|------------------|--------------------------------------------------|
| `publish-status` | Success/failure status (`success` or `failure`)  |
| `descriptor-url` | URL of the published descriptor in FAR           |
| `http-code`      | HTTP response code from the publish request      |

## Usage

### Example 1: Publish from file path

```yaml
- name: Publish Application Descriptor
  uses: folio-org/kitfox-github/.github/actions/publish-app-descriptor@master
  with:
    descriptor-path: ./application-descriptor.json
    far-url: ${{ vars.FAR_URL }}
```

### Example 2: Publish from artifact

```yaml
- name: Publish Application Descriptor
  uses: folio-org/kitfox-github/.github/actions/publish-app-descriptor@master
  with:
    descriptor-artifact-name: app-acquisitions-descriptor
    descriptor-file-name: app-acquisitions-1.0.0.json
    far-url: ${{ vars.FAR_URL }}
```

### Example 3: Conditional publish with status check

```yaml
- name: Publish Application Descriptor
  id: publish
  uses: folio-org/kitfox-github/.github/actions/publish-app-descriptor@master
  with:
    descriptor-path: /tmp/app-descriptors/app-descriptor.json
    far-url: ${{ vars.FAR_URL }}

- name: Check Publish Status
  if: steps.publish.outputs.publish-status == 'success'
  run: |
    echo "Descriptor published to: ${{ steps.publish.outputs.descriptor-url }}"
```

## Notes

- Either `descriptor-path` OR `descriptor-artifact-name` must be provided (not both)
- When using `descriptor-artifact-name`, `descriptor-file-name` is required
- The action extracts the descriptor ID from the JSON file's `id` field to construct the descriptor URL
- Publish failures will cause the action to exit with status code 1
- Response body is logged to stderr on failures for debugging
