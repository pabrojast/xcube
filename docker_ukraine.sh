#!/bin/bash

# ==============================================================================
# Build and Run Script for Ukraine LWQ xcube Service Docker Container
# ==============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="xcube-ukraine-lwq"
IMAGE_TAG="latest"
CONTAINER_NAME="xcube-ukraine-service"
PORT=8080

echo -e "${BLUE}=========================================="
echo "Ukraine LWQ xcube Service - Docker"
echo -e "==========================================${NC}"
echo ""

# Function to print colored messages
print_info() {
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

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Parse command line arguments
COMMAND=${1:-help}

case $COMMAND in
    build)
        print_info "Building Docker image: ${IMAGE_NAME}:${IMAGE_TAG}"
        docker build \
            -f Dockerfile.ukraine \
            -t ${IMAGE_NAME}:${IMAGE_TAG} \
            --progress=plain \
            .
        
        if [ $? -eq 0 ]; then
            print_success "Docker image built successfully!"
            docker images | grep ${IMAGE_NAME}
        else
            print_error "Docker build failed!"
            exit 1
        fi
        ;;
    
    run)
        print_info "Starting container: ${CONTAINER_NAME}"
        
        # Stop and remove existing container if it exists
        if docker ps -a | grep -q ${CONTAINER_NAME}; then
            print_warning "Stopping existing container..."
            docker stop ${CONTAINER_NAME} 2>/dev/null || true
            docker rm ${CONTAINER_NAME} 2>/dev/null || true
        fi
        
        # Run container
        docker run -d \
            --name ${CONTAINER_NAME} \
            -p ${PORT}:8080 \
            -e AZURE_STORAGE_ACCOUNT_NAME="ihpwinsdata" \
            -e AZURE_STORAGE_ACCOUNT_KEY="<AZURE_STORAGE_ACCOUNT_KEY>" \
            --restart unless-stopped \
            ${IMAGE_NAME}:${IMAGE_TAG}
        
        if [ $? -eq 0 ]; then
            print_success "Container started successfully!"
            echo ""
            print_info "Service URLs:"
            echo "  - Main API: http://localhost:${PORT}"
            echo "  - Datasets: http://localhost:${PORT}/datasets"
            echo "  - WMTS Capabilities: http://localhost:${PORT}/wmts/1.0.0/WMTSCapabilities.xml"
            echo "  - API Documentation: http://localhost:${PORT}/openapi.html"
            echo ""
            print_info "To view logs: ./docker_ukraine.sh logs"
            print_info "To stop: ./docker_ukraine.sh stop"
        else
            print_error "Failed to start container!"
            exit 1
        fi
        ;;
    
    start)
        if docker ps -a | grep -q ${CONTAINER_NAME}; then
            print_info "Starting container: ${CONTAINER_NAME}"
            docker start ${CONTAINER_NAME}
            print_success "Container started!"
        else
            print_error "Container ${CONTAINER_NAME} does not exist. Run: ./docker_ukraine.sh run"
            exit 1
        fi
        ;;
    
    stop)
        print_info "Stopping container: ${CONTAINER_NAME}"
        docker stop ${CONTAINER_NAME}
        print_success "Container stopped!"
        ;;
    
    restart)
        print_info "Restarting container: ${CONTAINER_NAME}"
        docker restart ${CONTAINER_NAME}
        print_success "Container restarted!"
        ;;
    
    logs)
        print_info "Showing logs for: ${CONTAINER_NAME}"
        docker logs -f ${CONTAINER_NAME}
        ;;
    
    exec)
        print_info "Opening shell in container: ${CONTAINER_NAME}"
        docker exec -it ${CONTAINER_NAME} /bin/bash
        ;;
    
    status)
        print_info "Container status:"
        docker ps -a | grep ${CONTAINER_NAME} || echo "Container not found"
        echo ""
        print_info "Recent logs:"
        docker logs --tail 20 ${CONTAINER_NAME} 2>&1 || echo "No logs available"
        ;;
    
    clean)
        print_warning "Stopping and removing container..."
        docker stop ${CONTAINER_NAME} 2>/dev/null || true
        docker rm ${CONTAINER_NAME} 2>/dev/null || true
        print_success "Container removed!"
        ;;
    
    clean-all)
        print_warning "Stopping and removing container and image..."
        docker stop ${CONTAINER_NAME} 2>/dev/null || true
        docker rm ${CONTAINER_NAME} 2>/dev/null || true
        docker rmi ${IMAGE_NAME}:${IMAGE_TAG} 2>/dev/null || true
        print_success "Container and image removed!"
        ;;
    
    test)
        print_info "Testing service endpoints..."
        echo ""
        
        # Wait for service to be ready
        print_info "Waiting for service to start..."
        for i in {1..30}; do
            if curl -s http://localhost:${PORT}/datasets > /dev/null 2>&1; then
                print_success "Service is ready!"
                break
            fi
            echo -n "."
            sleep 1
        done
        echo ""
        
        # Test endpoints
        print_info "Testing /datasets endpoint..."
        curl -s http://localhost:${PORT}/datasets | jq '.' || print_error "Failed"
        
        echo ""
        print_info "Testing dataset metadata..."
        curl -s http://localhost:${PORT}/datasets/ukraine_lwq | jq '.id, .title, .bbox' || print_error "Failed"
        
        echo ""
        print_info "Testing timeseries endpoint..."
        curl -s -X POST "http://localhost:${PORT}/timeseries/ukraine_lwq/turbidity_mean" \
            -H "Content-Type: application/json" \
            -d '{"type":"Point","coordinates":[30.52,50.45]}' | jq '.result[0:3]' || print_error "Failed"
        
        print_success "All tests passed!"
        ;;
    
    help|*)
        echo "Usage: ./docker_ukraine.sh [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  build       - Build the Docker image"
        echo "  run         - Run the container (stops existing one)"
        echo "  start       - Start stopped container"
        echo "  stop        - Stop running container"
        echo "  restart     - Restart container"
        echo "  logs        - View container logs (follow mode)"
        echo "  exec        - Open shell in running container"
        echo "  status      - Show container status and recent logs"
        echo "  test        - Test service endpoints"
        echo "  clean       - Stop and remove container"
        echo "  clean-all   - Stop and remove container and image"
        echo "  help        - Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./docker_ukraine.sh build     # Build image"
        echo "  ./docker_ukraine.sh run       # Start service"
        echo "  ./docker_ukraine.sh logs      # View logs"
        echo "  ./docker_ukraine.sh test      # Test endpoints"
        echo ""
        ;;
esac
