# Generate Application Descriptor Action

A GitHub Action that generates or updates FOLIO application descriptors. This action supports two modes:

- **Generate Mode**: Creates descriptors from template files
- **Update Mode**: Synchronizes module versions from template to state file using version constraint resolution

## Features

- **Template-Driven Updates**: Resolves version constraints (`^2.0.0`, `~1.2.3`) to actual versions
- **Full Module Synchronization**: Adds new modules, removes unlisted modules, upgrades/downgrades versions
- **Artifact Validation**: Validates Docker images and NPM packages exist before resolution
- **Template Validation**: Validates all module versions are valid semver or semver range format
- **Maven Integration**: Uses the FOLIO application generator Maven plugin
- **Maven Dependency Caching**: Caches `~/.m2/repository` to reduce Maven Central downloads and avoid rate limiting
- **Artifact Upload**: Optionally uploads generated descriptors as GitHub artifacts
- **Detailed Change Tracking**: Outputs detailed information about module changes

## Usage

### Generate Mode (Default)

```yaml
- name: Generate Application Descriptor
  uses: folio-org/kitfox-github/.github/actions/generate-application-descriptor@master
  with:
    app_name: 'my-folio-app'
    template_file: 'application.template.json'
```

### Update Mode (Template-Driven State Management)

```yaml
- name: Update Application from Template
  uses: folio-org/kitfox-github/.github/actions/generate-application-descriptor@master
  with:
    app_name: 'my-folio-app'
    generation_mode: 'update'
    state_file: 'application.lock.json'
    template_file: 'application.template.json'
    validate_artifacts: 'true'
    pre_release: 'true'
    build_number: '1002000000000125'
```

## Inputs

| Input                     | Required | Default                       | Description                                                                                 |
|---------------------------|----------|-------------------------------|---------------------------------------------------------------------------------------------|
| `app_name`                | Yes      | -                             | Application name used for naming the generated descriptor file                              |
| `state_file`              | No       | `application-descriptor.json` | Path to the application state file (JSON format)                                            |
| `generation_mode`         | No       | `generate`                    | Mode: `generate` (from template) or `update` (sync from template)                           |
| `template_file`           | No       | `application.template.json`   | Path to template file                                                                       |
| `validate_artifacts`      | No       | `true`                        | Validate Docker/NPM artifacts exist before resolution                                       |
| `build_number`            | No       | -                             | Build number for snapshot versions                                                          |
| `pre_release`             | No       | `true`                        | Pre-release filter: `true` (include), `false` (release only), `only`                        |
| `use_project_version`     | No       | `true`                        | When true, uses pom.xml version; when false, increments patch from descriptor (update mode) |
| `no_version_bump`         | No       | `true`                        | Skip automatic version incrementing, keeping the version unchanged (update mode)            |
| `upload_artifact`         | No       | `true`                        | Whether to upload the generated descriptor as a GitHub artifact                             |
| `artifact_name`           | No       | `{app_name}-descriptor`       | Name for the uploaded artifact                                                              |
| `artifact_retention_days` | No       | `1`                           | Number of days to retain the uploaded artifact                                              |

## Outputs

### Core Outputs

| Output                 | Description                                                                            |
|------------------------|----------------------------------------------------------------------------------------|
| `generated`            | Whether the descriptor was generated with changes (`true` only when new descriptor file was created) |
| `descriptor_file`      | Name of the generated descriptor file (e.g., `my-app-1.0.0.json`)                      |
| `descriptor_file_name` | Name of the descriptor file without extension (e.g., `my-app-1.0.0`)                   |
| `artifact_name`        | Name of the uploaded artifact                                                          |
| `failure_reason`       | Reason for failure if generation failed (e.g., invalid template versions)              |

### Update Mode Outputs

