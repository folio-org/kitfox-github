# Collect Application Version

A GitHub Action for collecting and parsing Maven application versions from FOLIO repositories. This action extracts the project version directly from `pom.xml` and breaks it down into semantic version components, with special handling for SNAPSHOT versions.

## Features

- **Direct pom.xml parsing**: Reads the project `<version>` element via `awk` — no Maven invocation, no Maven Central dependency
- **Semantic version parsing**: Breaks down versions into major, minor, patch components
- **SNAPSHOT support**: Properly handles SNAPSHOT versions with build numbers
- **Parent-aware**: Skips any `<version>` nested in a `<parent>` block so the project version is selected, not the parent's
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
    app_name: folio-org/${{ matrix.application }}
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

| Input           | Description                                                                              | Required | Default                          |
|-----------------|------------------------------------------------------------------------------------------|----------|----------------------------------|
| `app_name`      | Full repository path (e.g., `folio-org/app-platform`)                                    | ✅       | \-                               |
| `branch`        | Branch (or any git ref) to read `pom.xml` from                                           | ✅       | \-                               |
| `token`         | GitHub token with read access to the target repository                                   | ❌       | `${{ github.token }}` if not set |

## Outputs

| Output                    | Description                                                                            | Example             |
|---------------------------|----------------------------------------------------------------------------------------|---------------------|
| `version`                 | Complete version string from pom.xml                                                   | `1.2.3-SNAPSHOT.45` |
| `major`                   | Major version number                                                                   | `1`                 |
| `minor`                   | Minor version number                                                                   | `2`                 |
| `patch`                   | Patch version number                                                                   | `3`                 |
| `is_snapshot`             | Whether this is a SNAPSHOT version                                                     | `true` or `false`   |
| `build_number`            | Build number (for SNAPSHOT versions)                                                   | `45`                |
| `is_infrastructure_error` | Reserved for backwards compatibility; always emits `false` after [RANCHER-2977](https://folio-org.atlassian.net/browse/RANCHER-2977) (no `mvn` invocation remains) | `false`             |
| `error_category`          | `NONE` \| `POM_NOT_FOUND` \| `INVALID_VERSION_FORMAT`                                  | `NONE`              |
| `failure_reason`          | Standard failure message when the read failed (empty on success)                       | `Could not extract project <version> from pom.xml` |

The action always exits 1 on any failure, classifying the cause:

| Failure                                     | Exit | `is_infrastructure_error` | `error_category`         |
|---------------------------------------------|------|---------------------------|--------------------------|
| `pom.xml` not found on `<branch>` (or `gh api` request failed) | 1 | `false` | `POM_NOT_FOUND`          |
| Version doesn't match `X.Y.Z[-SNAPSHOT[.N]]`                   | 1 | `false` | `INVALID_VERSION_FORMAT` |

`is_infrastructure_error` and the `INFRASTRUCTURE` category remain in the output schema for backwards compatibility with callers wired to suppress team-channel notifications on transient mvn flakes (see [RANCHER-2962](https://folio-org.atlassian.net/browse/RANCHER-2962)). Since the implementation no longer invokes `mvn`, that failure class is structurally absent and the flag is always `false`.

## Version Format Support

This action supports Maven versions following these patterns:

### Release Versions
- `1.0.0` → Major: 1, Minor: 0, Patch: 0
- `2.3.5` → Major: 2, Minor: 3, Patch: 5

### SNAPSHOT Versions
- `1.0.0-SNAPSHOT` → Major: 1, Minor: 0, Patch: 0, is_snapshot: SNAPSHOT
- `1.0.0-SNAPSHOT.123` → Major: 1, Minor: 0, Patch: 0, is_snapshot: SNAPSHOT, build_number: 123

## How It Works

1. **POM Fetch**: Reads `pom.xml` from `repos/<app_name>/contents/pom.xml?ref=<branch>` via the GitHub Contents API (`gh api`) — no repository checkout, no Maven invocation
2. **POM Parse**: `awk` finds the first `<version>` element outside any `<parent>` block (the project's own version)
3. **Version Validation**: Validates the version follows semantic versioning patterns
4. **Component Parsing**: Breaks down the version into individual components
5. **Output Generation**: Provides all components as action outputs

## Requirements

### Repository Structure
The target repository must:
- Have a `pom.xml` file in the root
- Have the project version defined in the top-level `<version>` element (not inside a `<parent>` block)
- Follow semantic versioning conventions

### Permissions
The calling workflow needs appropriate permissions:

```yaml
permissions:
  contents: read     # To read pom.xml via the GitHub Contents API
```

## Error Handling

The action provides clear error messages for common issues:

- **Missing pom.xml**: If the repository doesn't contain a `pom.xml` file
- **Invalid version format**: If the version doesn't follow semantic versioning
- **Could not extract project `<version>`**: If `pom.xml` exists but no top-level `<version>` element is found outside `<parent>` (rare; usually means a malformed pom)

## Use Cases

### Release Preparation
Collect current versions before calculating next release versions:

```yaml
- name: Collect Current Versions
  id: versions
  uses: folio-org/kitfox-github/.github/actions/collect-app-version@main
  with:
    app_name: folio-org/${{ matrix.application }}
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
  id: platform
  uses: folio-org/kitfox-github/.github/actions/collect-app-version@main
  with:
    app_name: folio-org/app-platform-complete
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
    app_name: folio-org/${{ matrix.app }}
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

**Could not extract project `<version>`**
- The first `<version>` element outside any `<parent>` block is treated as the project version. If your pom has neither, the action fails with `INVALID_VERSION_FORMAT`.
- Inspect the pom: there must be a top-level `<version>X.Y.Z[-SNAPSHOT[.N]]</version>` element.

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