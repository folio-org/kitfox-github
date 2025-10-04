# Update Application Workflow

**Workflow**: `update-application.yml`  
**Purpose**: Module version checking and descriptor generation for FOLIO applications  
**Type**: Reusable workflow (`workflow_call`)

## 🎯 Overview

This workflow handles the core logic for checking module versions and updating application descriptors. It supports both snapshot (development) and release modes, handles placeholder versions for release preparation, and generates updated state files for downstream processing.

## 📋 Workflow Interface

### Inputs

| Input                     | Description                                     | Required | Type    | Default             |
|---------------------------|-------------------------------------------------|----------|---------|---------------------|
| `app_name`                | Application name                                | Yes      | string  | -                   |
| `repo`                    | Application repository name (org/repo format)   | Yes      | string  | -                   |
| `branch`                  | Branch to update                                | No       | string  | `'snapshot'`        |
| `workflow_run_number`     | GitHub run number for display                   | Yes      | string  | -                   |
| `descriptor_build_offset` | Offset for application artifact version         | No       | string  | `'100100000000000'` |
| `mode`                    | Update mode: 'snapshot' or 'release'            | No       | string  | `'snapshot'`        |
| `target_version`          | Specific version to set (overrides calculation) | No       | string  | `''`                |
| `placeholder_modules`     | Set module versions to `<CHANGE_ME>`            | No       | boolean | `false`             |

### Outputs

| Output                      | Description                           |
|-----------------------------|---------------------------------------|
| `app_name`                  | Application name (pass-through)       |
| `updated`                   | Whether application was updated       |
| `previous_version`          | Previous application version          |
| `new_version`               | New application version if updated    |
| `updates_cnt`               | Number of updated modules             |
| `updated_modules`           | List of updated modules               |
| `failure_reason`            | Reason for failure                    |
| `app_descriptor_file`       | Path to generated descriptor artifact |
| `app_descriptor_file_name`  | Name of generated descriptor file     |

## 🔄 Workflow Execution Flow

### 1. Repository Setup
- Checkout application repository
- Set up Maven environment
- Configure Git for automated operations

### 2. Version Collection
- Extract current version from `pom.xml`
- Parse semantic version components (major.minor.patch)
- Read current state from `application-descriptor.json`

### 3. Module Version Discovery
- Query FOLIO registry for latest module versions
- Apply mode filters:
  - **Snapshot mode**: `preRelease=only`, `npmSnapshot=only`
  - **Release mode**: `preRelease=false`, `npmSnapshot=false`
- Validate artifact availability in Docker Hub/NPM

### 4. Version Comparison and Updates
- Compare current vs. available module versions
- Update state file with new versions
- Calculate updated modules count

### 5. Placeholder Module Handling (Release Preparation)
- If `placeholder_modules=true`:
  - Set all module versions to `<CHANGE_ME>`
  - Used for release branch preparation
- Skip descriptor generation when using placeholders

### 6. Application Version Calculation
- If `target_version` provided: Use specified version
- If release mode with updates: Increment patch version
- If snapshot mode: Generate build number with offset

### 7. POM Version Update
- Update `pom.xml` when:
  - `target_version` is provided, OR
  - In release mode with module updates
- Skip for snapshot mode unless explicitly targeted

### 8. Descriptor Generation
- Use Maven folio-application-generator
- Generate application descriptor JSON
- Skip if using placeholder modules

### 9. Artifact Upload
- Upload state files:
  - `application-descriptor.json`
  - `pom.xml`
- Artifacts retained for downstream workflows

## 🔧 Mode-Specific Behavior

### Snapshot Mode (`mode: 'snapshot'`)
- Fetches latest snapshot/pre-release module versions
- Generates version with build number: `X.Y.Z-SNAPSHOT.BUILD`
- Updates only application-descriptor.json (not pom.xml)
- Used for continuous integration builds

### Release Mode (`mode: 'release'`)
- Fetches stable release module versions
- Increments patch version: `X.Y.(Z+1)`
- Updates both application-descriptor.json and pom.xml
- Used for release preparation and tagging

### Placeholder Mode (`placeholder_modules: true`)
- Sets all modules to `<CHANGE_ME>` version
- Used during release branch creation
- Teams manually update versions later
- Skips descriptor generation

## 📊 Usage Examples

### Basic Snapshot Update
```yaml
- uses: ./.github/workflows/update-application.yml
  with:
    app_name: ${{ inputs.app_name }}
    repo: ${{ inputs.repo }}
    workflow_run_number: ${{ github.run_number }}
```

### Release Mode Update
```yaml
- uses: ./.github/workflows/update-application.yml
  with:
    app_name: ${{ inputs.app_name }}
    repo: ${{ inputs.repo }}
    mode: 'release'
    workflow_run_number: ${{ github.run_number }}
```

### Release Preparation with Placeholders
```yaml
- uses: ./.github/workflows/update-application.yml
  with:
    app_name: ${{ inputs.app_name }}
    repo: ${{ inputs.repo }}
    mode: 'release'
    target_version: '2.0.0'
    placeholder_modules: true
```

### Specific Version Override
```yaml
- uses: ./.github/workflows/update-application.yml
  with:
    app_name: ${{ inputs.app_name }}
    repo: ${{ inputs.repo }}
    target_version: '1.5.0'
    workflow_run_number: ${{ github.run_number }}
```

## 🔍 Module Version Discovery

### Registry Endpoints
- **FOLIO Registry**: `https://folio-registry.dev.folio.org/_/proxy/modules`
- **Docker Registry**: Docker Hub API for backend modules
- **NPM Registry**: NPM repository for UI modules

### Version Filtering
```bash
# Snapshot mode
preRelease=only     # Backend modules
npmSnapshot=only    # UI modules

# Release mode  
preRelease=false    # Backend modules
npmSnapshot=false   # UI modules
```

## 🛡️ Error Handling

### Common Failure Scenarios
- **State file missing**: application-descriptor.json not found
- **Registry unavailable**: FOLIO registry connection failed
- **Invalid module versions**: Artifact validation failed
- **Maven errors**: POM parsing or generation issues

### Failure Outputs
The workflow provides detailed `failure_reason` output for troubleshooting.

## 📈 Performance Considerations

- **Parallel Processing**: Module version checks run concurrently
- **Artifact Caching**: State files cached as artifacts
- **Selective Updates**: Only processes changed modules
- **Efficient Queries**: Optimized registry API usage

## 📚 Related Documentation

- **[app-update.md](app-update.md)**: Orchestrator workflow documentation
- **[Verify Application Action](../actions/verify-application/README.md)**: Validation and registry upload action
- **[commit-application-changes.md](commit-application-changes.md)**: Git operations workflow

---

**Last Updated**: September 2025  
**Workflow Version**: 1.0  
**Compatibility**: All FOLIO application repositories
