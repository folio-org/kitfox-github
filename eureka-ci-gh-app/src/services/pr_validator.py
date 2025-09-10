import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class PRValidator:
    """Validate pull requests based on release configuration."""
    
    def __init__(self, config_loader):
        """
        Initialize PR validator.
        
        Args:
            config_loader: Release configuration loader instance
        """
        self.config_loader = config_loader
    
    def validate_pr(
        self,
        config: Optional[Dict[str, Any]],
        target_branch: str,
        source_branch: str,
        pr_labels: List[str],
        default_branch: str
    ) -> Dict[str, Any]:
        """
        Validate PR based on release configuration.
        
        Args:
            config: Release configuration
            target_branch: PR target branch
            source_branch: PR source branch
            pr_labels: List of PR labels
            default_branch: Repository default branch
            
        Returns:
            Validation result dictionary with 'valid', 'message', and other details
        """
        result = {
            'valid': False,
            'message': '',
            'config_exists': False,
            'scan_enabled': False,
            'branch_configured': False,
            'labels_valid': True,
            'missing_labels': [],
            'conclusion': 'failure'
        }
        
        # Check if configuration exists
        if not config:
            result['message'] = 'Release configuration file not found (.github/release-config.yml)'
            logger.warning(f"No release config found for validation")
            return result
        
        result['config_exists'] = True
        
        # Check if scanning is enabled
        scan_config = config.get('scan_config', {})
        if not scan_config.get('enabled', False):
            result['message'] = 'Release scanning is disabled in configuration'
            result['conclusion'] = 'skipped'
            logger.info("Release scanning is disabled")
            return result
        
        result['scan_enabled'] = True
        
        # Check if target branch is configured for release scanning
        release_branches = config.get('release_branches', [])
        update_format = scan_config.get('update_branch_format', '')
        
        is_release_branch = target_branch in release_branches
        is_update_branch = self._matches_update_format(target_branch, update_format) if update_format else False
        is_default_branch = target_branch == default_branch
        
        if not (is_release_branch or is_update_branch or is_default_branch):
            result['message'] = f'Target branch {target_branch} is not configured for release scanning'
            result['conclusion'] = 'skipped'
            logger.info(f"Branch {target_branch} not configured for scanning")
            return result
        
        result['branch_configured'] = True
        
        # Check required labels
        required_labels = scan_config.get('labels', [])
        if required_labels:
            missing_labels = []
            for label in required_labels:
                if label and label not in pr_labels:
                    missing_labels.append(label)
            
            if missing_labels:
                result['labels_valid'] = False
                result['missing_labels'] = missing_labels
                result['message'] = f'PR is missing required labels: {", ".join(missing_labels)}'
                result['conclusion'] = 'skipped'
                logger.info(f"PR missing required labels: {missing_labels}")
                return result
        
        # All validations passed
        result['valid'] = True
        result['message'] = 'PR validation passed'
        result['conclusion'] = 'success'
        logger.info("PR validation successful")
        
        return result
    
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
            import re
            # Convert format pattern to regex
            # "release-update/{0}" -> "release-update/.*"
            pattern = format_pattern.replace('{0}', '.*')
            pattern = pattern.replace('{1}', '.*')  # Support multiple placeholders
            pattern = f'^{pattern}$'
            
            return bool(re.match(pattern, branch_name))
        except Exception as e:
            logger.error(f"Failed to match pattern: {e}")
            return False