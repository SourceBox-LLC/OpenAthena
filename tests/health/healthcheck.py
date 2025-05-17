"""
OpenAthena Health Check Utilities

This module provides functions to check the health and status of an OpenAthena instance.
Can be run as a standalone script or imported into other modules.
"""

import os
import sys
import json
import time
import argparse
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Add the project root to the path so we can import modules when running as script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class HealthCheckResult:
    """Class to hold health check results."""
    
    def __init__(self, name: str):
        self.name = name
        self.status = "unknown"
        self.message = ""
        self.timestamp = datetime.now().isoformat()
        self.details = {}
        self.duration_ms = 0
    
    def set_status(self, status: str, message: str, details: Optional[Dict] = None):
        """Set the status, message, and optional details."""
        self.status = status
        self.message = message
        if details:
            self.details = details
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "timestamp": self.timestamp,
            "details": self.details,
            "duration_ms": self.duration_ms
        }


class OpenAthenaHealthChecker:
    """
    Class to perform health checks on an OpenAthena instance.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
    
    def check_api_health(self) -> HealthCheckResult:
        """
        Check if the API is responsive by calling the health endpoint.
        """
        result = HealthCheckResult("api_health")
        start_time = time.time()
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            end_time = time.time()
            result.duration_ms = int((end_time - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok":
                    result.set_status("healthy", "API is responding correctly", data)
                else:
                    result.set_status("degraded", f"API reported non-healthy status: {data.get('status')}", data)
            else:
                result.set_status("unhealthy", f"API returned status code: {response.status_code}", 
                                 {"status_code": response.status_code})
        
        except requests.exceptions.ConnectionError:
            end_time = time.time()
            result.duration_ms = int((end_time - start_time) * 1000)
            result.set_status("unhealthy", "Failed to connect to API", 
                             {"error": "ConnectionError"})
        
        except Exception as e:
            end_time = time.time()
            result.duration_ms = int((end_time - start_time) * 1000)
            result.set_status("unhealthy", f"Exception occurred: {str(e)}", 
                             {"error": str(e), "type": type(e).__name__})
        
        self.results.append(result)
        return result
    
    def check_tables_availability(self) -> HealthCheckResult:
        """
        Check if tables are available by calling the tables endpoint.
        """
        result = HealthCheckResult("tables_availability")
        start_time = time.time()
        
        try:
            response = requests.get(f"{self.base_url}/tables", timeout=5)
            end_time = time.time()
            result.duration_ms = int((end_time - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                if "tables" in data and data["tables"]:
                    table_count = len(data["tables"])
                    result.set_status("healthy", f"Found {table_count} tables", 
                                     {"table_count": table_count, "tables": list(data["tables"].keys())})
                else:
                    result.set_status("degraded", "No tables available", data)
            else:
                result.set_status("unhealthy", f"Tables endpoint returned status code: {response.status_code}", 
                                 {"status_code": response.status_code})
        
        except Exception as e:
            end_time = time.time()
            result.duration_ms = int((end_time - start_time) * 1000)
            result.set_status("unhealthy", f"Exception occurred: {str(e)}", 
                             {"error": str(e), "type": type(e).__name__})
        
        self.results.append(result)
        return result
    
    def check_query_execution(self) -> HealthCheckResult:
        """
        Check if query execution is working by running a simple query.
        """
        result = HealthCheckResult("query_execution")
        start_time = time.time()
        
        try:
            # Try to run a simple query against system tables
            query = "SELECT 1 as health_check"
            response = requests.post(
                f"{self.base_url}/sql",
                data=query,
                headers={"Content-Type": "text/plain"},
                timeout=10
            )
            end_time = time.time()
            result.duration_ms = int((end_time - start_time) * 1000)
            
            if response.status_code == 200:
                result.set_status("healthy", "Query execution successful", 
                                 {"query": query, "response_time_ms": result.duration_ms})
            else:
                result.set_status("unhealthy", f"Query execution failed with status code: {response.status_code}", 
                                 {"status_code": response.status_code})
        
        except Exception as e:
            end_time = time.time()
            result.duration_ms = int((end_time - start_time) * 1000)
            result.set_status("unhealthy", f"Exception occurred: {str(e)}", 
                             {"error": str(e), "type": type(e).__name__})
        
        self.results.append(result)
        return result
    
    def run_all_checks(self) -> List[HealthCheckResult]:
        """
        Run all health checks and return results.
        """
        self.results = []
        self.check_api_health()
        self.check_tables_availability()
        self.check_query_execution()
        return self.results
    
    def get_overall_status(self) -> Tuple[str, str]:
        """
        Get the overall status based on all check results.
        Returns a tuple of (status, message)
        """
        if not self.results:
            return "unknown", "No health checks have been run"
        
        statuses = [result.status for result in self.results]
        
        if all(status == "healthy" for status in statuses):
            return "healthy", "All systems operational"
        elif any(status == "unhealthy" for status in statuses):
            return "unhealthy", "One or more critical checks failed"
        elif any(status == "degraded" for status in statuses):
            return "degraded", "System is operational but some checks indicate issues"
        else:
            return "unknown", "System status could not be determined"
    
    def print_results(self, json_format: bool = False):
        """
        Print the results of the health checks.
        """
        overall_status, overall_message = self.get_overall_status()
        
        if json_format:
            output = {
                "timestamp": datetime.now().isoformat(),
                "overall_status": overall_status,
                "overall_message": overall_message,
                "checks": [result.to_dict() for result in self.results]
            }
            print(json.dumps(output, indent=2))
        else:
            print(f"OpenAthena Health Check - {datetime.now().isoformat()}")
            print(f"Status: {overall_status.upper()} - {overall_message}")
            print("\nIndividual Checks:")
            
            for result in self.results:
                status_display = {
                    "healthy": "✅ HEALTHY",
                    "degraded": "⚠️ DEGRADED",
                    "unhealthy": "❌ UNHEALTHY",
                    "unknown": "❓ UNKNOWN"
                }.get(result.status, result.status.upper())
                
                print(f"\n[{status_display}] {result.name}")
                print(f"  Message: {result.message}")
                print(f"  Duration: {result.duration_ms}ms")
                
                if result.details:
                    print("  Details:")
                    for key, value in result.details.items():
                        if isinstance(value, (list, dict)):
                            print(f"    {key}: {json.dumps(value)}")
                        else:
                            print(f"    {key}: {value}")


def main():
    """
    Main function when running as a script.
    """
    parser = argparse.ArgumentParser(description="OpenAthena Health Check Tool")
    parser.add_argument("--url", default="http://localhost:8000", help="URL of the OpenAthena server")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--check", choices=["api", "tables", "query", "all"], default="all",
                        help="Specific check to run (default: all)")
    
    args = parser.parse_args()
    
    checker = OpenAthenaHealthChecker(args.url)
    
    if args.check == "api":
        checker.check_api_health()
    elif args.check == "tables":
        checker.check_tables_availability()
    elif args.check == "query":
        checker.check_query_execution()
    else:  # all
        checker.run_all_checks()
    
    checker.print_results(json_format=args.json)
    
    # Return exit code based on overall status
    overall_status, _ = checker.get_overall_status()
    sys.exit(0 if overall_status == "healthy" else 1)


if __name__ == "__main__":
    main()
