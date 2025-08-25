# Workflow Implementation Guide

**kitfox-github Workflow Infrastructure** - Implementation details, usage patterns, and technical documentation for reusable GitHub Actions workflows.

## 🎯 Overview

This directory contains the **workflow infrastructure** that powers FOLIO's distributed CI/CD operations. These workflows are designed to be called from other repositories across the FOLIO ecosystem, providing standardized, secure, and efficient automation.

## 🏗️ Workflow Architecture

### Reusable Workflow Pattern

All workflows in this repository follow the `workflow_call` pattern, enabling:

- **🔄 Cross-Repository Reuse**: Called from multiple FOLIO repositories
- **🛡️ Security Separation**: Authorization handled by calling repositories
- **📊 Result Aggregation**: Structured outputs for orchestrator consumption
- **🧪 Testing Support**: Built-in dry-run capabilities for safe validation

### Distributed Coordination Model

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Orchestrator   │    │  Shared Infra   │    │  Worker Repos   │
│  (platform-lsp) │───▶│  (kitfox-github)│◀───│  (app-*)        │
│                 │    │                 │    │                 │
│ • Authorization │    │ • Reusable      │    │ • Execution     │
│ • Coordination  │    │   Workflows     │    │ • Reporting     │
│ • Aggregation   │    │ • Actions       │    │ • Notifications │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Available Workflows

### Application Update
**File**: [`app-update.yml`](workflows/app-update.yml)  
**Purpose**: Automated module version updates and application descriptor management  
**Documentation**: [App Update Guide](docs/app-update.md)

**Key Features**:
- Automated module version discovery from FOLIO registry
- Application descriptor updates with latest module versions
- Maven artifact generation and validation
- FAR registry integration and publishing
- Comprehensive validation and rollback handling
- Dry-run support for safe testing

### Application Update Notification
**File**: [`app-update-notification.yml`](workflows/app-update-notification.yml)  
**Purpose**: Rich Slack notifications for application update operations  
**Documentation**: [App Update Notification Guide](docs/app-update-notification.md)

**Key Features**:
- Detailed update notifications with module-level changes
- Success and failure message templates with rich formatting
- Direct links to commits, descriptors, and workflow runs
- Integration with Eureka CI Slack channels

### Application Release Preparation
**File**: [`app-release-preparation.yml`](workflows/app-release-preparation.yml)  
**Purpose**: Standardized release branch preparation for FOLIO applications  
**Documentation**: [App Release Preparation Guide](docs/app-release-preparation.md)

**Key Features**:
- Maven version extraction and validation
- Release branch creation and preparation
- Application descriptor updates with placeholder versions
- Git operations with proper commit messages
- Dry-run support for safe testing

### Application Release Notification
**File**: [`app-release-preparation-notification.yml`](workflows/app-release-preparation-notification.yml)  
**Purpose**: Standardized Slack notifications for application operations  
**Documentation**: [App Notification Guide](docs/app-notification.md)

**Key Features**:
- Slack notification with rich formatting
- Success and failure message templates
- Application context and operation details
- Integration with FOLIO Slack channels

## 🔧 Universal Actions

### Core Infrastructure Actions

Each action includes comprehensive documentation with usage examples, input/output specifications, and implementation details.

#### Orchestrate External Workflow
**Documentation**: [`actions/orchestrate-external-workflow/README.md`](actions/orchestrate-external-workflow/README.md)  
**Purpose**: Universal workflow triggering and monitoring across repositories  
**Key Features**: UUID dispatch tracking, YAML parameters, polling with timeout, exit status monitoring

#### Validate Team Membership
**Documentation**: [`actions/validate-team-membership/README.md`](actions/validate-team-membership/README.md)  
**Purpose**: Team-based authorization for critical operations  
**Key Features**: Real-time team validation, multi-org support, boolean authorization output, comprehensive logging

#### Collect Application Version
**Documentation**: [`actions/collect-app-version/README.md`](actions/collect-app-version/README.md)  
**Purpose**: Maven version extraction and semantic version parsing  
**Key Features**: Maven version extraction, semantic parsing, cross-repo collection, SNAPSHOT support

## 🛡️ Security Implementation

### Authorization Pattern

**Critical Principle**: Reusable workflows in kitfox-github **NEVER** contain authorization logic.

```yaml
# ✅ CORRECT: Authorization in calling repository
jobs:
  validate-authorization:
    uses: folio-org/kitfox-github/.github/actions/validate-team-membership@main
    with:
      username: ${{ github.actor }}

  execute-operation:
    needs: validate-authorization
    if: needs.validate-authorization.outputs.authorized == 'true'
    uses: folio-org/kitfox-github/.github/workflows/app-release-preparation.yml@main
```

### Security Boundaries

- **Team Validation**: Always performed by calling repository
- **Token Management**: App tokens generated in calling context
- **Audit Trail**: Authorization decisions logged in orchestrator
- **Fail-Closed Design**: Unauthorized access denied by default

## 📊 Usage Patterns

### Standard Calling Pattern

