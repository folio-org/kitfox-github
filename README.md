# kitfox-github

**Shared Infrastructure for FOLIO Distributed CI/CD** - Reusable GitHub Actions and workflow templates that enable coordinated operations across the FOLIO ecosystem.

## 🎯 Repository Purpose

This repository serves as the **central infrastructure hub** for FOLIO's distributed CI/CD ecosystem, providing:

- **🔧 Universal Actions**: Reusable composite actions for cross-repository operations
- **📋 Workflow Templates**: Standardized reusable workflows for common FOLIO processes
- **🛡️ Security Infrastructure**: Team-based authorization patterns for critical operations
- **⚡ Distributed Coordination**: Tools for orchestrating operations across multiple repositories

## 🏗️ Repository Structure

### `.github/actions/` - Universal Composite Actions

Composite actions that solve common cross-repository challenges:

#### Action Design Principles
- **🎯 Single Responsibility**: Each action solves one specific problem well
- **🔄 Cross-Repository Reuse**: Built for use across multiple FOLIO repositories
- **🛡️ Security-First**: Fail-closed design with clear authorization boundaries
- **📖 Self-Documenting**: Each action includes comprehensive README.md

### `.github/workflows/` - Reusable Workflow Templates

Standardized workflow templates for common FOLIO operations:

#### Template Design Principles
- **📋 Workflow Call Interface**: Clean `workflow_call` definitions with typed inputs
- **🔄 Universal Applicability**: Work across all application repositories
- **📢 Consistent Experience**: Standardized patterns and notification formats
- **🧪 Testing Support**: Built-in dry-run capabilities for safe validation

### `.github/` - Infrastructure Documentation

- **`README.md`** - Workflow-specific implementation details and usage guides
- **`docs/`** - Detailed technical documentation for each component

## 🎯 Architectural Patterns

### Distributed Orchestration Pattern

The repository implements a **distributed orchestration architecture** where:

**Central Orchestrator** (platform-lsp):
- Provides team authorization and access control
- Coordinates operations across multiple repositories  
- Aggregates results and provides comprehensive reporting
- Manages platform-level state and notifications

**Distributed Workers** (app-* repositories):
- Execute application-specific processing using shared templates
- Report results back to orchestrator via artifacts
- Send individual notifications using shared notification services
- Maintain clean separation between authorization and functionality

**Shared Infrastructure** (kitfox-github):
- Provides universal actions for common operations
- Offers reusable workflow templates for standard processes
- Maintains security and authorization components
- Enables consistent patterns across the entire ecosystem

### Key Architectural Benefits

- **⚡ Parallel Processing**: Operations execute concurrently across multiple repositories
- **🛡️ Fault Isolation**: Individual repository failures don't block entire operations
- **🔒 Centralized Security**: Authorization enforced at orchestration level
- **📊 Result Aggregation**: Comprehensive reporting from distributed execution
- **🔄 Code Reuse**: Universal actions eliminate duplication across repositories
- **📢 Consistent Experience**: Standardized notifications and status reporting

## 🛡️ Security Architecture

### Team-Based Authorization

All critical FOLIO operations require explicit team membership validation:

```
Authorization Flow:
1. User initiates operation
2. Orchestrator validates team membership
3. Authorization result controls workflow execution
4. Protected operations only run for authorized users
```

**Supported Teams**:
- `folio-org/kitfox` - DevOps and infrastructure operations
- Extensible for other team-based authorization needs

### Security Principles

- **🔒 Fail-Closed Design**: Unauthorized access denied by default
- **🎯 Least Privilege**: Teams only access operations they need
- **📋 Audit Trail**: All authorization attempts logged
- **⚡ Real-Time Validation**: Team membership checked at execution time

## 🔧 Development Guidelines

### When to Create Universal Actions

**✅ Create actions for**:
- Operations needed by 3+ different workflows
- Complex cross-repository coordination logic
- Security-sensitive operations requiring authorization
- External API integrations with authentication requirements

**❌ Avoid creating actions for**:
- Simple, single-repository operations
- Context-specific business logic
- Basic command sequences that don't need reuse

## 🔧 Technical Standards

### Programming Language Requirements

**Shell Scripting (Primary)**:
- **Version**: Bash 4.0+ compatible
- **Settings**: `set -euo pipefail` mandatory in all scripts
- **IFS**: Set to `IFS=$'\n\t'` for safety
- **Tools**: Prefer `jq`, `yq`, `gh` over custom implementations

