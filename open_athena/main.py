"""
Main entry point for OpenAthena.

This module provides the main entry point for running OpenAthena as a standalone application.
"""

import os
import sys
import argparse
from pathlib import Path
import getpass
from typing import Dict, Any

from open_athena.api import app, get_db
from open_athena.config import get_config
from open_athena import __version__


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="OpenAthena - SQL analytics engine for OpenS3 powered by DuckDB"
    )
    
    parser.add_argument(
        "--config", 
        help="Path to configuration file",
        default=os.environ.get("OPENATHENA_CONFIG_PATH")
    )
    
    parser.add_argument(
        "--catalog", 
        help="Path to catalog file",
        default=os.environ.get("OPENATHENA_CATALOG_PATH", "catalog.yml")
    )
    
    parser.add_argument(
        "--port", 
        type=int,
        help="API server port",
        default=int(os.environ.get("OPENATHENA_PORT", "8000"))
    )
    
    parser.add_argument(
        "--host", 
        help="API server host",
        default=os.environ.get("OPENATHENA_HOST", "0.0.0.0")
    )
    
    parser.add_argument(
        "--version", 
        action="store_true",
        help="Show version and exit"
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    if args.version:
        print(f"OpenAthena v{__version__}")
        sys.exit(0)
    
    # Load configuration
    config = get_config(args.config)
    
    # Override catalog path if specified
    if args.catalog:
        os.environ["OPENATHENA_CATALOG_PATH"] = args.catalog
    
    # Override API host/port if specified
    if args.host:
        os.environ["OPENATHENA_HOST"] = args.host
    
    if args.port:
        os.environ["OPENATHENA_PORT"] = str(args.port)
    
    # Start the API server
    import uvicorn
    print(f"Starting OpenAthena v{__version__}")
    print(f"Catalog path: {args.catalog}")
    print(f"API server: http://{args.host}:{args.port}")
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port
    )


def configure_opens3():
    """
    Interactive configuration of OpenS3 connection settings.
    Creates a .env file with appropriate environment variables.
    """
    print("\n" + "="*50)
    print("OpenAthena - OpenS3 Connection Configuration")
    print("="*50)

    # Default settings for the Raspberry Pi server
    default_endpoint = "http://10.0.0.204:80"
    
    # Get input from user with defaults
    print("\nEnter your OpenS3 connection details (press Enter to use defaults):")
    
    endpoint = input(f"OpenS3 Endpoint URL [default: {default_endpoint}]: ").strip() or default_endpoint
    
    # For security, don't show default credentials and always prompt
    access_key = input("OpenS3 Access Key: ").strip()
    if not access_key:
        print("Warning: Access Key is required for OpenS3 access")
    
    # Use getpass for the secret key to avoid showing it in the terminal
    secret_key = getpass.getpass("OpenS3 Secret Key: ").strip()
    if not secret_key:
        print("Warning: Secret Key is required for OpenS3 access")
    
    # Ask if the user wants to create the .env file
    create_env = input("\nCreate .env file with these settings? (y/n) [default: y]: ").strip().lower() or "y"
    
    if create_env == "y":
        env_path = Path(".env")
        
        # Create or overwrite the .env file
        with open(env_path, "w") as env_file:
            env_file.write(f"# OpenAthena Environment Configuration\n")
            env_file.write(f"# Created by OpenAthena setup.py\n\n")
            
            # OpenS3 connection settings
            env_file.write(f"# OpenS3 Connection Settings\n")
            env_file.write(f"OPENS3_ENDPOINT={endpoint}\n")
            if access_key:
                env_file.write(f"OPENS3_ACCESS_KEY={access_key}\n")
            if secret_key:
                env_file.write(f"OPENS3_SECRET_KEY={secret_key}\n")
            
            # Additional optional settings with comments
            env_file.write(f"\n# Optional OpenAthena Settings\n")
            env_file.write(f"# OPENATHENA_CATALOG_PATH=catalog.yml\n")
            env_file.write(f"# OPENATHENA_DB_PATH=openathena.db\n")
            env_file.write(f"# OPENATHENA_HOST=0.0.0.0\n")
            env_file.write(f"# OPENATHENA_PORT=8000\n")
            env_file.write(f"# OPENATHENA_THREADS=4\n")
            env_file.write(f"# OPENATHENA_MEMORY_LIMIT=4GB\n")
            
        print(f"\n✅ .env file created successfully at: {env_path.absolute()}")
        print("You can edit this file later to update your configuration.")
    else:
        print("\nSkipped .env file creation.")
    
    print("\nTo start the OpenAthena server:")
    print("  python -m open_athena.api")
    print("\nFor more information, see the README.md file.")
    print("="*50 + "\n")


if __name__ == "__main__":
    main()
