.PHONY: dev backend frontend seed test eval lint clean reset docker-up docker-down help

# ── Colors ───────────────────────────────────────────────────────────────────
BLUE  := \033[0;34m
GREEN := \033[0;32m
AMBER := \033[0;33m
RED   := \033[0;31m
NC    := \033[0m

# ── Paths ─────────────────────────────────────────────────────────────────────
BACKEND_DIR  := backend
FRONTEND_DIR := frontend

help: ## Show this help
	@echo ""
	@echo "  $(BLUE)Healthcare Triage Assistant — BPUT Hackathon 2026$(NC)"
	@echo "  $(AMBER)Educational prototype. Not a medical device.$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""

# ── Development ──────────────────────────────────────────────────────────────
dev: ## Start backend + frontend concurrently
	@echo "$(BLUE)Starting backend and frontend...$(NC)"
	@$(MAKE) -j2 backend frontend

backend: ## Start FastAPI backend on port 8000
	@echo "$(BLUE)Starting backend on http://localhost:8000$(NC)"
	@cd $(BACKEND_DIR) && \
		python -m uvicorn app.main:app --reload --port 8000 --host 0.0.0.0

frontend: ## Start Next.js frontend on port 3000
	@echo "$(BLUE)Starting frontend on http://localhost:3000$(NC)"
	@cd $(FRONTEND_DIR) && npm run dev

# ── Setup ─────────────────────────────────────────────────────────────────────
install: ## Install all dependencies
	@echo "$(BLUE)Installing backend dependencies...$(NC)"
	@cd $(BACKEND_DIR) && pip install -r requirements.txt
	@echo "$(BLUE)Installing frontend dependencies...$(NC)"
	@cd $(FRONTEND_DIR) && npm install

install-backend: ## Install only backend dependencies
	@cd $(BACKEND_DIR) && pip install -r requirements.txt

install-frontend: ## Install only frontend dependencies
	@cd $(FRONTEND_DIR) && npm install

# ── Database ──────────────────────────────────────────────────────────────────
seed: ## Load 25 synthetic patients and demo users into the database
	@echo "$(BLUE)Seeding database with synthetic data...$(NC)"
	@cd $(BACKEND_DIR) && python seed.py
	@echo "$(GREEN)Seed complete. 25 fictional patients loaded.$(NC)"

seed-reset: ## Reset database and re-seed
	@echo "$(AMBER)Resetting database...$(NC)"
	@cd $(BACKEND_DIR) && python seed.py --reset
	@echo "$(GREEN)Database reset and re-seeded.$(NC)"

migrate: ## Run database migrations (create tables)
	@cd $(BACKEND_DIR) && python -c "from app.core.database import init_db; init_db(); print('DB initialized')"

# ── Testing ───────────────────────────────────────────────────────────────────
test: ## Run all backend tests
	@echo "$(BLUE)Running tests...$(NC)"
	@cd $(BACKEND_DIR) && python -m pytest tests/ -v --tb=short

test-coverage: ## Run tests with coverage report
	@cd $(BACKEND_DIR) && python -m pytest tests/ -v --cov=app --cov-report=term-missing

# ── Evaluation ────────────────────────────────────────────────────────────────
eval: ## Run evaluation harness against all 25 synthetic patients
	@echo "$(BLUE)Running evaluation harness...$(NC)"
	@cd $(BACKEND_DIR) && python -m pytest tests/eval/ -v --tb=short -s
	@echo "$(GREEN)Evaluation complete. Check eval_report.md$(NC)"

# ── Code Quality ──────────────────────────────────────────────────────────────
lint: ## Lint backend (ruff) and frontend (eslint)
	@echo "$(BLUE)Linting backend...$(NC)"
	@cd $(BACKEND_DIR) && python -m ruff check app/ || true
	@echo "$(BLUE)Linting frontend...$(NC)"
	@cd $(FRONTEND_DIR) && npm run lint || true

format: ## Format backend code
	@cd $(BACKEND_DIR) && python -m ruff format app/ || true

# ── Docker ────────────────────────────────────────────────────────────────────
docker-up: ## Start with Docker Compose
	@docker compose up --build

docker-down: ## Stop Docker Compose
	@docker compose down

# ── Demo ──────────────────────────────────────────────────────────────────────
demo: seed ## Reset and seed demo data, then start dev
	@echo "$(GREEN)Demo ready! Open http://localhost:3000$(NC)"
	@echo "$(AMBER)Demo users: health_worker_1/demo123, nurse_1/demo123, doctor_1/demo123, admin_1/demo123$(NC)"
	@$(MAKE) dev

# ── Cleanup ───────────────────────────────────────────────────────────────────
clean: ## Remove generated files (DB, uploads, __pycache__)
	@echo "$(AMBER)Cleaning up...$(NC)"
	@rm -f $(BACKEND_DIR)/triage.db
	@rm -rf $(BACKEND_DIR)/uploads/*
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)Clean complete.$(NC)"

reset: clean seed ## Full reset: clean + re-seed
	@echo "$(GREEN)Full reset complete.$(NC)"

# ── Health Check ──────────────────────────────────────────────────────────────
check: ## Check backend health endpoint
	@curl -s http://localhost:8000/health | python -m json.tool || echo "Backend not running"
