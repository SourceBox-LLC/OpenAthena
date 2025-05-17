"""
API module for OpenAthena.

This module provides a FastAPI-based REST API for executing SQL queries against
the DuckDB database and managing the catalog.
"""

import os
import io
import json
from typing import Dict, List, Any, Optional

import pyarrow as pa
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from open_athena.database import DuckDBManager
from open_athena.catalog import get_catalog_tables, create_catalog_table
from open_athena import __version__


# Initialize FastAPI app
app = FastAPI(
    title="OpenAthena API",
    description="SQL analytics engine for OpenS3 powered by DuckDB",
    version=__version__
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global database manager instance
db_manager = None


def get_db() -> DuckDBManager:
    """Get or initialize the database manager."""
    global db_manager
    if db_manager is None:
        # Get configuration from environment or use defaults
        db_path = os.environ.get("OPENATHENA_DB_PATH")
        catalog_path = os.environ.get("OPENATHENA_CATALOG_PATH", "catalog.yml")
        threads = int(os.environ.get("OPENATHENA_THREADS", "4"))
        memory_limit = os.environ.get("OPENATHENA_MEMORY_LIMIT", "4GB")
        enable_caching = os.environ.get("OPENATHENA_ENABLE_CACHING", "true").lower() == "true"
        
        # Initialize database manager
        db_manager = DuckDBManager(
            database_path=db_path,
            catalog_path=catalog_path,
            threads=threads,
            memory_limit=memory_limit,
            enable_caching=enable_caching
        )
        
        # Configure S3 credentials from environment
        db_manager.configure_s3_credentials()
    
    return db_manager


@app.get("/", tags=["General"])
async def root() -> Dict[str, str]:
    """Root endpoint with basic API information."""
    return {
        "name": "OpenAthena API",
        "version": __version__,
        "description": "SQL analytics engine for OpenS3 powered by DuckDB"
    }


@app.post("/sql", tags=["Queries"])
async def execute_sql(
    request: Request,
    db: DuckDBManager = Depends(get_db),
    format: str = "arrow"
) -> Response:
    """
    Execute a SQL query and return the results.
    
    Args:
        request: FastAPI request object with SQL query in body
        db: DuckDB manager instance
        format: Output format (arrow or csv)
        
    Returns:
        Query results in specified format
    """
    # Get SQL from request body
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="SQL query not provided")
    
    sql = body.decode()
    
    try:
        # Execute query
        result = db.execute_query(sql)
        
        if format.lower() == "csv":
            # Return CSV
            csv_data = io.StringIO()
            result.to_csv(csv_data)
            return StreamingResponse(
                iter([csv_data.getvalue()]),
                media_type="text/csv"
            )
        else:
            # Return Arrow format (default)
            table = result.arrow()
            batch_reader = pa.RecordBatchReader.from_batches(
                table.schema, table.to_batches()
            )
            sink = io.BytesIO()
            with pa.ipc.new_stream(sink, batch_reader.schema) as writer:
                for batch in batch_reader:
                    writer.write_batch(batch)
            
            return StreamingResponse(
                io.BytesIO(sink.getvalue()),
                media_type="application/vnd.apache.arrow.stream"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tables", tags=["Catalog"])
async def list_tables(db: DuckDBManager = Depends(get_db)) -> Dict[str, Any]:
    """
    List all tables in the catalog.
    
    Args:
        db: DuckDB manager instance
        
    Returns:
        Dictionary of tables from the catalog
    """
    catalog_tables = get_catalog_tables(db.catalog_path)
    return {"tables": catalog_tables}


@app.post("/catalog/reload", tags=["Catalog"])
async def reload_catalog(db: DuckDBManager = Depends(get_db)) -> Dict[str, str]:
    """
    Reload the catalog configuration.
    
    Args:
        db: DuckDB manager instance
        
    Returns:
        Success message
    """
    db.reload_catalog()
    return {"status": "ok", "message": "Catalog reloaded successfully"}


@app.post("/catalog/tables", tags=["Catalog"])
async def add_table(
    table_name: str,
    bucket: str,
    prefix: str,
    file_format: str = "parquet",
    db: DuckDBManager = Depends(get_db)
) -> Dict[str, str]:
    """
    Add a new table to the catalog.
    
    Args:
        table_name: Name of the table to create
        bucket: S3 bucket name
        prefix: Prefix path within the bucket
        file_format: File format (parquet, csv, json)
        db: DuckDB manager instance
        
    Returns:
        Success message
    """
    try:
        create_catalog_table(
            db.catalog_path, 
            table_name, 
            bucket, 
            prefix, 
            file_format
        )
        db.reload_catalog()
        return {
            "status": "ok", 
            "message": f"Table '{table_name}' added to catalog"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", tags=["General"])
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


def start():
    """Start the API server using uvicorn."""
    import uvicorn
    port = int(os.environ.get("OPENATHENA_PORT", "8000"))
    host = os.environ.get("OPENATHENA_HOST", "0.0.0.0")
    uvicorn.run("open_athena.api:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    start()
