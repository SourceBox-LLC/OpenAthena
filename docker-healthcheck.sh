#!/bin/sh
# Docker HEALTHCHECK script for OpenAthena
# This script is used by Docker to determine if the container is healthy

# Run the health check script
python /app/tests/health/run_healthcheck.py --format json

# Return the exit code from the health check script
exit $?
