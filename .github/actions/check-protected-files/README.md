# Check Protected Files Action

**Action**: `check-protected-files`
**Purpose**: Validates that critical application files are not deleted
**Type**: Composite action

## Overview

This action checks whether protected files have been deleted in a PR or commit. It prevents accidental removal of critical application files:

- **Lock files** (`application.lock.json`): Tracks deployed module versions
- **Template files** (`application.template.json`): Application configuration template

The action supports two contexts:
- **PR context**: Uses GitHub API to check file changes
- **Merge queue context**: Uses `git diff` to check file changes

## Inputs

| Input                     | Description                              | Required | Default                     |
|---------------------------|------------------------------------------|----------|-----------------------------|
| `check_type`              | Type of check: `pr` or `merge_queue`     | Yes      | -                           |
| `repo_owner`              | Repository owner                         | Yes      | -                           |
| `repo_name`               | Repository name                          | Yes      | -                           |
| `pr_number`               | Pull request number (for PR context)     | No       | -                           |
| `head_sha`                | Commit SHA (for logging in merge_queue)  | No       | -                           |
| `github_token`            | GitHub token                             | Yes      | -                           |
| `protected_lock_file`     | Lock file name to protect                | No       | `application.lock.json`     |
| `protected_template_file` | Template file name to protect            | No       | `application.template.json` |

## Outputs

| Output          | Description                                    |
|-----------------|------------------------------------------------|
| `has_violations`| Whether violations were found (`true`/`false`) |
| `violations`    | Semicolon-separated violation messages         |

## How It Works

### PR Context (`check_type: pr`)

Uses GitHub API to retrieve files changed in the PR:

```javascript
const { data: files } = await github.rest.pulls.listFiles({
  owner: repo_owner,
  repo: repo_name,
  pull_number: pr_number
});
```

Checks each file for:
- `status === 'removed'`
- Filename matches protected file names

### Merge Queue Context (`check_type: merge_queue`)

Uses git diff to check file changes:

```bash
git diff --name-status HEAD~1 HEAD
```

Parses output for:
- Files with status `D` (deleted)
- Filename matches protected file names

## Usage

### In PR Check Workflow

```yaml
- name: Check Protected Files
  id: check-protected
  uses: folio-org/kitfox-github/.github/actions/check-protected-files@master
  with:
    check_type: pr
    repo_owner: ${{ inputs.repo_owner }}
    repo_name: ${{ inputs.repo_name }}
    pr_number: ${{ inputs.pr_number }}
    github_token: ${{ steps.app-token.outputs.token }}
    protected_lock_file: application.lock.json
    protected_template_file: application.template.json
```

### In Merge Queue Check Workflow

```yaml
- name: Check Protected Files
  id: check-protected
  uses: folio-org/kitfox-github/.github/actions/check-protected-files@master
  with:
    check_type: merge_queue
    repo_owner: ${{ inputs.repo_owner }}
    repo_name: ${{ inputs.repo_name }}
    head_sha: ${{ inputs.head_sha }}
    github_token: ${{ steps.app-token.outputs.token }}
```

### Using Output

```yaml
- name: Handle Violations
  if: steps.check-protected.outputs.has_violations == 'true'
  run: |
    echo "Protected file violations found:"
    echo "${{ steps.check-protected.outputs.violations }}"
```

## Violation Messages

When violations are found, the `violations` output contains messages like:

```
application.lock.json: lock file deletion not allowed; application.template.json: template file deletion not allowed
```

Messages are semicolon-separated for multiple violations.

## Prerequisites

### For PR Context

- GitHub token must have read access to pull requests
- PR number must be valid

### For Merge Queue Context

- Repository must be checked out with `fetch-depth: 2`
- Allows comparison with previous commit (`HEAD~1`)

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 2
```

## Error Handling

The action logs violations but does not fail:
- Violations are reported via outputs
- Calling workflow decides how to handle violations
- Typically used with `check-run-create` to create failure status

## Related Documentation

- **[Check Run Create Action](../check-run-create/README.md)**: Creates check run based on violations
- **[PR Check Workflow](../../docs/pr-check.md)**: Uses this action
- **[Merge Queue Check Workflow](../../docs/merge-queue-check.md)**: Uses this action

---

**Last Updated**: December 2025
**Version**: 1.0
