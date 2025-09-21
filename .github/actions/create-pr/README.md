# Create Pull Request Action

## Overview

The **Create PR** action provides automated pull request creation with intelligent duplicate detection, label management, and reviewer assignment. It ensures that only one pull request exists between any two branches while supporting comprehensive PR configuration.

## Features

- **Duplicate Prevention**: Automatically detects existing PRs between branches
- **Label Management**: Creates missing labels and assigns them to PRs
- **Reviewer Assignment**: Supports both individual and team reviewers
- **Graceful Error Handling**: Continues operation even if some reviewers fail
- **Comprehensive Outputs**: Provides detailed status information

## Usage

```yaml
- name: Create Pull Request
  uses: folio-org/kitfox-github/.github/actions/create-pr@master
  with:
    repo: ${{ github.repository }}
    base_branch: 'main'
    head_branch: 'feature/new-feature'
    pr_title: 'Add new feature'
    pr_body: 'This PR adds a new feature to the application'
    pr_labels: 'enhancement,documentation'
    pr_reviewers: 'user1,user2,org/team-name'
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

## Inputs

| Input          | Required  | Description                                            | Default  |
|----------------|-----------|--------------------------------------------------------|----------|
| `repo`         | **Yes**   | Repository in org/repo format                          | -        |
| `base_branch`  | **Yes**   | Target branch for the PR                               | -        |
| `head_branch`  | **Yes**   | Source branch containing changes                       | -        |
| `pr_title`     | **Yes**   | Title for the pull request                             | -        |
| `pr_body`      | **Yes**   | Description/body of the pull request                   | -        |
| `pr_labels`    | No        | Comma-separated list of labels                         | -        |
| `pr_reviewers` | No        | Comma-separated list of reviewers (users or org/teams) | -        |
| `github_token` | **Yes**   | GitHub token with repo and pull request permissions    | -        |

## Outputs

| Output                 | Description                                             |
|------------------------|---------------------------------------------------------|
| `pr_created`           | Boolean indicating if a new PR was created              |
| `pr_exists`            | Boolean indicating if a PR already exists               |
| `pr_number`            | The PR number (new or existing)                         |
| `pr_url`               | Full URL to the pull request                            |
| `successful_reviewers` | Comma-separated list of successfully assigned reviewers |
| `failed_reviewers`     | Comma-separated list of reviewers that failed to assign |

## Examples

### Basic Pull Request

```yaml
- name: Create Simple PR
  uses: folio-org/kitfox-github/.github/actions/create-pr@master
  with:
    repo: 'folio-org/my-app'
    base_branch: 'main'
    head_branch: 'feature/update-deps'
    pr_title: 'Update dependencies'
    pr_body: 'Updates all dependencies to latest versions'
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

### PR with Labels and Reviewers

```yaml
- name: Create PR with Metadata
  uses: folio-org/kitfox-github/.github/actions/create-pr@master
  with:
    repo: ${{ github.repository }}
    base_branch: 'release/v2.0'
    head_branch: 'hotfix/security-patch'
    pr_title: 'Security: Fix vulnerability in authentication'
    pr_body: |
      ## Changes
      - Patches security vulnerability
      - Updates authentication library

      ## Testing
      - Unit tests added
      - Security scan passed
    pr_labels: 'security,high-priority,hotfix'
    pr_reviewers: 'security-team-lead,org/security-team'
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

### Conditional PR Creation

```yaml
- name: Create PR if Not Exists
  id: create_pr
  uses: folio-org/kitfox-github/.github/actions/create-pr@master
  with:
    repo: ${{ github.repository }}
    base_branch: ${{ github.event.repository.default_branch }}
    head_branch: 'automated/dependency-updates'
    pr_title: 'Automated dependency updates'
    pr_body: 'This PR was automatically generated'
    github_token: ${{ secrets.GITHUB_TOKEN }}

- name: Report Status
  if: steps.create_pr.outputs.pr_created == 'true'
  run: |
    echo "New PR created: ${{ steps.create_pr.outputs.pr_url }}"
    echo "PR Number: ${{ steps.create_pr.outputs.pr_number }}"
```

## Behavior

### PR Detection
The action first checks if a pull request already exists between the specified branches:
- If a PR exists, it returns the existing PR information
- If no PR exists, it creates a new one with the specified configuration

### Label Handling
- Labels that don't exist in the repository are automatically created
- Label colors are automatically assigned for new labels
- Multiple labels can be specified as a comma-separated list

### Reviewer Assignment
- Individual users: Specified as `username`
- Teams: Specified as `org/team-name`
- The action continues even if some reviewers fail to assign
- Failed reviewers are reported in the `failed_reviewers` output

### Error Handling
The action handles various error scenarios:
- **Existing PR**: Returns existing PR info without error
- **Missing Labels**: Creates them automatically
- **Invalid Reviewers**: Reports in `failed_reviewers` output
- **Permission Issues**: Fails with clear error message

## Requirements

- **GitHub Token**: Must have `repo` and `pull_request` permissions
- **Branch Access**: Both branches must exist and be accessible
- **Repository Permissions**: Token must have write access to create PRs

## Troubleshooting

### Common Issues

**PR Already Exists**
- The action will not create duplicate PRs
- Check `pr_exists` output to detect this condition

**Reviewer Assignment Failed**
- Check `failed_reviewers` output for details
- Verify reviewer usernames and team names
- Ensure the token has permission to assign reviewers

**Label Creation Failed**
- Verify the token has permission to create labels
- Check for label name formatting issues

### Debug Output

Enable debug logging for detailed information:
```yaml
- name: Create PR with Debug
  env:
    ACTIONS_STEP_DEBUG: true
  uses: folio-org/kitfox-github/.github/actions/create-pr@master
  # ... other inputs
```

## Integration with Workflows

This action is commonly used in:
- **Release Workflows**: Creating release PRs
- **Automated Updates**: Dependency or configuration updates
- **Cross-Branch Synchronization**: Syncing changes between branches

## Related Actions

- [`update-pr`](../update-pr/README.md): Update existing pull requests
- [`orchestrate-external-workflow`](../orchestrate-external-workflow/README.md): Trigger workflows in other repositories

## Support

For issues or questions:
- Create an issue in [kitfox-github](https://github.com/folio-org/kitfox-github/issues)
- Contact the Kitfox DevOps team

---

**Action Version**: 1.0.0
**Last Updated**: September 2024
**Maintained By**: Kitfox DevOps Team