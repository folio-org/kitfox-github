import logging
import json
from typing import Dict, Any, Optional
from .github_client import GitHubClient

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class WorkflowTrigger:
    """Handles triggering GitHub Actions workflows via the GitHub API"""

    def __init__(self, github_client: GitHubClient):
        """
        Initialize the WorkflowTrigger with a GitHub client

        Args:
            github_client: Authenticated GitHub client instance
        """
        self.github_client = github_client

    def trigger_workflow(self, owner: str, repo: str, workflow_file: str,
                        ref: str = "main", inputs: Dict[str, Any] = None) -> bool:
        """
        Trigger a GitHub Actions workflow

        Args:
            owner: Repository owner
            repo: Repository name
            workflow_file: Workflow file path (e.g., ".github/workflows/ci.yml")
            ref: Git reference (branch, tag, or commit SHA)
            inputs: Workflow input parameters

        Returns:
            True if successful, False otherwise
        """
        try:
            # Remove leading slash if present
            if workflow_file.startswith('/'):
                workflow_file = workflow_file[1:]

            # Extract just the workflow filename (GitHub API needs filename, not full path)
            # e.g., ".github/workflows/pr-check.yml" -> "pr-check.yml"
            workflow_id = workflow_file.split('/')[-1]

            # Prepare the request payload
            payload = {
                "ref": ref
            }

            if inputs:
                payload["inputs"] = inputs

            logger.info(f"Triggering workflow {workflow_file} in {owner}/{repo} on ref {ref}")
            logger.debug(f"Workflow trigger payload: {json.dumps(payload)}")

            # Trigger the workflow using workflow_dispatch event
            endpoint = f"repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches"
            response = self.github_client.make_request(
                method="POST",
                endpoint=endpoint,
                json=payload
            )

            # GitHub returns 204 No Content for successful workflow dispatch
            # make_request() will have raised an exception if the request failed
            # If we got here, the request was successful
            logger.info(f"Successfully triggered workflow {workflow_file}")
            return True

        except Exception as e:
            # Try to get more details from the response
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.json()
                    logger.error(f"Error triggering workflow {workflow_file}: {e.response.status_code} - {error_details}")
                except:
                    logger.error(f"Error triggering workflow {workflow_file}: {e.response.status_code} - {e.response.text}")
            else:
                logger.error(f"Error triggering workflow {workflow_file}: {e}", exc_info=True)
            return False

    def get_workflow_runs(self, owner: str, repo: str, workflow_id: str = None,
                         status: str = None, limit: int = 10) -> Optional[Dict[str, Any]]:
        """
        Get workflow runs for a repository

        Args:
            owner: Repository owner
            repo: Repository name
            workflow_id: Optional workflow ID to filter by
            status: Optional status to filter by (e.g., "in_progress", "completed")
            limit: Maximum number of runs to return

        Returns:
            List of workflow runs if successful, None otherwise
        """
        try:
            endpoint = f"repos/{owner}/{repo}/actions/runs"
            params = {
                "per_page": limit
            }

            if workflow_id:
                params["workflow_id"] = workflow_id

            if status:
                params["status"] = status

            response = self.github_client.make_request(
                method="GET",
                endpoint=endpoint,
                params=params
            )

            if response:
                return response.get("workflow_runs", [])

            return None

        except Exception as e:
            logger.error(f"Error getting workflow runs: {e}", exc_info=True)
            return None

    def get_workflow_run_status(self, owner: str, repo: str, run_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the status of a specific workflow run

        Args:
            owner: Repository owner
            repo: Repository name
            run_id: Workflow run ID

        Returns:
            Workflow run details if successful, None otherwise
        """
        try:
            endpoint = f"repos/{owner}/{repo}/actions/runs/{run_id}"

            response = self.github_client.make_request(
                method="GET",
                endpoint=endpoint
            )

            if response:
                return {
                    "id": response.get("id"),
                    "status": response.get("status"),
                    "conclusion": response.get("conclusion"),
                    "html_url": response.get("html_url"),
                    "created_at": response.get("created_at"),
                    "updated_at": response.get("updated_at")
                }

            return None

        except Exception as e:
            logger.error(f"Error getting workflow run status: {e}", exc_info=True)
            return None