# Release Update Flow Workflow

**Workflow**: `release-update-flow.yml`
**Purpose**: Comprehensive release branch update orchestration with intelligent PR management
**Type**: Reusable workflow (`workflow_call`)

## 🎯 Overview

This workflow represents the core implementation of the FOLIO release update system. It orchestrates a sophisticated multi-stage process that determines source branches, updates application modules, compares versions, commits changes, and manages pull requests. The workflow is designed to handle complex release branch scenarios including existing update branches, PR management, reviewer assignment, and comprehensive error handling throughout the entire flow.

## 📋 Workflow Interface

### Inputs

| Input                 | Description                                          | Required | Type    | Default |
|-----------------------|------------------------------------------------------|----------|---------|---------|
| `app_name`            | Application name                                     | Yes      | string  | -       |
| `repo`                | Application repository name (org/repo format)       | Yes      | string  | -       |
| `release_branch`      | Release branch to scan (e.g., R1-2025)              | Yes      | string  | -       |
| `update_branch`       | Update branch name for this release branch          | Yes      | string  | -       |
| `workflow_run_number` | GitHub run number for display                        | Yes      | string  | -       |
| `dry_run`             | Perform dry run without creating PRs                 | No       | boolean | `false` |
| `pr_reviewers`        | Comma-separated list of reviewers (users/teams)     | No       | string  | `''`    |
| `pr_labels`           | Comma-separated list of labels to add to PR         | No       | string  | `''`    |

### Outputs

| Output                | Description                                |
|-----------------------|--------------------------------------------|
| `pr_created`          | Whether a PR was created or updated        |
| `pr_number`           | PR number if created or updated            |
| `pr_url`              | PR URL if created or updated               |
| `successful_reviewers`| Successfully added reviewers               |
| `failed_reviewers`    | Failed to add reviewers                    |
| `updated`             | Whether the application was updated        |
| `updated_modules`     | List of updated modules                    |
| `new_version`         | New version of the application             |
| `updates_cnt`         | Number of updates                          |
| `workflow_status`     | Overall workflow status                    |
| `failure_reason`      | Reason for workflow failure if any         |

### Permissions

| Permission        | Level  | Purpose                              |
|-------------------|--------|--------------------------------------|
| `contents`        | write  | Repository content and branch access |
| `pull-requests`   | write  | PR creation and management           |
| `issues`          | write  | Issue and PR interaction             |

## 🔄 Workflow Execution Flow

### 1. Source Branch Determination
**Job**: `determine-source-branch`

This intelligent step decides which branch to scan based on existing repository state:

**Branch Logic**:
- **Primary Check**: Verifies if update branch already exists
- **Source Selection**: Uses update branch if exists, otherwise uses release branch
- **Status Tracking**: Records branch existence status for downstream jobs

**PR Status Check**:
- **Conditional Execution**: Only runs when update branch exists
- **PR Discovery**: Searches for existing PRs from update branch to release branch
- **State Recording**: Captures PR number and URL for reuse

**Output Generation**:
```bash
# Branch determination
if gh api "repos/$REPO/branches/$UPDATE_BRANCH" >/dev/null 2>&1; then
  echo "source_branch=$UPDATE_BRANCH"
  echo "update_branch_exists=true"
else
  echo "source_branch=$RELEASE_BRANCH"
  echo "update_branch_exists=false"
fi

# PR existence check
pr_json=$(gh pr list --repo "$REPO" --base "$BASE_BRANCH" --head "$HEAD_BRANCH" --json number,url --jq '.[0]')
```

### 2. Application Module Updates
**Job**: `update-application`

Delegates to the `update-application.yml` workflow with release-specific configuration:

**Configuration**:
- **Mode**: Set to 'release' for release branch handling
- **Source Branch**: Uses determined source branch from step 1
- **Module Discovery**: Scans for available module updates
- **Version Processing**: Handles release-specific version calculations

**Artifacts Generated**:
- Updated application descriptor
- Module update state files
- Version information

### 3. Version Comparison (Conditional)
**Job**: `compare-applications`

**Execution Condition**: Only runs when update branch already exists

**Comparison Logic**:
- **Base Branch**: Always uses the original release branch
- **Head Source**: Uses either update branch or artifact based on update status
- **Change Detection**: Identifies differences between versions
- **Module Analysis**: Provides detailed module-level comparison

**Flexible Input Handling**:
```yaml
head_branch: ${{ needs.update-application.outputs.updated != 'true' && inputs.update_branch || '' }}
artifact_name: ${{ needs.update-application.outputs.updated == 'true' && format('{0}-update-files', inputs.app_name) || '' }}
```

