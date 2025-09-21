# Update Pull Request Action

A GitHub Action that updates existing pull requests with new titles, body content, labels, and reviewers. This action provides comprehensive PR management capabilities while preserving existing content when updates are not specified.

## Features

- **Selective Updates**: Update only the fields you specify (title, body, labels, reviewers)
- **Content Preservation**: Keeps existing content when new values are not provided
- **Smart Label Management**: Avoids duplicate labels and creates missing labels automatically
- **Reviewer Management**: Supports both individual users and teams as reviewers
- **Comprehensive Validation**: Checks PR existence and validates all operations
- **Detailed Reporting**: Provides outputs for successful and failed operations
- **Error Handling**: Graceful handling of missing PRs and permission issues

## Usage

### Basic Usage

```yaml
- name: Update Pull Request
  uses: ./.github/actions/update-pr
  with:
    repo: 'my-org/my-repo'
    pr_number: '123'
    pr_title: 'Updated: Feature implementation'
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

### Update with Body and Labels

```yaml
- name: Update Pull Request
  uses: ./.github/actions/update-pr
  with:
    repo: ${{ github.repository }}
    pr_number: ${{ github.event.pull_request.number }}
    pr_title: 'Release: v2.1.0'
    pr_body: |
      ## Release Notes

      This PR contains the following changes:
      - Feature A implementation
      - Bug fixes for issue #456
      - Documentation updates

      ## Testing
      - [x] Unit tests passed
      - [x] Integration tests passed
    pr_labels: 'release,automated,ready-for-review'
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

### Add Reviewers and Teams

```yaml
- name: Update Pull Request with Reviewers
  uses: ./.github/actions/update-pr
  with:
    repo: 'folio-org/platform-complete'
    pr_number: '789'
    pr_reviewers: 'john-doe,jane-smith,folio-org/platform-team'
    pr_labels: 'needs-review,high-priority'
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

## Inputs

| Input          | Required  | Default   | Description                                                           |
|----------------|-----------|-----------|-----------------------------------------------------------------------|
| `repo`         | Yes       | -         | Repository in `org/repo` format where the PR exists                   |
| `pr_number`    | Yes       | -         | Pull request number to update                                         |
| `pr_title`     | No        | `''`      | New pull request title (keeps existing if not provided)               |
| `pr_body`      | No        | `''`      | New pull request body content (keeps existing if not provided)        |
| `pr_labels`    | No        | `''`      | Comma-separated list of labels to add to the PR                       |
| `pr_reviewers` | No        | `''`      | Comma-separated list of reviewers (users or teams with `org/` prefix) |
| `github_token` | Yes       | -         | GitHub token for authentication (needs PR write permissions)          |

## Outputs

| Output                 | Description                                                            |
|------------------------|------------------------------------------------------------------------|
| `pr_exists`            | Whether the specified PR exists in the repository (`true`/`false`)     |
| `pr_updated`           | Whether the PR title or body was successfully updated (`true`/`false`) |
| `pr_url`               | URL of the pull request (if it exists)                                 |
| `successful_reviewers` | Space-separated list of reviewers that were successfully added         |
| `failed_reviewers`     | Space-separated list of reviewers that failed to be added              |
| `labels_added`         | Space-separated list of labels that were successfully added            |

## Examples

### Complete Workflow Example

```yaml
name: Update Release PR

on:
  workflow_dispatch:
    inputs:
      pr_number:
        description: 'PR number to update'
        required: true
        type: string
      release_version:
        description: 'Release version'
        required: true
        type: string

jobs:
  update-pr:
    runs-on: ubuntu-latest
    steps:
      - name: Update Release PR
        id: update
        uses: ./.github/actions/update-pr
        with:
          repo: ${{ github.repository }}
          pr_number: ${{ github.event.inputs.pr_number }}
          pr_title: 'Release: ${{ github.event.inputs.release_version }}'
          pr_body: |
            ## Release ${{ github.event.inputs.release_version }}

            ### Changes Included
            - Updated version numbers
            - Generated application descriptors
            - Updated documentation

            ### Validation
            - [x] All tests passing
            - [x] Descriptors generated successfully
            - [x] No breaking changes detected

            ### Deployment Notes
            This release requires the following deployment steps:
            1. Deploy backend modules first
            2. Update UI modules
            3. Verify all services are healthy

            ---
            *This PR was automatically updated by GitHub Actions*
          pr_labels: 'release,automated,ready-for-review'
          pr_reviewers: 'release-team,john-doe,jane-smith'
          github_token: ${{ secrets.GITHUB_TOKEN }}

      - name: Report Update Status
        run: |
          if [ "${{ steps.update.outputs.pr_exists }}" == "true" ]; then
            echo "✅ PR found: ${{ steps.update.outputs.pr_url }}"

            if [ "${{ steps.update.outputs.pr_updated }}" == "true" ]; then
              echo "✅ PR content updated successfully"
            else
              echo "ℹ️ No content updates were needed"
            fi

            if [ -n "${{ steps.update.outputs.labels_added }}" ]; then
              echo "✅ Labels added: ${{ steps.update.outputs.labels_added }}"
            fi

            if [ -n "${{ steps.update.outputs.successful_reviewers }}" ]; then
              echo "✅ Reviewers added: ${{ steps.update.outputs.successful_reviewers }}"
            fi

            if [ -n "${{ steps.update.outputs.failed_reviewers }}" ]; then
              echo "⚠️ Failed to add reviewers: ${{ steps.update.outputs.failed_reviewers }}"
            fi
          else
            echo "❌ PR #${{ github.event.inputs.pr_number }} not found"
            exit 1
          fi
