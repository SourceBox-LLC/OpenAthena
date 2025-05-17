# query.ps1 - Easy command-line interface for OpenAthena
# Usage: .\query.ps1 -Query "SELECT * FROM sales_2025 LIMIT 10"

param (
    [Parameter(Position=0, ValueFromRemainingArguments=$true)]
    [string]$Query,
    
    [Parameter()]
    [string]$Server = "http://localhost:8000",
    
    [Parameter()]
    [ValidateSet("csv", "arrow")]
    [string]$Format = "csv",
    
    [Parameter()]
    [switch]$Help
)

# Show usage information
function Show-Usage {
    Write-Host "Usage: .\query.ps1 -Query `"SQL QUERY`" [-Server url] [-Format format]"
    Write-Host ""
    Write-Host "Parameters:"
    Write-Host "  -Query `"SQL QUERY`"   The SQL query to execute"
    Write-Host "  -Server url          Server URL (default: http://localhost:8000)"
    Write-Host "  -Format format       Output format: csv, arrow (default: csv)"
    Write-Host "  -Help                Show this help message"
    Write-Host ""
    Write-Host "Example:"
    Write-Host "  .\query.ps1 -Query `"SELECT * FROM sales_2025 LIMIT 10`""
    Write-Host "  .\query.ps1 -Query `"SELECT COUNT(*) FROM web_logs`" -Format arrow"
    exit 1
}

# Display help if requested or no query provided
if ($Help -or [string]::IsNullOrEmpty($Query)) {
    Show-Usage
}

# Execute query
try {
    $uri = "$Server/sql?format=$Format"
    
    if ($Format -eq "arrow") {
        # For Arrow format, pipe to DuckDB for display if available
        $response = Invoke-WebRequest -Uri $uri -Method Post -Body $Query -ContentType "text/plain" -ErrorAction Stop
        
        # Save the response to a temporary file
        $tempFile = [System.IO.Path]::GetTempFileName()
        [System.IO.File]::WriteAllBytes($tempFile, $response.Content)
        
        # Check if DuckDB is available
        $duckdbAvailable = $null -ne (Get-Command "duckdb" -ErrorAction SilentlyContinue)
        
        if ($duckdbAvailable) {
            # Use DuckDB to display the Arrow data
            duckdb -c "COPY (SELECT * FROM read_arrow_auto('$tempFile')) TO stdout (FORMAT CSV);"
        } else {
            Write-Host "Arrow format received, but DuckDB is not available to display it."
            Write-Host "Install DuckDB or use -Format csv for readable output."
        }
        
        # Clean up temp file
        Remove-Item -Path $tempFile -Force
    } else {
        # For CSV format, just display the output
        $response = Invoke-WebRequest -Uri $uri -Method Post -Body $Query -ContentType "text/plain" -ErrorAction Stop
        Write-Host $response.Content
    }
} catch {
    Write-Host "Error executing query: $_" -ForegroundColor Red
    Write-Host "Make sure the OpenAthena server is running at $Server" -ForegroundColor Red
}
