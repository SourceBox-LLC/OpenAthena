FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install testing dependencies
RUN pip install --no-cache-dir pytest requests

# Copy OpenAthena code
COPY . .

# Make health check script executable
RUN chmod +x /app/docker-healthcheck.sh

# Install OpenAthena
RUN pip install -e .

# Default environment variables
ENV OPENATHENA_HOST=0.0.0.0
ENV OPENATHENA_PORT=8000
ENV OPENATHENA_CATALOG_PATH=catalog.yml

# Configure Docker health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /app/docker-healthcheck.sh

# Expose port
EXPOSE 8000

# Command to run the server
CMD ["python", "-m", "open_athena.api"]
