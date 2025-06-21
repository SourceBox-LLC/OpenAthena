"""
Configuration module for OpenAthena.

This module handles loading configuration from environment variables and config files.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


# Load environment variables from .env file if it exists
load_dotenv()


class Config:
    """Configuration handler for OpenAthena."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration from environment variables and config file.

        Args:
            config_path: Path to configuration YAML file (optional)
        """
        self.config_data = {}

        # Load from config file if provided
        if config_path and os.path.exists(config_path):
            self.config_data = yaml.safe_load(Path(config_path).read_text()) or {}

        # Setup default configuration
        self._setup_defaults()

        # Override with environment variables
        self._override_from_env()

    def _setup_defaults(self) -> None:
        """Set up default configuration values."""
        self.config_data.setdefault("database", {})
        self.config_data.setdefault("api", {})
        self.config_data.setdefault("s3", {})

        # Database defaults
        self.config_data["database"].setdefault("path", None)  # In-memory by default
        self.config_data["database"].setdefault("catalog_path", "catalog.yml")
        self.config_data["database"].setdefault("threads", 4)
        self.config_data["database"].setdefault("memory_limit", "4GB")
        self.config_data["database"].setdefault("enable_caching", True)

        # API defaults
        self.config_data["api"].setdefault("host", "0.0.0.0")
        self.config_data["api"].setdefault("port", 8000)

        # S3 defaults
        self.config_data["s3"].setdefault("endpoint", None)
        self.config_data["s3"].setdefault("region", "us-east-1")
        self.config_data["s3"].setdefault("use_ssl", True)

    def _override_from_env(self) -> None:
        """Override configuration from environment variables."""
        # Database settings
        if os.environ.get("OPENATHENA_DB_PATH"):
            self.config_data["database"]["path"] = os.environ.get("OPENATHENA_DB_PATH")

        if os.environ.get("OPENATHENA_CATALOG_PATH"):
            self.config_data["database"]["catalog_path"] = os.environ.get(
                "OPENATHENA_CATALOG_PATH"
            )

        if os.environ.get("OPENATHENA_THREADS"):
            self.config_data["database"]["threads"] = int(
                os.environ.get("OPENATHENA_THREADS")
            )

        if os.environ.get("OPENATHENA_MEMORY_LIMIT"):
            self.config_data["database"]["memory_limit"] = os.environ.get(
                "OPENATHENA_MEMORY_LIMIT"
            )

        if os.environ.get("OPENATHENA_ENABLE_CACHING"):
            self.config_data["database"]["enable_caching"] = (
                os.environ.get("OPENATHENA_ENABLE_CACHING").lower() == "true"
            )

        # API settings
        if os.environ.get("OPENATHENA_HOST"):
            self.config_data["api"]["host"] = os.environ.get("OPENATHENA_HOST")

        if os.environ.get("OPENATHENA_PORT"):
            self.config_data["api"]["port"] = int(os.environ.get("OPENATHENA_PORT"))

        # S3 settings
        # Check for OpenS3 specific environment variables first, then fall back to AWS ones
        if os.environ.get("OPENS3_ENDPOINT"):
            self.config_data["s3"]["endpoint"] = os.environ.get("OPENS3_ENDPOINT")
        elif os.environ.get("S3_ENDPOINT"):
            self.config_data["s3"]["endpoint"] = os.environ.get("S3_ENDPOINT")

        if os.environ.get("AWS_REGION"):
            self.config_data["s3"]["region"] = os.environ.get("AWS_REGION")

        # We don't override access_key and secret_key here as they're handled separately
        # for security reasons - they should come from environment or secure storage

    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return self.config_data["database"]

    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration."""
        return self.config_data["api"]

    def get_s3_config(self) -> Dict[str, Any]:
        """Get S3 configuration."""
        return self.config_data["s3"]

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.

        Args:
            key: Configuration key (dot notation for nested keys)
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self.config_data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value


# Global configuration instance
_config_instance = None


def get_config(config_path: Optional[str] = None) -> Config:
    """
    Get or initialize the global configuration instance.

    Args:
        config_path: Path to configuration YAML file (optional)

    Returns:
        Configuration instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_path)

    return _config_instance
