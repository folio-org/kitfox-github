import hmac
import hashlib
import logging

logger = logging.getLogger(__name__)


def validate_github_signature(payload: str, signature: str, secret: str) -> bool:
    """
    Validate GitHub webhook signature.
    
    Args:
        payload: Request body as string
        signature: GitHub signature header value (sha256=...)
        secret: Webhook secret
        
    Returns:
        True if signature is valid, False otherwise
    """
    if not signature or not signature.startswith('sha256='):
        logger.error("Invalid signature format")
        return False
    
    # Extract the signature hash
    signature_hash = signature[7:]  # Remove 'sha256=' prefix
    
    # Compute expected signature
    if isinstance(payload, str):
        payload = payload.encode('utf-8')
    if isinstance(secret, str):
        secret = secret.encode('utf-8')
    
    expected_signature = hmac.new(
        secret,
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures using constant-time comparison
    is_valid = hmac.compare_digest(expected_signature, signature_hash)
    
    if not is_valid:
        logger.warning("Signature validation failed")
    
    return is_valid