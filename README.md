# kitfox-github

**FOLIO Infrastructure Actions & Workflows** - Shared GitHub Actions and workflow templates for the FOLIO distributed CI/CD ecosystem.

## Overview

This repository provides the core infrastructure for FOLIO's distributed release management and CI/CD workflows. It contains reusable GitHub Actions and workflow templates that enable coordinated operations across all FOLIO application repositories while maintaining clear separation of concerns and team-based authorization.

## 🎯 Key Features

- **🚀 Universal workflow orchestration** across multiple repositories
- **🔒 Team-based authorization** for critical operations
- **📊 Maven version management** with semantic version parsing
- **⚡ Distributed execution** with centralized coordination
- **🛡️ Security-first design** with fail-closed authorization

## Components

### 🔧 **Core Infrastructure Actions** (`.github/actions/`)

#### `orchestrate-external-workflow`
- **Purpose**: Universal workflow triggering, tracking, and completion monitoring
- **Features**: UUID dispatch tracking, YAML parameter format, timeout handling
- **Usage**: Coordinate complex operations across multiple repositories
- **Inputs**: `repository`, `workflow_file`, `workflow_branch`, `workflow_parameters` (YAML), `timeout_minutes`
- **Outputs**: `dispatch_id`, `run_id`
- **📖 [Full Documentation](/.github/actions/orchestrate-external-workflow/README.md)**

#### `collect-app-version`
- **Purpose**: Extract and parse Maven application versions from FOLIO repositories
- **Features**: Semantic version breakdown, SNAPSHOT support, cross-repo collection
- **Usage**: Version management for release preparation and compatibility checking
- **Inputs**: `app_name`, `branch`, `token`
- **Outputs**: `version`, `major`, `minor`, `patch`, `is_snapshot`, `build_number`
- **📖 [Full Documentation](/.github/actions/collect-app-version/README.md)**

#### `validate-team-membership`
- **Purpose**: Team-based authorization for sensitive workflows
- **Features**: GitHub team membership validation, secure fail-closed design
- **Usage**: Ensure only authorized team members can execute critical operations
- **Inputs**: `username`, `organization` (default: folio-org), `team` (default: kitfox), `token`
- **Outputs**: `authorized` (true/false)
- **📖 [Full Documentation](/.github/actions/validate-team-membership/README.md)**

### 📋 **Reusable Workflows** (`.github/workflows/`)

#### `app-release-preparation.yml`
- **Purpose**: Complete application release preparation workflow
- **Features**:
  - ✅ Application version determination based on FOLIO release patterns
  - ✅ Release branch creation and management
  - ✅ File updates (pom.xml, *.template.json) with version changes
  - ✅ Automated commit and push operations
  - ✅ Dry-run support for testing
  - ✅ Result artifact generation for orchestrator consumption
- **Usage**: Called by individual application repositories for release preparation

#### `app-release-preparation-notification.yml`
- **Purpose**: Centralized Slack notification service for application release workflows
- **Features**:
  - ✅ SUCCESS and FAILURE notification support
  - ✅ Rich Slack message formatting with workflow details
  - ✅ Clickable links to repositories, branches, and commits
  - ✅ Workflow run tracking with GitHub URLs
  - ✅ Conditional execution based on workflow result
- **Usage**: Called by application repositories to send standardized Slack notifications

## Architecture

### FOLIO Distributed CI/CD Architecture

The FOLIO ecosystem uses a **distributed orchestration pattern** with the `orchestrate-external-workflow` action providing universal workflow coordination:

