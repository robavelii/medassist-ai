#!/bin/bash
# setup_repo.sh - Initialize git repo with sequential commit history
# Run this script from the medassist-ai directory
set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_DIR"

echo "Setting up MedAssist AI repository..."

# Initialize git
git init
echo "Initialized git repository."

# ============================================================
# Commit 1: Initial project scaffold
# ============================================================
git add pyproject.toml .python-version .gitignore .dockerignore .pre-commit-config.yaml
git commit -m "Initialize project scaffold with pyproject.toml and tooling config"

# ============================================================
# Commit 2: Docker and CI configuration
# ============================================================
git add Dockerfile docker-compose.dev.yml .github/
git commit -m "Add Dockerfile, docker-compose, and CI workflow"

# ============================================================
# Commit 3: Alembic database migrations
# ============================================================
git add alembic.ini alembic/
git commit -m "Add alembic configuration and database migrations"

# ============================================================
# Commit 4: Core application config and database layer
# ============================================================
git add src/__init__.py src/core/
git commit -m "Add core configuration, database layer, and DI container"

# ============================================================
# Commit 5: Data models
# ============================================================
git add src/models/
git commit -m "Add LLM cache model and clinical data models"

# ============================================================
# Commit 6: Security utilities
# ============================================================
git add src/utils/
git commit -m "Add prompt injection protection and security utilities"

# ============================================================
# Commit 7: LLM caching service
# ============================================================
git add src/services/__init__.py src/services/llm_caching_service.py
git commit -m "Add LLM response caching service with cost tracking"

# ============================================================
# Commit 8: Clinical prompt templates
# ============================================================
git add src/prompts/
git commit -m "Add clinical prompt templates for all modules"

# ============================================================
# Commit 9: Clinical assistant service
# ============================================================
git add src/services/clinical_assistant_service.py
git commit -m "Add clinical assistant service with all analysis methods"

# ============================================================
# Commit 10: Health check and auth endpoints
# ============================================================
git add src/api/__init__.py src/api/endpoints/__init__.py
git add src/api/endpoints/health.py src/api/endpoints/auth.py
git commit -m "Add health check and API key authentication endpoints"

# ============================================================
# Commit 11: Clinical analysis endpoints
# ============================================================
git add src/api/endpoints/clinical.py
git commit -m "Add clinical analysis endpoints for all modules"

# ============================================================
# Commit 12: Demo and capabilities endpoint
# ============================================================
git add src/api/endpoints/demo.py
git commit -m "Add demo endpoint with capabilities listing and sample data"

# ============================================================
# Commit 13: API route aggregation and application entry point
# ============================================================
git add src/api/routes.py src/main.py
git commit -m "Add API route aggregation and FastAPI application entry point"

# ============================================================
# Commit 14: Unit tests
# ============================================================
git add src/tests/
git commit -m "Add unit tests for clinical assistant and caching services"

# ============================================================
# Commit 15: Documentation and environment config
# ============================================================
git add README.md DOCKER_SETUP.md .env.example
git commit -m "Add project documentation and environment configuration"

echo ""
echo "Repository setup complete."
echo "Total commits: $(git log --oneline | wc -l)"
echo ""
git log --oneline
