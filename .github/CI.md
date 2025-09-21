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

### Workflow Hierarchy

The workflows follow a layered architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                   High-Level Orchestrators                   │
│  • snapshot-update.yml                                       │
│  • release-update.yml                                        │
│  • release-preparation.yml                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Mid-Level Orchestrators                    │
│  • app-update.yml                                           │
│  • release-update-flow.yml                                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Core Utilities                          │
│  • update-application.yml                                    │
│  • commit-application-changes.yml                           │
│  • verify-application.yml                                   │
│  • compare-applications.yml                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       Notifications                          │
│  • release-preparation-notification.yml                      │
│  • Integrated notifications in orchestrator workflows        │
└─────────────────────────────────────────────────────────────┘
```

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

### High-Level Orchestrators

#### Snapshot Update
**File**: [`snapshot-update.yml`](workflows/snapshot-update.yml)
**Purpose**: Complete snapshot update workflow with integrated notifications
**Documentation**: [Snapshot Update Guide](docs/snapshot-update.md)

**Key Features**:
- Orchestrates the complete snapshot update process
- Integrates platform descriptor fetching
- Built-in Slack notifications (team and general channels)
- Comprehensive workflow summary generation
- Notification status tracking and reporting
- Support for scheduled and manual triggers
- FAR registry support

#### Release Update
**File**: [`release-update.yml`](workflows/release-update.yml)
**Purpose**: Release branch scanning and update orchestration
**Documentation**: [Release Update Guide](docs/release-update.md)

**Key Features**:
- Scans release branches for required updates
- Creates pull requests for module updates
- Integrated Slack notifications with status tracking
- Comprehensive summary generation
- Support for dry-run mode
- Reviewer and label management for PRs

#### Release Preparation
**File**: [`release-preparation.yml`](workflows/release-preparation.yml)
**Purpose**: Release branch creation and preparation
**Documentation**: [Release Preparation Guide](docs/release-preparation.md)

**Key Features**:
- Creates new release branches from previous releases or snapshots
- Updates application versions for release
- Handles both snapshot and release version sources
- Comprehensive Git operations with error handling
- Dry-run support for safe testing

### Mid-Level Orchestrators

#### Application Update
**File**: [`app-update.yml`](workflows/app-update.yml)
**Purpose**: Core application update orchestration
**Documentation**: [App Update Guide](docs/app-update.md)

**Key Features**:
- Coordinates update, verification, and commit operations
- Module version discovery from FOLIO registry
- Application descriptor generation and validation
- FAR registry integration
- Rollback handling on failures
- Comprehensive output for upstream workflows

#### Release Update Flow
**File**: [`release-update-flow.yml`](workflows/release-update-flow.yml)
**Purpose**: Release branch update workflow implementation
**Documentation**: [Release Update Flow Guide](docs/release-update-flow.md)

**Key Features**:
- Manages the complete release update flow
- Version comparison between branches
- Pull request creation and management
- Reviewer assignment with fallback handling
- Label management for PRs

### Core Utility Workflows

#### Update Application
**File**: [`update-application.yml`](workflows/update-application.yml)
**Purpose**: Core application descriptor update logic
**Documentation**: [Update Application Guide](docs/update-application.md)

**Key Features**:
- Module version resolution from registry
- Application descriptor generation
- Version management and validation
- Platform descriptor integration
- Detailed change tracking

#### Commit Application Changes
**File**: [`commit-application-changes.yml`](workflows/commit-application-changes.yml)
**Purpose**: Git operations for application updates
**Documentation**: [Commit Application Changes Guide](docs/commit-application-changes.md)

**Key Features**:
- Atomic Git operations with error handling
- Standardized commit message formatting
- Branch management and pushing
- Dry-run support for validation
- Rollback capabilities

#### Verify Application
**File**: [`verify-application.yml`](workflows/verify-application.yml)
**Purpose**: Application validation and registry upload
**Documentation**: [Verify Application Guide](docs/verify-application.md)

**Key Features**:
- Application descriptor validation
- Maven artifact verification
- Registry upload capabilities
- Comprehensive error reporting
- Integration with FAR registry

#### Compare Applications
**File**: [`compare-applications.yml`](workflows/compare-applications.yml)
**Purpose**: Version comparison and change detection
**Documentation**: [Compare Applications Guide](docs/compare-applications.md)

**Key Features**:
- Cross-branch version comparison
- Module change detection
- Detailed diff generation
- Support for artifact comparison
- Structured output for upstream processing

### Notification Workflows

#### Release Preparation Notification
**File**: [`release-preparation-notification.yml`](workflows/release-preparation-notification.yml)
**Purpose**: Slack notifications for release preparation
**Documentation**: [Release Preparation Notification Guide](docs/release-preparation-notification.md)

**Key Features**:
- Rich Slack message formatting
- Success and failure templates
- Direct links to branches and commits
- Error handling for notification failures
- Output status for tracking

## 🔧 Universal Actions

### Core Infrastructure Actions

Each action includes comprehensive documentation with usage examples, input/output specifications, and implementation details.

#### Workflow Orchestration

##### Orchestrate External Workflow
**Documentation**: [`actions/orchestrate-external-workflow/README.md`](actions/orchestrate-external-workflow/README.md)
**Purpose**: Universal workflow triggering and monitoring across repositories
**Key Features**: UUID dispatch tracking, YAML parameters, polling with timeout, exit status monitoring

#### Pull Request Management

##### Create PR
**Documentation**: [`actions/create-pr/README.md`](actions/create-pr/README.md)
**Purpose**: Automated pull request creation with duplicate detection
**Key Features**: Label management, reviewer assignment, existing PR detection, graceful error handling

##### Update PR
**Documentation**: [`actions/update-pr/README.md`](actions/update-pr/README.md)
**Purpose**: Update existing pull requests with new content and metadata
**Key Features**: Selective updates, label and reviewer management, content preservation

#### Application Management

##### Generate Application Descriptor
**Documentation**: [`actions/generate-application-descriptor/README.md`](actions/generate-application-descriptor/README.md)
**Purpose**: Generate FOLIO application descriptors from state files
**Key Features**: Maven integration, placeholder validation, artifact upload, comprehensive validation

##### Collect Application Version
**Documentation**: [`actions/collect-app-version/README.md`](actions/collect-app-version/README.md)
**Purpose**: Maven version extraction and semantic version parsing
**Key Features**: POM.xml parsing, semantic version handling, version state detection

#### Configuration and Security

##### Get Release Config
**Documentation**: [`actions/get-release-config/README.md`](actions/get-release-config/README.md)
**Purpose**: Read and validate release configuration from repository files
**Key Features**: Branch validation, configuration parsing, dynamic workflow configuration

##### Validate Team Membership
**Documentation**: [`actions/validate-team-membership/README.md`](actions/validate-team-membership/README.md)
**Purpose**: Team-based authorization for critical operations
**Key Features**: Real-time team validation, multi-org support, boolean authorization output

## 🚀 Usage Patterns

### Calling a Reusable Workflow

```yaml
jobs:
  update-snapshot:
    uses: folio-org/kitfox-github/.github/workflows/snapshot-update.yml@master
    with:
      app_name: ${{ github.event.repository.name }}
      repo: ${{ github.repository }}
      descriptor_build_offset: '100100000000000'
      rely_on_FAR: false
      dry_run: false
    secrets: inherit
