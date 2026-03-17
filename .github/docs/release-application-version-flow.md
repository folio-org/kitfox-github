# Release Application Version Flow

**Workflow**: `release-application-version-flow.yml`
**Purpose**: Creates a GitHub Release with git tag and application-descriptor.json asset for FOLIO applications
**Type**: Reusable workflow (`workflow_call`)

## Overview

This workflow automates GitHub Release creation for FOLIO application repositories. It tags a specific commit with the application version, creates a GitHub Release, and uploads `application-descriptor.json` as a release asset — matching the existing Jenkins release convention.

The workflow can be triggered in two ways:

1. **Automated**: Called by `post-merge-flow.yml` after a successful FAR publish
2. **Manual**: Via `workflow_dispatch` wrapper in each app repo (`release-application-version.yml`)

## Workflow Interface

### Inputs

| Input           | Description                                 | Required | Type    | Default   |
|-----------------|---------------------------------------------|----------|---------|-----------|
| `repo_owner`    | Repository owner (organization)             | Yes      | string  | -         |
| `repo_name`     | Repository name (e.g., `app-acquisitions`)  | Yes      | string  | -         |
| `commit_sha`    | Commit SHA to tag (empty = branch HEAD)     | No       | string  | `''`      |
| `base_branch`   | Branch to checkout and release from         | No       | string  | `''`      |
| `release_notes` | Release notes body text                     | No       | string  | `''`      |
| `dry_run`       | Simulate without creating tag/release       | No       | boolean | `false`   |

### Outputs

| Output            | Description                                          |
|-------------------|------------------------------------------------------|
| `release_created` | Whether release was created (`true`/`false`/`skipped`/`dry_run`) |
| `release_url`     | URL of the created GitHub Release                    |
| `tag_name`        | Tag name created (e.g., `v1.0.28`)                  |
| `app_version`     | Application version (e.g., `1.0.28`)                |
| `failure_reason`  | Reason for failure if any                            |

### Permissions

| Permission | Level | Purpose                    |
|------------|-------|----------------------------|
| `contents` | read  | Read repository content    |

Note: Tag and release creation use the GitHub App Token, not `GITHUB_TOKEN`.

### Secrets

| Secret                      | Description                       | Required |
|-----------------------------|-----------------------------------|----------|
| `EUREKA_CI_APP_KEY`         | GitHub App private key            | Yes      |
| `EUREKA_CI_SLACK_BOT_TOKEN` | Slack bot token for notifications | Yes      |

### Variables

| Variable                      | Description                        | Required |
|-------------------------------|------------------------------------|----------|
| `EUREKA_CI_APP_ID`            | GitHub App ID                      | Yes      |
| `SLACK_NOTIF_CHANNEL`         | Team Slack notification channel    | No       |
| `GENERAL_SLACK_NOTIF_CHANNEL` | General Slack notification channel | No       |

### Concurrency

Concurrent releases for the same repo are serialized:
```yaml
concurrency:
  group: release-app-version-{repo_owner}-{repo_name}
  cancel-in-progress: false
```

## Workflow Execution Flow

### 1. Create GitHub Release
**Job**: `create-release`

Creates tag, GitHub Release, and uploads application-descriptor.json.

**Steps**:
1. Generate GitHub App Token
2. Checkout Repository at `commit_sha` or `base_branch`
3. Validate Descriptor — verify `application.lock.json` exists
4. Extract Version — `jq -r '.version' application.lock.json`; reject SNAPSHOT versions
5. Check Existing Tag and Release — idempotent skip if already exists
6. Determine Commit SHA — resolve from input or HEAD
7. Prepare Release Asset — copy `application.lock.json` → `application-descriptor.json`
8. Create GitHub Release — `gh release create` with tag, title, notes, and asset

**Release Convention** (matches Jenkins):
- Tag: `v{version}` (e.g., `v1.0.28`)
- Title: same as tag
- Asset: `application-descriptor.json` (~500KB resolved descriptor)
- Not draft, not prerelease

### 2. Send Notifications
**Job**: `notify`

Sends Slack notifications with release results.

**Condition**: Runs unless dry_run or cancelled

**Message Format**:
```
*app-acquisitions release published #42*

Tag: v1.0.28
Version: 1.0.28
Branch: R2-2025
Commit: ee30528...
```

**Color Coding**:
- Green: Release created successfully
- Yellow: Skipped (tag already exists)
- Red: Release failed

