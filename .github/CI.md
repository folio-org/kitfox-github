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
│                   High-Level Orchestrators                  │
│  • application-update.yml (unified)                         │
│  • release-preparation.yml                                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        Flow Layer                           │
│  • application-update-flow.yml                              │
│  • release-pr-check.yml                                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Core Utilities                         │
│  • commit-and-push-changes.yml                              │
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

#### Application Update
**File**: [`application-update.yml`](workflows/application-update.yml)
**Purpose**: Unified configuration-driven orchestrator for updating FOLIO application module dependencies across all branch types
**Documentation**: [Application Update Guide](docs/application-update.md)

**Key Features**:
- Configuration-driven behavior from `update-config.yml`
- Supports all branch types (snapshot, release, custom)
- Handles both direct commits and PR-based updates
- Flexible pre-release mode (true/false/only)
- Built-in Slack notifications (team and general channels)
- Comprehensive workflow summary generation
- Platform descriptor integration
- FAR registry support
- Dry-run mode for testing

#### Release Preparation
**File**: [`release-preparation.yml`](workflows/release-preparation.yml)
**Purpose**: Release branch creation and preparation with template-based version management
**Documentation**: [Release Preparation Guide](docs/release-preparation.md)

**Key Features**:
- Creates new release branches from previous releases or snapshots
- **Template-based approach**: Updates `application.template.json` with `^VERSION` placeholders
- **State file management**: Deletes generated state files (application.lock.json) for CI regeneration
- **Update configuration**: Manages `update-config.yml` to track branches for automatic updates
- **GitHub API integration**: Dynamic default branch detection using GitHub API
- Handles both snapshot and release version sources
- Updates Maven pom.xml version if present
- Separate commits for release branch and configuration updates
- Comprehensive Git operations with error handling
- Dry-run support for safe testing

### Flow Layer

#### Application Update Flow
**File**: [`application-update-flow.yml`](workflows/application-update-flow.yml)
**Purpose**: Core application update flow implementation for all branch types
**Documentation**: [Application Update Flow Guide](docs/application-update-flow.md)

**Key Features**:
- Coordinates update, verification, and commit operations
- Module version discovery from FOLIO registry
- Supports both direct commits and PR-based updates
- Application descriptor generation and validation
- FAR registry integration
- Platform descriptor fetching and validation
- Rollback handling on failures
- Comprehensive output for upstream workflows

### Core Utility Workflows

#### Commit and Push Changes
**File**: [`commit-and-push-changes.yml`](workflows/commit-and-push-changes.yml)
**Purpose**: Generic Git operations for committing and pushing changes
**Documentation**: [Commit and Push Changes Guide](docs/commit-and-push-changes.md)

**Key Features**:
- Atomic Git operations with error handling
- Standardized commit message formatting
- Branch management and pushing
- **File deletion**: Supports deleting specified files before commit (multiline list format)
- Source branch specification for new branch creation
- GitHub App or standard token authentication
- Dry-run support for validation
- Rollback capabilities

#### Validate Application
**Action**: [`validate-application`](actions/validate-application/)
**Purpose**: Application descriptor validation
**Documentation**: [Validate Application Action README](actions/validate-application/README.md)

**Key Features**:
- Application descriptor validation
- Module interface integrity checks
- Conditional dependency validation
- Comprehensive error reporting
- Integration with FAR registry for validation

#### Publish Application Descriptor
**Action**: [`publish-app-descriptor`](actions/publish-app-descriptor/)
**Purpose**: Publish application descriptors to FAR
**Documentation**: [Publish Application Descriptor README](actions/publish-app-descriptor/README.md)

**Key Features**:
- Publishes validated descriptors to FAR
- Supports artifact and file path inputs
- Unique temporary directories to avoid conflicts
- Comprehensive error handling

#### Unpublish Application Descriptor
**Action**: [`unpublish-app-descriptor`](actions/unpublish-app-descriptor/)
**Purpose**: Remove application descriptors from FAR
**Documentation**: [Unpublish Application Descriptor README](actions/unpublish-app-descriptor/README.md)