### 4. Change Commitment
**Job**: `commit-changes`

**Execution Condition**: Only when updates are found

**Process**:
- **GitHub App Authentication**: Uses GitHub App for enhanced permissions
- **Branch Management**: Creates or updates the update branch
- **Commit Generation**: Creates descriptive commit with module details
- **Source Branch Handling**: Properly handles branching from determined source

**Commit Message Format**:
```
Update modules to {new_version}.

Updated modules:
{detailed_module_list}
```

### 5. Pull Request Management
**Job**: `manage-pr`

This sophisticated job handles both PR creation and updates:

**Execution Conditions**:
- Not in dry run mode
- Update job succeeded
- Always runs (even if other jobs failed)

**GitHub App Token Generation**:
- **Enhanced Permissions**: Uses GitHub App for broader access
- **Repository Scoped**: Scoped to specific application repository
- **Fallback Support**: Falls back to standard GitHub token

**PR Creation Logic**:
```yaml
if: |
  needs.determine-source-branch.outputs.pr_exists != 'true' &&
  (needs.update-application.outputs.updated == 'true' ||
   needs.determine-source-branch.outputs.update_branch_exists == 'true')
```

**PR Update Logic**:
```yaml
if: |
  needs.determine-source-branch.outputs.pr_exists == 'true' &&
  needs.update-application.outputs.updated == 'true'
```

**Dynamic Content Generation**:
- **Title**: Uses comparison or update results for version information
- **Body**: Comprehensive module update details
- **Reviewers**: Processes comma-separated reviewer lists
- **Labels**: Applies configurable labels

## 🔍 Advanced Features

### Intelligent Branch Strategy

**Update Branch Lifecycle**:
1. **First Run**: Scans release branch directly
2. **Subsequent Runs**: Scans existing update branch
3. **Continuous Updates**: Accumulates changes in update branch
4. **PR Management**: Maintains single PR throughout lifecycle

**Benefits**:
- **Reduced Noise**: Single PR per release branch
- **Incremental Updates**: Accumulates multiple update cycles
- **Review Efficiency**: Reviewers see consolidated changes

### Dynamic Version Handling

**Version Source Priority**:
1. **Comparison Results**: Uses compare-applications output when available
2. **Update Results**: Falls back to update-application output
3. **Graceful Degradation**: Handles missing version information

**Example Version Resolution**:
```yaml
new_version: ${{ needs.compare-applications.outputs.new_version || needs.update-application.outputs.new_version || 'No updates' }}
```

### Comprehensive Error Tracking

**Workflow Status Calculation**:
```yaml
workflow_status: ${{
  jobs.determine-source-branch.result == 'failure' && 'failure' ||
  (jobs.update-application.result == 'failure' && 'failure' ||
   (jobs.commit-changes.result == 'failure' && 'failure' ||
    (jobs.manage-pr.result == 'failure' && 'failure' || 'success')))
}}
```

**Failure Reason Mapping**:
- **Source Branch**: "Failed to determine source branch"
- **Update Application**: "Failed to update application modules"
- **Commit Changes**: "Failed to commit changes to branch"
- **Manage PR**: "Failed to manage pull request"

### Reviewer Management

**User and Team Support**:
- **Individual Users**: Direct GitHub usernames
- **Team References**: Organization teams with 'org/' prefix
- **Mixed Lists**: Comma-separated combinations
- **Success Tracking**: Reports successful and failed assignments

## 📊 Usage Examples

### Basic Release Update

```yaml
jobs:
  update-release:
    uses: folio-org/kitfox-github/.github/workflows/release-update-flow.yml@master
    with:
      app_name: ${{ github.event.repository.name }}
      repo: ${{ github.repository }}
      release_branch: 'R1-2025'
      update_branch: 'R1-2025-update'
      workflow_run_number: ${{ github.run_number }}
    secrets: inherit
```

### Advanced Configuration with Reviewers and Labels

```yaml
jobs:
  comprehensive-update:
    uses: folio-org/kitfox-github/.github/workflows/release-update-flow.yml@master
    with:
      app_name: ${{ github.event.repository.name }}
      repo: ${{ github.repository }}
      release_branch: 'R2-2025'
      update_branch: 'R2-2025-maintenance'
      workflow_run_number: ${{ github.run_number }}
      pr_reviewers: 'release-lead,senior-dev,folio-org/platform-team'
      pr_labels: 'release-update,automated,priority-high'
      dry_run: false
    secrets: inherit
```

### Testing with Dry Run