### 3. Workflow Summary
**Job**: `summarize`

Generates workflow summary in GitHub Actions UI.

**Summary Sections**:
1. Repository, branch, commit info
2. Release Status — tag, version, release URL (or failure reason)
3. Notification Status — Slack delivery status

## Features

### Idempotent Re-runs

If a release for the same version already exists, the workflow:
- Detects the existing tag and release via `gh release view`
- Outputs `release_created=skipped` with the existing release URL
- Does not fail or create duplicates

### SNAPSHOT Guard

SNAPSHOT versions (e.g., `1.0.0-SNAPSHOT`) are rejected:
- Prevents accidental snapshot releases
- Outputs descriptive failure reason
- Manual trigger on snapshot branch is safely handled

### Dry Run Mode

When `dry_run: true`:
- All validation runs normally
- Tag and release creation are skipped
- Notifications are suppressed
- Summary shows what would have been created

### Asset Upload

The `application-descriptor.json` release asset is:
- A copy of `application.lock.json` (the fully resolved descriptor)
- Contains all concrete module versions (~500KB)
- Same file published to FAR
- Matches existing Jenkins convention

## Usage Examples

### Automated (from post-merge-flow)

Called automatically after a PR merge publishes to FAR:

```yaml
release:
  uses: folio-org/kitfox-github/.github/workflows/release-application-version-flow.yml@master
  with:
    repo_owner: ${{ inputs.repo_owner }}
    repo_name: ${{ inputs.repo_name }}
    commit_sha: ${{ inputs.head_sha }}
    base_branch: ${{ needs.pre-check.outputs.base_branch }}
    release_notes: ${{ needs.pre-check.outputs.pr_body }}
  secrets: inherit
```

### Manual (from app repo)

Dev teams trigger from their repo's Actions tab:

```yaml
# .github/workflows/release-application-version.yml (in app repo)
jobs:
  release:
    uses: folio-org/kitfox-github/.github/workflows/release-application-version-flow.yml@master
    with:
      repo_owner: ${{ github.repository_owner }}
      repo_name: ${{ github.event.repository.name }}
      commit_sha: ${{ inputs.commit_sha }}
      base_branch: ${{ github.ref_name }}
      release_notes: ${{ inputs.release_notes }}
      dry_run: ${{ inputs.dry_run }}
    secrets: inherit
```

## Error Handling

### Failure Scenarios

**Descriptor Not Found**:
- `application.lock.json` missing from checkout
- Outputs `failure_reason` with descriptive message
- Release not created

**SNAPSHOT Version**:
- Version contains "SNAPSHOT"
- Outputs `failure_reason` explaining SNAPSHOT rejection
- Release not created

**Release Creation Failed**:
- `gh release create` command failed
- Could be permissions, network, or GitHub API issue
- Outputs `failure_reason` with error details

### Graceful Degradation

- Existing tag/release: skipped gracefully (not an error)
- Notification failures: `continue-on-error: true`
- Summary always runs regardless of outcome

## Troubleshooting

### Common Issues

**Release Not Created**:
1. Check `application.lock.json` exists on the target branch/commit
2. Verify version is not SNAPSHOT
3. Check GitHub App has `contents: write` permission on the repo
4. Review create-release job logs

**Tag Already Exists**:
- Normal behavior on re-runs
- Workflow outputs `skipped` with existing URL
- Not an error condition

### Debug Commands

**Test Manually (dry run)**:
Select the release branch in the app repo's Actions tab, then trigger with `dry_run: true`.

**Check Existing Releases**:
```bash
gh release list --repo folio-org/app-acquisitions --limit 5
```

**View Specific Release**:
```bash
gh release view v1.0.28 --repo folio-org/app-acquisitions
```

**Check Application Version**:
```bash
gh api repos/folio-org/app-acquisitions/contents/application.lock.json \
  --jq '.content' | base64 -d | jq '.version'
```

## Related Documentation

- **[Post-Merge Flow](post-merge-flow.md)**: Calls this workflow after FAR publish
- **[Publish App Descriptor Action](../actions/publish-app-descriptor/README.md)**: FAR publishing
- **[Release Preparation](release-preparation.md)**: Release branch creation
- **[Application Update](application-update.md)**: Module version updates

---

**Last Updated**: March 2026
**Workflow Version**: 1.0
**Compatibility**: GitHub App webhook integration, requires `application.lock.json` in repository
