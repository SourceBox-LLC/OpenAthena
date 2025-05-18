# Set OpenS3 credentials
$env:AWS_ACCESS_KEY_ID = "admin"
$env:AWS_SECRET_ACCESS_KEY = "password" 
$env:S3_ENDPOINT = "http://localhost:8001"
$env:S3_USE_SSL = "false"

# Start OpenAthena server
python -m open_athena.api