```

### Workflow Outputs

All orchestrator workflows provide structured outputs:

```yaml
outputs:
  update_result:
    description: 'Result of the update operation'
  updated:
    description: 'Whether changes were made'
  new_version:
    description: 'New application version'
  notification_outcome:
    description: 'Status of notifications'
```

### Error Handling

Workflows implement comprehensive error handling:

- **Graceful Failures**: Non-blocking notification failures
- **Rollback Support**: Automatic rollback on critical failures
- **Dry-Run Mode**: Safe testing without making changes
- **Status Tracking**: Complete status reporting through outputs

## 📚 Implementation Details

### Security Considerations

- **GitHub App Authentication**: Used for cross-repository operations
- **Secrets Management**: Inherited from calling workflows
- **Team-Based Authorization**: Critical operations require team membership
- **Token Scope Validation**: Minimal required permissions

### Performance Optimization

- **Parallel Execution**: Matrix strategies for bulk operations
- **Artifact Caching**: Reuse of platform descriptors
- **Conditional Steps**: Skip unnecessary operations
- **Concurrency Control**: Prevent duplicate runs

### Monitoring and Observability

- **Workflow Summaries**: Comprehensive GitHub Action summaries
- **Slack Notifications**: Real-time status updates
- **Structured Outputs**: Machine-readable results
- **Detailed Logging**: Step-by-step execution logs

## 📖 Documentation

### Workflow Documentation

#### High-Level Orchestrators
- **[Snapshot Update](docs/snapshot-update.md)**: Complete snapshot update process with notifications
- **[Release Update](docs/release-update.md)**: Release branch update management
- **[Release Preparation](docs/release-preparation.md)**: Release branch creation and setup

#### Mid-Level Orchestrators
- **[App Update](docs/app-update.md)**: Core application update orchestration
- **[Release Update Flow](docs/release-update-flow.md)**: Comprehensive release update implementation

#### Core Utilities
- **[Update Application](docs/update-application.md)**: Application descriptor update logic
- **[Commit Application Changes](docs/commit-application-changes.md)**: Git operations management
- **[Verify Application](docs/verify-application.md)**: Validation and registry upload
- **[Compare Applications](docs/compare-applications.md)**: Version comparison and change detection

#### Notifications
- **[Release Preparation Notification](docs/release-preparation-notification.md)**: Slack notifications for release operations

### Implementation References

- **[FOLIO Release Process](https://folio-org.atlassian.net/wiki/spaces/FOLIJET/pages/886178625/Release+preparation)**: Official release preparation documentation
- **[Eureka CI Flow](https://folio-org.atlassian.net/wiki/spaces/FOLIJET/pages/887488514/CI+flow+release)**: FOLIO CI/CD process overview
- **[Slack Integration](https://api.slack.com/messaging/composing)**: Slack message formatting and best practices

---

**Infrastructure Team**: Kitfox DevOps  
**Last Updated**: September 2025  
**Purpose**: Workflow Implementation and Usage Guide