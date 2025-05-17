#!/bin/bash
# query.sh - Easy command-line interface for OpenAthena
# Usage: ./query.sh "SELECT * FROM sales_2025 LIMIT 10"

# Default values
SERVER="http://localhost:8000"
FORMAT="csv"

# Show usage information
function show_usage {
  echo "Usage: ./query.sh [options] \"SQL QUERY\""
  echo ""
  echo "Options:"
  echo "  -s, --server URL    Server URL (default: http://localhost:8000)"
  echo "  -f, --format TYPE   Output format: csv, arrow (default: csv)"
  echo "  -h, --help          Show this help message"
  echo ""
  echo "Example:"
  echo "  ./query.sh \"SELECT * FROM sales_2025 LIMIT 10\""
  echo "  ./query.sh -f arrow \"SELECT COUNT(*) FROM web_logs\""
  exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -s|--server)
      SERVER="$2"
      shift 2
      ;;
    -f|--format)
      FORMAT="$2"
      shift 2
      ;;
    -h|--help)
      show_usage
      ;;
    *)
      QUERY="$1"
      shift
      ;;
  esac
done

# Check if query is provided
if [ -z "$QUERY" ]; then
  echo "Error: No SQL query provided."
  show_usage
fi

# Execute query
if [ "$FORMAT" == "arrow" ]; then
  # For Arrow format, pipe to DuckDB for display
  curl -s -X POST "$SERVER/sql?format=arrow" \
       --data "$QUERY" |
    duckdb -c "COPY (SELECT * FROM read_arrow_auto('/dev/stdin')) TO stdout (FORMAT CSV);"
else
  # For CSV format, just display the output
  curl -s -X POST "$SERVER/sql?format=csv" \
       --data "$QUERY"
fi