```yaml
jobs:
  test-release-flow:
    uses: folio-org/kitfox-github/.github/workflows/release-update-flow.yml@master
    with:
      app_name: ${{ github.event.repository.name }}
      repo: ${{ github.repository }}
      release_branch: 'R1-2025'
      update_branch: 'R1-2025-test'
      workflow_run_number: ${{ github.run_number }}
      dry_run: true
    secrets: inherit
```

### Matrix Strategy for Multiple Releases

```yaml
jobs:
  update-multiple-releases:
    strategy:
      fail-fast: false
      matrix:
        release:
          - { branch: 'R1-2025', update: 'R1-2025-update', reviewers: 'team-a' }
          - { branch: 'R2-2025', update: 'R2-2025-update', reviewers: 'team-b' }
          - { branch: 'R3-2025', update: 'R3-2025-update', reviewers: 'team-c' }
    uses: folio-org/kitfox-github/.github/workflows/release-update-flow.yml@master
    with:
      app_name: ${{ github.event.repository.name }}
      repo: ${{ github.repository }}
      release_branch: ${{ matrix.release.branch }}
      update_branch: ${{ matrix.release.update }}
      workflow_run_number: ${{ github.run_number }}
      pr_reviewers: ${{ matrix.release.reviewers }}
      pr_labels: 'automated,release-maintenance'
    secrets: inherit
```

## 🛡️ Error Handling and Recovery

### Failure Scenarios and Responses

**Source Branch Determination Failure**:
- **Cause**: API access issues or invalid branch names
- **Response**: Workflow stops early with clear error message
- **Recovery**: Verify branch names and repository permissions

**Module Update Failure**:
- **Cause**: Registry connectivity or invalid descriptors
- **Response**: Update job fails, other jobs skip appropriately
- **Recovery**: Check module registry status and descriptor validity

**Commit Failure**:
- **Cause**: Git conflicts or permission issues
- **Response**: PR management skips, error reported
- **Recovery**: Resolve conflicts manually or check permissions

**PR Management Failure**:
- **Cause**: GitHub API issues or reviewer problems
- **Response**: Error logged with specific failure details
- **Recovery**: Check GitHub API status and reviewer validity

### Graceful Degradation

**Partial Success Handling**:
```yaml
# PR creation with fallback content
pr_title: "Release: Update to ${{ needs.compare-applications.outputs.new_version || needs.update-application.outputs.new_version || 'No updates' }}"

# Reviewer management with success/failure tracking
successful_reviewers: ${{ steps.create-pr.outputs.successful_reviewers || steps.update-pr.outputs.successful_reviewers || '' }}
failed_reviewers: ${{ steps.create-pr.outputs.failed_reviewers || steps.update-pr.outputs.failed_reviewers || '' }}
```

## 🧪 Testing Strategy

### Test Scenarios

**New Release Branch**:
- **Setup**: Fresh release branch with no update branch
- **Expected**: Scans release branch, creates update branch and PR
- **Validation**: PR created with correct base/head branches

**Existing Update Branch**:
- **Setup**: Update branch already exists
- **Expected**: Scans update branch, updates existing PR
- **Validation**: PR updated with accumulated changes

**No Updates Available**:
- **Setup**: All modules are current
- **Expected**: No commits, no PR changes
- **Validation**: Workflow completes without side effects

**Dry Run Mode**:
- **Setup**: Dry run enabled
- **Expected**: All analysis runs, no commits or PRs
- **Validation**: No repository changes made

**Reviewer Failures**:
- **Setup**: Invalid reviewer names in list
- **Expected**: Partial success with failure tracking
- **Validation**: Working reviewers added, failures reported

### Validation Checklist

- [ ] Release branch exists and is accessible
- [ ] Update branch naming follows conventions
- [ ] Repository permissions allow branch creation
- [ ] PR permissions allow creation and updates
- [ ] Reviewer names are valid GitHub users/teams
- [ ] Labels are valid for repository
- [ ] GitHub App credentials are configured
- [ ] Module registry connectivity

## 📈 Performance Considerations

### Optimization Features

**Conditional Execution**:
- **Smart Skipping**: Jobs skip when preconditions aren't met
- **Resource Conservation**: No unnecessary computation
- **Early Termination**: Fails fast on critical errors

**Efficient API Usage**:
- **Batch Operations**: Minimizes GitHub API calls
- **Caching Strategy**: Reuses branch and PR information
- **Parallel Processing**: Independent jobs run concurrently

**Resource Management**:
- **Memory Efficiency**: Minimal state retention between jobs
- **Network Optimization**: Consolidated API operations
- **Time Efficiency**: Parallel execution where possible

### Concurrency Handling

