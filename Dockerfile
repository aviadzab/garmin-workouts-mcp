# Use Python 3.10 slim image as base
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -e .

# Copy the application code
COPY garmin_workouts_mcp/ ./garmin_workouts_mcp/

# Create a non-root user for security
RUN useradd -m -u 1000 mcpuser && chown -R mcpuser:mcpuser /app
USER mcpuser

# Create directory for Garmin credentials
RUN mkdir -p /home/mcpuser/.garth

# Expose the port the app runs on
EXPOSE 3333
EXPOSE 3334

# Health check
# HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
#     CMD curl -f http://localhost:3333/mcp || exit 1

# Set default environment variables (can be overridden at runtime)
ENV GARTH_HOME=/home/mcpuser/.garth

# Run the application
CMD ["python", "-m", "garmin_workouts_mcp.main"]
