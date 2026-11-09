# Trigger Jenkins Job

Triggers a parameterized Jenkins job, waits for the build to finish and reports its result. Used by the
platform-lsp merge-queue check to run the deployment gate configured in a branch's `deployment` block
(see [update-config.md](../../docs/update-config.md#deployment-configuration)).

## Usage

```yaml
- name: Deploy
  id: deploy
  uses: folio-org/kitfox-github/.github/actions/trigger-jenkins-job@master
  with:
    jenkins_url: ${{ vars.JENKINS_URL }}
    jenkins_user: ${{ secrets.JENKINS_USER }}
    jenkins_token: ${{ secrets.JENKINS_API_TOKEN }}
    job: folioScheduledProvisioning/createDailySnapshotEureka
    parameters: '{"PLATFORM_BRANCH": "gh-readonly-queue/snapshot/pr-42-0123abcd"}'
    timeout_minutes: 280
```

## Inputs

| Input                   | Required | Default | Description                                                                     |
|-------------------------|----------|---------|---------------------------------------------------------------------------------|
| `jenkins_url`           | Yes      | -       | Jenkins base URL                                                                |
| `jenkins_user`          | Yes      | -       | Jenkins user the API token belongs to                                           |
| `jenkins_token`         | Yes      | -       | Jenkins API token                                                               |
| `job`                   | Yes      | -       | Job path, folders separated by `/`                                              |
| `parameters`            | No       | `{}`    | JSON object of build parameters, sent as form fields to `buildWithParameters`   |
| `poll_interval_seconds` | No       | `60`    | Interval between status polls                                                   |
| `timeout_minutes`       | No       | `280`   | Minutes to wait for the build, Jenkins queue time included                      |

## Outputs

| Output           | Description                                                                           |
|------------------|---------------------------------------------------------------------------------------|
| `result`         | `success` or `failure`                                                                |
| `build_url`      | URL of the Jenkins build, empty if it never left the queue                            |
| `build_number`   | Jenkins build number, empty if it never left the queue                                |
| `jenkins_result` | Jenkins build result (`SUCCESS`, `FAILURE`, `ABORTED`, `UNSTABLE`, ...)               |
| `failure_reason` | Why the action failed, empty on success                                               |

The step fails whenever `result` is `failure`; the outputs written before the failure stay readable from
`steps.<id>.outputs`.

## Behaviour

1. `POST {job}/buildWithParameters` with the parameters as form fields. Jenkins answers `201` with the queue
   item in the `Location` header. The trigger is sent once and never retried, so a slow response cannot
   start a second build. When Jenkins rejects it, `failure_reason` carries the HTTP status and the cause from
   the response page, such as `is missing the Job/Build permission` or `No valid crumb was included in the
   request`.
2. The queue item is polled until Jenkins assigns a build. A job with concurrent builds disabled may wait
   here behind a running build; that time counts against `timeout_minutes`. A queue item cancelled in
   Jenkins fails the action.
3. The build is polled until it stops building. Only `SUCCESS` passes.
4. When `timeout_minutes` runs out the action stops the build (or cancels the queue item) and fails. The same
   happens when the step receives `SIGINT`/`SIGTERM`, for example on job cancellation.

Polls tolerate up to 10 consecutive errors before failing, so a Jenkins restart during a long build does not
fail the check on its own.

## Authentication

Basic authentication with a Jenkins API token, which needs no CSRF crumb. The credential is passed to `curl`
through a config file descriptor, never on the command line, so it does not appear in the process list or the
log. Grant the Jenkins user only the permissions to build and read the configured job.