**GitHub App Token Management**:
- **Scoped Access**: Repository-specific tokens
- **Rate Limit Awareness**: Efficient token usage
- **Fallback Strategy**: Standard token when app unavailable

## 🔄 Integration Patterns

### Scheduled Release Maintenance

```yaml
on:
  schedule:
    - cron: '0 2 * * MON,WED,FRI'  # Monday, Wednesday, Friday at 2 AM

jobs:
  maintain-active-releases:
    strategy:
      matrix:
        include:
          - release: 'R1-2025'
            update: 'R1-2025-update'
            team: 'platform-team'
          - release: 'R2-2025'
            update: 'R2-2025-update'
            team: 'core-team'
    uses: ./.github/workflows/release-update-flow.yml
    with:
      app_name: ${{ github.event.repository.name }}
      repo: ${{ github.repository }}
      release_branch: ${{ matrix.release }}
      update_branch: ${{ matrix.update }}
      workflow_run_number: ${{ github.run_number }}
      pr_reviewers: 'folio-org/${{ matrix.team }}'
      pr_labels: 'scheduled,automated,release-maintenance'
```

### Release Pipeline Integration

```yaml
jobs:
  create-release:
    # Release creation logic
    outputs:
      release_branch: ${{ steps.create.outputs.branch }}

  initial-update:
    needs: create-release
    uses: ./.github/workflows/release-update-flow.yml
    with:
      app_name: ${{ github.event.repository.name }}
      repo: ${{ github.repository }}
      release_branch: ${{ needs.create-release.outputs.release_branch }}
      update_branch: '${{ needs.create-release.outputs.release_branch }}-initial'
      workflow_run_number: ${{ github.run_number }}
      pr_reviewers: 'release-manager'
      pr_labels: 'initial-release,requires-review'

  validate-release:
    needs: initial-update
    if: needs.initial-update.outputs.pr_created == 'true'
    # Release validation steps
```

### Custom Action Integration

```yaml
jobs:
  pre-update-checks:
    runs-on: ubuntu-latest
    outputs:
      should_update: ${{ steps.check.outputs.result }}
    steps:
      - name: Check if update needed
        id: check
        # Custom logic to determine if update should run

  conditional-update:
    needs: pre-update-checks
    if: needs.pre-update-checks.outputs.should_update == 'true'
    uses: ./.github/workflows/release-update-flow.yml
    with:
      app_name: ${{ github.event.repository.name }}
      repo: ${{ github.repository }}
      release_branch: 'R1-2025'
      update_branch: 'R1-2025-conditional'
      workflow_run_number: ${{ github.run_number }}

  post-update-actions:
    needs: conditional-update
    if: always() && needs.conditional-update.outputs.updated == 'true'
    # Custom post-update logic
```

## 🔍 Troubleshooting

### Common Issues and Solutions

**Branch Determination Failures**:
```bash
# Verify branch exists
gh api repos/:owner/:repo/branches/R1-2025

# Check permissions
gh auth status
```

**PR Creation Issues**:
```bash
# Test GitHub App token
gh auth status --hostname github.com

# Verify repository permissions
gh api user/repos | jq '.[] | select(.name=="app-name") | .permissions'
```

**Reviewer Assignment Problems**:
```bash
# Validate user exists
gh api users/username

# Check team membership
gh api orgs/folio-org/teams/platform-team/members
```

**Module Update Failures**:
```bash
# Test registry connectivity
curl -s https://folio-registry.dev.folio.org/_/proxy/modules

# Validate descriptor
jq '.' application-descriptor.json
```

### Debug Configuration

```yaml
jobs:
  debug-flow:
    uses: ./.github/workflows/release-update-flow.yml
    with:
      app_name: ${{ github.event.repository.name }}
      repo: ${{ github.repository }}
      release_branch: 'R1-2025'
      update_branch: 'R1-2025-debug'
      workflow_run_number: ${{ github.run_number }}
      dry_run: true  # Safe debugging
      pr_reviewers: 'debug-team'
      pr_labels: 'debug,testing'
    secrets: inherit
```

## 📚 Related Documentation

- **[Release Update](release-update.md)**: Main orchestration workflow
- **[Compare Applications](compare-applications.md)**: Version comparison implementation
- **[Update Application](update-application.md)**: Module update mechanics
- **[Commit Application Changes](commit-application-changes.md)**: Change commitment workflow
- **[GitHub Actions: Create PR](../actions/create-pr/README.md)**: PR creation action
- **[GitHub Actions: Update PR](../actions/update-pr/README.md)**: PR update action

---

**Last Updated**: September 2025
**Workflow Version**: 1.0
**Compatibility**: All FOLIO release management workflows