import json
import os
import boto3
import logging
from typing import Dict, Any

from utils.signature_validator import validate_github_signature

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sqs = boto3.client('sqs')
secrets_manager = boto3.client('secretsmanager')

SQS_QUEUE_URL = os.environ['SQS_QUEUE_URL']
WEBHOOK_SECRET_ARN = os.environ['WEBHOOK_SECRET_ARN']
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')


def get_webhook_secret() -> str:
    """Retrieve webhook secret from AWS Secrets Manager."""
    try:
        response = secrets_manager.get_secret_value(SecretId=WEBHOOK_SECRET_ARN)
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
        API Gateway response
    """
    try:
        logger.info(f"Received webhook event: {json.dumps(event.get('headers', {}))}")
        
        # Extract request details
        body = event.get('body', '')
        headers = event.get('headers', {})
        
        # Get GitHub event type
        github_event = headers.get('x-github-event', '')
        delivery_id = headers.get('x-github-delivery', '')
        
        logger.info(f"GitHub event: {github_event}, Delivery ID: {delivery_id}")
        
        # Validate webhook signature
        signature = headers.get('x-hub-signature-256', '')
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
        
        # Parse webhook payload
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
                    'environment': ENVIRONMENT
                }
                
                sqs.send_message(
                    QueueUrl=SQS_QUEUE_URL,
                    MessageBody=json.dumps(message),
                    MessageAttributes={
                        'event_type': {'DataType': 'String', 'StringValue': github_event},
                        'action': {'DataType': 'String', 'StringValue': action},
                        'delivery_id': {'DataType': 'String', 'StringValue': delivery_id}
                    }
                )
                
                logger.info(f"Queued check_suite event for processing: {delivery_id}")
        
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