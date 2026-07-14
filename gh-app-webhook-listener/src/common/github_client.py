import os
import time
import logging
import requests
import jwt
import boto3
from typing import Dict, Any, Optional

logger = logging.getLogger()

# Transient GitHub failures worth retrying. The workflow_dispatch endpoint
# intermittently returns 500 "Failed to run workflow dispatch"; without a retry
# such a response was previously swallowed and the dispatch lost.
RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})
MAX_REQUEST_ATTEMPTS = 3
RETRY_BASE_DELAY_SECONDS = 1.0


class GitHubClient:
    """Client for interacting with GitHub API as a GitHub App."""

    def __init__(self):
        self.app_id = os.environ.get('GITHUB_APP_ID')
        self.installation_id = os.environ.get('GITHUB_INSTALLATION_ID')
        self.private_key = self._get_private_key()
        self.base_url = "https://api.github.com"

    def _get_private_key(self) -> str:
        """Retrieve GitHub App private key from Secrets Manager."""
        try:
            secrets_manager = boto3.client('secretsmanager')
            response = secrets_manager.get_secret_value(
                SecretId=os.environ['GITHUB_PRIVATE_KEY_ARN']
            )
            return response['SecretString']
        except Exception as e:
            logger.error(f"Failed to retrieve GitHub App private key: {e}")
            raise

    def _create_jwt(self) -> str:
        """Create a JWT for GitHub App authentication."""
        now = int(time.time())
        payload = {
            'iat': now - 60,  # Issued at time (60 seconds in the past)
            'exp': now + (10 * 60),  # JWT expiration time (10 minutes maximum)
            'iss': self.app_id  # GitHub App ID
        }

        return jwt.encode(payload, self.private_key, algorithm='RS256')

    def _get_installation_token(self) -> str:
        """Get an installation access token."""
        jwt_token = self._create_jwt()
        if not jwt_token:
            raise ValueError("Failed to create JWT token")

        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        url = f"{self.base_url}/app/installations/{self.installation_id}/access_tokens"

        try:
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            return response.json()['token']
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get installation token: {e}")
            raise

    @staticmethod
    def _retry_delay(response, attempt: int) -> float:
        """Delay before the next retry: honor Retry-After, else exponential backoff."""
        retry_after = response.headers.get('Retry-After')
        if retry_after:
            try:
                return float(retry_after)
            except (TypeError, ValueError):
                pass
        return RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 1))

    def make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an authenticated request to GitHub API.

        Transient failures (HTTP 429/5xx and connection/timeout errors) are retried
        with exponential backoff. Other 4xx errors raise immediately (no retry).
        """
        token = self._get_installation_token()

        headers = kwargs.pop('headers', {})
        headers.update({
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        })

        # Ensure proper URL construction with slash
        if not endpoint.startswith('/'):
            endpoint = f'/{endpoint}'
        url = f"{self.base_url}{endpoint}"

        for attempt in range(1, MAX_REQUEST_ATTEMPTS + 1):
            try:
                response = requests.request(method, url, headers=headers, **kwargs)

                if (response.status_code in RETRYABLE_STATUS_CODES
                        and attempt < MAX_REQUEST_ATTEMPTS):
                    delay = self._retry_delay(response, attempt)
                    logger.warning(
                        f"GitHub API {method} {endpoint} returned {response.status_code}; "
                        f"retry {attempt}/{MAX_REQUEST_ATTEMPTS - 1} in {delay:.1f}s"
                    )
                    time.sleep(delay)
                    continue

                response.raise_for_status()
                return response.json() if response.text else {}

            except (requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout) as e:
                if attempt < MAX_REQUEST_ATTEMPTS:
                    delay = RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 1))
                    logger.warning(
                        f"GitHub API {method} {endpoint} connection error ({e}); "
                        f"retry {attempt}/{MAX_REQUEST_ATTEMPTS - 1} in {delay:.1f}s"
                    )
                    time.sleep(delay)
                    continue
                logger.error(f"GitHub API request failed: {e}")
                raise
            except requests.exceptions.RequestException as e:
                logger.error(f"GitHub API request failed: {e}")
                raise

        # Unreachable: the final attempt always returns or raises above.
        raise RuntimeError("make_request exhausted retries without returning")