**YAML Configuration**:
- **Indentation**: 2 spaces, no tabs
- **Line Length**: 120 characters maximum
- **Quoting**: Use single quotes for strings unless interpolation needed
- **Comments**: Document complex logic and security requirements

**JSON Processing**:
- **Primary Tool**: `jq` for all JSON operations
- **Error Handling**: Use `jq -e` for existence checks
- **Output**: `jq -c` for compact output in variables, pretty print for logging

### Code Style Requirements

#### Shell Script Standards
```bash
#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# Function naming: snake_case
function validate_input() {
    local input_value="$1"
    
    # Variable naming: snake_case with descriptive names
    local validation_result
    validation_result=$(echo "$input_value" | jq -r '.field // "default"')
    
    # Error handling: specific error messages
    if [[ -z "$validation_result" ]]; then
        echo "::error title=Invalid Input::Field 'field' is required"
        return 1
    fi
    
    echo "$validation_result"
}
```

#### GitHub Actions Annotation Standards
```bash
# Required annotation patterns:
echo "::group::Descriptive Operation Name"
echo "::notice title=Success::Operation completed successfully"
echo "::warning title=Fallback Used::Using alternative approach"
echo "::error title=Validation Failed::Specific error description"
echo "::endgroup::"
```

#### YAML Workflow Structure
```yaml
name: 'Descriptive Action Name'
description: 'Single sentence describing the action purpose'

inputs:
  required_param:
    description: 'Clear description of parameter purpose and format'
    required: true
    type: string
  optional_param:
    description: 'Optional parameter with default behavior'
    required: false
    type: boolean
    default: false

outputs:
  result:
    description: 'Clear description of output value and format'
    value: ${{ steps.step-id.outputs.result }}

runs:
  using: 'composite'
  steps:
    - name: 'Descriptive Step Name'
      id: step-id
      shell: bash
      env:
        PARAM_VALUE: ${{ inputs.required_param }}
      run: |
        # Implementation here
```

### Job Composition Standards

#### Single Responsibility Jobs
```yaml
# ✅ GOOD: Focused job
job-name:
  name: 'Specific Operation Name'
  runs-on: ubuntu-latest
  outputs:
    result: ${{ steps.operation.outputs.result }}
  steps:
    - name: 'Single Focused Operation'
      id: operation
      run: |
        # Implementation

# ❌ BAD: Multiple responsibilities
job-name:
  steps:
    - name: 'Validate and Process and Notify'  # Too many things
```

#### Step Granularity Requirements

**Optimal Step Size**:
- **Single Logical Operation**: Each step performs one conceptual task
- **5-15 Lines**: Shell scripts should be 5-15 lines per step
- **Clear Dependencies**: Steps should have obvious input/output relationships
- **Minimal Context**: Each step should be understandable in isolation

**Step Examples**:
```yaml
# ✅ GOOD: Appropriate granularity
- name: 'Extract Version from POM'
  id: extract-version
  run: |
    version=$(mvn help:evaluate -Dexpression=project.version -q -DforceStdout)
    echo "version=$version" >> "$GITHUB_OUTPUT"

- name: 'Parse Semantic Version'
  id: parse-version
  env:
    VERSION: ${{ steps.extract-version.outputs.version }}
  run: |
    if [[ "$VERSION" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+) ]]; then
      echo "major=${BASH_REMATCH[1]}" >> "$GITHUB_OUTPUT"
      echo "minor=${BASH_REMATCH[2]}" >> "$GITHUB_OUTPUT"
      echo "patch=${BASH_REMATCH[3]}" >> "$GITHUB_OUTPUT"
    fi

# ❌ BAD: Too granular
- name: 'Set Version Variable'
  run: echo "VERSION=1.0.0" >> "$GITHUB_ENV"

- name: 'Echo Version'
  run: echo "$VERSION"
```

### Security Implementation Requirements

#### Team Authorization Pattern
```yaml
# Mandatory pattern for protected operations
validate-authorization:
  runs-on: ubuntu-latest
  outputs:
    authorized: ${{ steps.check.outputs.authorized }}
  steps:
    - name: 'Generate App Token'
      id: app-token
      uses: actions/create-github-app-token@v1
      with:
        app-id: ${{ vars.EUREKA_CI_APP_ID }}
        private-key: ${{ secrets.EUREKA_CI_APP_KEY }}
    
    - name: 'Validate Team Membership'
      id: check
      uses: folio-org/kitfox-github/.github/actions/validate-team-membership@master
      with:
        username: ${{ github.actor }}
        organization: 'folio-org'
        team: 'kitfox'
        token: ${{ steps.app-token.outputs.token }}

protected-operation:
  needs: validate-authorization
  if: needs.validate-authorization.outputs.authorized == 'true'
  runs-on: ubuntu-latest
  steps:
    - name: 'Protected Operation'
      run: echo "Only authorized users can execute this"
```

