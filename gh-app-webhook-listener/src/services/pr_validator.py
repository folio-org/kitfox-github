import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class PRValidator:
    """Validate pull requests against configured rules."""

    def __init__(self, github_api):
        """
        Initialize PR validator.

        Args:
            github_api: GitHubAPI instance
        """
        self.github_api = github_api

    def validate_pull_request(
        self,
        repository: Dict[str, Any],
        pull_request: Dict[str, Any],
        rules: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate a pull request against rules.

        Args:
            repository: Repository information
            pull_request: Pull request information
            rules: Validation rules (optional)

        Returns:
            Validation result with 'valid' boolean and details
        """
        errors = []
        warnings = []

        try:
            # Use provided rules or load default
            if not rules:
                from services.config_loader import ConfigLoader
                config_loader = ConfigLoader()
                rules = config_loader.load_validation_rules(repository.get('full_name', ''))

            pr_rules = rules.get('pull_request', {})

            # Validate title
            title_errors = self._validate_title(pull_request, pr_rules.get('title', {}))
            errors.extend(title_errors)

            # Validate description
            desc_errors = self._validate_description(pull_request, pr_rules.get('description', {}))
            errors.extend(desc_errors)

            # Validate branches
            branch_errors = self._validate_branches(pull_request, pr_rules.get('branch', {}))
            errors.extend(branch_errors)

            # Validate files
            file_errors = self._validate_files(repository, pull_request, pr_rules.get('files', {}))
            errors.extend(file_errors)

            # Validate labels
            label_errors = self._validate_labels(pull_request, pr_rules.get('labels', {}))
            errors.extend(label_errors)

            # Check for merge conflicts
            if pull_request.get('mergeable_state') == 'dirty':
                errors.append("Pull request has merge conflicts")

            # Check draft status
            if pr_rules.get('allow_draft', False) is False and pull_request.get('draft'):
                errors.append("Draft pull requests are not allowed")

            # Determine overall validity
            valid = len(errors) == 0

            return {
                'valid': valid,
                'errors': errors,
                'warnings': warnings,
                'message': self._format_validation_message(valid, errors, warnings)
            }

        except Exception as e:
            logger.error(f"Error validating pull request: {str(e)}", exc_info=True)
            return {
                'valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': [],
                'message': f"Failed to validate pull request: {str(e)}"
            }

    def _validate_title(
        self,
        pull_request: Dict[str, Any],
        rules: Dict[str, Any]
    ) -> List[str]:
        """Validate pull request title."""
        errors = []
        title = pull_request.get('title', '')

        # Check if title is required
        if rules.get('required', True) and not title:
            errors.append("Pull request title is required")
            return errors

        # Check minimum length
        min_length = rules.get('min_length', 0)
        if len(title) < min_length:
            errors.append(f"Title must be at least {min_length} characters long")

        # Check maximum length
        max_length = rules.get('max_length', 500)
        if len(title) > max_length:
            errors.append(f"Title must not exceed {max_length} characters")

        # Check patterns
        patterns = rules.get('patterns', {})

        # Check allowed patterns
        allowed = patterns.get('allowed', [])
        if allowed and not any(re.match(pattern, title) for pattern in allowed):
            errors.append(f"Title must match one of the allowed patterns: {', '.join(allowed)}")

        # Check forbidden patterns
        forbidden = patterns.get('forbidden', [])
        for pattern in forbidden:
            if re.search(pattern, title):
                errors.append(f"Title contains forbidden pattern: {pattern}")

        # Check conventional commit format if enabled
        if rules.get('conventional_commits', False):
            if not self._is_conventional_commit(title):
                errors.append("Title must follow conventional commit format (e.g., 'feat: add new feature')")

        return errors

    def _validate_description(
        self,
        pull_request: Dict[str, Any],
        rules: Dict[str, Any]
    ) -> List[str]:
        """Validate pull request description."""
        errors = []
        description = pull_request.get('body', '') or ''

        # Check if description is required
        if rules.get('required', False) and not description.strip():
            errors.append("Pull request description is required")

        # Check minimum length
        min_length = rules.get('min_length', 0)
        if len(description) < min_length:
            errors.append(f"Description must be at least {min_length} characters long")

        # Check for required sections
        required_sections = rules.get('required_sections', [])
        for section in required_sections:
            if section.lower() not in description.lower():
                errors.append(f"Description must include section: {section}")

        # Check for template compliance
        if rules.get('template_required', False):
            template_markers = ['## Description', '## Type of Change', '## Testing']
            if not any(marker in description for marker in template_markers):
                errors.append("Description must use the pull request template")

        return errors

    def _validate_branches(
        self,
        pull_request: Dict[str, Any],
        rules: Dict[str, Any]
    ) -> List[str]:
        """Validate source and target branches."""
        errors = []
        base_branch = pull_request.get('base', {}).get('ref', '')
        head_branch = pull_request.get('head', {}).get('ref', '')

        patterns = rules.get('patterns', {})

        # Validate source branch
        source_patterns = patterns.get('source', {})
        source_allowed = source_patterns.get('allowed', [])
        source_forbidden = source_patterns.get('forbidden', [])

        if source_allowed and not any(re.match(p, head_branch) for p in source_allowed):
            errors.append(f"Source branch '{head_branch}' doesn't match allowed patterns")

        for pattern in source_forbidden:
            if re.match(pattern, head_branch):
                errors.append(f"Source branch '{head_branch}' matches forbidden pattern: {pattern}")

        # Validate target branch
        target_patterns = patterns.get('target', {})
        target_allowed = target_patterns.get('allowed', [])
        target_forbidden = target_patterns.get('forbidden', [])

        if target_allowed and not any(re.match(p, base_branch) for p in target_allowed):
            errors.append(f"Target branch '{base_branch}' is not allowed")

        for pattern in target_forbidden:
            if re.match(pattern, base_branch):
                errors.append(f"Target branch '{base_branch}' is forbidden: {pattern}")

        # Check for direct commits to protected branches
        protected_branches = rules.get('protected_branches', ['main', 'master', 'develop'])
        if head_branch in protected_branches:
            errors.append(f"Cannot create PR from protected branch: {head_branch}")

        return errors

    def _validate_files(
        self,
        repository: Dict[str, Any],
        pull_request: Dict[str, Any],
        rules: Dict[str, Any]
    ) -> List[str]:
        """Validate files changed in the pull request."""
        errors = []

        try:
            # Get files changed in the PR
            files = self.github_api.get_pull_request_files(
                owner=repository['owner']['login'],
                repo=repository['name'],
                pr_number=pull_request['number']
            )

            # Check maximum number of changes
            max_changes = rules.get('max_changes', 1000)
            total_changes = sum(f.get('changes', 0) for f in files)
            if total_changes > max_changes:
                errors.append(f"Too many changes ({total_changes}). Maximum allowed: {max_changes}")

            # Check maximum number of files
            max_files = rules.get('max_files', 100)
            if len(files) > max_files:
                errors.append(f"Too many files changed ({len(files)}). Maximum allowed: {max_files}")

            # Check forbidden paths
            forbidden_paths = rules.get('forbidden_paths', [])
            for file in files:
                filename = file.get('filename', '')
                for pattern in forbidden_paths:
                    if re.match(pattern, filename):
                        errors.append(f"Changes to forbidden path: {filename}")

            # Check required paths
            required_paths = rules.get('required_paths', [])
            file_paths = [f.get('filename', '') for f in files]
            for pattern in required_paths:
                if not any(re.match(pattern, path) for path in file_paths):
                    errors.append(f"Missing required file changes matching: {pattern}")

            # Check file size limits
            max_file_size = rules.get('max_file_size', 10485760)  # 10MB default
            for file in files:
                if file.get('size', 0) > max_file_size:
                    errors.append(f"File too large: {file.get('filename')} ({file.get('size')} bytes)")

        except Exception as e:
            logger.error(f"Error validating files: {str(e)}")
            # Don't fail validation if we can't check files
            pass

        return errors

    def _validate_labels(
        self,
        pull_request: Dict[str, Any],
        rules: Dict[str, Any]
    ) -> List[str]:
        """Validate pull request labels."""
        errors = []
        pr_labels = [label.get('name', '') for label in pull_request.get('labels', [])]

        # Check required labels
        required_labels = rules.get('required', [])
        for label in required_labels:
            if label not in pr_labels:
                errors.append(f"Missing required label: {label}")

        # Check forbidden labels
        forbidden_labels = rules.get('forbidden', [])
        for label in forbidden_labels:
            if label in pr_labels:
                errors.append(f"Forbidden label present: {label}")

        # Check for at least one label from groups
        label_groups = rules.get('require_one_of', [])
        for group in label_groups:
            if not any(label in pr_labels for label in group):
                errors.append(f"Must have at least one label from: {', '.join(group)}")

        return errors

    def _is_conventional_commit(self, title: str) -> bool:
        """Check if title follows conventional commit format."""
        # Basic conventional commit pattern
        pattern = r'^(feat|fix|docs|style|refactor|perf|test|chore|build|ci)(\(.+\))?: .+'
        return bool(re.match(pattern, title, re.IGNORECASE))

    def _format_validation_message(
        self,
        valid: bool,
        errors: List[str],
        warnings: List[str]
    ) -> str:
        """Format validation result message."""
        if valid:
            return "Pull request validation passed"

        message = "Pull request validation failed:\n"
        if errors:
            message += "\nErrors:\n"
            message += "\n".join(f"- {error}" for error in errors)

        if warnings:
            message += "\n\nWarnings:\n"
            message += "\n".join(f"- {warning}" for warning in warnings)

        return message