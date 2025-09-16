import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class WorkflowOrchestrator:
    """Orchestrate GitHub Actions workflow triggers based on configuration."""

    def __init__(self, github_api, config_loader):
        """
        Initialize workflow orchestrator.

        Args:
            github_api: GitHubAPI instance
            config_loader: ConfigLoader instance
        """
        self.github_api = github_api
        self.config_loader = config_loader

    def trigger_workflows(
        self,
        repository: Dict[str, Any],
        pull_request: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Trigger configured workflows for a pull request.

        Args:
            repository: Repository information
            pull_request: Pull request information

        Returns:
            List of triggered workflows
        """
        triggered = []
        repo_full_name = repository.get('full_name', '')

        try:
            # Load workflow configuration
            config = self.config_loader.load_workflow_config(repo_full_name)
            workflows = config.get('workflows', [])

            logger.info(f"Found {len(workflows)} configured workflows for {repo_full_name}")

            for workflow in workflows:
                if self._should_trigger_workflow(workflow, pull_request):
                    result = self._trigger_workflow(
                        repository,
                        pull_request,
                        workflow
                    )
                    if result:
                        triggered.append(result)

            logger.info(f"Successfully triggered {len(triggered)} workflows")
            return triggered

        except Exception as e:
            logger.error(f"Error triggering workflows: {str(e)}", exc_info=True)
            return triggered

    def _should_trigger_workflow(
        self,
        workflow: Dict[str, Any],
        pull_request: Dict[str, Any]
    ) -> bool:
        """
        Determine if a workflow should be triggered.

        Args:
            workflow: Workflow configuration
            pull_request: Pull request information

        Returns:
            True if workflow should be triggered
        """
        # Check if workflow is enabled
        if not workflow.get('enabled', True):
            logger.debug(f"Workflow {workflow.get('name')} is disabled")
            return False

        # Check branch patterns
        if 'branch_patterns' in workflow:
            patterns = workflow['branch_patterns']
            base_branch = pull_request.get('base', {}).get('ref', '')
            head_branch = pull_request.get('head', {}).get('ref', '')

            if not self._matches_patterns(base_branch, patterns.get('base', [])):
                logger.debug(f"Base branch {base_branch} doesn't match patterns")
                return False

            if not self._matches_patterns(head_branch, patterns.get('head', [])):
                logger.debug(f"Head branch {head_branch} doesn't match patterns")
                return False

        # Check labels
        if 'required_labels' in workflow:
            pr_labels = [label.get('name', '') for label in pull_request.get('labels', [])]
            required = workflow['required_labels']

            if not all(label in pr_labels for label in required):
                logger.debug(f"Missing required labels: {required}")
                return False

        # Check file patterns
        if 'file_patterns' in workflow:
            # This would require fetching PR files, which we'll skip for now
            # to avoid additional API calls unless necessary
            pass

        return True

    def _trigger_workflow(
        self,
        repository: Dict[str, Any],
        pull_request: Dict[str, Any],
        workflow_config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Trigger a specific workflow.

        Args:
            repository: Repository information
            pull_request: Pull request information
            workflow_config: Workflow configuration

        Returns:
            Workflow trigger result or None if failed
        """
        try:
            workflow_name = workflow_config.get('name', 'unknown')
            workflow_file = workflow_config.get('file', f"{workflow_name}.yml")

            # Prepare workflow inputs
            inputs = self._prepare_workflow_inputs(pull_request, workflow_config)

            # Trigger the workflow
            success = self.github_api.trigger_workflow(
                owner=repository['owner']['login'],
                repo=repository['name'],
                workflow_id=workflow_file,
                ref=pull_request['head']['ref'],
                inputs=inputs
            )

            if success:
                logger.info(f"Successfully triggered workflow: {workflow_name}")
                return {
                    'name': workflow_name,
                    'file': workflow_file,
                    'triggered_at': datetime.utcnow().isoformat(),
                    'inputs': inputs
                }
            else:
                logger.error(f"Failed to trigger workflow: {workflow_name}")
                return None

        except Exception as e:
            logger.error(f"Error triggering workflow: {str(e)}", exc_info=True)
            return None

    def _prepare_workflow_inputs(
        self,
        pull_request: Dict[str, Any],
        workflow_config: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Prepare inputs for workflow dispatch.

        Args:
            pull_request: Pull request information
            workflow_config: Workflow configuration

        Returns:
            Workflow inputs dictionary
        """
        # Start with configured inputs
        inputs = workflow_config.get('inputs', {}).copy()

        # Add standard PR information
        inputs.update({
            'pr_number': str(pull_request.get('number', '')),
            'pr_title': pull_request.get('title', ''),
            'pr_author': pull_request.get('user', {}).get('login', ''),
            'base_branch': pull_request.get('base', {}).get('ref', ''),
            'head_branch': pull_request.get('head', {}).get('ref', ''),
            'head_sha': pull_request.get('head', {}).get('sha', '')
        })

        # Convert all values to strings (GitHub Actions requirement)
        return {k: str(v) for k, v in inputs.items()}

    def _matches_patterns(self, text: str, patterns: List[str]) -> bool:
        """
        Check if text matches any of the given patterns.

        Args:
            text: Text to check
            patterns: List of patterns (supports wildcards)

        Returns:
            True if text matches any pattern
        """
        if not patterns:
            return True

        import fnmatch
        return any(fnmatch.fnmatch(text, pattern) for pattern in patterns)

    def get_workflow_status(
        self,
        repository: Dict[str, Any],
        workflow_run_id: int
    ) -> Dict[str, Any]:
        """
        Get the status of a workflow run.

        Args:
            repository: Repository information
            workflow_run_id: Workflow run ID

        Returns:
            Workflow run status
        """
        try:
            # This would require additional GitHub API methods
            # For now, return a placeholder
            return {
                'id': workflow_run_id,
                'status': 'unknown',
                'conclusion': None
            }
        except Exception as e:
            logger.error(f"Error getting workflow status: {str(e)}")
            return {
                'id': workflow_run_id,
                'status': 'error',
                'error': str(e)
            }