import yaml
import logging
from typing import Dict, Any, Optional, List
from services.github_api import GitHubAPI

logger = logging.getLogger(__name__)


class ReleaseConfigLoader:
    """Load and parse release-config.yml from repositories."""
    
    def __init__(self, github_api: GitHubAPI):
        """
        Initialize release config loader.
        
        Args:
            github_api: GitHub API client
        """
        self.github = github_api
        self._cache = {}
    
    def get_release_config(
        self,
        access_token: str,
        repo_full_name: str,
        ref: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get release configuration from repository.
        
        Args:
            access_token: GitHub installation access token
            repo_full_name: Repository full name (owner/repo)
            ref: Git ref (branch/tag/sha). If None, uses default branch
            
        Returns:
            Release configuration dictionary or None if not found
        """
        cache_key = f"{repo_full_name}:{ref or 'default'}"
        
        # Check cache
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            # Get file content from GitHub
            content = self.github.get_file_content(
                access_token=access_token,
                repo_full_name=repo_full_name,
                path='.github/release-config.yml',
                ref=ref
            )
            
            if not content:
                logger.info(f"No release-config.yml found in {repo_full_name}")
                return None
            
            # Parse YAML
            config = yaml.safe_load(content)
            
            # Cache the result
            self._cache[cache_key] = config
            
            logger.info(f"Loaded release config for {repo_full_name}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load release config for {repo_full_name}: {e}")
            return None
    
    def should_process_branch(
        self,
        config: Dict[str, Any],
        branch_name: str,
        default_branch: str,
        is_pr: bool = False,
        pr_labels: List[str] = None
    ) -> bool:
        """
        Check if a branch should be processed based on release config.
        
        Args:
            config: Release configuration
            branch_name: Branch name to check
            default_branch: Repository's default branch name
            is_pr: Whether this is a pull request
            pr_labels: PR labels if applicable
            
        Returns:
            True if branch should be processed
        """
        if not config:
            return False
        
        # Check if scanning is enabled
        scan_config = config.get('scan_config', {})
        if not scan_config.get('enabled', False):
            logger.info("Scanning is disabled in release config")
            return False
        
        # For PRs, check if required labels are present
        if is_pr and pr_labels is not None:
            required_labels = scan_config.get('labels', [])
            if required_labels:
                has_required_label = any(
                    label in pr_labels for label in required_labels
                )
                if not has_required_label:
                    logger.info(f"PR missing required labels: {required_labels}")
                    return False
        
        # Check release branches
        release_branches = config.get('release_branches', [])
        if branch_name in release_branches:
            logger.info(f"Branch {branch_name} is a release branch")
            return True
        
        # Check update branch format
        update_format = scan_config.get('update_branch_format', '')
        if update_format and self._matches_update_format(branch_name, update_format):
            logger.info(f"Branch {branch_name} matches update format")
            return True
        
        # Check if it's the default branch
        if branch_name == default_branch:
            logger.info(f"Branch {branch_name} is the default branch")
            return True
        
        logger.info(f"Branch {branch_name} should not be processed")
        return False
    
    def _matches_update_format(self, branch_name: str, format_pattern: str) -> bool:
        """
        Check if branch name matches update branch format.
        
        Args:
            branch_name: Branch name to check
            format_pattern: Format pattern like "release-update/{0}"
            
        Returns:
            True if branch matches pattern
        """
        try:
            # Convert format pattern to regex
            # "release-update/{0}" -> "release-update/.*"
            import re
            pattern = format_pattern.replace('{0}', '.*')
            pattern = pattern.replace('{1}', '.*')  # Support multiple placeholders
            pattern = f'^{pattern}$'
            
            return bool(re.match(pattern, branch_name))
        except Exception as e:
            logger.error(f"Failed to match pattern: {e}")
            return False
    
    def get_pr_reviewers(self, config: Dict[str, Any]) -> List[str]:
        """
        Get PR reviewers from release config.
        
        Args:
            config: Release configuration
            
        Returns:
            List of reviewer usernames/teams
        """
        scan_config = config.get('scan_config', {})
        reviewers = scan_config.get('pr_reviewers', [])
        
        # Filter out commented reviewers (lines starting with #)
        active_reviewers = [
            r for r in reviewers 
            if r and not str(r).strip().startswith('#')
        ]
        
        return active_reviewers
    
    def clear_cache(self, repo_full_name: str = None) -> None:
        """
        Clear cached configurations.
        
        Args:
            repo_full_name: Specific repository to clear, or None to clear all
        """
        if repo_full_name:
            keys_to_remove = [
                k for k in self._cache.keys() 
                if k.startswith(f"{repo_full_name}:")
            ]
            for key in keys_to_remove:
                del self._cache[key]
        else:
            self._cache.clear()