```
┌─────────────────────────────────────────────────────────────┐
│ platform-lsp (Central Orchestrator)                         │
├─────────────────────────────────────────────────────────────┤
│ 🎯 release-preparation.yml                                  │
│   ├── Team Authorization (validate-team-membership)         │
│   ├── Release Planning & Validation                         │
│   ├── Application Matrix Orchestration                      │
│   │   └── orchestrate-external-workflow ────────────────┐   │
│   ├── Result Collection & Aggregation                   │   │
│   └── Platform-Level Slack Notifications                │   │
└─────────────────────────────────────────────────────────│───┘
                                                          │
            UUID Dispatch Tracking + YAML Parameters      │
                                                          ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ app-minimal  │    │ app-complete │    │ app-*        │
├──────────────┤    ├──────────────┤    ├──────────────┤
│ 📋 Wrapper   │    │ 📋 Wrapper   │... │ 📋 Wrapper   │
│ Workflow     │    │ Workflow     │    │ Workflow     │
│      ▼       │    │      ▼       │    │      ▼       │
│ 🏭 app-      │    │ 🏭 app-     │     │ 🏭 app-      │
│ release-     │    │ release-     │    │ release-     │
│ preparation  │    │ preparation  │    │ preparation  │
│ (shared)     │    │ (shared)     │    │ (shared)     │
│      ▼       │    │      ▼       │    │      ▼       │
│ 📢 slack-    │    │ 📢 slack-    │    │ 📢 slack-    │
│ notification │    │ notification │    │ notification │
│ (shared)     │    │ (shared)     │    │ (shared)     │
└──────────────┘    └──────────────┘    └──────────────┘
       ▲                     ▲                   ▲
       │ uses: kitfox-github/.github/workflows/  │
       └─────────────────────────────────────────┘
```

**Architecture Benefits**:
- **🎯 Centralized Orchestration**: Platform-lsp coordinates all operations with single entry point
- **⚡ Distributed Execution**: Applications process independently with fault isolation
- **🔍 Universal Tracking**: UUID dispatch IDs enable reliable workflow monitoring
- **📊 Semantic Coordination**: YAML parameters provide clean, readable configuration
- **🛡️ Security Boundaries**: Team authorization enforced at orchestration level
- **🔄 Parallel Processing**: Matrix strategy enables concurrent application updates
- **📢 Dual Notifications**: Both platform-level and individual app notifications via reusable workflows
- **📈 Result Aggregation**: Centralized collection of distributed execution results

## Usage Patterns

### 🎯 **Universal Workflow Orchestration**

Using the `orchestrate-external-workflow` action for distributed operations:

```yaml
# Platform orchestrator example
- name: Trigger Application Release Preparation
  uses: folio-org/kitfox-github/.github/actions/orchestrate-external-workflow@main
  with:
    repository: folio-org/${{ matrix.application }}
    workflow_file: app-release-preparation.yml
    workflow_branch: ${{ env.DOWNSTREAM_WF_BRANCH }}
    workflow_parameters: |
      previous_release_branch: ${{ inputs.previous_release_branch }}
      new_release_branch: ${{ inputs.new_release_branch }}
      use_snapshot_fallback: ${{ inputs.use_snapshot_fallback }}
      dry_run: ${{ inputs.dry_run }}
```

### 🔒 **Team Authorization Pattern**

Implementing security-first workflow design:

```yaml
jobs:
  authorize:
    runs-on: ubuntu-latest
    outputs:
      authorized: ${{ steps.team-check.outputs.authorized }}
    steps:
      - name: Validate Kitfox Team Membership
        id: team-check
        uses: folio-org/kitfox-github/.github/actions/validate-team-membership@main
        with:
          username: ${{ github.actor }}
          team: kitfox
          token: ${{ secrets.GITHUB_TOKEN }}

  release-preparation:
    needs: authorize
    if: needs.authorize.outputs.authorized == 'true'
    runs-on: ubuntu-latest
    # ... protected operations
```

### 📊 **Version Management Pattern**

Collecting and managing application versions:

```yaml
- name: Collect Application Version
  id: app-version
  uses: folio-org/kitfox-github/.github/actions/collect-app-version@main
  with:
    app_name: ${{ matrix.application }}
    branch: ${{ inputs.previous_release_branch }}

- name: Calculate Next Version
  run: |
    current_major=${{ steps.app-version.outputs.major }}
    next_major=$((current_major + 1))
    echo "Next version: ${next_major}.0.0"
```

### 📢 **Reusable Slack Notification Pattern**

Centralized notification service for consistent Slack messaging:

```yaml
# Application workflows using reusable Slack notifications
slack_notification:
  name: Slack Notification
  needs: prepare-app-release
  if: always() && inputs.dry_run == false && vars.SLACK_NOTIF_CHANNEL != ''
  uses: folio-org/kitfox-github/.github/workflows/app-release-preparation-notification.yml@main
  with:
    app_name: ${{ github.repository }}
    new_release_branch: ${{ inputs.new_release_branch }}
    source_branch: ${{ needs.prepare-app-release.outputs.source_branch }}
    app_version: ${{ needs.prepare-app-release.outputs.app_version }}
    commit_sha: ${{ needs.prepare-app-release.outputs.commit_sha }}
    workflow_result: ${{ needs.prepare-app-release.result }}
    workflow_run_id: ${{ github.run_id }}
    workflow_run_number: ${{ github.run_number }}
    slack_notif_channel: ${{ vars.SLACK_NOTIF_CHANNEL }}
  secrets: inherit
```

