#!/bin/bash

# Eezy Peezy MCP Servers Stop Script
# Usage: ./scripts/stop-servers.sh [--all]

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

# Check command line arguments
STOP_ALL=false
if [ "$1" = "--all" ]; then
    STOP_ALL=true
fi

if [ "$STOP_ALL" = true ]; then
    print_status "Stopping all Eezy Peezy services..."
    
    # Stop all services
    docker-compose down
    
    print_success "All services stopped!"
else
    print_status "Stopping MCP servers..."
    
    # Stop only MCP services
    docker-compose stop \
        excel-mcp
    
    print_success "MCP servers stopped!"
    print_status "Main application services (if running) are still active."
    print_status "To stop all services, use: ./scripts/stop-servers.sh --all"
fi

# Show remaining running containers
print_status "Currently running containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(CONTAINER|eezy_peezy_)" || print_status "No Eezy Peezy containers running."
