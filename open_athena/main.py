"""
Main entry point for OpenAthena.

This module provides the main entry point for running OpenAthena as a standalone application.
"""

import os
import sys
import argparse
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


if __name__ == "__main__":
    main()
