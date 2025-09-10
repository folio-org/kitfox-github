import jwt
import time
import requests
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class GitHubAPI:
    """GitHub API client for App authentication and API operations."""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, app_id: str, private_key: str):
        """
        Initialize GitHub API client.
        
        Args:
            app_id: GitHub App ID
            private_key: GitHub App private key in PEM format
        """
        self.app_id = app_id
        self.private_key = private_key
    
    def get_jwt_token(self) -> str:
        """
        Generate a JWT token for GitHub App authentication.
        
        Returns:
            JWT token string
        """
        now = int(time.time())
        payload = {
            'iat': now - 60,  # Issued at time (60 seconds in the past)
            'exp': now + 600,  # Expiration time (10 minutes)
            'iss': self.app_id  # GitHub App ID
        }
        
        return jwt.encode(payload, self.private_key, algorithm='RS256')
    
    def get_installation_token(self, installation_id: int) -> str:
        """
        Get an installation access token for API operations.
        
        Args:
            installation_id: GitHub App installation ID
            
        Returns:
            Installation access token
        """
        jwt_token = self.get_jwt_token()
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        url = f"{self.BASE_URL}/app/installations/{installation_id}/access_tokens"
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        
        return response.json()['token']
    
    def create_check_run(
        self,
        access_token: str,
        repo_full_name: str,
        name: str,
        head_sha: str,
        status: str = 'queued',
        conclusion: Optional[str] = None,
        details_url: Optional[str] = None,
        output: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a check run for a commit.
        
        Args:
            access_token: Installation access token
            repo_full_name: Repository full name (owner/repo)
            name: Check run name
            head_sha: Git commit SHA
            status: Check run status (queued, in_progress, completed)
            conclusion: Check run conclusion (success, failure, neutral, cancelled, skipped, timed_out, action_required)
            details_url: URL with more details about the check run
            output: Check run output (title, summary, text, annotations)
            
        Returns:
            Created check run data
        """
        headers = {
            'Authorization': f'token {access_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        data = {
            'name': name,
            'head_sha': head_sha,
            'status': status
        }
        
        if conclusion:
            data['conclusion'] = conclusion
        if details_url:
            data['details_url'] = details_url
        if output:
            data['output'] = output
        if status == 'in_progress':
            data['started_at'] = self.get_current_time()
        if status == 'completed':
            data['completed_at'] = self.get_current_time()
        
        url = f"{self.BASE_URL}/repos/{repo_full_name}/check-runs"
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        
        return response.json()
    
    def update_check_run(
        self,
        access_token: str,
        repo_full_name: str,
        check_run_id: int,
        status: Optional[str] = None,
        conclusion: Optional[str] = None,
        started_at: Optional[str] = None,
        completed_at: Optional[str] = None,
        output: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update an existing check run.
        
        Args:
            access_token: Installation access token
            repo_full_name: Repository full name (owner/repo)
            check_run_id: Check run ID
            status: Check run status
            conclusion: Check run conclusion
            started_at: ISO 8601 timestamp when check started
            completed_at: ISO 8601 timestamp when check completed
            output: Check run output
            
        Returns:
            Updated check run data
        """
        headers = {
            'Authorization': f'token {access_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        data = {}
        if status:
            data['status'] = status
        if conclusion:
            data['conclusion'] = conclusion
        if started_at:
            data['started_at'] = started_at
        if completed_at:
            data['completed_at'] = completed_at
        if output:
            data['output'] = output
        
        url = f"{self.BASE_URL}/repos/{repo_full_name}/check-runs/{check_run_id}"
        response = requests.patch(url, json=data, headers=headers)
        response.raise_for_status()
        
        return response.json()
    
    def trigger_workflow_dispatch(
        self,
        access_token: str,
        repo_full_name: str,
        workflow_file: str,
        ref: str,
        inputs: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Trigger a GitHub Actions workflow via workflow_dispatch.
        
        Args:
            access_token: Installation access token
            repo_full_name: Repository full name (owner/repo)
            workflow_file: Workflow file name (e.g., 'eureka-ci-check.yml')
            ref: Git ref (branch or tag)
            inputs: Workflow input parameters
        """
        headers = {
            'Authorization': f'token {access_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        data = {'ref': ref}
        if inputs:
            data['inputs'] = inputs
        
        url = f"{self.BASE_URL}/repos/{repo_full_name}/actions/workflows/{workflow_file}/dispatches"
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        
        logger.info(f"Triggered workflow {workflow_file} on {ref} for {repo_full_name}")
    
    def get_repository_info(
        self,
        access_token: str,
        repo_full_name: str
    ) -> Dict[str, Any]:
        """
        Get repository information.
        
        Args:
            access_token: Installation access token
            repo_full_name: Repository full name (owner/repo)
            
        Returns:
            Repository information including default branch
        """
        headers = {
            'Authorization': f'token {access_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        url = f"{self.BASE_URL}/repos/{repo_full_name}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()
    
    def get_file_content(
        self,
        access_token: str,
        repo_full_name: str,
        path: str,
        ref: str = None
    ) -> Optional[str]:
        """
        Get file content from repository.
        
        Args:
            access_token: Installation access token
            repo_full_name: Repository full name (owner/repo)
            path: File path in repository
            ref: Git ref (branch/tag/sha). If None, uses default branch
            
        Returns:
            File content as string or None if not found
        """
        headers = {
            'Authorization': f'token {access_token}',
            'Accept': 'application/vnd.github.v3.raw'
        }
        
        url = f"{self.BASE_URL}/repos/{repo_full_name}/contents/{path}"
        params = {}
        if ref:
            params['ref'] = ref
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.text
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    def get_pull_request(
        self,
        access_token: str,
        repo_full_name: str,
        pr_number: int
    ) -> Dict[str, Any]:
        """
        Get pull request information.
        
        Args:
            access_token: Installation access token
            repo_full_name: Repository full name (owner/repo)
            pr_number: Pull request number
            
        Returns:
            Pull request data including labels
        """
        headers = {
            'Authorization': f'token {access_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        url = f"{self.BASE_URL}/repos/{repo_full_name}/pulls/{pr_number}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()
    
    @staticmethod
    def get_current_time() -> str:
        """
        Get current time in ISO 8601 format.
        
        Returns:
            ISO 8601 formatted timestamp
        """
        return datetime.now(timezone.utc).isoformat()