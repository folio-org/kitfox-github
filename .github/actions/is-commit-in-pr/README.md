# Is Commit in PR

Checks if a specific commit SHA exists in a pull request.

## Description

This action verifies whether a given commit SHA (full or short form) exists within a pull request's commit history. It's particularly useful for security and validation workflows that need to ensure a commit belongs to a specific PR before taking actions.

The action handles pagination automatically, checking all commits in the PR regardless of how many pages the GitHub API returns.

## Inputs

| Input          | Description                                                                      | Required  | Default               |
|----------------|----------------------------------------------------------------------------------|-----------|-----------------------|
| `repository`   | Target repository (owner/repo format). If not provided, uses current repository  | No        | Current repository    |
| `pr_number`    | Pull request number to check against                                             | Yes       | -                     |
| `commit_sha`   | Commit SHA to check (full or short)                                              | Yes       | -                     |
| `github_token` | GitHub token for API access                                                      | Yes       | `${{ github.token }}` |

## Outputs

| Output         | Description                                       |
|----------------|---------------------------------------------------|
| `commit_found` | Whether the commit exists in the PR (true/false)  |
| `skip_reason`  | Reason for failure if commit is not found         |

## Usage

### Basic Example (Current Repository)

```yaml
- name: Check Commit in PR
  id: check
  uses: folio-org/kitfox-github/.github/actions/is-commit-in-pr@master
  with:
    pr_number: ${{ github.event.pull_request.number }}
    commit_sha: ${{ github.event.after }}
    github_token: ${{ github.token }}

- name: Proceed if valid
  if: steps.check.outputs.commit_found == 'true'
  run: echo "Commit is valid in this PR"
```

### Cross-Repository Example

```yaml
- name: Check Commit in PR from Another Repository
  id: check
  uses: folio-org/kitfox-github/.github/actions/is-commit-in-pr@master
  with:
    repository: folio-org/app-acquisitions
    pr_number: 123
    commit_sha: abc123def456
    github_token: ${{ secrets.GITHUB_TOKEN }}

- name: Proceed if valid
  if: steps.check.outputs.commit_found == 'true'
  run: echo "Commit abc123def456 is valid in folio-org/app-acquisitions PR #123"
```

### Security Check Before Running Tests

```yaml
- name: Check Commit in PR
  id: check-commit
  uses: folio-org/kitfox-github/.github/actions/is-commit-in-pr@master
  with:
    pr_number: ${{ inputs.pr_number }}
    commit_sha: ${{ inputs.head_sha }}
    github_token: ${{ github.token }}

- name: Stop if commit is invalid
  if: steps.check-commit.outputs.commit_found != 'true'
  run: |
    echo "Error: Commit does not belong to this PR"
    echo "Reason: ${{ steps.check-commit.outputs.skip_reason }}"
    exit 1

- name: Run tests
  if: steps.check-commit.outputs.commit_found == 'true'
  run: npm test
```

### Using with Workflow Dispatch

```yaml
name: Manual PR Check

on:
  workflow_dispatch:
    inputs:
      pr_number:
        description: 'Pull Request Number'
        required: true
      commit_sha:
        description: 'Commit SHA to check'
        required: true

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Check Commit in PR
        id: check
        uses: folio-org/kitfox-github/.github/actions/is-commit-in-pr@master
        with:
          pr_number: ${{ inputs.pr_number }}
          commit_sha: ${{ inputs.commit_sha }}
          github_token: ${{ github.token }}

      - name: Display result
        run: |
          if [[ "${{ steps.check.outputs.commit_found }}" == "true" ]]; then
            echo "✓ Commit ${{ inputs.commit_sha }} is valid in PR #${{ inputs.pr_number }}"
          else
            echo "✗ Commit check failed"
            echo "Reason: ${{ steps.check.outputs.skip_reason }}"
            exit 1
          fi
```

### Combined with Get PR Info Action

```yaml
- name: Get Pull Request Information
  id: pr-info
  uses: folio-org/kitfox-github/.github/actions/get-pr-info@master
  with:
    pr_number: ${{ inputs.pr_number }}
    github_token: ${{ github.token }}

- name: Check Commit in PR
  id: check-commit
  if: steps.pr-info.outputs.pr_exists == 'true'
  uses: folio-org/kitfox-github/.github/actions/is-commit-in-pr@master
  with:
    pr_number: ${{ inputs.pr_number }}
    commit_sha: ${{ inputs.head_sha }}
    github_token: ${{ github.token }}

- name: Checkout if valid
  if: |
    steps.pr-info.outputs.pr_exists == 'true' &&
    steps.check-commit.outputs.commit_found == 'true'
  uses: actions/checkout@v4
  with:
    ref: ${{ inputs.head_sha }}
```

## How It Works

1. **SHA Matching**: The action supports both full and short SHA formats. It checks:
   - Exact match: `commit.sha === providedSha`
   - Full SHA starts with provided short SHA: `commit.sha.startsWith(providedSha)`
   - Provided SHA is a full SHA that starts with short SHA: `providedSha.startsWith(commit.sha)`

2. **Pagination**: The action automatically handles GitHub API pagination (100 commits per page) to check all commits in the PR.

3. **Early Exit**: The action stops searching as soon as it finds the commit, making it efficient for PRs with many commits.

## Error Handling

The action handles the following cases:

1. **Commit Not Found**: If the commit doesn't exist in the PR after checking all pages, `commit_found` will be `false` and `skip_reason` will indicate the commit was not found.
2. **API Errors**: If the GitHub API call fails, `commit_found` will be `false` and `skip_reason` will contain the error message.

## Example Output

When check succeeds:

```yaml
commit_found: 'true'
skip_reason: ''
```

When check fails:

```yaml
commit_found: 'false'
skip_reason: 'Commit abc123 not found in PR #123'
```

## Security Considerations

This action is particularly useful for security-sensitive workflows where you need to ensure that:

- The commit being processed actually belongs to the PR
- No unauthorized commits are being checked out or deployed
- Workflow dispatch events reference valid commits within the specified PR

## Notes

- The action requires read access to pull requests
- Both full (40-character) and short (7+ character) SHA formats are supported
- The action logs progress as it checks each page of commits
- Large PRs with many commits may take longer to check, but the action efficiently handles pagination
- When using the `repository` parameter to access a different repository, ensure the `github_token` has appropriate permissions for that repository
- For cross-repository access, consider using a GitHub App token or a Personal Access Token with sufficient scope
