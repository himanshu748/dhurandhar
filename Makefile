.DEFAULT_GOAL := help

.PHONY: help setup install demo dev dev-backend dev-frontend test lint build docker up down logs clean

help: ## Show available targets
	@awk 'BEGIN {FS = ":.*## "; printf "Dhurandhar targets:\n\n"} /^[a-zA-Z_-]+:.*## / {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Create a local .env from safe sample defaults
	@test -f .env || cp .env.example .env
	@echo "Local configuration is ready in .env (sample/read-only by default)."

install: ## Install backend and frontend dependencies
	python -m pip install -r backend/requirements.txt
	cd frontend && npm ci

demo: setup ## Run the deterministic, offline demo
	DHURANDHAR_RUNTIME=deterministic DHURANDHAR_SEED_DEMO=true docker compose up --build

dev: ## Start the production-shaped local stack
	docker compose up --build

dev-backend: ## Start FastAPI with reload
	uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload

dev-frontend: ## Start the Vite development server
	cd frontend && npm run dev -- --host 0.0.0.0

test: ## Run backend and frontend tests
	cd backend && pytest -q
	cd frontend && npm run test --if-present -- --run

lint: ## Run available backend and frontend static checks
	python -m compileall -q backend/app
	@if command -v ruff >/dev/null 2>&1; then ruff check backend; else echo "ruff not installed; skipped"; fi
	cd frontend && npm run lint --if-present

build: ## Build the production frontend
	cd frontend && npm run build

docker: ## Build the production container
	docker build --tag dhurandhar:local .

up: setup ## Start Dhurandhar in the background
	docker compose up --build --detach
	@echo "Dhurandhar: http://localhost:$${APP_PORT:-8000}"

down: ## Stop the local stack
	docker compose down

logs: ## Follow application logs
	docker compose logs --follow app

clean: ## Remove generated local build and test artifacts (not Docker volumes)
	rm -rf frontend/dist frontend/.vite .pytest_cache .ruff_cache htmlcov