```yaml
name: 'Application Operation'

on:
  workflow_dispatch:
    inputs:
      app_name:
        description: 'Application name'
        required: true

jobs:
  validate-actor:
    runs-on: ubuntu-latest
    outputs:
      authorized: ${{ steps.validate.outputs.authorized }}
    steps:
      - name: 'Validate Team Membership'
        id: validate
        uses: folio-org/kitfox-github/.github/actions/validate-team-membership@main
        with:
          username: ${{ github.actor }}
          organization: 'folio-org'
          team: 'kitfox'

  execute-workflow:
    needs: validate-actor
    if: needs.validate-actor.outputs.authorized == 'true'
    uses: folio-org/kitfox-github/.github/workflows/app-release-preparation.yml@main
    with:
      app_name: ${{ inputs.app_name }}
      previous_release_branch: ${{ inputs.previous_release_branch }}
      new_release_branch: ${{ inputs.new_release_branch }}
      dry_run: ${{ inputs.dry_run }}

  send-notification:
    needs: [validate-actor, execute-workflow]
    if: always() && needs.validate-actor.outputs.authorized == 'true'
    uses: folio-org/kitfox-github/.github/workflows/app-release-preparation-notification.yml@main
    with:
      app_name: ${{ inputs.app_name }}
      operation_status: ${{ needs.execute-workflow.result }}
    secrets:
      slack_bot_token: ${{ secrets.SLACK_BOT_TOKEN }}
```

### Snapshot CI Pattern

```yaml
on:
  schedule:
    - cron: "*/20 * * * *"  # Automated snapshot updates

jobs:
  fetch-platform-descriptor:
    steps:
      - uses: actions/checkout@v4
        with:
          repository: folio-org/platform-lsp
          ref: snapshot
      - uses: actions/upload-artifact@v4
        with:
          name: platform-descriptor
          path: platform-descriptor.json

  update-application:
    needs: fetch-platform-descriptor
    uses: folio-org/kitfox-github/.github/workflows/app-update.yml@master
    with:
      app_name: ${{ github.event.repository.name }}
      repo: ${{ github.repository }}
      workflow_run_number: ${{ github.run_number }}
    secrets: inherit

  notify-results:
    needs: update-application
    if: always() && needs.update-application.outputs.updated == 'true'
    uses: folio-org/kitfox-github/.github/workflows/app-update-notification.yml@master
    with:
      app_name: ${{ github.event.repository.name }}
      repo: ${{ github.repository }}
      new_version: ${{ needs.update-application.outputs.new_version }}
      previous_version: ${{ needs.update-application.outputs.previous_version }}
      workflow_result: ${{ needs.update-application.result }}
      slack_notif_channel: ${{ vars.SLACK_NOTIF_CHANNEL }}
    secrets: inherit
```

### Matrix Orchestration Pattern

```yaml
strategy:
  matrix:
    application: ${{ fromJson(needs.setup.outputs.applications) }}
  fail-fast: false    # Continue processing other apps if one fails
  max-parallel: 5     # Standard concurrency limit for distributed operations

steps:
  - name: 'Process Application'
    uses: folio-org/kitfox-github/.github/actions/orchestrate-external-workflow@main
    with:
      repository: 'folio-org/${{ matrix.application }}'
      workflow_file: 'app-release-preparation.yml'
      workflow_branch: 'master'
      workflow_parameters: |
        previous_release_branch: ${{ inputs.previous_release_branch }}
        new_release_branch: ${{ inputs.new_release_branch }}
        dry_run: ${{ inputs.dry_run }}
```

## 🧪 Testing and Validation

### Dry-Run Support

All reusable workflows support `dry_run` parameter:

```yaml
inputs:
  dry_run:
    description: 'Perform dry run without making changes'
    required: false
    type: boolean
    default: false
```

**Dry-Run Behavior**:
- Validation steps execute normally
- Git operations are simulated (no actual commits/pushes)
- Notifications include "DRY RUN" indicators
- Results are logged but not persisted

### Testing Strategy

1. **Individual Workflow Testing**: Test each workflow in isolation with dry-run
2. **Integration Testing**: Test calling patterns from multiple repositories
3. **Matrix Testing**: Validate distributed operations across multiple applications
4. **Authorization Testing**: Verify security boundaries with different user contexts

## 📚 Detailed Documentation

### Workflow-Specific Guides

- **[App Update](docs/app-update.md)**: Automated module updates and descriptor management
- **[App Update Notification](docs/app-update-notification.md)**: Rich Slack notifications for update operations
- **[App Release Preparation](docs/app-release-preparation.md)**: Complete guide to release preparation workflow
- **[App Notification](docs/app-notification.md)**: Slack notification patterns and customization
- **[Distributed Orchestration](docs/distributed-orchestration.md)**: Cross-repository coordination patterns
- **[Security Implementation](docs/security-implementation.md)**: Authorization and access control patterns

### Implementation References

- **[FOLIO Release Process](https://folio-org.atlassian.net/wiki/spaces/FOLIJET/pages/886178625/Release+preparation)**: Official release preparation documentation
- **[Eureka CI Flow](https://folio-org.atlassian.net/wiki/spaces/FOLIJET/pages/887488514/CI+flow+release)**: FOLIO CI/CD process overview
- **[Slack Integration](https://api.slack.com/messaging/composing)**: Slack message formatting and best practices

## 🔄 Workflow Evolution

### Adding New Workflows

**Requirements Checklist**:
- [ ] Evidence of reuse across 3+ repositories
- [ ] Clear `workflow_call` interface with typed inputs
- [ ] Comprehensive README.md with usage examples
- [ ] Dry-run support for safe testing
- [ ] Security review and authorization boundary analysis
- [ ] Integration testing across multiple calling repositories

### Maintenance Guidelines

- **Backward Compatibility**: Maintain input/output interfaces
- **Version Tagging**: Use semantic versioning for breaking changes
- **Documentation Updates**: Keep workflow documentation synchronized
- **Security Reviews**: Regular audit of authorization patterns

---

**Infrastructure Team**: Kitfox DevOps  
**Last Updated**: August 2025  
**Purpose**: Workflow Implementation and Usage Guide
