#!/bin/bash

# Eezy Peezy MCP Servers Startup Script
# Usage: ./scripts/start-servers.sh [mode]
# Mode: stdio (default) or sse

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found!"
    print_status "Please copy .env.example to .env and configure your API keys:"
    print_status "cp .env.example .env"
    exit 1
fi

# Get mode from command line argument (default: stdio)
MODE=${1:-stdio}

# Validate mode
if [ "$MODE" != "stdio" ] && [ "$MODE" != "sse" ]; then
    print_error "Invalid mode: $MODE"
    print_status "Valid modes: stdio, sse"
    exit 1
fi

print_status "Starting Eezy Peezy MCP Servers in $MODE mode..."

# Export environment variables
export MODE=$MODE

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# No external API keys required for Excel MCP
print_status "No external API keys required for Excel MCP."

# Start the MCP servers
print_status "Starting MCP server containers..."

# Start only the Excel MCP service
docker-compose up -d \
    excel-mcp

# Wait a moment for containers to initialize
sleep 3

# Check container status
print_status "Checking container status..."

containers=("eezy_peezy_excel_mcp")
all_running=true

for container in "${containers[@]}"; do
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$container"; then
        status=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep "$container" | awk '{print $2}')
        print_success "$container: $status"
    else
        print_error "$container: Not running"
        all_running=false
    fi
done

if [ "$all_running" = true ]; then
    print_success "All MCP servers started successfully!"
    echo
    print_status "MCP Servers are running on the following ports:"
    print_status "  • Excel MCP:      http://localhost:9105"
    echo
    print_status "Mode: $MODE"
    if [ "$MODE" = "stdio" ]; then
        print_status "STDIO mode: Use with MCP clients that support direct process communication"
    else
        print_status "SSE mode: HTTP endpoints available for web applications"
    fi
    echo
    print_status "To view logs: docker-compose logs -f [service-name]"
    print_status "To stop servers: ./scripts/stop-servers.sh"
else
    print_error "Some MCP servers failed to start. Check logs with:"
    print_status "docker-compose logs"
fi
