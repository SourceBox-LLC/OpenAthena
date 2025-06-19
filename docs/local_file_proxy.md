# OpenAthena Local File Proxy for OpenS3 Integration

## Overview

The Local File Proxy is a temporary workaround solution to address compatibility issues between DuckDB v1.2.2's HTTP/S3 client and the OpenS3 server API. This document explains how the proxy works, why it's needed, and how to revert to direct S3 access once compatibility issues are resolved.

## Why the Proxy is Needed

1. **DuckDB/OpenS3 Compatibility Issue**: DuckDB v1.2.2's HTTP client and S3 protocol handler are not compatible with OpenS3's API responses. This causes I/O errors when attempting to query data directly from OpenS3 buckets.

2. **Error Symptoms**:
   - Empty query results when querying S3-backed tables
   - HTTP 403/404 errors in logs when DuckDB tries to access S3 files
   - S3 credential and endpoint warnings in OpenAthena logs
   - "URL needs to contain a bucket name" errors
   - I/O errors when trying to access OpenS3 via HTTP paths

## How the Local File Proxy Works

The proxy operates as follows:

1. When OpenAthena encounters a file path with a prefix like `s3://bucket-name/path/*` or an HTTP URL pointing to OpenS3, the proxy intercepts the request.
2. The proxy downloads the file(s) from OpenS3 to a local temporary directory.
3. For wildcard patterns (`*.csv`, `*.parquet`), the proxy:
   - Lists all objects in the bucket
   - Filters by file extension or matching pattern
   - Downloads matching files
4. The catalog paths are rewritten to point to these local temporary files for DuckDB to query.
5. For catalog metadata tables, the proxy:
   - Lists objects in the specified bucket with the given prefix
   - Downloads matching files based on format
   - Properly escapes Windows paths (especially those with apostrophes)

## Configuration Requirements

1. **Environment Variables**:
   - `OPENS3_ACCESS_KEY`: OpenS3 access key (usually "admin")
   - `OPENS3_SECRET_KEY`: OpenS3 secret key (usually "password")
   - `S3_ENDPOINT`: The endpoint URL for the OpenS3 server (e.g., `http://localhost:8001`)

   > **IMPORTANT**: Do not use AWS_* environment variables as they may conflict with OpenS3 integration

2. **Starting Services**:
   - Ensure OpenS3 is running before starting OpenAthena
   - Use the included PowerShell script `start-openathena.ps1` to set environment variables and start OpenAthena

## How to Revert to Direct S3 Access

When DuckDB compatibility with OpenS3 is resolved (either through DuckDB updates or OpenS3 API changes), you can revert to direct S3 access by:

1. Edit the `auto_discover.py` script to disable the proxy by setting `USE_LOCAL_FILE_PROXY = False`
2. Update catalog entries to use direct S3 URLs in the appropriate format
3. Ensure environment variables are still properly set for direct S3 access

## Limitations

1. **Performance**: Files must be downloaded before they can be queried, adding latency
2. **Storage**: Temporary local copies of files consume disk space
3. **Caching**: Downloaded files are cached but may become stale if OpenS3 content changes
4. **Wildcards**: Limited wildcard pattern matching support compared to DuckDB's built-in S3 client

## Troubleshooting

1. **No files found for wildcard pattern**: 
   - Verify the wildcard pattern matches actual files in the bucket
   - Check if files are at the bucket root instead of in subdirectories
   - Ensure OpenS3 server is running and accessible

2. **SQL syntax errors with file paths**:
   - Check for apostrophes in Windows usernames or paths
   - The proxy should double-escape apostrophes in SQL statements (`'` → `''`)
   - For direct SQL, you may need to double-escape backslashes as well

3. **Parser errors or catalog view creation failures**:
   - Ensure all environment variables are set correctly
   - Check that the OpenS3 server is running and accessible
   - For parquet files, make sure to use `read_parquet()` (not `read_parquet_auto()`)

4. **Proxy logging**:
   - Check proxy logs for debugging information about file paths and downloads
   - Enable verbose logging with the `DEBUG_PROXY` environment variable

5. **Environment variables**:
   - Confirm that OpenS3 credentials and endpoint are set correctly
   - Check that the values are being propagated to the OpenAthena server process
   - Restart the server after setting environment variables

---

*This workaround will be removed once direct OpenAthena to OpenS3 integration is fully functional. Future work should focus on ensuring DuckDB and OpenS3 API compatibility for direct querying.*
