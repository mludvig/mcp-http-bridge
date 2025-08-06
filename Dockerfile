FROM python:3.12-slim

# Install Node.js for npx support and curl for health checks
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for Python package management
RUN pip install uv

# Create app directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

# Install Python dependencies
RUN uv sync

# Copy configuration file
COPY config.json ./

# Create non-root user
RUN groupadd -r mcp && useradd -m -g mcp -s /bin/false mcp
RUN chown -R mcp:mcp /app
USER mcp

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/mcp || exit 1

# Set Python path and run the server
# ENV PYTHONPATH=/app/src
CMD ["uv", "run", "mcp-wrapper", "config.json", "--host", "0.0.0.0"]
