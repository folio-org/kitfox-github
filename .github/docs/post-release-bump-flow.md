# Post-Release Bump (Flow)

**Workflow**: `kitfox-github/.github/workflows/post-release-bump-flow.yml`
**Type**: `workflow_call` reusable workflow (per-app worker)
**Called by**: `platform-lsp/.github/workflows/post-release-bump-orchestrator.yml` (operator runbook: [post-release-bump-orchestrator.md](https://github.com/folio-org/platform-lsp/blob/master/.github/docs/post-release-bump-orchestrator.md))

This document covers the per-app component contract: inputs, the bump sequence, failure semantics, and the result artifact shape. For operator-facing run procedure, see the orchestrator doc.

## Inputs

| Input | Type | Required | Notes |
|---|---|---|---|
| `app_name` | string | yes | Application name (e.g., `app-acquisitions`). Used in artifact names and logs. |
| `repo` | string | yes | Target repository in `org/repo` form (e.g., `folio-org/app-acquisitions`). |
| `release_branch` | string | yes | Release branch to read the base version from (e.g., `R1-2026`). |
| `target_branch` | string | no (default `snapshot`) | Branch to bump — current version is read from here, the pom edit is committed here. Default `snapshot` is correct for the standard post-release workflow; configurable for non-standard lineages. |
| `dry_run` | boolean | no (default `false`) | When true, preflight + version compute + pom edit run; commit-and-push skips the actual push. |

## Per-App Sequence

1. **Mint App token** — single-repo-scoped token via `actions/create-github-app-token@v1` using `vars.EUREKA_CI_APP_ID` + `secrets.EUREKA_CI_APP_KEY`, with `owner: folio-org` and `repositories: ${{ inputs.app_name }}`. Least-privilege per matrix shard.
2. **Preflight** — confirms the release branch and `snapshot` branch exist via `gh api repos/folio-org/<app>/branches/<branch>`. Fast-fail with `release_branch_missing` or `snapshot_branch_missing`.
3. **Collect release-branch version** — calls the shared [`collect-app-version`](../actions/collect-app-version/README.md) action with `branch: <release_branch>`. The action reads `pom.xml` via the GitHub Contents API and returns `version`, `major`, `minor`, `patch`, `is_snapshot`. RANCHER-2977 retired mvn-based reads, so no Maven Central dependency.
4. **Validate release version is not SNAPSHOT** — if the action returns `is_snapshot == 'true'`, fail with `pom_invalid_release_version`. Release branches must hold a clean `X.Y.Z` version.
5. **Compute target** — `<major>.<minor + 1>.0-SNAPSHOT`.
6. **Collect target-branch version** — same action, `branch: <target_branch>` (default `snapshot`). Returns the same output shape.
7. **Idempotency** — numeric tuple comparison on `(major, minor, patch)`. If `snapshot ≥ target`, the run resolves to `status=skipped`, `skipped_reason=already_at_or_above_target`. Snapshot is never downgraded.
8. **Checkout snapshot** — `actions/checkout@v4` against `ref: snapshot` with the App token.
9. **Edit `pom.xml`** — targeted `awk` that rewrites the first `<version>` element on the file. The project version is the first `<version>` in every FOLIO app pom (no `<parent>` block in any of them). `application.template.json` references `${project.version}` so it cascades on the next CI build — no second file to edit.
10. **Commit & push** — via the reusable `commit-and-push-changes.yml` workflow with `use_github_app: true` and `branch: snapshot`. The App must be in the snapshot branch ruleset's `bypass_actors` for the push to succeed; this is already configured by every app's `update-config.yml` (`actor_type: Integration, bypass_mode: always`).
11. **Result artifact** — `result-<app>.json` uploaded for orchestrator aggregation.

## Result Artifact

`result-<app_name>.json`:

```json
{
  "application": "app-acquisitions",
  "status": "success | skipped | failed",
  "release_branch": "R1-2026",
  "release_branch_version": "2.0.0",
  "previous_snapshot_version": "1.2.0-SNAPSHOT",
  "new_snapshot_version": "2.1.0-SNAPSHOT",
  "commit_sha": "abc1234",
  "failure_reason": "",
  "skipped_reason": "",
  "dry_run": false
}
```

Uploaded with `actions/upload-artifact@v4` and name `result-<app_name>`. The orchestrator's `collect-results` job downloads with `pattern: "result-*"`, `merge-multiple: true`.

## Failure Reason Codes

| Reason | Meaning | Remediation |
|---|---|---|
| `release_branch_missing` | The release branch does not exist on the target repo. | Confirm `release-preparation-orchestrator.yml` ran for this app, or drop the app from scope. |
| `snapshot_branch_missing` | The `snapshot` branch does not exist on the target repo. | Investigate the repo state — every Eureka-CI app should have a `snapshot` branch. |
| `pom_release_read_failed` | The `collect-app-version` action failed reading the release branch's `pom.xml`. Action's `error_category` (`POM_NOT_FOUND` or `INVALID_VERSION_FORMAT`) is surfaced in the step logs. | Inspect the pom on the release branch; check the App token has read access. |
| `pom_invalid_release_version` | Release-branch version carries `-SNAPSHOT`. Release branches must hold a clean `X.Y.Z` version. | Investigate the release-prep run for that app before retrying. |
| `pom_snapshot_read_failed` | The `collect-app-version` action failed reading snapshot's `pom.xml`. Same surface as `pom_release_read_failed`. | Inspect the pom on `snapshot`. |
| `pom_edit_no_op` | The `awk` transform produced no diff (defensive — should not normally trigger after the idempotency step). | Investigate the pom structure and retry. |
| `commit_failed` | `commit-and-push-changes.yml` failed (push rejected, network error, etc.). | Check the push step logs. Verify the App is in the snapshot ruleset's `bypass_actors`. |

## Skipped Reason Codes

| Reason | Meaning |
|---|---|
| `already_at_or_above_target` | Snapshot's `(major, minor, patch)` ≥ target's. No action needed. |

## Authentication

- One GitHub App token is minted **per matrix shard**, scoped to a **single target repository** via `repositories: ${{ inputs.app_name }}`. A token leak in one shard's logs cannot compromise other repos.
- Auth requires `vars.EUREKA_CI_APP_ID` and `secrets.EUREKA_CI_APP_KEY` — already available org-wide.
- For the push to succeed, the App identity must be in the snapshot branch ruleset's `bypass_actors`. This is already configured in every app's `update-config.yml`.

## Related Workflows

- `commit-and-push-changes.yml` — reused for the commit step; see [`commit-and-push-changes.md`](commit-and-push-changes.md).
- `release-preparation-flow.yml` — the per-app worker for release branch creation, called by `release-preparation-orchestrator.yml`. This flow runs *after* release-preparation completes.
- `application-update-flow.yml` — the per-app worker for routine snapshot module-version updates. Different concern: it bumps module versions in `application.template.json`, not the project version in `pom.xml`.
