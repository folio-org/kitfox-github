import json
import boto3
import logging
from typing import Dict, Any, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Load and cache configuration from S3."""
    
    def __init__(self, bucket_name: str):
        """
        Initialize configuration loader.
        
        Args:
            bucket_name: S3 bucket name containing configuration
        """
        self.bucket_name = bucket_name
        self.s3 = boto3.client('s3')
        self._config_cache = {}
    
    @lru_cache(maxsize=1)
    def load_repositories_config(self) -> Dict[str, Any]:
        """
        Load repositories configuration from S3.
        
        Returns:
            Repositories configuration dictionary
        """
        try:
            response = self.s3.get_object(
                Bucket=self.bucket_name,
                Key='config/repositories.json'
            )
            content = response['Body'].read().decode('utf-8')
            config = json.loads(content)
            
            logger.info(f"Loaded configuration for {len(config)} repositories")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load repositories config: {e}")
            return {}
    
    def get_repository_config(self, repo_full_name: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific repository.
        
        Args:
            repo_full_name: Repository full name (owner/repo)
            
        Returns:
            Repository configuration or None if not found
        """
        config = self.load_repositories_config()
        repo_config = config.get(repo_full_name)
        
        if repo_config:
            logger.info(f"Found configuration for {repo_full_name}")
        else:
            logger.warning(f"No configuration found for {repo_full_name}")
        
        return repo_config
    
    def get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration for repositories without specific config.
        
        Returns:
            Default configuration dictionary
        """
        config = self.load_repositories_config()
        return config.get('_default', {
            'workflows': [],
            'branch_patterns': ['main', 'master'],
            'trigger_events': ['check_suite.requested', 'check_suite.rerequested']
        })
    
    def reload_config(self) -> None:
        """Force reload of configuration from S3."""
        self.load_repositories_config.cache_clear()
        self._config_cache.clear()
        logger.info("Configuration cache cleared")