```

### Conditional Update Example

```yaml
- name: Get PR Information
  id: pr-info
  run: |
    pr_exists=$(gh pr view ${{ github.event.pull_request.number }} --json state --jq '.state' 2>/dev/null || echo "notfound")
    echo "pr_state=$pr_exists" >> "$GITHUB_OUTPUT"

- name: Update PR if Open
  if: steps.pr-info.outputs.pr_state == 'OPEN'
  uses: ./.github/actions/update-pr
  with:
    repo: ${{ github.repository }}
    pr_number: ${{ github.event.pull_request.number }}
    pr_body: |
      ## Automated Update

      This PR has been automatically updated with the latest changes.

      **Last Updated**: ${{ github.event.head_commit.timestamp }}
      **Commit**: ${{ github.sha }}
    pr_labels: 'auto-updated'
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

### Matrix Update Example

```yaml
strategy:
  matrix:
    pr:
      - number: 123
        title: 'Release: Platform Core v1.0'
        labels: 'release,core,high-priority'
      - number: 124
        title: 'Release: Platform UI v1.0'
        labels: 'release,ui,high-priority'

steps:
  - name: Update PR ${{ matrix.pr.number }}
    uses: ./.github/actions/update-pr
    with:
      repo: ${{ github.repository }}
      pr_number: ${{ matrix.pr.number }}
      pr_title: ${{ matrix.pr.title }}
      pr_labels: ${{ matrix.pr.labels }}
      pr_reviewers: 'release-team'
      github_token: ${{ secrets.GITHUB_TOKEN }}
```

### Incremental Update Example

