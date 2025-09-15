import json
import os
import logging
from typing import Dict, Any, List
from datetime import datetime
import boto3

from services.github_api import GitHubAPI
from services.config_loader import ConfigLoader
from services.workflow_orchestrator import WorkflowOrchestrator
from services.pr_validator import PRValidator

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Process check suite events from SQS queue.

    Args:
        event: SQS event containing GitHub webhook data
        context: Lambda context object

    Returns:
        Processing result
    """
    try:
        # Process each record from SQS
        for record in event.get('Records', []):
            process_sqs_record(record)

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Processing complete'})
        }

    except Exception as e:
        logger.error(f"Error processing check suite event: {str(e)}", exc_info=True)
        raise


def process_sqs_record(record: Dict[str, Any]) -> None:
    """Process a single SQS record containing a GitHub event."""
    try:
        # Parse the message body
        message = json.loads(record['body'])
        event_type = message.get('event_type')
        action = message.get('action')
        payload = message.get('payload', {})

        logger.info(f"Processing {event_type} event with action: {action}")

        # Initialize services
        github_api = GitHubAPI(
            app_id=os.environ['GITHUB_APP_ID'],
            installation_id=payload.get('installation', {}).get('id')
        )

        config_loader = ConfigLoader()
        workflow_orchestrator = WorkflowOrchestrator(github_api, config_loader)

        # Handle check_suite events
        if event_type == 'check_suite':
            handle_check_suite(payload, github_api, workflow_orchestrator)

        # Handle pull_request events
        elif event_type == 'pull_request':
            handle_pull_request(payload, github_api, workflow_orchestrator)

    except Exception as e:
        logger.error(f"Error processing SQS record: {str(e)}", exc_info=True)
        raise


def handle_check_suite(
    payload: Dict[str, Any],
    github_api: GitHubAPI,
    workflow_orchestrator: WorkflowOrchestrator
) -> None:
    """Handle check suite events."""
    try:
        check_suite = payload.get('check_suite', {})
        repository = payload.get('repository', {})

        logger.info(f"Processing check suite {check_suite.get('id')} for repository {repository.get('full_name')}")

        # Get pull requests associated with this check suite
        pull_requests = check_suite.get('pull_requests', [])

        if not pull_requests:
            logger.info("No pull requests associated with this check suite")
            # Create a check run for branch validation if needed
            create_branch_check(github_api, repository, check_suite)
            return

        # Process each associated pull request
        for pr in pull_requests:
            process_pull_request_checks(
                github_api,
                workflow_orchestrator,
                repository,
                pr,
                check_suite
            )

    except Exception as e:
        logger.error(f"Error handling check suite: {str(e)}", exc_info=True)
        raise


def handle_pull_request(
    payload: Dict[str, Any],
    github_api: GitHubAPI,
    workflow_orchestrator: WorkflowOrchestrator
) -> None:
    """Handle pull request events."""
    try:
        pull_request = payload.get('pull_request', {})
        repository = payload.get('repository', {})

        logger.info(f"Processing pull request #{pull_request.get('number')} for repository {repository.get('full_name')}")

        # Validate PR and trigger checks
        pr_validator = PRValidator(github_api)
        validation_result = pr_validator.validate_pull_request(repository, pull_request)

        if validation_result.get('valid'):
            # Trigger workflows based on PR changes
            workflow_orchestrator.trigger_workflows(repository, pull_request)
        else:
            # Create a check run with validation errors
            create_validation_check(
                github_api,
                repository,
                pull_request,
                validation_result
            )

    except Exception as e:
        logger.error(f"Error handling pull request: {str(e)}", exc_info=True)
        raise


def process_pull_request_checks(
    github_api: GitHubAPI,
    workflow_orchestrator: WorkflowOrchestrator,
    repository: Dict[str, Any],
    pull_request: Dict[str, Any],
    check_suite: Dict[str, Any]
) -> None:
    """Process checks for a pull request."""
    try:
        # Create initial check run
        check_run = github_api.create_check_run(
            owner=repository['owner']['login'],
            repo=repository['name'],
            name="Eureka CI Checks",
            head_sha=check_suite['head_sha'],
            status="in_progress",
            started_at=datetime.utcnow().isoformat() + 'Z',
            output={
                "title": "Running Eureka CI Checks",
                "summary": "Validating pull request and triggering workflows..."
            }
        )

        check_run_id = check_run['id']

        # Validate the pull request
        pr_validator = PRValidator(github_api)
        pr_details = github_api.get_pull_request(
            owner=repository['owner']['login'],
            repo=repository['name'],
            pr_number=pull_request['number']
        )

        validation_result = pr_validator.validate_pull_request(repository, pr_details)

        if not validation_result.get('valid'):
            # Update check run with validation failures
            github_api.update_check_run(
                owner=repository['owner']['login'],
                repo=repository['name'],
                check_run_id=check_run_id,
                status="completed",
                conclusion="failure",
                completed_at=datetime.utcnow().isoformat() + 'Z',
                output={
                    "title": "Validation Failed",
                    "summary": validation_result.get('message', 'Pull request validation failed'),
                    "text": format_validation_errors(validation_result.get('errors', []))
                }
            )
            return

        # Trigger workflows
        triggered_workflows = workflow_orchestrator.trigger_workflows(repository, pr_details)

        # Update check run with success
        github_api.update_check_run(
            owner=repository['owner']['login'],
            repo=repository['name'],
            check_run_id=check_run_id,
            status="completed",
            conclusion="success",
            completed_at=datetime.utcnow().isoformat() + 'Z',
            output={
                "title": "Checks Passed",
                "summary": f"Successfully triggered {len(triggered_workflows)} workflow(s)",
                "text": format_triggered_workflows(triggered_workflows)
            }
        )

    except Exception as e:
        logger.error(f"Error processing pull request checks: {str(e)}", exc_info=True)

        # Update check run with error
        try:
            github_api.update_check_run(
                owner=repository['owner']['login'],
                repo=repository['name'],
                check_run_id=check_run_id,
                status="completed",
                conclusion="failure",
                completed_at=datetime.utcnow().isoformat() + 'Z',
                output={
                    "title": "Check Processing Failed",
                    "summary": "An error occurred while processing checks",
                    "text": str(e)
                }
            )
        except:
            pass

        raise


def create_branch_check(
    github_api: GitHubAPI,
    repository: Dict[str, Any],
    check_suite: Dict[str, Any]
) -> None:
    """Create a check run for branch validation."""
    try:
        github_api.create_check_run(
            owner=repository['owner']['login'],
            repo=repository['name'],
            name="Branch Validation",
            head_sha=check_suite['head_sha'],
            status="completed",
            conclusion="success",
            completed_at=datetime.utcnow().isoformat() + 'Z',
            output={
                "title": "Branch Validated",
                "summary": f"Branch {check_suite.get('head_branch', 'unknown')} is valid"
            }
        )
    except Exception as e:
        logger.error(f"Error creating branch check: {str(e)}")


def create_validation_check(
    github_api: GitHubAPI,
    repository: Dict[str, Any],
    pull_request: Dict[str, Any],
    validation_result: Dict[str, Any]
) -> None:
    """Create a check run for validation results."""
    try:
        github_api.create_check_run(
            owner=repository['owner']['login'],
            repo=repository['name'],
            name="PR Validation",
            head_sha=pull_request['head']['sha'],
            status="completed",
            conclusion="failure",
            completed_at=datetime.utcnow().isoformat() + 'Z',
            output={
                "title": "Validation Failed",
                "summary": validation_result.get('message', 'Pull request validation failed'),
                "text": format_validation_errors(validation_result.get('errors', []))
            }
        )
    except Exception as e:
        logger.error(f"Error creating validation check: {str(e)}")


def format_validation_errors(errors: List[str]) -> str:
    """Format validation errors for check run output."""
    if not errors:
        return "No specific errors provided"

    formatted = "### Validation Errors\n\n"
    for error in errors:
        formatted += f"- ❌ {error}\n"

    return formatted


def format_triggered_workflows(workflows: List[Dict[str, Any]]) -> str:
    """Format triggered workflows for check run output."""
    if not workflows:
        return "No workflows were triggered"

    formatted = "### Triggered Workflows\n\n"
    for workflow in workflows:
        formatted += f"- ✅ {workflow.get('name', 'Unknown workflow')}\n"
        if workflow.get('run_url'):
            formatted += f"  - [View Run]({workflow['run_url']})\n"

    return formatted