| Output             | Description                                            |
|--------------------|--------------------------------------------------------|
| `updates_cnt`      | Total number of module changes                         |
| `be_added`         | Backend modules added (comma-separated)                |
| `be_upgraded`      | Backend modules upgraded (comma-separated)             |
| `be_downgraded`    | Backend modules downgraded (comma-separated)           |
| `be_removed`       | Backend modules removed (comma-separated)              |
| `ui_added`         | UI modules added (comma-separated)                     |
| `ui_upgraded`      | UI modules upgraded (comma-separated)                  |
| `ui_downgraded`    | UI modules downgraded (comma-separated)                |
| `ui_removed`       | UI modules removed (comma-separated)                   |
| `updated_modules`  | Summary of all module changes (multiline)              |

## Generation Modes

### Generate Mode (`generation_mode: generate`)

Creates a new application descriptor from the template file using the `generateFromJson` Maven goal.

```bash
mvn org.folio:folio-application-generator:generateFromJson \
  -DtemplatePath=application.template.json
```

**Use Cases**:
- Initial descriptor generation
- Rebuilding descriptors from templates
- CI/CD pipelines that need fresh descriptors

### Update Mode (`generation_mode: update`)

Synchronizes module versions from template to state file using the `updateFromTemplate` Maven goal. Supports version constraint resolution.

```bash
mvn org.folio:folio-application-generator:updateFromTemplate \
  -DappDescriptorPath=application.lock.json \
  -DtemplatePath=application.template.json \
  -DvalidateArtifacts=true \
  -DbuildNumber=1002000000000125
```

**Capabilities**:
- **Version Constraint Resolution**: `^2.0.0` resolves to latest compatible version (e.g., `2.3.1`)
- **Module Synchronization**: Adds modules in template, removes modules not in template
- **Artifact Validation**: Validates Docker images and NPM packages exist
- **Pre-release Filtering**: Respects `preRelease` setting per module

**Output File** (`target/update-result.json`):
```json
{
  "beAdded": ["mod-new-1.0.0"],
  "beUpgraded": ["mod-core (2.0.0 -> 2.1.0)"],
  "beDowngraded": [],
  "beRemoved": ["mod-old-1.0.0"],
  "uiAdded": [],
  "uiUpgraded": ["folio_test (2.0.0 -> 2.1.0)"],
  "uiDowngraded": [],
  "uiRemoved": []
}
```

## Version Constraint Support

The update mode supports semver version constraints in the template file:

| Constraint  | Description                                  | Example Resolution |
|-------------|----------------------------------------------|-------------------|
| `^2.0.0`    | Compatible with 2.x.x (>=2.0.0 <3.0.0)      | `2.3.1`           |
| `~1.2.3`    | Patch-level changes (>=1.2.3 <1.3.0)        | `1.2.9`           |
| `>=1.0.0`   | Greater than or equal                        | `2.5.0`           |
| `1.0.0`     | Exact version                                | `1.0.0`           |

## Artifact Validation

When `validate_artifacts: true`, the action validates that module artifacts exist before resolution:

**Default Registries**:
- **Backend (Docker)**:
  - Release: DockerHub `folioorg`
  - Pre-release: DockerHub `folioci`
- **UI (NPM)**:
  - Release: `npm-folio`
  - Pre-release: `npm-folioci`

## Examples

### Complete Update Workflow

```yaml
jobs:
  update-application:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Java
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'

      - name: Update Application from Template
        id: update
        uses: folio-org/kitfox-github/.github/actions/generate-application-descriptor@master
        with:
          app_name: 'app-platform'
          generation_mode: 'update'
          state_file: 'application.lock.json'
          template_file: 'application.template.json'
          validate_artifacts: 'true'
          pre_release: 'true'
          build_number: '${{ github.run_number }}'

      - name: Check for Updates
        if: steps.update.outputs.generated == 'true'
        run: |
          echo "Found ${{ steps.update.outputs.updates_cnt }} module updates"
          echo "Changes:"
          echo "${{ steps.update.outputs.updated_modules }}"
```

