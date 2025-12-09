import json
import os
import boto3
import logging
import fnmatch
from typing import Dict, Any, Optional, List
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.github_client import GitHubClient
from common.workflow_trigger import WorkflowTrigger

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')

def load_config(bucket_name: str, config_key: str) -> Dict[str, Any]:
    """Load configuration from S3 bucket or local file"""
    try:
        if bucket_name and config_key:
            response = s3.get_object(Bucket=bucket_name, Key=config_key)
            config_content = response['Body'].read().decode('utf-8')
            return json.loads(config_content)
    except Exception as e:
        logger.warning(f"Failed to load config from S3: {e}")

    # Fallback to local config file
    local_config_path = os.environ.get('LOCAL_CONFIG_PATH', '/var/task/config/github_events_config.json')
    if os.path.exists(local_config_path):
        with open(local_config_path, 'r') as f:
            return json.load(f)

    logger.error("No configuration file found")
    return {}

def matches_pattern(value: str, pattern: str) -> bool:
    """Check if value matches the given pattern (supports wildcards)"""
    return fnmatch.fnmatch(value, pattern)

def matches_branch(branch: str, branch_patterns: Any) -> bool:
    """Check if branch matches the configured patterns"""
    if branch_patterns == "*":
        return True

    if isinstance(branch_patterns, list):
        return any(matches_pattern(branch, pattern) for pattern in branch_patterns)

    if isinstance(branch_patterns, dict):
        # Handle base/head branch patterns for PRs
        return True  # Will be handled by specific event processors

    return matches_pattern(branch, str(branch_patterns))

