# Collect Application Version

A GitHub Action for collecting and parsing Maven application versions from FOLIO repositories. This action extracts version information from `pom.xml` files and breaks it down into semantic version components, with special handling for SNAPSHOT versions.

## Features

- **Maven version extraction**: Reads version from `pom.xml` using Maven
- **Semantic version parsing**: Breaks down versions into major, minor, patch components
- **SNAPSHOT support**: Properly handles SNAPSHOT versions with build numbers
- **Cross-repository support**: Can collect versions from any FOLIO application repository
- **Validation**: Ensures version follows expected semantic versioning patterns

## Usage

### Basic Example

```yaml
- name: Get Application Version
  id: app-version
  uses: folio-org/kitfox-github/.github/actions/collect-app-version@main
  with:
    app_name: app-platform-minimal
    branch: main

- name: Use Version Information
  run: |
    echo "Version: ${{ steps.app-version.outputs.version }}"
    echo "Major: ${{ steps.app-version.outputs.major }}"
    echo "Minor: ${{ steps.app-version.outputs.minor }}"
    echo "Patch: ${{ steps.app-version.outputs.patch }}"
    echo "Is Snapshot: ${{ steps.app-version.outputs.is_snapshot }}"
```

### Release Workflow Example

```yaml
- name: Collect Current Version
  id: current-version
  uses: folio-org/kitfox-github/.github/actions/collect-app-version@main
  with:
    app_name: ${{ matrix.application }}
    branch: ${{ inputs.previous_release_branch }}

- name: Calculate Next Version
  id: next-version
  run: |
    current_major=${{ steps.current-version.outputs.major }}
    next_major=$((current_major + 1))
    echo "next_version=${next_major}.0.0" >> "$GITHUB_OUTPUT"

- name: Update Application Version
  run: |
    echo "Updating from ${{ steps.current-version.outputs.version }} to ${{ steps.next-version.outputs.next_version }}"
```

### Matrix Strategy Example

```yaml
jobs:
  collect-versions:
    strategy:
      matrix:
        application: [app-platform-minimal, app-acquisitions, app-agreements]
    steps:
      - name: Collect Application Version
        id: version
        uses: folio-org/kitfox-github/.github/actions/collect-app-version@main
        with:
          app_name: ${{ matrix.application }}
          branch: R1-2025

      - name: Report Version
        run: |
          echo "${{ matrix.application }}: ${{ steps.version.outputs.version }}"
```

### With Custom Token

```yaml
- name: Collect Version from Private Repository
  uses: folio-org/kitfox-github/.github/actions/collect-app-version@main
  with:
    app_name: private-application
    branch: main
    token: ${{ secrets.PRIVATE_REPO_TOKEN }}
```

## Inputs

| Input      | Description                                                 | Required | Default                        |
|------------|-------------------------------------------------------------|----------|--------------------------------|
| `app_name` | Application repository name \(without `folio-org/` prefix\) | ✅        | \-                             |
| `branch`   | Branch name to collect version from                         | ✅        | \-                             |
| `token`    | GitHub token with repository read permissions               | ❌        | `${{ secrets.GITHUB_TOKEN }}`  |

## Outputs

| Output         | Description                          | Example             |
|----------------|--------------------------------------|---------------------|
| `version`      | Complete version string from pom.xml | `1.2.3-SNAPSHOT.45` |
| `major`        | Major version number                 | `1`                 |
| `minor`        | Minor version number                 | `2`                 |
| `patch`        | Patch version number                 | `3`                 |
| `is_snapshot`  | Whether this is a SNAPSHOT version   | `SNAPSHOT` or empty |
| `build_number` | Build number (for SNAPSHOT versions) | `45`                |

## Version Format Support

This action supports Maven versions following these patterns:

### Release Versions
- `1.0.0` → Major: 1, Minor: 0, Patch: 0
- `2.3.5` → Major: 2, Minor: 3, Patch: 5

### SNAPSHOT Versions
- `1.0.0-SNAPSHOT` → Major: 1, Minor: 0, Patch: 0, is_snapshot: SNAPSHOT
- `1.0.0-SNAPSHOT.123` → Major: 1, Minor: 0, Patch: 0, is_snapshot: SNAPSHOT, build_number: 123

## How It Works

1. **Repository Checkout**: Checks out the specified application repository and branch
2. **Maven Version Extraction**: Uses Maven to extract the version from `pom.xml`
3. **Version Validation**: Validates the version follows semantic versioning patterns
4. **Component Parsing**: Breaks down the version into individual components
5. **Output Generation**: Provides all components as action outputs

## Requirements

### Repository Structure
The target repository must:
- Be a Maven project with a `pom.xml` file in the root
- Have the version defined in the `<version>` element
- Follow semantic versioning conventions

### Maven
This action uses Maven (`mvn`) which is pre-installed on GitHub runners.

### Permissions
The calling workflow needs appropriate permissions:

```yaml
permissions:
  contents: read     # To checkout repositories
```

## Error Handling

