#!/usr/bin/env python
"""
Simple runner script for OpenAthena health checks.
Can be used in monitoring systems, CI/CD pipelines, or as a Docker HEALTHCHECK.
"""

import os
import sys
import argparse
import time
from healthcheck import OpenAthenaHealthChecker


def main():
    parser = argparse.ArgumentParser(description="Run OpenAthena health checks")
    parser.add_argument(
        "--url",
        default=os.environ.get("OPENATHENA_URL", "http://localhost:8000"),
        help="OpenAthena server URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Timeout in seconds for health checks (default: 10)",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=1,
        help="Number of retries for failed checks (default: 1)",
    )
    parser.add_argument(
        "--wait",
        type=int,
        default=2,
        help="Wait time between retries in seconds (default: 2)",
    )

    args = parser.parse_args()

    # Create health checker
    checker = OpenAthenaHealthChecker(args.url)

    # Run checks with retries
    success = False
    for attempt in range(args.retries + 1):
        if attempt > 0:
            print(f"Attempt {attempt + 1}/{args.retries + 1}...")
            time.sleep(args.wait)

        try:
            checker.run_all_checks()
            status, message = checker.get_overall_status()

            if status == "healthy":
                success = True
                break
        except Exception as e:
            print(f"Error during health check: {e}")

    # Print results
    checker.print_results(json_format=(args.format == "json"))

    # Return appropriate exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
