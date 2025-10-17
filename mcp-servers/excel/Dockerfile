# Excel MCP Server Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md ./
COPY src ./src

# Install package and dependencies
RUN pip install --upgrade pip \
    && pip install --no-cache-dir .

# Create directory for Excel files
RUN mkdir -p /app/excel_files

# Expose port for SSE mode
EXPOSE 9100

# Create entrypoint script for mode handling
RUN cat > /entrypoint.sh << 'EOF' && chmod +x /entrypoint.sh
#!/bin/bash
if [ "$MODE" = "sse" ]; then
    exec excel-mcp-server sse --port 9100
else
    exec excel-mcp-server stdio
fi
EOF

ENTRYPOINT ["/entrypoint.sh"] 