#!/bin/bash

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    set -a  # automatically export all variables
    source .env
    set +a
fi

#-----------------------------------------------------------------------------
# Global config.

# Build mode: up, image or local (default: up)
BUILD_MODE="up"

# Cloud images (only for backend)
CLOUD_BACKEND_IMAGE="theta-public-registry.cn-hangzhou.cr.aliyuncs.com/theta/mirobody-backend"

# Local images
BACKEND_IMAGE="mirobody-backend"
DATABASE_IMAGE="mirobody-db"

USED_PORTS="18080 6379 5432"

DOCKER_COMPOSE_FILE="docker/docker-compose.yaml"

#-----------------------------------------------------------------------------
# Parse command line arguments.

for arg in "$@"; do
    case $arg in
        --mode=*)
            BUILD_MODE="${arg#*=}"
            shift
            ;;
        --help)
            echo "Usage: ./deploy.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --mode=image    Pull pre-built backend image, build db locally"
            echo "  --mode=local    Build all images from official base images"
            echo "  --mode=up       Skip build, directly compose up (default)"
            echo "  --help          Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./deploy.sh                  # Skip build and start (default)"
            echo "  ./deploy.sh --mode=image     # Pull pre-built backend + pgvector db"
            echo "  ./deploy.sh --mode=local     # Ubuntu backend + pgvector db"
            echo "  ./deploy.sh --mode=up        # Skip build and start"
            echo ""
            echo "Note: Database always built from pgvector/pgvector:pg17"
            exit 0
            ;;
        *)
            echo "Unknown argument: $arg"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate build mode
if [[ "$BUILD_MODE" != "up" && "$BUILD_MODE" != "image" && "$BUILD_MODE" != "local" ]]; then
    echo "Error: BUILD_MODE must be 'up', 'image' or 'local', got: $BUILD_MODE"
    exit 1
fi

echo "=========================================="
echo "Build Mode: $BUILD_MODE"
echo "=========================================="

#-----------------------------------------------------------------------------
# Functions.

# stop_containers_by_ports {ports}
stop_containers_by_ports() {
    for port in $@; do
        results=($(docker ps | grep ":$port->"))
        if [ ${#results[@]} -gt 0 ]; then
            echo "docker container stop ${results[0]}"
            docker container stop ${results[0]}
        fi
    done
}

#-----------------------------------------------------------------------------
# Stop running containers.

stop_containers_by_ports $USED_PORTS

#-----------------------------------------------------------------------------
# Build or prepare images based on mode.

# Set Redis and MinIO images based on mode
if [[ "$BUILD_MODE" == "image" ]]; then
    export REDIS_IMAGE="theta-public-registry.cn-hangzhou.cr.aliyuncs.com/docker.io/redis:7.0"
    export MINIO_IMAGE="theta-public-registry.cn-hangzhou.cr.aliyuncs.com/docker.io/minio:latest"
else
    # Local and up mode use official images
    export REDIS_IMAGE="redis:7.0-alpine"
    export MINIO_IMAGE="minio/minio:latest"
fi

if [[ "$BUILD_MODE" == "up" ]]; then
    echo "=========================================="
    echo "Up Mode: Skip build, use existing images"
    echo "=========================================="
    
    echo "Using existing images:"
    echo "  - $BACKEND_IMAGE:latest"
    echo "  - $DATABASE_IMAGE:latest"
    
    # Check if images exist
    if ! docker image inspect $BACKEND_IMAGE:latest > /dev/null 2>&1; then
        echo "Error: Backend image $BACKEND_IMAGE:latest not found."
        echo "Please run with --mode=image or --mode=local first."
        exit 1
    fi
    
    if ! docker image inspect $DATABASE_IMAGE:latest > /dev/null 2>&1; then
        echo "Error: Database image $DATABASE_IMAGE:latest not found."
        echo "Please run with --mode=image or --mode=local first."
        exit 1
    fi

elif [[ "$BUILD_MODE" == "image" ]]; then
    echo "=========================================="
    echo "Image Mode: Pulling pre-built backend"
    echo "=========================================="
    
    # Backend: Pull cloud image and build with pip install
    echo "Pulling backend base image from cloud..."
    docker pull $CLOUD_BACKEND_IMAGE:latest
    
    echo "Building backend image with local requirements..."
    docker build -f docker/Dockerfile.backend.cloud -t $BACKEND_IMAGE:latest .
    
    # Database: Always build from pgvector base (unified with local mode)
    echo "Building database image from pgvector base..."
    docker build -f docker/Dockerfile.postgres -t $DATABASE_IMAGE:latest .

else
    echo "=========================================="
    echo "Local Mode: Building images from scratch"
    echo "=========================================="
    
    # Backend: Build from Ubuntu base
    echo "Building backend image from Ubuntu base..."
    docker build -f docker/Dockerfile.backend -t $BACKEND_IMAGE:latest .
    
    # Database: Build from pgvector base
    echo "Building database image from pgvector base..."
    docker build -f docker/Dockerfile.postgres -t $DATABASE_IMAGE:latest .
fi

#-----------------------------------------------------------------------------
# Docker compose.

docker compose -f $DOCKER_COMPOSE_FILE down
docker compose -f $DOCKER_COMPOSE_FILE up -d --remove-orphans
docker compose -f $DOCKER_COMPOSE_FILE logs -f


