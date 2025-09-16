import json
import os
import boto3
import logging
import requests
from typing import Dict, Any, Optional
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.github_client import GitHubClient
from common.check_runner import CheckRunner

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Process check suite requests from SQS queue.

    Args:
        event: SQS event containing GitHub webhook data
        context: Lambda context object

    Returns:
        Response indicating processing status
    """
    logger.info(f"Processing SQS event: {json.dumps(event)}")

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

            # Initialize GitHub client
            github_client = GitHubClient()

            # Process check_suite events
            if event_type == 'check_suite':
                check_suite = payload.get('check_suite', {})
                repository = payload.get('repository', {})

                # Create check run
                check_runner = CheckRunner(github_client)
                check_run = check_runner.create_check_run(
                    owner=repository.get('owner', {}).get('login'),
                    repo=repository.get('name'),
                    check_suite_id=check_suite.get('id'),
                    head_sha=check_suite.get('head_sha')
                )

                if check_run:
                    logger.info(f"Created check run: {check_run.get('id')}")

                    # Run checks (placeholder for actual check logic)
                    result = check_runner.run_checks(
                        owner=repository.get('owner', {}).get('login'),
                        repo=repository.get('name'),
                        check_run_id=check_run.get('id')
                    )

                    logger.info(f"Check run completed with result: {result}")

            # Process pull_request events
            elif event_type == 'pull_request':
                pull_request = payload.get('pull_request', {})
                repository = payload.get('repository', {})

                # Create check run for PR
                check_runner = CheckRunner(github_client)
                check_run = check_runner.create_check_run(
                    owner=repository.get('owner', {}).get('login'),
                    repo=repository.get('name'),
                    head_sha=pull_request.get('head', {}).get('sha')
                )

                if check_run:
                    logger.info(f"Created check run for PR: {check_run.get('id')}")

                    # Run checks
                    result = check_runner.run_checks(
                        owner=repository.get('owner', {}).get('login'),
                        repo=repository.get('name'),
                        check_run_id=check_run.get('id')
                    )

                    logger.info(f"PR check run completed with result: {result}")

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