def find_matching_workflows(event_type: str, action: str, repository: Dict[str, str],
                           branch_info: Dict[str, str], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Find workflows that match the event criteria"""
    matching_workflows = []

    for mapping in config.get('event_mappings', []):
        # Check event type
        if mapping.get('event_type') != event_type:
            continue

        # Check action (if specified)
        if 'actions' in mapping and action not in mapping.get('actions', []):
            continue

        # Check repository patterns
        for repo_pattern in mapping.get('repository_patterns', []):
            owner_pattern = repo_pattern.get('owner', '*')
            repo_name_pattern = repo_pattern.get('repository', '*')

            if not matches_pattern(repository.get('owner'), owner_pattern):
                continue

            if not matches_pattern(repository.get('name'), repo_name_pattern):
                continue

            # Check branch patterns
            branch_patterns = repo_pattern.get('branches', '*')
            branch_matched = False

            if event_type == 'check_suite':
                # For check_suite, we check against head branch
                head_branch = branch_info.get('head_branch', '')
                branch_matched = matches_branch(head_branch, branch_patterns)
            elif event_type == 'pull_request':
                # For PRs, check both base and head branches
                if isinstance(branch_patterns, dict):
                    base_patterns = branch_patterns.get('base', ['*'])
                    head_patterns = branch_patterns.get('head', ['*'])
                    base_branch = branch_info.get('base_branch', '')
                    head_branch = branch_info.get('head_branch', '')
                    branch_matched = (
                        any(matches_pattern(base_branch, p) for p in base_patterns) and
                        any(matches_pattern(head_branch, p) for p in head_patterns)
                    )
                else:
                    branch_matched = True
            else:
                branch_matched = True

            if branch_matched:
                matching_workflows.extend(repo_pattern.get('workflows', []))

    return matching_workflows

def substitute_template_variables(value: Any, variables: Dict[str, str]) -> Any:
    """Substitute template variables in configuration values"""
    if isinstance(value, str):
        for var_name, var_value in variables.items():
            value = value.replace(f"{{{var_name}}}", var_value)
        return value
    elif isinstance(value, dict):
        return {k: substitute_template_variables(v, variables) for k, v in value.items()}
    elif isinstance(value, list):
        return [substitute_template_variables(item, variables) for item in value]
    return value

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Process check suite requests from SQS queue and trigger workflows.

    Args:
        event: SQS event containing GitHub webhook data
        context: Lambda context object

    Returns:
        Response indicating processing status
    """
    logger.info(f"Processing SQS event: {json.dumps(event)}")

    config_bucket = os.environ.get('CONFIG_BUCKET_NAME')
    config_key = os.environ.get('CONFIG_FILE_KEY', 'github_events_config.json')
    config = load_config(config_bucket, config_key)

    if not config:
        logger.error("No configuration loaded, skipping processing")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Configuration not found'})
        }

    processed_count = 0
    error_count = 0

    for record in event.get('Records', []):
        try:
            # Parse SQS message
            message = json.loads(record['body'])
            event_type = message.get('event_type')
            action = message.get('action')
            delivery_id = message.get('delivery_id')
            payload = message.get('payload')

            logger.info(f"Processing {event_type} event (action: {action}, delivery: {delivery_id})")

            github_client = GitHubClient()
            workflow_trigger = WorkflowTrigger(github_client)

            repository = payload.get('repository', {})
            repo_info = {
                'owner': repository.get('owner', {}).get('login'),
                'name': repository.get('name')
            }

            event_object = payload.get(event_type, {})

            head_branch = (
                event_object.get('head_branch', '') or  # check_suite events
                event_object.get('head', {}).get('ref', '')  # pull_request events
            )

            base_branch = (
                event_object.get('base_branch', '') or  # if it exists in some events
                event_object.get('base', {}).get('ref', '')  # pull_request events
            )

            branch_info = {
                'head_branch': head_branch,
                'base_branch': base_branch
            }

            workflows = find_matching_workflows(
                event_type, action, repo_info, branch_info, config
            )

            if not workflows:
                logger.info(f"No matching workflows found for {repo_info['owner']}/{repo_info['name']}")
                processed_count += 1
                continue

            pr_number = '0'
            base_branch = ''
            base_sha = ''

            merged = 'false'
            if event_type == 'pull_request':
                pr_number = str(event_object.get('number', '0'))
                base_branch = event_object.get('base', {}).get('ref', '')
                base_sha = event_object.get('base', {}).get('sha', '')
                merged = str(event_object.get('merged', False)).lower()
            elif event_type in ['check_suite', 'check_run']:
                # For check_suite and check_run events, look in the pull_requests array
                pull_requests = event_object.get('pull_requests', [])
                if pull_requests:
                    pr_number = str(pull_requests[0].get('number', ''))
                    base_branch = pull_requests[0].get('base', {}).get('ref', '')
                    base_sha = pull_requests[0].get('base', {}).get('sha', '')
                else:
                    pr_number = '0'

            if event_type == 'pull_request':
                head_sha = event_object.get('head', {}).get('sha', '')
                head_branch = event_object.get('head', {}).get('ref', '')
            else:
                head_sha = event_object.get('head_sha', '')
                head_branch = event_object.get('head_branch', '')

            template_vars = {
                'owner': repo_info['owner'],
                'repository': repo_info['name'],
                'head_sha': head_sha,
                'head_branch': head_branch,
                'base_branch': base_branch,
                'base_sha': base_sha,
                'check_suite_id': str(event_object.get('id', '')),
                'pr_number': pr_number,
                'merged': merged,
            }

            for workflow_config in workflows:
                try:
                    workflow_config = substitute_template_variables(workflow_config, template_vars)

                    logger.info(f"Triggering workflow: {workflow_config}")

                    result = workflow_trigger.trigger_workflow(
                        owner=workflow_config.get('owner'),
                        repo=workflow_config.get('repository'),
                        workflow_file=workflow_config.get('workflow_file'),
                        ref=workflow_config.get('ref', 'main'),
                        inputs=workflow_config.get('inputs', {})
                    )

                    if result:
                        logger.info(f"Successfully triggered workflow: {workflow_config.get('workflow_file')}")
                    else:
                        logger.error(f"Failed to trigger workflow: {workflow_config.get('workflow_file')}")

                except Exception as e:
                    logger.error(f"Error triggering workflow: {e}", exc_info=True)

            processed_count += 1

        except Exception as e:
            logger.error(f"Error processing record: {e}", exc_info=True)
            error_count += 1

    return {
        'statusCode': 200,
        'body': json.dumps({
            'processed': processed_count,
            'errors': error_count
        })
    }