#### Environment-Based Fallback
```yaml
# Required fallback for non-team members
approve-run:
  needs: validate-authorization
  if: needs.validate-authorization.outputs.authorized == 'false'
  runs-on: ubuntu-latest
  environment: 'Eureka CI'  # Manual approval required
  steps:
    - name: 'Manual Approval'
      run: echo "Manual approval granted"
```

### Distributed Orchestration Requirements

#### UUID Dispatch Tracking
```bash
# Mandatory pattern for workflow orchestration
dispatch_id=$(uuidgen)
echo "dispatch_id=$dispatch_id" >> "$GITHUB_OUTPUT"

# Trigger with tracking ID
gh workflow run "$WORKFLOW_FILE" \
  --repo "$REPOSITORY" \
  --ref "$BRANCH" \
  -f dispatch_id="$dispatch_id"

# Poll for run ID using dispatch ID
for i in {1..60}; do
  run_id=$(gh run list \
    --workflow "$WORKFLOW_FILE" \
    --repo "$REPOSITORY" \
    --json databaseId,displayTitle \
    --jq "map(select(.displayTitle | contains(\"$dispatch_id\")))[0].databaseId")
  
  [[ -n "$run_id" ]] && break
  sleep 5
done

# Monitor completion
gh run watch "$run_id" --repo "$REPOSITORY" --exit-status
```

#### YAML Parameter Format
```yaml
# Required parameter format for orchestration
workflow_parameters: |
  previous_release_branch: ${{ inputs.previous_release_branch }}
  new_release_branch: ${{ inputs.new_release_branch }}
  dry_run: ${{ inputs.dry_run }}
  # Clean YAML format - no JSON strings
```

#### Matrix Configuration Standards
```yaml
# Required matrix configuration
strategy:
  matrix:
    application: ${{ fromJson(needs.setup.outputs.applications) }}
  fail-fast: false    # Never use fail-fast: true for distributed operations
  max-parallel: 5     # Standard concurrency limit
```

### Error Handling Requirements

#### Failure Isolation
```bash
# Required pattern for non-critical failures
operation_result="success"

if ! critical_operation; then
    echo "::error title=Operation Failed::Critical operation failed"
    operation_result="failure"
fi

# Continue with cleanup regardless of failure
cleanup_operation || echo "::warning::Cleanup failed but continuing"

echo "result=$operation_result" >> "$GITHUB_OUTPUT"
```

#### Result Aggregation Pattern
```yaml
# Required for collecting distributed results
- name: 'Upload Result Artifact'
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: 'result-${{ matrix.item }}'
    path: 'result.json'

# Aggregation job
collect-results:
  needs: [distributed-job]
  if: always()
  steps:
    - name: 'Download All Results'
      uses: actions/download-artifact@v4
      with:
        pattern: 'result-*'
        merge-multiple: true
    
    - name: 'Aggregate with jq'
      run: |
        success_count=$(jq -s 'map(select(.success)) | length' result-*.json)
        failed_items=$(jq -s 'map(select(.success | not) | .item) | join(" ")' result-*.json)
        echo "success_count=$success_count" >> "$GITHUB_OUTPUT"
        echo "failed_items=$failed_items" >> "$GITHUB_OUTPUT"
```

## 📋 Component Requirements

### Composite Action Structure
```
action-name/
├── action.yml           # Action definition with strict input/output typing
├── README.md           # Comprehensive usage documentation
└── scripts/            # Optional: Complex shell scripts (if needed)
    └── operation.sh
```

### Reusable Workflow Structure
```yaml
name: 'Workflow Template Name'

on:
  workflow_call:
    inputs:
      required_input:
        description: 'Input description'
        required: true
        type: string
      optional_input:
        description: 'Optional input description'
        required: false
        type: boolean
        default: false
    outputs:
      result:
        description: 'Output description'
        value: ${{ jobs.main-job.outputs.result }}

jobs:
  main-job:
    name: 'Main Operation'
    runs-on: ubuntu-latest
    outputs:
      result: ${{ steps.operation.outputs.result }}
    steps:
      - name: 'Operation Step'
        id: operation
        run: |
          # Implementation
```

### Documentation Requirements



