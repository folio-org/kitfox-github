# Orchestrate External Workflow

A universal GitHub Action for triggering, tracking, and waiting for completion of workflows in external repositories. This action provides a robust workflow orchestration pattern with automatic retry, timeout handling, and comprehensive status reporting.

## Features

- **Universal workflow triggering**: Works with any repository and workflow file
- **YAML parameter format**: Clean, readable parameter passing
- **Automatic tracking**: Uses UUID dispatch IDs for reliable workflow identification
- **Timeout support**: Configurable timeout with GitHub Actions default fallback
- **Comprehensive logging**: Grouped output with clear status messages
- **Error handling**: Detailed error reporting for failed workflows

## Usage

### Basic Example

```yaml
- name: Trigger Release Preparation
  uses: folio-org/kitfox-github/.github/actions/orchestrate-external-workflow@main
  with:
    repository: folio-org/app-platform-minimal
    workflow_file: app-release-preparation.yml
    workflow_branch: main
    workflow_parameters: |
      previous_release_branch: R2-2024
      new_release_branch: R1-2025
      dry_run: false
```

### Complete Example with All Parameters

```yaml
- name: Orchestrate External Workflow
  id: external-workflow
  uses: folio-org/kitfox-github/.github/actions/orchestrate-external-workflow@main
  with:
    repository: folio-org/target-repository
    workflow_file: my-workflow.yml
    workflow_branch: feature-branch
    timeout_minutes: 60
    workflow_parameters: |
      environment: staging
      version: 1.2.3
      deploy_mode: blue-green
      notifications: true

- name: Check Result
  run: |
    echo "Workflow Status: ${{ steps.external-workflow.outputs.status }}"
    echo "Run ID: ${{ steps.external-workflow.outputs.run_id }}"
    echo "Dispatch ID: ${{ steps.external-workflow.outputs.dispatch_id }}"
```

### Matrix Strategy Example

```yaml
jobs:
  orchestrate-multiple:
    strategy:
      matrix:
        application: [app-platform-minimal, app-acquisitions, app-agreements]
      fail-fast: false
    steps:
      - name: Trigger Application Workflow
        uses: folio-org/kitfox-github/.github/actions/orchestrate-external-workflow@main
        with:
          repository: folio-org/${{ matrix.application }}
          workflow_file: release-workflow.yml
          workflow_branch: ${{ env.TARGET_BRANCH }}
          workflow_parameters: |
            release_version: ${{ inputs.version }}
            environment: production
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `repository` | Target repository in `org/repo-name` format | ✅ | - |
| `workflow_file` | Workflow filename (e.g., `my-workflow.yml`) | ✅ | - |
| `workflow_branch` | Branch to trigger workflow on | ✅ | - |
| `workflow_parameters` | YAML string of key-value pairs for workflow inputs | ❌ | `''` |
| `timeout_minutes` | Minutes to wait for workflow completion | ❌ | GitHub Actions default (360 minutes) |

### YAML Parameters Format

The `workflow_parameters` input accepts YAML format for clean, readable parameter definition:

```yaml
workflow_parameters: |
  parameter_one: value1
  parameter_two: value2
  boolean_param: true
  numeric_param: 42
  github_expression: ${{ inputs.some_input }}
```

These are automatically converted to GitHub CLI `-f` flags:
```bash
gh workflow run workflow.yml -f parameter_one=value1 -f parameter_two=value2 -f boolean_param=true
```

## Outputs

| Output | Description |
|--------|-------------|
| `dispatch_id` | Generated UUID for tracking the triggered workflow |
| `run_id` | GitHub run ID of the triggered workflow |

## How It Works

1. **Generate Dispatch ID**: Creates a unique UUID for tracking
2. **Parse Parameters**: Converts YAML parameters to CLI flags using `yq`
3. **Trigger Workflow**: Uses `gh workflow run` with the target repository
4. **Poll for Run ID**: Waits up to 5 minutes for the workflow to appear
5. **Watch Completion**: Monitors workflow execution until completion or timeout

## Requirements

### GitHub CLI
This action uses the GitHub CLI (`gh`) which is pre-installed on GitHub runners.

### YQ
The action uses `yq` for YAML processing, which is available on GitHub runners by default.

### Permissions
The calling workflow needs appropriate permissions:

```yaml
permissions:
  actions: read      # To trigger workflows
  contents: read     # To access repositories
