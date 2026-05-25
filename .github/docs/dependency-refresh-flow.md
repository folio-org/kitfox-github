# Dependency Refresh (Flow)

**Workflow**: `kitfox-github/.github/workflows/dependency-refresh-flow.yml`
**Type**: `workflow_call` reusable workflow (per-app worker)
**Called by**: `platform-lsp/.github/workflows/post-release-bump-orchestrator.yml` — the `dependency-refresh` matrix job that runs after `bump`.

Component contract for the per-app template constraint refresh introduced in RANCHER-2983. Bumps `application.template.json` dependency constraints that no longer semver-match the dependee's current snapshot major. Closes the manual gap RANCHER-2982 documented.

## Inputs

| Input | Type | Required | Notes |
|---|---|---|---|
| `app_name` | string | yes | Application name (e.g., `app-acquisitions`). Used for artifact names, App-token scoping, and logs. |
| `repo` | string | yes | Target repository in `org/repo` form (e.g., `folio-org/app-acquisitions`). |
| `target_branch` | string | no (default `snapshot`) | Branch whose `application.template.json` is refreshed. Default `snapshot` is correct for the standard post-release workflow. |
| `dry_run` | boolean | no (default `false`) | When true, preflight + stale detection + template rewrite run, but the commit job's push is skipped. |

## Per-App Sequence

1. **Mint App token** — `actions/create-github-app-token@v3` scoped to `repositories: ${{ inputs.app_name }}`. Least-privilege per matrix shard.
2. **Preflight** — confirms `<target_branch>` and `application.template.json` exist on the target repo. Fast-fails with `target_branch_missing` or `template_missing`.
3. **Fetch template** — `gh api repos/folio-org/<app>/contents/application.template.json?ref=<target_branch>` → base64-decode → write to a working directory. Validate with `jq -e '.dependencies'`. Fails with `template_parse_failed` if the file is malformed or lacks `.dependencies`.
4. **Detect stale constraints** — iterate `.dependencies[]`. For each entry:
   - Skip if the constraint doesn't match `^X.Y.Z[-SNAPSHOT[.N]]` (unrecognized form; log warning).
   - Fetch the dependee's `pom.xml` from `<target_branch>` via Contents API.
   - Parse the dependee's `<version>` (using the same `<parent>`-aware awk as `collect-app-version`).
   - Skip if the dependee's pom is unreadable or unparseable (log warning).
   - **Stale test**: constraint's major ≠ dep's current major → mark stale; new constraint = `^<dep-current-major>.<dep-current-minor>.0-SNAPSHOT` (narrow-minor).
5. **Idempotency gate** — if no entries are stale, the run resolves to `status=skipped`, `skipped_reason=no_stale_deps`, no commit.
6. **Rewrite template** — single `jq` pass applies all stale updates. Verifies a real diff was produced (defensive check; `template_edit_no_op` otherwise).
7. **Stage + upload artifact** — the modified `application.template.json` is uploaded as artifact `${app_name}-dependency-refresh-files`.
8. **Commit & push** — `commit-and-push-changes.yml@master` is called with `branch: <target_branch>`, `use_github_app: true`. The commit message lists each refreshed entry in the form `<dep>: <old> → <new>`.
9. **Result artifact** — `<app_name>-deprefresh.json` (artifact name `deprefresh-<app_name>`) emitted for orchestrator aggregation.

## Result Artifact

`deprefresh-<app_name>`:

```json
{
  "application": "app-bulk-edit",
  "phase": "deprefresh",
  "status": "success | skipped | failed",
  "target_branch": "snapshot",
  "refreshed_count": 1,
  "refreshed_constraints": [
    { "dep": "app-fqm", "old": "^1.2.0-SNAPSHOT", "new": "^2.1.0-SNAPSHOT" }
  ],
  "commit_sha": "abc1234",
  "failure_reason": "",
  "skipped_reason": "",
  "dry_run": false
}
```

Uploaded with `actions/upload-artifact@v4` and name `deprefresh-<app_name>`. The orchestrator's `collect-results` job downloads with `pattern: "deprefresh-*"`, `merge-multiple: true`. The artifact name space is intentionally distinct from the bump phase's `result-*` artifacts so both can coexist in `collect-results`.

## Refresh Policy

**Stale-only**. A constraint is touched only when its major no longer semver-matches the dependee's current snapshot major. Constraints that still match (within-major bumps to the dependee, or no change at all) are left untouched.

The new constraint uses **narrow-minor form**: `^<dep-current-major>.<dep-current-minor>.0-SNAPSHOT`. The `^` carat semver covers all of the dependee's current minor lineage and onwards within the same major, so re-running won't trigger another refresh until the dependee crosses major again.

## Failure Reason Codes

| Reason | Meaning | Remediation |
|---|---|---|
| `target_branch_missing` | `<target_branch>` doesn't exist on the target repo. | Confirm the post-release bump phase ran for this app, or drop the app from scope. |
| `template_missing` | `application.template.json` doesn't exist on `<target_branch>`. | Investigate the repo's state — every FOLIO app should carry this file. |
| `template_parse_failed` | The fetched `application.template.json` isn't valid JSON or lacks `.dependencies`. | Inspect the file on the target branch. |
| `dep_version_read_failed` | The detect-stale step failed entirely. Likely a token scope or rate-limit issue. | Check the step logs for the per-dep warnings. |
| `template_edit_no_op` | The `jq` rewrite produced no diff despite stale entries being detected. Defensive — shouldn't normally trigger. | Inspect the template structure; possible non-standard formatting. |
| `commit_failed` | `commit-and-push-changes.yml` failed to push. | Check the push step logs; verify the App is in the target branch's ruleset `bypass_actors`. |

## Skipped Reason Codes

| Reason | Meaning |
|---|---|
| `no_stale_deps` | Every dependency constraint already semver-matches the dependee's current major. No commit needed. |

## Authentication

- One GitHub App token is minted **per matrix shard**, scoped to a single target repository via `repositories: ${{ inputs.app_name }}`. Token leak in one shard's logs cannot compromise other repos.
- Auth requires `vars.EUREKA_CI_APP_ID` and `secrets.EUREKA_CI_APP_KEY`.
- For the push to succeed, the App identity must be in the target branch ruleset's `bypass_actors` (already configured by every app's `update-config.yml`).

## Out-of-Scope Behavior

- **Does not touch `<app_name>.template.json`** — only `application.template.json`. The two files coexist in each repo but the former is not maintained in lockstep; editing it creates noise.
- **Does not refresh module/UI module versions** — those are handled by `application-update-flow.yml` on a different cadence.
- **Does not narrow constraints that still semver-match** — locked stale-only policy. If a dependee bumped within-major (e.g., 2.1.0 → 2.2.0), a `^2.1.0-SNAPSHOT` or `^2.0.0-SNAPSHOT` constraint stays untouched.

## Related Workflows

- `post-release-bump-flow.yml` — the bump phase that runs immediately before this flow in the orchestrator. See [`post-release-bump-flow.md`](post-release-bump-flow.md).
- `commit-and-push-changes.yml` — reused for the commit step; see [`commit-and-push-changes.md`](commit-and-push-changes.md).
- `collect-app-version` action — the same `gh api + awk` read pattern is used inline here for each dependee; see [`actions/collect-app-version/README.md`](../actions/collect-app-version/README.md).
