import os
import jwt
import time
import requests
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class GitHubAPI:
    """GitHub API client with GitHub App authentication."""

    def __init__(self, app_id: str, installation_id: Optional[int] = None):
        """
        Initialize GitHub API client.

        Args:
            app_id: GitHub App ID
            installation_id: Installation ID for the app
        """
        self.app_id = app_id
        self.installation_id = installation_id
        self.base_url = "https://api.github.com"
        self._token = None
        self._token_expires_at = None

    def get_private_key(self) -> str:
        """Get GitHub App private key from AWS Secrets Manager."""
        try:
            secrets_manager = boto3.client('secretsmanager')
            response = secrets_manager.get_secret_value(SecretId=os.environ['GITHUB_PRIVATE_KEY_ARN'])
            return response['SecretString']
        except Exception as e:
            logger.error(f"Failed to retrieve private key: {e}")
            raise

    def generate_jwt(self) -> str:
        """Generate a JWT for GitHub App authentication."""
        private_key = self.get_private_key()

        # JWT expires in 10 minutes (maximum allowed by GitHub)
        now = int(time.time())
        expiration = now + (10 * 60)

        payload = {
            'iat': now,
            'exp': expiration,
            'iss': self.app_id
        }

        return jwt.encode(payload, private_key, algorithm='RS256')

    def get_installation_token(self) -> str:
        """Get or refresh installation access token."""
        # Check if token is still valid
        if self._token and self._token_expires_at and datetime.utcnow() < self._token_expires_at:
            return self._token

        # Generate new installation token
        app_jwt = self.generate_jwt()

        headers = {
            'Authorization': f'Bearer {app_jwt}',
            'Accept': 'application/vnd.github.v3+json'
        }

        response = requests.post(
            f"{self.base_url}/app/installations/{self.installation_id}/access_tokens",
            headers=headers
        )

        if response.status_code != 201:
            logger.error(f"Failed to get installation token: {response.text}")
            raise Exception(f"Failed to get installation token: {response.status_code}")

        data = response.json()
        self._token = data['token']
        # Token expires in 1 hour, but we'll refresh it after 50 minutes
        self._token_expires_at = datetime.utcnow() + timedelta(minutes=50)

        return self._token

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> requests.Response:
        """Make an authenticated request to GitHub API."""
        token = self.get_installation_token()

        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        url = f"{self.base_url}{endpoint}"

        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data,
            params=params
        )

        return response

    def create_check_run(
        self,
        owner: str,
        repo: str,
        name: str,
        head_sha: str,
        status: str = "queued",
        conclusion: Optional[str] = None,
        started_at: Optional[str] = None,
        completed_at: Optional[str] = None,
        output: Optional[Dict[str, Any]] = None,
        actions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Create a check run."""
        data = {
            "name": name,
            "head_sha": head_sha,
            "status": status
        }

        if conclusion:
            data["conclusion"] = conclusion
        if started_at:
            data["started_at"] = started_at
        if completed_at:
            data["completed_at"] = completed_at
        if output:
            data["output"] = output
        if actions:
            data["actions"] = actions

        response = self._make_request(
            "POST",
            f"/repos/{owner}/{repo}/check-runs",
            data=data
        )

        if response.status_code != 201:
            logger.error(f"Failed to create check run: {response.text}")
            raise Exception(f"Failed to create check run: {response.status_code}")

        return response.json()

    def update_check_run(
        self,
        owner: str,
        repo: str,
        check_run_id: int,
        status: Optional[str] = None,
        conclusion: Optional[str] = None,
        completed_at: Optional[str] = None,
        output: Optional[Dict[str, Any]] = None,
        actions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Update an existing check run."""
        data = {}

        if status:
            data["status"] = status
        if conclusion:
            data["conclusion"] = conclusion
        if completed_at:
            data["completed_at"] = completed_at
        if output:
            data["output"] = output
        if actions:
            data["actions"] = actions

        response = self._make_request(
            "PATCH",
            f"/repos/{owner}/{repo}/check-runs/{check_run_id}",
            data=data
        )

        if response.status_code != 200:
            logger.error(f"Failed to update check run: {response.text}")
            raise Exception(f"Failed to update check run: {response.status_code}")

        return response.json()

    def get_pull_request(
        self,
        owner: str,
        repo: str,
        pr_number: int
    ) -> Dict[str, Any]:
        """Get pull request details."""
        response = self._make_request(
            "GET",
            f"/repos/{owner}/{repo}/pulls/{pr_number}"
        )

        if response.status_code != 200:
            logger.error(f"Failed to get pull request: {response.text}")
            raise Exception(f"Failed to get pull request: {response.status_code}")

        return response.json()

    def get_pull_request_files(
        self,
        owner: str,
        repo: str,
        pr_number: int
    ) -> List[Dict[str, Any]]:
        """Get files changed in a pull request."""
        files = []
        page = 1
        per_page = 100

        while True:
            response = self._make_request(
                "GET",
                f"/repos/{owner}/{repo}/pulls/{pr_number}/files",
                params={"page": page, "per_page": per_page}
            )

            if response.status_code != 200:
                logger.error(f"Failed to get pull request files: {response.text}")
                raise Exception(f"Failed to get pull request files: {response.status_code}")

            page_files = response.json()
            files.extend(page_files)

            if len(page_files) < per_page:
                break

            page += 1

        return files

    def create_issue_comment(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        body: str
    ) -> Dict[str, Any]:
        """Create a comment on an issue or pull request."""
        data = {"body": body}

        response = self._make_request(
            "POST",
            f"/repos/{owner}/{repo}/issues/{issue_number}/comments",
            data=data
        )

        if response.status_code != 201:
            logger.error(f"Failed to create comment: {response.text}")
            raise Exception(f"Failed to create comment: {response.status_code}")

        return response.json()

    def trigger_workflow(
        self,
        owner: str,
        repo: str,
        workflow_id: str,
        ref: str,
        inputs: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Trigger a GitHub Actions workflow."""
        data = {"ref": ref}
        if inputs:
            data["inputs"] = inputs

        response = self._make_request(
            "POST",
            f"/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches",
            data=data
        )

        if response.status_code != 204:
            logger.error(f"Failed to trigger workflow: {response.text}")
            return False

        return True

    def get_repository(
        self,
        owner: str,
        repo: str
    ) -> Dict[str, Any]:
        """Get repository information."""
        response = self._make_request(
            "GET",
            f"/repos/{owner}/{repo}"
        )

        if response.status_code != 200:
            logger.error(f"Failed to get repository: {response.text}")
            raise Exception(f"Failed to get repository: {response.status_code}")

        return response.json()

    def get_branch(
        self,
        owner: str,
        repo: str,
        branch: str
    ) -> Dict[str, Any]:
        """Get branch information."""
        response = self._make_request(
            "GET",
            f"/repos/{owner}/{repo}/branches/{branch}"
        )

        if response.status_code != 200:
            logger.error(f"Failed to get branch: {response.text}")
            raise Exception(f"Failed to get branch: {response.status_code}")

        return response.json()

    def get_file_content(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get file content from repository."""
        params = {}
        if ref:
            params["ref"] = ref

        response = self._make_request(
            "GET",
            f"/repos/{owner}/{repo}/contents/{path}",
            params=params
        )

        if response.status_code != 200:
            logger.error(f"Failed to get file content: {response.text}")
            raise Exception(f"Failed to get file content: {response.status_code}")

        return response.json()