The action provides clear error messages for common issues:

- **Missing pom.xml**: If the repository doesn't contain a `pom.xml` file
- **Invalid version format**: If the version doesn't follow semantic versioning
- **Maven execution failure**: If Maven cannot extract the version

## Use Cases

### Release Preparation
Collect current versions before calculating next release versions:

```yaml
- name: Collect Current Versions
  id: versions
  uses: folio-org/kitfox-github/.github/actions/collect-app-version@main
  with:
    app_name: ${{ matrix.application }}
    branch: ${{ inputs.current_release_branch }}

- name: Increment Major Version
  run: |
    next_major=$(({{ steps.versions.outputs.major }} + 1))
    echo "Next version will be: ${next_major}.0.0"
```

### Version Compatibility Checking
Ensure version compatibility across applications:

```yaml
- name: Check Platform Compatibility
  uses: folio-org/kitfox-github/.github/actions/collect-app-version@main
  with:
    app_name: platform-complete
    branch: main

- name: Validate Compatibility
  run: |
    platform_major=${{ steps.platform.outputs.major }}
    app_major=${{ steps.app.outputs.major }}
    if [[ $app_major -gt $platform_major ]]; then
      echo "::warning::Application version is ahead of platform"
    fi
```

### SNAPSHOT Tracking
Track SNAPSHOT build progression:

```yaml
- name: Get Current SNAPSHOT
  id: snapshot
  uses: folio-org/kitfox-github/.github/actions/collect-app-version@main
  with:
    app_name: ${{ matrix.app }}
    branch: snapshot

- name: Report SNAPSHOT Status
  run: |
    if [[ "${{ steps.snapshot.outputs.is_snapshot }}" == "SNAPSHOT" ]]; then
      echo "SNAPSHOT build: ${{ steps.snapshot.outputs.build_number }}"
    else
      echo "Release version: ${{ steps.snapshot.outputs.version }}"
    fi
```

### Version Comparison
Compare versions between branches:

```yaml
- name: Get Main Version
  id: main-version
  uses: folio-org/kitfox-github/.github/actions/collect-app-version@main
  with:
    app_name: ${{ inputs.app_name }}
    branch: main

- name: Get Feature Version
  id: feature-version
  uses: folio-org/kitfox-github/.github/actions/collect-app-version@main
  with:
    app_name: ${{ inputs.app_name }}
    branch: ${{ inputs.feature_branch }}

- name: Compare Versions
  run: |
    echo "Main: ${{ steps.main-version.outputs.version }}"
    echo "Feature: ${{ steps.feature-version.outputs.version }}"
```

## Best Practices

### Token Management
- Use the default `GITHUB_TOKEN` for public repositories
- Use a personal access token for private repositories or cross-organization access
- Ensure tokens have appropriate read permissions

### Branch Strategy
- Use stable branch names for consistent version collection
- Consider using specific commit SHAs for reproducible version collection
- Validate branch existence before running the action

### Version Validation
Always validate version outputs before using them:

```yaml
- name: Validate Version
  run: |
    version="${{ steps.collect.outputs.version }}"
    if [[ -z "$version" || "$version" == "unknown" ]]; then
      echo "::error::Failed to collect valid version"
      exit 1
    fi
```

### Error Handling
Implement proper error handling for version collection failures:

```yaml
- name: Collect Version
  id: version
  uses: folio-org/kitfox-github/.github/actions/collect-app-version@main
  with:
    app_name: ${{ inputs.app_name }}
    branch: ${{ inputs.branch }}
  continue-on-error: true

- name: Handle Version Collection Failure
  if: steps.version.outcome == 'failure'
  run: |
    echo "::warning::Could not collect version for ${{ inputs.app_name }}"
    echo "Using fallback version strategy..."
```

## Troubleshooting

### Common Issues

**pom.xml not found**
- Verify the repository contains a Maven project
- Check that `pom.xml` exists in the repository root
- Ensure the specified branch exists and contains the file

**Invalid version format**
- Verify the version in `pom.xml` follows semantic versioning
- Check for typos or non-standard version formats
- Ensure the version is properly defined in the `<version>` element

**Permission denied**
- Verify the GitHub token has read access to the repository
- For private repositories, ensure the token has appropriate permissions
- Check repository visibility and access settings

**Maven execution failure**
- The repository may not be a valid Maven project
- Dependencies might be missing or misconfigured
- Check the Maven project structure and configuration

## Integration with FOLIO Workflows

This action is specifically designed for FOLIO application repositories and integrates with:

- **Release preparation workflows**: For version collection and increment calculation
- **Platform integration**: For version compatibility checking
- **CI/CD pipelines**: For automated version management
- **Dependency tracking**: For cross-application version monitoring

## Contributing

This action is part of the FOLIO Kitfox infrastructure. For issues or improvements:

1. Create an issue in the kitfox-github repository
2. Follow FOLIO contribution guidelines
3. Include Kitfox team members in reviews

## License

Apache License 2.0 - See the LICENSE file in the repository root. 