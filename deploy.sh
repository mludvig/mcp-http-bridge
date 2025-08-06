#!/bin/bash
# MCP Wrapper deployment and testing script.
#
# This script provides convenient commands for:
# - Installing dependencies
# - Running tests
# - Starting the development server
# - Building and running Docker containers

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Show help
show_help() {
    cat << EOF
MCP Wrapper - Deployment Script

Usage: $0 <command>

Commands:
    install     Install dependencies using uv
    test        Run the test suite
    dev         Start development server
    docker      Build and run Docker container
    docker-dev  Build and run Docker container with development config
    clean       Clean up build artifacts
    help        Show this help message

Examples:
    $0 install
    $0 test
    $0 dev --port 9000
    $0 docker

EOF
}

# Install dependencies
install_deps() {
    info "Installing dependencies with uv..."
    uv add fastmcp pydantic pytest pytest-asyncio
    info "Dependencies installed successfully"
}

# Run tests
run_tests() {
    info "Running test suite..."
    PYTHONPATH=src uv run pytest tests/ -v
    info "All tests passed!"
}

# Start development server
start_dev() {
    info "Starting development server..."
    PYTHONPATH=src uv run python -m mcp_wrapper.main config.json "$@"
}

# Build and run Docker
run_docker() {
    info "Building Docker image..."
    docker build -t mcp-wrapper .
    
    info "Starting Docker container..."
    docker run --rm -p 8000:8000 mcp-wrapper
}

# Build and run Docker with development setup
run_docker_dev() {
    info "Starting with docker-compose..."
    docker-compose up --build
}

# Clean up
clean() {
    info "Cleaning up..."
    rm -rf .pytest_cache/
    rm -rf src/mcp_wrapper/__pycache__/
    rm -rf tests/__pycache__/
    find . -name "*.pyc" -delete
    info "Cleanup completed"
}

# Check if uv is installed
check_uv() {
    if ! command -v uv &> /dev/null; then
        error "uv is not installed. Please install it first:"
        echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
}

# Main script logic
case "${1:-help}" in
    install)
        check_uv
        install_deps
        ;;
    test)
        check_uv
        run_tests
        ;;
    dev)
        check_uv
        shift
        start_dev "$@"
        ;;
    docker)
        run_docker
        ;;
    docker-dev)
        run_docker_dev
        ;;
    clean)
        clean
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
