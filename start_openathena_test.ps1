# Script to start OpenAthena with OpenS3 connection settings

# Set environment variables
# OpenS3 credentials - set both AWS_ and OPENS3_ variants for compatibility
$env:AWS_ACCESS_KEY_ID = "admin"
$env:AWS_SECRET_ACCESS_KEY = "password"
$env:OPENS3_ACCESS_KEY = "admin"
$env:OPENS3_SECRET_KEY = "password"

# S3 endpoint configuration - set both S3_ and OPENS3_ variants for compatibility
$env:S3_ENDPOINT = "localhost:8001"  # Important: Use without http:// to avoid protocol issues
$env:OPENS3_ENDPOINT = "localhost:8001"  # DuckDB will handle protocol internally
$env:S3_USE_SSL = "false"  # Disable SSL for local connections

# OpenAthena configuration
$env:OPENATHENA_CATALOG_PATH = "$PSScriptRoot\openathena_test_catalog.yml"

# Print configuration
Write-Host "Configuration:"
Write-Host "AWS_ACCESS_KEY_ID=$env:AWS_ACCESS_KEY_ID"
Write-Host "S3_ENDPOINT=$env:S3_ENDPOINT (without protocol for DuckDB compatibility)"
Write-Host "S3_USE_SSL=$env:S3_USE_SSL"
Write-Host "OPENATHENA_CATALOG_PATH=$env:OPENATHENA_CATALOG_PATH"
Write-Host ""

# Clean any DuckDB cache files first to ensure fresh configuration
if (Test-Path "*.duckdb") {
    Remove-Item "*.duckdb"
    Write-Host "Removed old DuckDB cache files"
}
if (Test-Path "*.duckdb.wal") {
    Remove-Item "*.duckdb.wal"
    Write-Host "Removed old DuckDB WAL files"
}

# Run the S3 configuration helper script
Write-Host "Running S3 configuration script..."
python configure_s3.py

Write-Host "Starting OpenAthena server..."

# Start OpenAthena
python -m open_athena.api
