import os
import boto3


def read_credential(arn_env: str, ssm_env: str) -> str:
    """Return a credential from SSM Parameter Store if <ssm_env> is set, else from Secrets Manager (<arn_env>)."""
    parameter = os.environ.get(ssm_env)
    if parameter:
        return boto3.client('ssm').get_parameter(Name=parameter, WithDecryption=True)['Parameter']['Value']
    return boto3.client('secretsmanager').get_secret_value(SecretId=os.environ[arn_env])['SecretString']