```

### Authentication
The action uses the standard `GITHUB_TOKEN` for authentication. For cross-organization workflows, you may need a personal access token with appropriate permissions.

## Error Handling

The action provides detailed error reporting:

- **Workflow not found**: If the target workflow doesn't exist or can't be triggered
- **Run ID timeout**: If the workflow doesn't appear within 5 minutes
- **Workflow failure**: If the target workflow fails execution
- **Timeout**: If the workflow exceeds the specified timeout

## Use Cases

### Release Orchestration
Coordinate release preparation across multiple repositories:

```yaml
- name: Trigger Application Releases
  uses: folio-org/kitfox-github/.github/actions/orchestrate-external-workflow@main
  with:
    repository: folio-org/${{ matrix.app }}
    workflow_file: release-preparation.yml
    workflow_branch: ${{ inputs.release_branch }}
    workflow_parameters: |
      version: ${{ inputs.version }}
      create_release: true
```

### Environment Deployment
Deploy applications to specific environments:

```yaml
- name: Deploy to Staging
  uses: folio-org/kitfox-github/.github/actions/orchestrate-external-workflow@main
  with:
    repository: folio-org/platform-complete
    workflow_file: deploy.yml
    workflow_branch: main
    timeout_minutes: 30
    workflow_parameters: |
      environment: staging
      version: ${{ github.sha }}
      rollback_enabled: true
```

### Testing Coordination
Trigger test suites across multiple repositories:

```yaml
- name: Run Integration Tests
  uses: folio-org/kitfox-github/.github/actions/orchestrate-external-workflow@main
  with:
    repository: folio-org/integration-tests
    workflow_file: full-suite.yml
    workflow_branch: main
    workflow_parameters: |
      test_environment: ${{ inputs.environment }}
      parallel_execution: true
      report_format: junit
```

## Best Practices

### Unique Dispatch IDs
The action automatically generates unique dispatch IDs for reliable workflow tracking. This prevents confusion when multiple workflows are triggered simultaneously.

### Timeout Configuration
- Use shorter timeouts for quick operations (5-15 minutes)
- Use longer timeouts for complex workflows (30-60 minutes)
- Omit timeout for critical operations that should not be interrupted

### Parameter Organization
Organize parameters logically in YAML format:

```yaml
workflow_parameters: |
  # Environment settings
  environment: production
  region: us-east-1
  
  # Application configuration
  version: 1.2.3
  features_enabled: true
  
  # Deployment options
  rollback_enabled: true
  health_check_timeout: 300
```

### Error Recovery
Always check the action outputs for proper error handling:

```yaml
- name: Handle Workflow Failure
  if: steps.orchestrate.outputs.status == 'failure'
  run: |
    echo "Workflow failed. Implementing rollback..."
    # Rollback logic here
```

## Troubleshooting

### Common Issues

**Workflow not found**
- Verify the repository and workflow file exist
- Check branch permissions and workflow file presence on target branch
- Ensure the calling token has access to the target repository

**Timeout during polling**
- The target workflow may not support dispatch_id tracking
- Network delays or high GitHub API load
- Verify the workflow is actually triggered by checking the target repository

**Permission denied**
- Verify the GitHub token has appropriate permissions
- For cross-organization workflows, use a personal access token
- Check repository visibility and access settings

## Contributing

This action is part of the FOLIO Kitfox infrastructure. For issues or improvements:

1. Create an issue in the kitfox-github repository
2. Follow FOLIO contribution guidelines
3. Include Kitfox team members in reviews

## License

Apache License 2.0 - See the LICENSE file in the repository root. 