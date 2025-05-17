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

# Copy OpenAthena code
COPY . .

# Install OpenAthena
RUN pip install -e .

# Default environment variables
ENV OPENATHENA_HOST=0.0.0.0
ENV OPENATHENA_PORT=8000
ENV OPENATHENA_CATALOG_PATH=catalog.yml

# Expose port
EXPOSE 8000

# Command to run the server
CMD ["python", "-m", "open_athena.api"]
