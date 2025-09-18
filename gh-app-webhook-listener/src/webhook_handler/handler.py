import json
import os
import boto3
import logging
from typing import Dict, Any
import hmac
import hashlib

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def validate_github_signature(payload: str, signature: str, secret: str) -> bool:
    """
    Validate signature.

    Args:
        payload: The raw payload
        signature: The signature
        secret: The secret

    Returns:
        True if the signature is valid, False otherwise
    """
    if not signature or not secret:
        logger.warning("Missing signature or secret")
        return False

    # The signature is sent with the 'sha256=' prefix
    if not signature.startswith('sha256='):
        logger.warning("Invalid signature format")
        return False

    is_valid = hmac.compare_digest(generate_signature(payload, secret), signature)

    if not is_valid:
        logger.warning("Signature validation failed")

    return is_valid


def generate_signature(payload: str, secret: str) -> str:
    """
    Generate a signature.

    Args:
        payload: The payload to sign
        secret: The secret

    Returns:
        The signature in format (sha256=...)
    """
    signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8') if isinstance(payload, str) else payload,
        hashlib.sha256
    ).hexdigest()

    return f"sha256={signature}"


def get_webhook_secret() -> str:
    """Retrieve webhook secret from AWS Secrets Manager."""
    try:
        secrets_manager = boto3.client('secretsmanager')
        response = secrets_manager.get_secret_value(SecretId=os.environ['WEBHOOK_SECRET_ARN'])
        return response['SecretString']
    except Exception as e:
        logger.error(f"Failed to retrieve webhook secret: {e}")
        raise


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle incoming GitHub webhooks.

    Args:
        event: API Gateway event containing webhook data
        context: Lambda context object

    Returns:
        API Gateway response object
    """
    try:
        # Log incoming event
        logger.info(f"Received webhook event: {json.dumps(event)}")
        logger.info(f"Received webhook event headers: {json.dumps(event.get('headers', {}))}")

        # Extract request details
        body = event.get('body', '')
        headers = event.get('headers', {})

        # Convert headers to lowercase for consistent access (API Gateway sometimes sends mixed case)
        headers_lower = {k.lower(): v for k, v in headers.items()}

        # Get GitHub event type
        github_event = headers_lower.get('x-github-event', '')
        delivery_id = headers_lower.get('x-github-delivery', '')

        logger.info(f"GitHub event: {github_event}, Delivery ID: {delivery_id}")

        # Validate webhook signature
        signature = headers_lower.get('x-hub-signature-256', '')
        if not signature:
            logger.error("Missing GitHub signature header")
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Missing signature'})
            }

        webhook_secret = get_webhook_secret()
        if not validate_github_signature(body, signature, webhook_secret):
            logger.error("Invalid GitHub signature")
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Invalid signature'})
            }

        try:
            payload = json.loads(body) if isinstance(body, str) else body
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse webhook payload: {e}")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid JSON payload'})
            }

        # Process check_suite events
        if github_event == 'check_suite':
            action = payload.get('action', '')
            logger.info(f"Processing check_suite action: {action}")

            if action in ['requested', 'rerequested']:
                # Send to SQS for async processing
                message = {
                    'event_type': github_event,
                    'action': action,
                    'delivery_id': delivery_id,
                    'payload': payload,
                    'environment': os.environ.get('ENVIRONMENT', 'dev')
                }

                sqs = boto3.client('sqs')
                sqs.send_message(
                    QueueUrl=os.environ['SQS_QUEUE_URL'],
                    MessageBody=json.dumps(message),
                    MessageAttributes={
                        'event_type': {'DataType': 'String', 'StringValue': github_event},
                        'action': {'DataType': 'String', 'StringValue': action},
                        'delivery_id': {'DataType': 'String', 'StringValue': delivery_id or ''}
                    }
                )

                logger.info(f"Queued check_suite event for processing: {delivery_id}")

        # Process pull_request events
        elif github_event == 'pull_request':
            action = payload.get('action', '')
            logger.info(f"Processing pull_request action: {action}")

            if action in ['opened', 'synchronize', 'reopened']:
                # Send to SQS for async processing
                message = {
                    'event_type': github_event,
                    'action': action,
                    'delivery_id': delivery_id,
                    'payload': payload,
                    'environment': os.environ.get('ENVIRONMENT', 'dev')
                }

                sqs = boto3.client('sqs')
                sqs.send_message(
                    QueueUrl=os.environ['SQS_QUEUE_URL'],
                    MessageBody=json.dumps(message),
                    MessageAttributes={
                        'event_type': {'DataType': 'String', 'StringValue': github_event},
                        'action': {'DataType': 'String', 'StringValue': action},
                        'delivery_id': {'DataType': 'String', 'StringValue': delivery_id or ''}
                    }
                )

                logger.info(f"Queued pull_request event for processing: {delivery_id}")

        # Return success immediately
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Webhook received',
                'delivery_id': delivery_id
            })
        }

    except Exception as e:
        logger.error(f"Unexpected error processing webhook: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }