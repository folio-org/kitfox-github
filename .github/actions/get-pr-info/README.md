# Get Pull Request Information

Fetches detailed information about a pull request including labels, branches, and SHA.

## Description

This action retrieves comprehensive information about a GitHub pull request using the GitHub API. It's useful for workflows that need to make decisions based on PR metadata such as labels, branch names, or current state.

## Inputs

| Input          | Description                                                                      | Required  | Default               |
|----------------|----------------------------------------------------------------------------------|-----------|-----------------------|
| `repository`   | Target repository (owner/repo format). If not provided, uses current repository  | No        | Current repository    |
| `pr_number`    | Pull request number to fetch information for                                     | Yes       | -                     |
| `github_token` | GitHub token for API access                                                      | Yes       | `${{ github.token }}` |

## Outputs

| Output             | Description                                          |
|--------------------|------------------------------------------------------|
| `pr_exists`        | Whether the PR exists and is accessible (true/false) |
| `current_head_sha` | Current HEAD SHA of the pull request                 |
| `head_ref`         | Head branch reference of the pull request            |
| `base_ref`         | Base branch reference of the pull request            |
| `labels`           | JSON array of label names                            |
| `state`            | State of the pull request (open, closed)             |
| `skip_reason`      | Reason for skipping if PR does not exist             |

## Usage

### Basic Example (Current Repository)

```yaml
- name: Get Pull Request Information
  id: pr-info
  uses: folio-org/kitfox-github/.github/actions/get-pr-info@master
  with:
    pr_number: ${{ github.event.pull_request.number }}
    github_token: ${{ github.token }}

- name: Check if PR has specific label
  if: contains(fromJson(steps.pr-info.outputs.labels), 'release')
  run: echo "PR has release label"
```

### Cross-Repository Example

```yaml
- name: Get Pull Request Information from Another Repository
  id: pr-info
  uses: folio-org/kitfox-github/.github/actions/get-pr-info@master
  with:
    repository: folio-org/app-acquisitions
    pr_number: 123
    github_token: ${{ secrets.GITHUB_TOKEN }}

- name: Display PR information
  run: |
    echo "Repository: folio-org/app-acquisitions"
    echo "PR #123 Head Branch: ${{ steps.pr-info.outputs.head_ref }}"
    echo "PR #123 Base Branch: ${{ steps.pr-info.outputs.base_ref }}"
```

### Using PR Information for Conditional Logic

```yaml
- name: Get Pull Request Information
  id: pr-info
  uses: folio-org/kitfox-github/.github/actions/get-pr-info@master
  with:
    pr_number: ${{ inputs.pr_number }}
    github_token: ${{ secrets.GITHUB_TOKEN }}

- name: Validate PR exists
  if: steps.pr-info.outputs.pr_exists != 'true'
  run: |
    echo "PR does not exist: ${{ steps.pr-info.outputs.skip_reason }}"
    exit 1

- name: Check base branch
  if: steps.pr-info.outputs.base_ref == 'main'
  run: echo "PR targets main branch"

- name: Display PR metadata
  run: |
    echo "Head Branch: ${{ steps.pr-info.outputs.head_ref }}"
    echo "Base Branch: ${{ steps.pr-info.outputs.base_ref }}"
    echo "Current SHA: ${{ steps.pr-info.outputs.current_head_sha }}"
    echo "State: ${{ steps.pr-info.outputs.state }}"
    echo "Labels: ${{ steps.pr-info.outputs.labels }}"
```

### Working with Labels

```yaml
- name: Get Pull Request Information
  id: pr-info
  uses: folio-org/kitfox-github/.github/actions/get-pr-info@master
  with:
    pr_number: ${{ github.event.number }}
    github_token: ${{ github.token }}

- name: Parse and check labels
  id: check-labels
  env:
    LABELS: ${{ steps.pr-info.outputs.labels }}
  run: |
    echo "PR Labels: $LABELS"

    if echo "$LABELS" | jq -r '.[]' | grep -q "^do-not-merge$"; then
      echo "PR has do-not-merge label, stopping workflow"
      exit 1
    fi

    if echo "$LABELS" | jq -r '.[]' | grep -q "^hotfix$"; then
      echo "is_hotfix=true" >> "$GITHUB_OUTPUT"
    fi
```

## Error Handling

The action handles the following error cases:

1. **Invalid PR Number**: If the PR number is not a valid positive integer, `pr_exists` will be `false` and `skip_reason` will contain the error message.
2. **PR Not Found**: If the PR doesn't exist or is inaccessible, `pr_exists` will be `false` and `skip_reason` will indicate the PR was not found.
3. **API Errors**: If the GitHub API call fails, `pr_exists` will be `false` and `skip_reason` will contain the error message.

## Example Output

When the action succeeds, the outputs will look like:

```yaml
pr_exists: 'true'
current_head_sha: 'abc123def456...'
head_ref: 'feature/new-feature'
base_ref: 'main'
labels: '["bug", "priority-high", "release"]'
state: 'open'
skip_reason: ''
```

When the action fails:

```yaml
pr_exists: 'false'
current_head_sha: ''
head_ref: ''
base_ref: ''
labels: ''
state: ''
skip_reason: 'PR #999 not found or inaccessible'
```

## Notes

- The action requires read access to pull requests
- The `labels` output is a JSON array string that can be parsed using `fromJson()` in workflow conditions
- The action will log PR details to the console for debugging purposes
- When using the `repository` parameter to access a different repository, ensure the `github_token` has appropriate permissions for that repository
- For cross-repository access, consider using a GitHub App token or a Personal Access Token with sufficient scope
