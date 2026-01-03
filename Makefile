.PHONY: help build dev prod stop clean logs shell test lint format network

# Docker configuration
IMAGE_NAME = ogna-project-management
CONTAINER_NAME = ogna-project-management-container
NETWORK_NAME = ogna-project-management-network
VOLUME_NAME = ogna-project-management-logs

# Default target
help:
	@echo "Available commands:"
	@echo ""
	@echo "Local Development:"
	@echo "  run          - Run server locally (no Docker)"
	@echo "  install      - Install dependencies locally"
	@echo "  test-local   - Run tests locally"
	@echo "  lint-local   - Run linting locally"
	@echo "  format-local - Format code locally"
	@echo ""
	@echo "Docker Development:"
	@echo "  build        - Build Docker image for development"
	@echo "  build-prod   - Build Docker image for production"
	@echo "  dev          - Run development container"
	@echo "  prod         - Run production container"
	@echo "  stop         - Stop and remove container"
	@echo "  logs         - Show container logs"
	@echo "  shell        - Access container shell"
	@echo "  test         - Run tests in container"
	@echo "  lint         - Run linting in container"
	@echo "  format       - Format code in container"
	@echo "  network      - Create Docker network"
	@echo "  clean        - Clean up containers, images, and volumes"
	@echo "  status       - Show container status"

# Local development commands
run:
	@echo "Starting FastAPI server locally..."
	@echo "Make sure you have installed dependencies: make install"
	@echo "Server will be available at http://localhost:8000"
	@echo "API docs at http://localhost:8000/docs"
	@echo ""
	uvicorn main:app --host 0.0.0.0 --port 8100 --reload

# Build targets
build:
	@echo "Building development image..."
	docker build --target development -t $(IMAGE_NAME):dev .

build-prod:
	@echo "Building production image..."
	docker build --target production -t $(IMAGE_NAME):prod .

# Network setup
network:
	@echo "Creating Docker network..."
	@docker network create $(NETWORK_NAME) 2>/dev/null || echo "Network $(NETWORK_NAME) already exists"

# Development container
dev: network build
	@echo "Starting development container..."
	@docker stop $(CONTAINER_NAME)-dev 2>/dev/null || true
	@docker rm $(CONTAINER_NAME)-dev 2>/dev/null || true
	docker run -d \
		--name $(CONTAINER_NAME)-dev \
		--network $(NETWORK_NAME) \
		-p 8000:8000 \
		-v $(PWD):/app \
		-v $(VOLUME_NAME):/app/logs \
		--env-file .env \
		$(IMAGE_NAME):dev
	@echo "Development container started on http://localhost:8000"
	@echo "API docs available at http://localhost:8000/docs"

# Production container
prod: network build-prod
	@echo "Starting production container..."
	@docker stop $(CONTAINER_NAME)-prod 2>/dev/null || true
	@docker rm $(CONTAINER_NAME)-prod 2>/dev/null || true
	docker run -d \
		--name $(CONTAINER_NAME)-prod \
		--network $(NETWORK_NAME) \
		-p 8000:8000 \
		-v $(VOLUME_NAME):/app/logs \
		--env-file .env.prod \
		--restart unless-stopped \
		--memory 512m \
		--cpus 0.5 \
		$(IMAGE_NAME):prod
	@echo "Production container started on http://localhost:8000"

# Container management
stop:
	@echo "Stopping containers..."
	@docker stop $(CONTAINER_NAME)-dev 2>/dev/null || true
	@docker stop $(CONTAINER_NAME)-prod 2>/dev/null || true
	@docker rm $(CONTAINER_NAME)-dev 2>/dev/null || true
	@docker rm $(CONTAINER_NAME)-prod 2>/dev/null || true

logs:
	@echo "Showing container logs..."
	@docker logs -f $(CONTAINER_NAME)-dev 2>/dev/null || docker logs -f $(CONTAINER_NAME)-prod 2>/dev/null || echo "No running containers found"

shell:
	@echo "Accessing container shell..."
	@docker exec -it $(CONTAINER_NAME)-dev /bin/bash 2>/dev/null || docker exec -it $(CONTAINER_NAME)-prod /bin/bash 2>/dev/null || echo "No running containers found"

status:
	@echo "Container status:"
	@docker ps -a --filter name=$(CONTAINER_NAME)

# Development tools
test:
	@echo "Running tests..."
	@docker exec $(CONTAINER_NAME)-dev pytest 2>/dev/null || echo "Development container not running. Start with 'make dev'"

lint:
	@echo "Running linting..."
	@docker exec $(CONTAINER_NAME)-dev flake8 app/ 2>/dev/null || echo "Development container not running. Start with 'make dev'"
	@docker exec $(CONTAINER_NAME)-dev mypy app/ 2>/dev/null || echo "Development container not running. Start with 'make dev'"

format:
	@echo "Formatting code..."
	@docker exec $(CONTAINER_NAME)-dev black app/ 2>/dev/null || echo "Development container not running. Start with 'make dev'"
	@docker exec $(CONTAINER_NAME)-dev isort app/ 2>/dev/null || echo "Development container not running. Start with 'make dev'"

# Cleanup
clean: stop
	@echo "Cleaning up Docker resources..."
	@docker rmi $(IMAGE_NAME):dev 2>/dev/null || true
	@docker rmi $(IMAGE_NAME):prod 2>/dev/null || true
	@docker volume rm $(VOLUME_NAME) 2>/dev/null || true
	@docker network rm $(NETWORK_NAME) 2>/dev/null || true
	@docker system prune -f
	@echo "Cleanup completed"

# Quick development restart
restart-dev: stop dev

# Quick production restart
restart-prod: stop prod