#### Action README.md Template
```markdown
# Action Name

Brief description of action purpose.

## Inputs

| Input        | Description        | Required | Default |
|--------------|--------------------|----------|---------|
| `input_name` | Input description  | Yes      | -       |

## Outputs

| Output        | Description          |
|---------------|----------------------|
| `output_name` | Output description   |

## Usage

```yaml
- uses: folio-org/kitfox-github/.github/actions/action-name@main
  with:
    input_name: 'value'
```

## Examples

```

## 🚫 Anti-Patterns

### Avoid These Patterns
```yaml
# ❌ BAD: Monolithic jobs
mega-job:
  steps:
    - name: 'Do Everything'
      run: |
        # 100+ lines of mixed operations

# ❌ BAD: Unclear naming
job1:
  steps:
    - name: 'Step'
      run: echo "unclear purpose"

# ❌ BAD: Mixed error handling
- name: 'Operation'
  run: |
    operation || true  # Silently ignoring failures
    
# ❌ BAD: Hardcoded values
- name: 'Operation'
  run: |
    gh workflow run workflow.yml --repo folio-org/hardcoded-repo
```

### Required Patterns
```yaml
# ✅ GOOD: Clear, focused jobs
validate-input:
  name: 'Validate Input Parameters'
  runs-on: ubuntu-latest
  outputs:
    validated: ${{ steps.validation.outputs.result }}
  steps:
    - name: 'Validate Required Parameters'
      id: validation
      env:
        INPUT_VALUE: ${{ inputs.required_input }}
      run: |
        if [[ -z "$INPUT_VALUE" ]]; then
          echo "::error title=Missing Input::Required parameter not provided"
          echo "result=false" >> "$GITHUB_OUTPUT"
        else
          echo "result=true" >> "$GITHUB_OUTPUT"
        fi
```

## 🔮 Evolution Criteria

### New Component Checklist
- [ ] **Evidence**: Used in 3+ different contexts
- [ ] **Documentation**: Complete README.md with examples
- [ ] **Testing**: Validated across multiple repositories
- [ ] **Security Review**: Kitfox team approval
- [ ] **Interface Stability**: Clear input/output contracts
- [ ] **Error Handling**: Comprehensive failure scenarios covered

### Quality Gates
1. **Code Review**: Two Kitfox team members
2. **Integration Testing**: Minimum 3 repository validation
3. **Documentation**: Usage examples and troubleshooting guide
4. **Security Assessment**: Authorization and secret handling review

## 📈 FOLIO Ecosystem Integration

### Supported Repository Types

This infrastructure serves the entire FOLIO ecosystem:

- **🏗️ Platform Repository**: `platform-lsp` - Central orchestration point
- **📦 Application Repositories**: `app-*` (31+ repositories) - Domain-specific module collections
- **🔧 Module Repositories**: `mod-*`, `ui-*` (100+ repositories) - Individual FOLIO modules
- **🌐 Edge Repositories**: `edge-*` - API gateway and integration modules

## 🔮 Evolution Strategy

### Evidence-Based Development

New infrastructure components are created based on **proven reuse patterns**:

1. **Identify Common Patterns**: Look for repeated code across 3+ repositories
2. **Extract Common Logic**: Create universal actions for shared functionality
3. **Test Across Ecosystem**: Validate new components across multiple repositories
4. **Document and Standardize**: Provide comprehensive documentation and usage examples
5. **Gradual Adoption**: Roll out new components incrementally with proper testing

## 📚 Documentation Structure

### Repository-Level Documentation
- **`README.md`** (this file) - Repository purpose and architectural guidance
- **`.github/README.md`** - Workflow implementation details and usage patterns
- **`.github/docs/`** - Detailed technical documentation for specific workflows

### Component-Level Documentation
- **`.github/actions/*/README.md`** - Individual action documentation
- **`.github/workflows/*.yml`** - Inline documentation for workflow templates

### External References
- Platform-specific documentation in consuming repositories
- FOLIO Eureka CI/CD process documentation
- Team-specific implementation guides

---

## 🎯 Mission Statement

**kitfox-github enables FOLIO's distributed CI/CD vision** by providing:

- **🏗️ Infrastructure Foundation**: Universal building blocks for complex operations
- **🔒 Security Framework**: Team-based authorization for critical infrastructure
- **⚡ Operational Efficiency**: Parallel processing with centralized coordination
- **📊 Ecosystem Consistency**: Standardized patterns across all FOLIO repositories
- **🔄 Maintainable Architecture**: Single point of change for infrastructure improvements

---

**Maintained by**: Kitfox Team DevOps  
**Last Updated**: August 2025  
**Repository Type**: Shared Infrastructure
