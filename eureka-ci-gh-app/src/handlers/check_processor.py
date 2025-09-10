import json
import os
import boto3
import logging
from typing import Dict, Any, Optional

from services.github_api import GitHubAPI
from services.workflow_orchestrator import WorkflowOrchestrator

logger = logging.getLogger()
logger.setLevel(logging.INFO)

secrets_manager = boto3.client('secretsmanager')
s3 = boto3.client('s3')

GITHUB_APP_ID = os.environ['GITHUB_APP_ID']
GITHUB_KEY_ARN = os.environ['GITHUB_KEY_ARN']
CONFIG_BUCKET = os.environ['CONFIG_BUCKET']
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')


def get_github_app_key() -> str:
    """Retrieve GitHub App private key from AWS Secrets Manager."""
    try:
        response = secrets_manager.get_secret_value(SecretId=GITHUB_KEY_ARN)
        return response['SecretString']
    except Exception as e:
        logger.error(f"Failed to retrieve GitHub App private key: {e}")
        raise


def get_workflow_config() -> Dict[str, Any]:
    """Load workflow configuration from S3."""
    try:
        response = s3.get_object(
            Bucket=CONFIG_BUCKET,
            Key='config/workflows.json'
        )
        content = response['Body'].read().decode('utf-8')
        return json.loads(content)
    except Exception as e:
        logger.error(f"Failed to load workflow config: {e}")
        # Return default config if S3 fails
        return {
            "check_suite_workflow": ".github/workflows/eureka-ci-check.yml",
            "kitfox_repo": "folio-org/kitfox-github"
        }


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Process check_suite events from SQS queue.
    
    Args:
        event: SQS event containing one or more messages
        context: Lambda context object
        
    Returns:
        Response indicating processing status
    """
    try:
        # Initialize services
        app_key = get_github_app_key()
        github = GitHubAPI(app_id=GITHUB_APP_ID, private_key=app_key)
        workflow_config = get_workflow_config()
        orchestrator = WorkflowOrchestrator(github, workflow_config)
        
        # Process each message from SQS
        for record in event.get('Records', []):
            try:
                message = json.loads(record['body'])
                logger.info(f"Processing message: {message.get('delivery_id')}")
                
                process_check_suite(orchestrator, message)
                
            except Exception as e:
                logger.error(f"Failed to process message: {e}", exc_info=True)
                # Re-raise to trigger retry via SQS
                raise
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Processing complete'})
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in check processor: {e}", exc_info=True)
        raise


def process_check_suite(
    orchestrator: WorkflowOrchestrator,
    message: Dict[str, Any]
) -> None:
    """
    Process a single check_suite event.
    
    Args:
        orchestrator: Workflow orchestrator instance
        message: Check suite message from SQS
    """
    payload = message.get('payload', {})
    check_suite = payload.get('check_suite', {})
    repository = payload.get('repository', {})
    installation = payload.get('installation', {})
    pull_requests = check_suite.get('pull_requests', [])
    
    repo_full_name = repository.get('full_name', '')
    repo_name = repository.get('name', '')
    check_suite_id = check_suite.get('id')
    head_sha = check_suite.get('head_sha')
    head_branch = check_suite.get('head_branch')
    
    logger.info(f"Processing check_suite {check_suite_id} for {repo_full_name} on branch {head_branch}")
    
    # Get installation access token
    installation_id = installation.get('id')
    access_token = orchestrator.github.get_installation_token(installation_id)
    
    # If no PRs associated, skip processing
    if not pull_requests:
        logger.info(f"No pull requests associated with check_suite {check_suite_id}")
        return
    
    # Process each associated PR
    for pr_info in pull_requests:
        pr_number = pr_info.get('number')
        
        logger.info(f"Processing PR #{pr_number} for check_suite {check_suite_id}")
        
        # Create initial check run
        check_run = orchestrator.github.create_check_run(
            access_token=access_token,
            repo_full_name=repo_full_name,
            name="Eureka CI Release Check",
            head_sha=head_sha,
            status='queued',
            details_url=f"https://github.com/{repo_full_name}/pull/{pr_number}/checks"
        )
        
        check_run_id = check_run.get('id')
        
        try:
            # Trigger the workflow in kitfox-github repository
            workflow_run_id = orchestrator.trigger_check_workflow(
                access_token=access_token,
                target_repo=repo_full_name,
                pr_number=pr_number,
                check_suite_id=check_suite_id,
                check_run_id=check_run_id,
                head_sha=head_sha,
                head_branch=head_branch
            )
            
            if workflow_run_id:
                # Update check run to in_progress
                orchestrator.github.update_check_run(
                    access_token=access_token,
                    repo_full_name=repo_full_name,
                    check_run_id=check_run_id,
                    status='in_progress',
                    started_at=orchestrator.github.get_current_time(),
                    details_url=f"https://github.com/{orchestrator.config['kitfox_repo']}/actions/runs/{workflow_run_id}"
                )
                
                # Monitor workflow execution (async - could be done via webhook or polling)
                # For now, we'll let the workflow update the check run directly via GitHub API
                logger.info(f"Triggered workflow run {workflow_run_id} for PR #{pr_number}")
            else:
                # Failed to trigger workflow
                orchestrator.github.update_check_run(
                    access_token=access_token,
                    repo_full_name=repo_full_name,
                    check_run_id=check_run_id,
                    status='completed',
                    conclusion='failure',
                    output={
                        'title': 'Failed to trigger check workflow',
                        'summary': 'Unable to start the Eureka CI check workflow',
                        'text': 'Please check the GitHub App configuration and permissions'
                    }
                )
                
        except Exception as e:
            logger.error(f"Error processing PR #{pr_number}: {e}", exc_info=True)
            
            # Update check run with error
            orchestrator.github.update_check_run(
                access_token=access_token,
                repo_full_name=repo_full_name,
                check_run_id=check_run_id,
                status='completed',
                conclusion='failure',
                output={
                    'title': 'Check Processing Error',
                    'summary': 'An unexpected error occurred while processing the check',
                    'text': str(e)
                }
            )