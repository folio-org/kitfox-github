import os
import json
import yaml
import logging
import boto3
from typing import Dict, Any, Optional, List
from functools import lru_cache

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class ConfigLoader:
    """Load and manage configuration from S3 and environment variables."""

    def __init__(self):
        """Initialize configuration loader."""
        self.s3 = boto3.client('s3')
        self.config_bucket = os.environ.get('CONFIG_BUCKET_NAME')
        self._config_cache = {}

    @lru_cache(maxsize=128)
    def load_workflow_config(self, repository_name: str) -> Dict[str, Any]:
        """
        Load workflow configuration for a repository.

        Args:
            repository_name: Full repository name (owner/repo)

        Returns:
            Workflow configuration dictionary
        """
        try:
            # Try to load repository-specific config
            config_key = f"workflows/{repository_name.replace('/', '_')}.json"
            config = self._load_from_s3(config_key)

            if config:
                logger.info(f"Loaded repository-specific config for {repository_name}")
                return config

            # Fall back to default config
            default_config = self._load_from_s3("workflows/default.json")
            if default_config:
                logger.info(f"Using default config for {repository_name}")
                return default_config

            # Return minimal default if no config found
            logger.warning(f"No config found for {repository_name}, using minimal defaults")
            return self._get_minimal_config()

        except Exception as e:
            logger.error(f"Error loading workflow config: {str(e)}")
            return self._get_minimal_config()

    def load_validation_rules(self, repository_name: str) -> Dict[str, Any]:
        """
        Load validation rules for a repository.

        Args:
            repository_name: Full repository name (owner/repo)

        Returns:
            Validation rules dictionary
        """
        try:
            # Try to load repository-specific rules
            rules_key = f"validation/{repository_name.replace('/', '_')}.yaml"
            rules = self._load_from_s3(rules_key, format='yaml')

            if rules:
                logger.info(f"Loaded repository-specific validation rules for {repository_name}")
                return rules

            # Fall back to default rules
            default_rules = self._load_from_s3("validation/default.yaml", format='yaml')
            if default_rules:
                logger.info(f"Using default validation rules for {repository_name}")
                return default_rules

            # Return minimal default rules
            return self._get_default_validation_rules()

        except Exception as e:
            logger.error(f"Error loading validation rules: {str(e)}")
            return self._get_default_validation_rules()

    def load_release_config(self, repository_name: str) -> Dict[str, Any]:
        """
        Load release configuration for a repository.

        Args:
            repository_name: Full repository name (owner/repo)

        Returns:
            Release configuration dictionary
        """
        try:
            # Try to load repository-specific release config
            config_key = f"release/{repository_name.replace('/', '_')}.json"
            config = self._load_from_s3(config_key)

            if config:
                logger.info(f"Loaded repository-specific release config for {repository_name}")
                return config

            # Fall back to default release config
            default_config = self._load_from_s3("release/default.json")
            if default_config:
                logger.info(f"Using default release config for {repository_name}")
                return default_config

            # Return minimal default
            return self._get_default_release_config()

        except Exception as e:
            logger.error(f"Error loading release config: {str(e)}")
            return self._get_default_release_config()

    def load_team_config(self, team_name: str) -> Dict[str, Any]:
        """
        Load configuration for a team.

        Args:
            team_name: Team name

        Returns:
            Team configuration dictionary
        """
        try:
            config_key = f"teams/{team_name}.json"
            config = self._load_from_s3(config_key)

            if config:
                logger.info(f"Loaded team config for {team_name}")
                return config

            return {}

        except Exception as e:
            logger.error(f"Error loading team config: {str(e)}")
            return {}

    def _load_from_s3(self, key: str, format: str = 'json') -> Optional[Dict[str, Any]]:
        """
        Load configuration file from S3.

        Args:
            key: S3 object key
            format: File format ('json' or 'yaml')

        Returns:
            Parsed configuration or None if not found
        """
        if not self.config_bucket:
            logger.warning("CONFIG_BUCKET_NAME not set")
            return None

        # Check cache first
        cache_key = f"{self.config_bucket}/{key}"
        if cache_key in self._config_cache:
            return self._config_cache[cache_key]

        try:
            response = self.s3.get_object(Bucket=self.config_bucket, Key=key)
            content = response['Body'].read().decode('utf-8')

            if format == 'json':
                config = json.loads(content)
            elif format == 'yaml':
                config = yaml.safe_load(content)
            else:
                raise ValueError(f"Unsupported format: {format}")

            # Cache the result
            self._config_cache[cache_key] = config
            return config

        except self.s3.exceptions.NoSuchKey:
            logger.debug(f"Config file not found: {key}")
            return None
        except Exception as e:
            logger.error(f"Error loading config from S3: {str(e)}")
            return None

    def _get_minimal_config(self) -> Dict[str, Any]:
        """Get minimal default configuration."""
        return {
            "workflows": [
                {
                    "name": "default-checks",
                    "triggers": ["pull_request", "check_suite"],
                    "enabled": True
                }
            ],
            "checks": {
                "auto_trigger": True,
                "required_checks": []
            }
        }

    def _get_default_validation_rules(self) -> Dict[str, Any]:
        """Get default validation rules."""
        return {
            "pull_request": {
                "title": {
                    "required": True,
                    "min_length": 10,
                    "patterns": {
                        "allowed": [],
                        "forbidden": []
                    }
                },
                "description": {
                    "required": False,
                    "min_length": 0
                },
                "branch": {
                    "patterns": {
                        "source": {
                            "allowed": [],
                            "forbidden": []
                        },
                        "target": {
                            "allowed": [],
                            "forbidden": []
                        }
                    }
                },
                "files": {
                    "max_changes": 1000,
                    "forbidden_paths": [],
                    "required_paths": []
                },
                "labels": {
                    "required": [],
                    "forbidden": []
                }
            }
        }

    def _get_default_release_config(self) -> Dict[str, Any]:
        """Get default release configuration."""
        return {
            "versioning": {
                "scheme": "semantic",
                "auto_increment": False
            },
            "branch": {
                "pattern": "release/*",
                "create_from": "main"
            },
            "changelog": {
                "enabled": False,
                "format": "markdown"
            },
            "artifacts": {
                "build": True,
                "publish": False
            }
        }

    def get_environment_config(self) -> Dict[str, str]:
        """Get environment-specific configuration."""
        return {
            "environment": os.environ.get("ENVIRONMENT", "dev"),
            "region": os.environ.get("AWS_REGION", "us-east-1"),
            "log_level": os.environ.get("LOG_LEVEL", "INFO"),
            "github_app_id": os.environ.get("GITHUB_APP_ID", ""),
            "config_bucket": self.config_bucket or ""
        }

    def refresh_cache(self) -> None:
        """Clear the configuration cache."""
        self._config_cache.clear()
        logger.info("Configuration cache cleared")