### 🏭 **Application Repository Integration**

Minimal wrapper workflows in application repositories:

```yaml
# app-*/.github/workflows/app-release-preparation.yml
name: Application Release Branch Preparation
on:
  workflow_dispatch:
    inputs:
      dispatch_id: { required: true, type: string }
      previous_release_branch: { required: true, type: string }
      new_release_branch: { required: true, type: string }
      dry_run: { type: boolean, default: false }

jobs:
  prepare-app-release:
    name: Prepare Application Release
    uses: folio-org/kitfox-github/.github/workflows/app-release-preparation.yml@main
    with:
      dispatch_id: ${{ inputs.dispatch_id }}
      previous_release_branch: ${{ inputs.previous_release_branch }}
      new_release_branch: ${{ inputs.new_release_branch }}
      dry_run: ${{ inputs.dry_run }}
    secrets: inherit

  slack_notification:
    name: Slack Notification
    needs: prepare-app-release
    if: always() && inputs.dry_run == false && vars.SLACK_NOTIF_CHANNEL != ''
    uses: folio-org/kitfox-github/.github/workflows/app-release-preparation-notification.yml@main
    with:
      app_name: ${{ github.repository }}
      new_release_branch: ${{ inputs.new_release_branch }}
      source_branch: ${{ needs.prepare-app-release.outputs.source_branch }}
      app_version: ${{ needs.prepare-app-release.outputs.app_version }}
      commit_sha: ${{ needs.prepare-app-release.outputs.commit_sha }}
      workflow_result: ${{ needs.prepare-app-release.result }}
      workflow_run_id: ${{ github.run_id }}
      workflow_run_number: ${{ github.run_number }}
      slack_notif_channel: ${{ vars.SLACK_NOTIF_CHANNEL }}
    secrets: inherit
```

## 🛡️ Security & Authorization

### Team-Based Access Control

Critical FOLIO infrastructure operations require **team-based authorization**:

| Operation | Required Team | Validation Action |
|-----------|---------------|-------------------|
| **Release Preparation** | `folio-org/kitfox` | `validate-team-membership` |
| **Infrastructure Changes** | `folio-org/kitfox` | `validate-team-membership` |
| **Platform Deployment** | `folio-org/kitfox` | `validate-team-membership` |

### Security Principles

- **🔒 Fail-Closed Design**: Unauthorized access attempts are denied by default
- **🎯 Principle of Least Privilege**: Teams only have access to operations they need
- **📋 Audit Trail**: All authorization attempts are logged in workflow runs
- **🔍 Real-Time Validation**: Team membership checked at execution time
- **⚡ Fast Authorization**: GitHub API-based checks with minimal latency

## Architecture Principles

### Distributed Execution Over Monolithic Processing
- **Parallel Processing**: Applications processed concurrently using matrix strategy
- **Fault Isolation**: Individual application failures don't stop entire release
- **Scalability**: Workflow load distributed across application repositories
- **Independent Capability**: Applications can be triggered independently or orchestrated

### Workflow Monitoring and Coordination
- **Dispatch Tracking**: Unique IDs for tracking distributed workflow executions
- **Run Monitoring**: Real-time watching of triggered workflows for completion status
- **Result Collection**: Artifacts gathered from each application for centralized reporting
- **Verification**: Post-execution validation of branch creation and version updates

### When to Create Custom Actions
✅ **DO create actions for**:
- Cross-workflow functionality (team validation)
- Complex, reusable business logic that appears in 3+ workflows
- External API integrations requiring authentication

❌ **DON'T create actions for**:
- Simple, context-specific logic (version determination)
- Basic command operations (git commands)  
- One-off workflow requirements

## 🎯 FOLIO Integration Context

### Release Workflow Integration

This infrastructure supports FOLIO's **distributed release preparation workflow** with comprehensive Slack notifications:

