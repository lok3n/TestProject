.PHONY: help install dev-install lint test format check build up down logs clean

help:
	@echo "Available commands:"
	@echo "  install      - Install production dependencies"
	@echo "  dev-install  - Install development dependencies"
	@echo "  lint         - Run linting (flake8, mypy)"
	@echo "  test         - Run tests"
	@echo "  format       - Format code (black, isort)"
	@echo "  check        - Run all checks (lint + test)"
	@echo "  build        - Build Docker images"
	@echo "  up           - Start services with docker compose"
	@echo "  down         - Stop services"
	@echo "  logs         - Show docker compose logs"
	@echo "  clean        - Clean up Docker resources"

install:
	pip install -r requirements.txt

dev-install:
	pip install -r requirements.txt
	pip install black isort pytest-cov

lint:
	@echo "Running flake8..."
	flake8 src/ tests/
	@echo "Running mypy..."
	mypy src/

test:
	@echo "Running tests..."
	pytest tests/ -v

format:
	@echo "Running black..."
	black src/ tests/
	@echo "Running isort..."
	isort src/ tests/

check: lint test
	@echo "All checks passed!"

build:
	docker compose build

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

clean:
	docker compose down -v
	docker system prune -f
