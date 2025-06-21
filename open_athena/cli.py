"""
Command-line interface for OpenAthena.

This module provides a CLI for executing queries against OpenAthena.
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, Optional

import pandas as pd

from open_athena import __version__
from open_athena.client import OpenAthenaClient


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="OpenAthena CLI - Execute SQL queries against OpenAthena"
    )

    # Query input options
    query_group = parser.add_mutually_exclusive_group(required=False)
    query_group.add_argument("-q", "--query", help="SQL query to execute")
    query_group.add_argument(
        "-f", "--file", help="File containing SQL query to execute"
    )

    # Output options
    parser.add_argument("-o", "--output", help="Output file path (default: stdout)")

    parser.add_argument(
        "--format",
        choices=["csv", "json", "table"],
        default="table",
        help="Output format (default: table)",
    )

    # Server configuration
    parser.add_argument(
        "--server",
        default="http://localhost:8000",
        help="OpenAthena server URL (default: http://localhost:8000)",
    )

    # Catalog management
    parser.add_argument(
        "--list-tables", action="store_true", help="List all tables in the catalog"
    )

    parser.add_argument(
        "--reload-catalog", action="store_true", help="Reload the catalog"
    )

    parser.add_argument(
        "--add-table", action="store_true", help="Add a new table to the catalog"
    )

    parser.add_argument("--table-name", help="Name of the table to add")

    parser.add_argument("--bucket", help="S3 bucket for the table")

    parser.add_argument("--prefix", help="S3 prefix for the table")

    parser.add_argument(
        "--table-format",
        default="parquet",
        choices=["parquet", "csv", "json"],
        help="File format for the table (default: parquet)",
    )

    # Miscellaneous
    parser.add_argument("--version", action="store_true", help="Show version and exit")

    return parser.parse_args()


def read_query_from_file(filepath: str) -> str:
    """Read SQL query from a file."""
    try:
        with open(filepath, "r") as f:
            return f.read().strip()
    except Exception as e:
        print(f"Error reading query file: {e}", file=sys.stderr)
        sys.exit(1)


def write_output(data: Any, output_path: Optional[str], output_format: str) -> None:
    """Write query results to output."""
    if isinstance(data, pd.DataFrame):
        if output_format == "csv":
            output = data.to_csv(index=False)
        elif output_format == "json":
            output = data.to_json(orient="records", indent=2)
        else:  # table
            output = data.to_string(index=False)
    else:
        # Handle non-DataFrame output (like catalog info)
        if output_format == "json":
            output = json.dumps(data, indent=2)
        else:
            output = str(data)

    if output_path:
        with open(output_path, "w") as f:
            f.write(output)
        print(f"Results written to {output_path}")
    else:
        print(output)


def main():
    """Main CLI entry point."""
    args = parse_args()

    if args.version:
        print(f"OpenAthena CLI v{__version__}")
        sys.exit(0)

    # Create client
    client = OpenAthenaClient(args.server)

    # Check if server is available
    try:
        client.health_check()
    except Exception as e:
        print(
            f"Error connecting to OpenAthena server at {args.server}: {e}",
            file=sys.stderr,
        )
        print(
            "Make sure the server is running and the URL is correct.", file=sys.stderr
        )
        sys.exit(1)

    # Handle catalog operations
    if args.list_tables:
        tables = client.list_tables()
        write_output(tables, args.output, args.format)
        sys.exit(0)

    if args.reload_catalog:
        result = client.reload_catalog()
        write_output(result, args.output, args.format)
        sys.exit(0)

    if args.add_table:
        if not all([args.table_name, args.bucket, args.prefix]):
            print(
                "Error: --table-name, --bucket, and --prefix are required for --add-table",
                file=sys.stderr,
            )
            sys.exit(1)

        result = client.add_table(
            table_name=args.table_name,
            bucket=args.bucket,
            prefix=args.prefix,
            file_format=args.table_format,
        )
        write_output(result, args.output, args.format)
        sys.exit(0)

    # Handle query execution
    query = None

    if args.query:
        query = args.query
    elif args.file:
        query = read_query_from_file(args.file)

    if query:
        # Execute query
        df = client.execute_query(query)
        write_output(df, args.output, args.format)
    else:
        # No action specified
        print(
            "Error: No action specified. Use --help to see available options.",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
