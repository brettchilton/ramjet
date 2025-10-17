#!/bin/bash

# Eezy Peezy MCP Servers Test Script
# Usage: ./scripts/test-servers.sh

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

print_status "Testing Eezy Peezy MCP Servers..."
echo

# Test function for each server
test_server() {
    local name=$1
    local container=$2
    local port=$3
    
    print_status "Testing $name..."
    
    # Check if container is running
    if ! docker ps --format "{{.Names}}" | grep -q "^$container$"; then
        print_error "$name container is not running"
        return 1
    fi
    
    # Check if container is healthy
    container_status=$(docker ps --format "{{.Names}}\t{{.Status}}" | grep "$container" | awk '{print $2}')
    if [[ "$container_status" == *"Up"* ]]; then
        print_success "$name container is running ($container_status)"
    else
        print_error "$name container status: $container_status"
        return 1
    fi
    
    # Test port connectivity (if in SSE mode)
    if command -v nc >/dev/null 2>&1; then
        if nc -z localhost $port 2>/dev/null; then
            print_success "$name port $port is accessible"
        else
            print_warning "$name port $port is not accessible (may be in STDIO mode)"
        fi
    fi
    
    # Test basic container health
    if docker exec "$container" echo "Container health check" >/dev/null 2>&1; then
        print_success "$name container responds to commands"
    else
        print_error "$name container is not responding"
        return 1
    fi
    
    echo
    return 0
}

# Run tests for each MCP server
failed_tests=0

# Test Excel MCP
if ! test_server "Excel MCP" "eezy_peezy_excel_mcp" "9105"; then
    failed_tests=$((failed_tests + 1))
fi

# Summary
echo "========================================="
if [ $failed_tests -eq 0 ]; then
    print_success "All MCP servers passed basic health checks!"
    echo
    print_status "MCP Servers Status:"
    print_status "  ✓ Excel MCP:      http://localhost:9105"
    echo
    print_status "For detailed logs: docker-compose logs [service-name]"
    print_status "Example: docker-compose logs -f excel-mcp"
else
    print_error "$failed_tests out of 1 MCP servers failed health checks"
    print_status "Check individual server logs for more details:"
    print_status "docker-compose logs [service-name]"
    exit 1
fi

# Show current mode
if [ -f ".env" ]; then
    mode=$(grep "^MODE=" .env | cut -d'=' -f2)
    if [ -n "$mode" ]; then
        echo
        print_status "Current mode: $mode"
        if [ "$mode" = "stdio" ]; then
            print_status "STDIO mode: Optimized for MCP client communication"
        elif [ "$mode" = "sse" ]; then
            print_status "SSE mode: HTTP endpoints available for web access"
        fi
    fi
fi