### Snapshot Branch Update

```yaml
- name: Update Snapshot Application
  uses: folio-org/kitfox-github/.github/actions/generate-application-descriptor@master
  with:
    app_name: 'app-platform'
    generation_mode: 'update'
    state_file: 'application.lock.json'
    template_file: 'application.template.json'
    pre_release: 'only'
    build_number: '${{ vars.BUILD_OFFSET }}${{ github.run_number }}'
```

### Release Branch Update

```yaml
- name: Update Release Application
  uses: folio-org/kitfox-github/.github/actions/generate-application-descriptor@master
  with:
    app_name: 'app-platform'
    generation_mode: 'update'
    state_file: 'application.lock.json'
    template_file: 'application.template.json'
    pre_release: 'false'
    validate_artifacts: 'true'
```

## File Structure

### Template File (`application.template.json`)

```json
{
  "name": "app-platform",
  "version": "1.0.0",
  "modules": [
    {
      "name": "mod-users",
      "version": "^19.0.0",
      "preRelease": "true"
    },
    {
      "name": "mod-inventory",
      "version": "~20.1.0",
      "preRelease": "false"
    }
  ],
  "uiModules": [
    {
      "name": "folio_users",
      "version": "^10.0.0",
      "preRelease": "true"
    }
  ]
}
```

### State File (`application.lock.json`)

Generated/updated by this action with resolved versions:

```json
{
  "name": "app-platform",
  "version": "1.0.0-SNAPSHOT.125",
  "modules": [
    {
      "name": "mod-users",
      "version": "19.2.1"
    },
    {
      "name": "mod-inventory",
      "version": "20.1.5"
    }
  ],
  "uiModules": [
    {
      "name": "folio_users",
      "version": "10.1.0"
    }
  ]
}
```

## Requirements

### Repository Structure

- **Maven Project**: Must contain a valid `pom.xml` file
- **Template File**: Application template in valid JSON format
- **State File**: Required for update mode
- **Build Environment**: Java and Maven must be available

### Maven Configuration

Your `pom.xml` should include the FOLIO application generator plugin:

```xml
<plugin>
  <groupId>org.folio</groupId>
  <artifactId>folio-application-generator</artifactId>
  <version>1.2.0</version>
</plugin>
```

## Troubleshooting

### Common Issues

#### Invalid Module Versions in Template
```
::error::Invalid module versions in template (must be semver or semver range):
::error::  - '<CHANGE_ME>'
```
**Solution**: Ensure all module versions in the template are valid semver (`1.0.0`) or semver range (`^2.0.0`, `~1.2.3`, `>=1.0.0`).

#### Artifact Validation Failed
```
::error::Failed to validate artifact for mod-example version 1.0.0
```
**Solution**: Ensure the module version exists in Docker Hub or NPM registry.

#### State File Not Found (Update Mode)
```
::error::State file not found: application.lock.json
```
**Solution**: Ensure the state file exists. For new applications, use `generate` mode first.

#### Template File Not Found
```
::error::Template file not found: application.template.json
```
**Solution**: Verify the template file path is correct.

#### Maven Central 403 Forbidden
```
Could not transfer artifact ... from/to central: status code: 403, reason phrase: Forbidden
```
**Cause**: GitHub-hosted runners share IP pools that can hit Maven Central rate limits.
**Mitigation**: The action uses `actions/cache@v5` to cache Maven dependencies. On cache hit, no Maven Central downloads are needed. Cache misses (first run, after 7-day eviction, pom.xml changes) may still encounter this issue - retry the workflow.

## Related Documentation

- **[Application Update Flow](../../docs/application-update-flow.md)**: Workflow that uses this action
- **[folio-application-generator](https://github.com/folio-org/folio-application-generator)**: Maven plugin documentation

---

**Last Updated**: January 2026
**Action Version**: 2.1 (Maven Dependency Caching)
