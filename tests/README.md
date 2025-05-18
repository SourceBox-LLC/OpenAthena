# OpenAthena Testing and Health Checks

This directory contains automated tests and health check utilities for OpenAthena.

## Testing Structure

The tests are organized into the following categories:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test multiple components working together
- **Health Checks**: Tools for monitoring and diagnosing OpenAthena instances
- **Utils**: Shared testing utilities and helper functions

## Running Tests

### Prerequisites

Install testing dependencies:

```bash
pip install pytest pytest-cov requests httpx
```

> **Note**: No OpenS3 instance is required for testing. The tests use dummy tables that are created in memory.

### Running All Tests

```bash
# From the project root directory
pytest
```

### Running Specific Test Types

```bash
# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run a specific test file
pytest tests/unit/test_catalog.py
```

### Test Coverage

To generate test coverage reports:

```bash
pip install pytest-cov
pytest --cov=open_athena
```

## Health Check Utilities

The `health` directory contains utilities to check the health and status of an OpenAthena instance.

### Using Health Checks

```bash
# Basic health check of a local OpenAthena instance
python -m tests.health.healthcheck

# Check a specific OpenAthena instance
python -m tests.health.healthcheck --url http://your-openathena-server:8000

# Get output in JSON format (useful for monitoring systems)
python -m tests.health.healthcheck --json

# Run a specific check
python -m tests.health.healthcheck --check api
```

### Health Check Runner

The `run_healthcheck.py` script is designed to be easily integrated with Docker, monitoring systems, or CI/CD pipelines:

```bash
# Basic usage
python tests/health/run_healthcheck.py

# With custom options
python tests/health/run_healthcheck.py --url http://your-server:8000 --format json --retries 3
```

### Docker Health Check Integration

The `docker-healthcheck.sh` script is configured in the Dockerfile to automatically monitor the health of the OpenAthena container:

```bash
# When building the Docker image, health checks are automatically configured
docker build -t openathena .

# View health status of running container
docker inspect --format='{{json .State.Health}}' <container_id>
```

## Adding New Tests

### Unit Tests

1. Create a new file in `tests/unit/` named `test_<module>.py`
2. Use pytest fixtures from `conftest.py` where appropriate
3. Keep tests focused on a single component

### Integration Tests

1. Create a new file in `tests/integration/` named `test_<feature>.py`
2. Test interactions between multiple components
3. Use mock objects when needed to isolate from external dependencies

## Continuous Integration

These tests are designed to be run in CI pipelines. Use the following command for CI runs:

```bash
pytest --junitxml=test-results.xml
```

## Troubleshooting

If tests are failing:

1. Ensure you have all dependencies installed
2. Check that the OpenAthena server is not already running when testing API endpoints
3. Verify the test catalog files are correctly formatted
4. Run tests with increased verbosity: `pytest -v`

For health check failures:

1. Ensure OpenAthena is running
2. Check network connectivity to the OpenAthena server
3. Verify OpenS3 credentials if using real OpenS3 data sources
