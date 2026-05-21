# Docker Setup for MedAssist AI

## Development Environment

### Starting Services

```bash
# Copy and configure environment variables
cp .env.example .env

# Start all services
docker-compose -f docker-compose.dev.yml up -d
```

### Services

| Service | Port | URL |
|---------|------|-----|
| MedAssist API | 7000 | http://localhost:7000 |
| PostgreSQL | 5432 | localhost:5432 |
| Dozzle (Logs) | 9090 | http://localhost:9090 |
| Adminer (DB UI) | 8081 | http://localhost:8081 |

### Common Commands

```bash
# View logs
docker-compose -f docker-compose.dev.yml logs -f app

# Restart API
docker-compose -f docker-compose.dev.yml restart app

# Stop all services
docker-compose -f docker-compose.dev.yml down

# Rebuild after dependency changes
docker-compose -f docker-compose.dev.yml up -d --build
```

## Database Migrations

```bash
# Run migrations
docker-compose -f docker-compose.dev.yml exec app uv run alembic upgrade head

# Create new migration
docker-compose -f docker-compose.dev.yml exec app uv run alembic revision --autogenerate -m "description"
```