1. **Platform Orchestration**: `platform-lsp` coordinates release across all applications
2. **Application Processing**: Each `app-*` repository processes its own release preparation
3. **Dual Notifications**: Both platform-level aggregation and individual app notifications
4. **Version Management**: Semantic version handling with SNAPSHOT support
5. **Team Coordination**: Kitfox team controls release timing and approval
6. **Result Aggregation**: Centralized collection and reporting of distributed execution results

### Eureka CI Ecosystem

Part of the broader FOLIO Eureka CI implementation:

- **🔄 Snapshot CI**: Automated module version updates
- **📦 Release CI**: Version management and release preparation
- **🗂️ Application Registry**: mgr-applications in FAR mode
- **🚀 Artifact Packaging**: Release tar.gz generation

## 📋 Development Guidelines

### Action Design Principles

Following [pragmatic GitHub Actions patterns](https://github.com/folio-org/kitfox-github/docs/coding-style.md):

- **🎯 Single Responsibility**: Each action does one thing well
- **📊 YAML Parameters**: Clean, readable parameter format over JSON
- **🛡️ Security First**: Fail-closed design with clear authorization
- **⚡ Platform Tools**: Use `gh`, `jq`, `yq` over custom implementations
- **🔍 Universal Design**: Build for reuse across multiple workflows

### Workflow Development Standards

- **✅ Dry Run Support**: Always include `dry_run` parameter for testing
- **📝 Clear Outputs**: Provide meaningful status and result outputs
- **🚫 Error Handling**: Graceful failure with actionable error messages
- **📋 Dispatch Tracking**: Use UUID tracking for distributed coordination
- **🎨 Consistent Logging**: Use `::group::`, `::notice::`, `::error::` annotations

### FOLIO Branching Strategy

- **🎫 Feature Branches**: Use Jira ticket names (`RANCHER-2320`, `FOLIO-1234`)
- **🧪 Testing**: Validate changes in feature branches before merging
- **📌 Branch References**: Update action references when merging to main
- **👥 Team Reviews**: Always include Kitfox team members in action reviews

## 🔮 Future Evolution

### Proven Reuse Pattern Approach

New actions are created based on **evidence of reuse**, not theoretical needs:

| **Potential Action** | **Evidence Required** | **Status** |
|----------------------|----------------------|------------|
| Module Version Management | RANCHER-2321/2322 implementation | 🔄 Pending |
| Registry Operations | mgr-applications deployment | 🔄 Pending |
| ~~Slack Notifications~~ | ~~Team notification patterns~~ | ✅ **Implemented** |
| Environment Deployment | Multi-env deployment patterns | 📋 Under Review |
| Application Version Collection | Cross-repo version management needs | ✅ **Implemented** |

### Evolution Principles

- **📈 Evidence-Based**: Actions created when 3+ workflows need the same functionality
- **🎯 Focused Scope**: Prefer small, composable actions over monolithic solutions
- **📚 Documentation First**: Every action includes comprehensive README
- **🔒 Security Review**: All actions undergo Kitfox team security review

---

## 📈 Architecture Evolution & Impact

### From Monolithic to Distributed

**Before**: Monolithic workflows processing all applications sequentially
**After**: Distributed orchestration with universal actions enabling:

- ⚡ **Parallel Processing**: 5x faster release preparation across 30+ applications
- 🛡️ **Fault Isolation**: Individual application failures don't block entire release
- 🎯 **Reusable Infrastructure**: Universal actions reduce code duplication by 80%
- 🔒 **Centralized Security**: Team authorization enforced at orchestration layer
- 📊 **Clean Coordination**: YAML parameters replace complex shell orchestration

### Key Metrics

- **Code Reduction**: 136 lines → 26 lines in platform orchestrator (80% reduction)
- **Action Reuse**: 3 universal actions + 2 reusable workflows serve 31+ repositories
- **Notification Standardization**: 31 application repositories use centralized Slack notifications
- **Security Coverage**: 100% of critical operations require team authorization
- **Maintenance**: Single point of change for workflow improvements
- **Dual Notification System**: Platform-level + individual app notifications via reusable workflows

### FOLIO Ecosystem Impact

This infrastructure enables FOLIO's **distributed CI/CD approach** across:
- **30+ Application Repositories** (`app-*`)
- **100+ Module Repositories** (`mod-*`, `ui-*`)
- **Platform Coordination** via `platform-lsp`
- **Release Management** with team-based authorization

*Supporting FOLIO's mission to provide flexible, distributed library management software through robust DevOps practices.* 