**Key Features**:
- Removes descriptors from FAR registry
- Used in cleanup-on-failure scenarios
- Comprehensive error handling

#### Release PR Check
**File**: [`release-pr-check.yml`](workflows/release-pr-check.yml)
**Purpose**: Automated validation of release pull requests
**Documentation**: [Release PR Check Guide](docs/release-pr-check.md)
**Trigger**: `workflow_dispatch` (called from GitHub App webhook)

**Key Features**:
- PR validation and commit verification
- Release configuration validation
- Label-based conditional execution
- Application descriptor generation and validation
- GitHub Checks API integration with interactive re-run buttons
- Real-time status updates on PR commits
- Platform descriptor integration for validation context
- Intelligent error handling (404 vs real errors)
- Slack notifications to team and general channels

**Workflow**:
1. **Pre-Check**: Validates PR existence, commit membership, and release configuration
2. **Application Check**: Generates and validates application descriptor
3. **Notifications**: Sends status updates to configured Slack channels
4. **Summary**: Generates comprehensive workflow summary

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

##### Get PR Info
**Documentation**: [`actions/get-pr-info/README.md`](actions/get-pr-info/README.md)
**Purpose**: Fetch detailed pull request information
**Key Features**: Cross-repository support, label retrieval, branch information, state checking

##### Is Commit in PR
**Documentation**: [`actions/is-commit-in-pr/README.md`](actions/is-commit-in-pr/README.md)
**Purpose**: Verify commit SHA exists in pull request
**Key Features**: Security validation, pagination support, short/full SHA matching

#### Application Management

##### Generate Application Descriptor
**Documentation**: [`actions/generate-application-descriptor/README.md`](actions/generate-application-descriptor/README.md)
**Purpose**: Generate or update FOLIO application descriptors using template-driven version resolution
**Key Features**: Template-driven updates, semver constraint resolution, module synchronization, artifact validation, Maven integration

##### Collect Application Version
**Documentation**: [`actions/collect-app-version/README.md`](actions/collect-app-version/README.md)
**Purpose**: Maven version extraction and semantic version parsing
**Key Features**: POM.xml parsing, semantic version handling, version state detection

#### Configuration and Security

##### Get Release Config
**Documentation**: [`actions/get-update-config/README.md`](actions/get-update-config/README.md)
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
  update-application:
    uses: folio-org/kitfox-github/.github/workflows/application-update.yml@master
    with:
      app_name: ${{ github.event.repository.name }}
      repo: ${{ github.repository }}
      branch: 'snapshot'
      pre_release: 'only'
      workflow_run_number: ${{ github.run_number }}
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
- **[Application Update](docs/application-update.md)**: Unified configuration-driven application update orchestrator
- **[Release Preparation](docs/release-preparation.md)**: Release branch creation and setup

#### Flow Layer
- **[Application Update Flow](docs/application-update-flow.md)**: Core application update flow implementation

#### Core Utilities
- **[Commit and Push Changes](docs/commit-and-push-changes.md)**: Git operations management
- **[Release PR Check](docs/release-pr-check.md)**: Automated PR validation with GitHub Checks integration
- **[Validate Application Action](actions/validate-application/README.md)**: Application descriptor validation
- **[Publish Application Descriptor](actions/publish-app-descriptor/README.md)**: Publish descriptors to FAR
- **[Unpublish Application Descriptor](actions/unpublish-app-descriptor/README.md)**: Remove descriptors from FAR


### Implementation References

- **[FOLIO Release Process](https://folio-org.atlassian.net/wiki/spaces/FOLIJET/pages/886178625/Release+preparation)**: Official release preparation documentation
- **[Eureka CI Flow](https://folio-org.atlassian.net/wiki/spaces/FOLIJET/pages/887488514/CI+flow+release)**: FOLIO CI/CD process overview
- **[Slack Integration](https://api.slack.com/messaging/composing)**: Slack message formatting and best practices

---

**Infrastructure Team**: Kitfox DevOps
**Last Updated**: November 2025
**Purpose**: Workflow Implementation and Usage Guide
