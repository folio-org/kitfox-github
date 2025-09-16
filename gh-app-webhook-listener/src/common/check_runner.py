import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger()


class CheckRunner:
    """Manages GitHub check runs."""

    def __init__(self, github_client):
        self.github = github_client

    def create_check_run(self, owner: str, repo: str, head_sha: str,
                        check_suite_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Create a new check run.

        Args:
            owner: Repository owner
            repo: Repository name
            head_sha: The SHA of the commit
            check_suite_id: Optional check suite ID

        Returns:
            The created check run or None if failed
        """
        try:
            data = {
                'name': 'GitHub App Check',
                'head_sha': head_sha,
                'status': 'in_progress',
                'started_at': datetime.utcnow().isoformat() + 'Z',
                'output': {
                    'title': 'Check in progress',
                    'summary': 'Running automated checks...'
                }
            }

            if check_suite_id:
                data['check_suite_id'] = check_suite_id

            result = self.github.make_request(
                'POST',
                f'/repos/{owner}/{repo}/check-runs',
                json=data
            )

            logger.info(f"Created check run: {result.get('id')}")
            return result

        except Exception as e:
            logger.error(f"Failed to create check run: {e}")
            return None

    def update_check_run(self, owner: str, repo: str, check_run_id: int,
                        status: str = None, conclusion: str = None,
                        output: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Update an existing check run.

        Args:
            owner: Repository owner
            repo: Repository name
            check_run_id: The check run ID
            status: Status (queued, in_progress, completed)
            conclusion: Conclusion (success, failure, neutral, cancelled, skipped, timed_out, action_required)
            output: Output details

        Returns:
            The updated check run or None if failed
        """
        try:
            data = {}

            if status:
                data['status'] = status

            if conclusion:
                data['conclusion'] = conclusion
                data['completed_at'] = datetime.utcnow().isoformat() + 'Z'

            if output:
                data['output'] = output

            result = self.github.make_request(
                'PATCH',
                f'/repos/{owner}/{repo}/check-runs/{check_run_id}',
                json=data
            )

            logger.info(f"Updated check run {check_run_id}: status={status}, conclusion={conclusion}")
            return result

        except Exception as e:
            logger.error(f"Failed to update check run: {e}")
            return None

    def run_checks(self, owner: str, repo: str, check_run_id: int) -> str:
        """
        Run actual checks (placeholder for custom check logic).

        Args:
            owner: Repository owner
            repo: Repository name
            check_run_id: The check run ID

        Returns:
            Check result (success/failure)
        """
        try:
            # Placeholder for actual check logic
            # This is where you would implement your custom checks
            logger.info(f"Running checks for {owner}/{repo}")

            # Example: Update check run as successful
            self.update_check_run(
                owner=owner,
                repo=repo,
                check_run_id=check_run_id,
                status='completed',
                conclusion='success',
                output={
                    'title': 'All checks passed',
                    'summary': 'Successfully completed all automated checks.',
                    'text': '✅ All checks passed successfully!'
                }
            )

            return 'success'

        except Exception as e:
            logger.error(f"Error running checks: {e}")

            # Update check run as failed
            self.update_check_run(
                owner=owner,
                repo=repo,
                check_run_id=check_run_id,
                status='completed',
                conclusion='failure',
                output={
                    'title': 'Check failed',
                    'summary': 'An error occurred during checks.',
                    'text': f'❌ Error: {str(e)}'
                }
            )

            return 'failure'