```yaml
- name: Add Labels to Existing PR
  uses: ./.github/actions/update-pr
  with:
    repo: ${{ github.repository }}
    pr_number: '456'
    pr_labels: 'ready-for-merge,approved'
    github_token: ${{ secrets.GITHUB_TOKEN }}

- name: Add Additional Reviewers
  uses: ./.github/actions/update-pr
  with:
    repo: ${{ github.repository }}
    pr_number: '456'
    pr_reviewers: 'security-team'
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

## Behavior

### Title and Body Updates

1. **Retrieves Current Content**: Gets existing PR title and body
2. **Compares Values**: Only updates fields that are different from current values
3. **Preserves Content**: Keeps existing content when new values are not provided
4. **Atomic Updates**: Updates title and body together when both are changed

### Label Management

1. **Checks Existing Labels**: Retrieves current PR labels to avoid duplicates
2. **Creates Missing Labels**: Automatically creates labels that don't exist in the repository
3. **Adds New Labels**: Only adds labels that aren't already applied to the PR
4. **Handles Failures**: Continues processing remaining labels if one fails

### Reviewer Management

1. **Supports User and Team Reviewers**: Handles both individual users and organization teams
2. **Detects Team Format**: Recognizes `org/team-name` format for team reviewers
3. **Avoids Duplicates**: Checks existing reviewers to prevent duplicate requests
4. **Handles Failures**: Reports failed reviewer additions without stopping the process

### Error Handling

1. **PR Existence Check**: Validates that the PR exists before attempting updates
2. **Permission Validation**: Handles authentication and permission errors gracefully
3. **Partial Success**: Allows some operations to succeed even if others fail
4. **Detailed Reporting**: Provides specific feedback on what succeeded or failed

## Requirements

### Permissions

The GitHub token must have the following permissions:

- **Pull requests: write**: To update PR title, body, labels, and reviewers
- **Contents: read**: To access repository information
- **Metadata: read**: To read repository and organization details

### Repository Access

- **Repository Access**: Token must have access to the specified repository
- **Team Access**: For team reviewers, token must have appropriate organization permissions
- **Label Creation**: Token must have permission to create labels if they don't exist

## Troubleshooting

### Common Issues

#### PR Not Found
```
::notice::PR #123 does not exist
```
**Solutions**:
- Verify the PR number is correct
- Check that the repository name is in the correct format (`org/repo`)
- Ensure the PR hasn't been deleted or closed
- Verify the GitHub token has repository access

#### Permission Denied
```
HTTP 403: Resource not accessible by integration
```
**Solutions**:
- Check that the GitHub token has the required permissions
- Verify the token is not expired
- Ensure the repository visibility matches token permissions
- For organization repositories, check organization settings

#### Label Creation Failed
```
::warning::Failed to create label 'custom-label'
```
**Solutions**:
- Check that the token has repository write permissions
- Verify label name doesn't contain invalid characters
- Ensure the label doesn't already exist with different casing
- Check repository settings for label restrictions

#### Reviewer Addition Failed
```
::warning::Failed to add user: john-doe
```
**Solutions**:
- Verify the username exists and is spelled correctly
- Check that the user has repository access
- For team reviewers, ensure the team exists and format is correct (`org/team`)
- Verify the user isn't already a reviewer or the PR author

#### No Updates Needed
```
::notice::No updates needed for PR #123
```
**Explanation**:
- This is normal when the provided title/body matches existing content
- The action skips unnecessary API calls when no changes are detected
- Use different values or check current PR content if updates are expected

### Debug Information

The action provides detailed logging:

- **PR Information**: Shows current title, body, and existing labels/reviewers
- **Update Operations**: Logs which fields are being updated
- **Label Processing**: Shows each label being processed and its status
- **Reviewer Processing**: Shows each reviewer being added and the result
- **API Responses**: Displays relevant API response information for debugging

### Validation Tips

**Check PR Status**:
```bash
gh pr view 123 --repo org/repo --json state,title,body,labels
```

**Verify Permissions**:
```bash
gh api repos/org/repo --jq '.permissions'
```

**Test Label Creation**:
```bash
gh label create "test-label" --repo org/repo --description "Test" --color "0366d6"
```

## Related Actions

- **[create-pr](../create-pr/README.md)**: Create new pull requests
- **[get-release-config](../get-release-config/README.md)**: Get configuration for PR reviewers and labels
- **[generate-application-descriptor](../generate-application-descriptor/README.md)**: Generate content for PR updates

## Integration Examples

### With Release Configuration

```yaml
- name: Get Release Configuration
  id: config
  uses: ./.github/actions/get-release-config
  with:
    repo: ${{ github.repository }}

- name: Update Release PR
  uses: ./.github/actions/update-pr
  with:
    repo: ${{ github.repository }}
    pr_number: ${{ github.event.inputs.pr_number }}
    pr_labels: ${{ steps.config.outputs.pr_labels }}
    pr_reviewers: ${{ steps.config.outputs.pr_reviewers }}
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

### With Generated Content

```yaml
- name: Generate Application Descriptor
  id: generate
  uses: ./.github/actions/generate-application-descriptor
  with:
    app_name: 'platform'

- name: Update PR with Generated Content
  if: steps.generate.outputs.generated == 'true'
  uses: ./.github/actions/update-pr
  with:
    repo: ${{ github.repository }}
    pr_number: ${{ github.event.pull_request.number }}
    pr_body: |
      ## Generated Application Descriptor

      ✅ **Descriptor Generated**: ${{ steps.generate.outputs.descriptor_file }}
      ✅ **No Placeholders**: All versions are properly specified

      The application descriptor has been successfully generated and is ready for review.
    pr_labels: 'descriptor-generated,ready-for-review'
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

### Automated PR Workflow

```yaml
name: Automated PR Updates

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  update-pr:
    runs-on: ubuntu-latest
    steps:
      - name: Add Initial Labels
        uses: ./.github/actions/update-pr
        with:
          repo: ${{ github.repository }}
          pr_number: ${{ github.event.pull_request.number }}
          pr_labels: 'needs-review,auto-labeled'
          github_token: ${{ secrets.GITHUB_TOKEN }}

      - name: Add Reviewers Based on Files
        if: contains(github.event.pull_request.changed_files, 'src/')
        uses: ./.github/actions/update-pr
        with:
          repo: ${{ github.repository }}
          pr_number: ${{ github.event.pull_request.number }}
          pr_reviewers: 'development-team'
          github_token: ${{ secrets.GITHUB_TOKEN }}
```