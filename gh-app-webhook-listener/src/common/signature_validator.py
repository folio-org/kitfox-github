import hmac
import hashlib
import logging

logger = logging.getLogger()


def validate_github_signature(payload: str, signature: str, secret: str) -> bool:
    """
    Validate GitHub webhook signature.

    Args:
        payload: The raw webhook payload
        signature: The signature from GitHub (x-hub-signature-256 header)
        secret: The webhook secret

    Returns:
        True if signature is valid, False otherwise
    """
    if not signature or not secret:
        logger.warning("Missing signature or secret")
        return False

    # GitHub sends the signature with 'sha256=' prefix
    if not signature.startswith('sha256='):
        logger.warning("Invalid signature format")
        return False

    # Remove the 'sha256=' prefix
    github_signature = signature[7:]

    # Calculate expected signature
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8') if isinstance(payload, str) else payload,
        hashlib.sha256
    ).hexdigest()

    # Use constant-time comparison to prevent timing attacks
    is_valid = hmac.compare_digest(expected_signature, github_signature)

    if not is_valid:
        logger.warning("Signature validation failed")

    return is_valid


def generate_signature(payload: str, secret: str) -> str:
    """
    Generate a GitHub-style webhook signature.

    Args:
        payload: The payload to sign
        secret: The webhook secret

    Returns:
        The signature in GitHub format (sha256=...)
    """
    signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8') if isinstance(payload, str) else payload,
        hashlib.sha256
    ).hexdigest()

    return f"sha256={signature}"