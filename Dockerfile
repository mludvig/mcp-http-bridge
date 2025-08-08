FROM python:3.13-slim

# Install dependencies
RUN apt-get update
RUN apt-get install -y curl

# Install Node.js (includes npm / npx)
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs

# Install uv for Python package management
RUN pip install uv

# Create app directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

# Install Python dependencies
RUN uv sync

# Create non-root user
RUN groupadd -r mcp && useradd -m -g mcp -s /bin/false mcp
RUN chown -R mcp:mcp /app
USER mcp

# Expose port
EXPOSE 8000

# Run the server
CMD ["uv", "run", "mcp-http-bridge", "--config", "config.json", "--host", "0.0.0.0", "--port", "8000"]
