# MedAssist AI

Clinical decision support platform for healthcare professionals. Built with FastAPI, OpenAI, and PostgreSQL.

## Features

- **10 Clinical Modules**: Triage, diagnosis, medication management, lab interpretation, radiology interpretation, inpatient monitoring, visit summaries, patient education
- **Context-Aware Chat**: Conversational interface with full medical history integration
- **Response Caching**: SHA-256 keyed response cache with cost tracking in PostgreSQL
- **Prompt Injection Protection**: Pattern-based detection and input sanitization
- **Cost Estimation**: Per-endpoint and aggregate cost projections across multiple models
- **API Key Authentication**: Configurable API key validation with development mode bypass

## Technology Stack

- **Python 3.13** with FastAPI 0.115+
- **OpenAI GPT-4o** for clinical analysis
- **PostgreSQL 15** with SQLAlchemy ORM
- **Alembic** for database migrations
- **Docker** with development and production configurations
- **uv** for dependency management

## Project Structure

```
medassist-ai/
├── src/
│   ├── main.py                 # FastAPI application entry point
│   ├── api/
│   │   ├── routes.py           # API router aggregation
│   │   └── endpoints/
│   │       ├── health.py       # Health check with uptime/version
│   │       ├── auth.py         # API key authentication
│   │       ├── clinical.py     # All clinical analysis endpoints
│   │       └── demo.py         # Showcase and capabilities listing
│   ├── core/
│   │   ├── config.py           # Application configuration
│   │   ├── container.py        # Dependency injection container
│   │   └── database.py         # Database connection management
│   ├── services/
│   │   ├── clinical_assistant_service.py  # Core clinical logic
│   │   └── llm_caching_service.py         # LLM response caching
│   ├── models/
│   │   ├── clinical_models.py  # Pydantic request/response models
│   │   └── llm_cache_model.py  # SQLAlchemy cache table model
│   ├── prompts/                # YAML prompt configurations (12 files)
│   ├── utils/
│   │   └── llm_security.py     # Prompt injection protection
│   └── tests/                  # Unit tests
├── alembic/                    # Database migrations
├── Dockerfile
├── docker-compose.dev.yml
└── pyproject.toml
```

## Quick Start

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) package manager
- OpenAI API key
- Docker & Docker Compose (optional)

### Local Development

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd medassist-ai
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key
   ```

4. **Run the application**:
   ```bash
   uv run uvicorn src.main:app --host 0.0.0.0 --port 7000 --reload
   ```

5. **Access the application**:
   - API Documentation: http://localhost:7000/docs
   - Health Check: http://localhost:7000/api/v1/health
   - Platform Capabilities: http://localhost:7000/api/v1/demo/capabilities

### Docker Development

```bash
cp .env.example .env
# Edit .env with your configuration
docker-compose -f docker-compose.dev.yml up -d
```

See [DOCKER_SETUP.md](DOCKER_SETUP.md) for detailed Docker instructions.

## API Endpoints

### Health & Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Service health check with uptime |
| POST | `/api/v1/auth/validate` | Validate API key |

### Clinical Modules
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/clinical/triage-cold-cases` | Cold case triage analysis |
| POST | `/api/v1/clinical/emergency-triage` | Emergency triage with color codes |
| POST | `/api/v1/clinical/outpatient-hpe` | History & physical exam analysis |
| POST | `/api/v1/clinical/lab-interpretation` | Lab result interpretation |
| POST | `/api/v1/clinical/radiology-interpretation` | Radiology image interpretation |
| POST | `/api/v1/clinical/diagnosis` | Ranked differential diagnosis |
| POST | `/api/v1/clinical/medication` | Medication management with safety checks |
| POST | `/api/v1/clinical/inpatient` | Inpatient monitoring guidance |
| POST | `/api/v1/clinical/visit-summary` | Visit summary generation |
| POST | `/api/v1/clinical/patient-education` | Patient education materials |
| POST | `/api/v1/clinical/chat` | Context-aware clinical chat |
| POST | `/api/v1/clinical/cost-estimation` | Cost estimation across models |

### Demo
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/demo/capabilities` | List all platform capabilities |
| GET | `/api/v1/demo/sample-request` | Sample request payload for testing |

## Security

- **API Key Authentication**: Configurable via `API_KEY_SECRET` environment variable
- **Prompt Injection Protection**: Pattern-based detection with input sanitization
- **Input Validation**: All inputs validated through Pydantic models
- **Rate Limiting**: Exponential backoff for external API calls
- **Non-Root Container**: Docker containers run as non-root user

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `API_KEY_SECRET` | API key for authentication | - |
| `DATABASE_URI` | PostgreSQL connection string | `sqlite:///./db.sqlite3` |
| `CORS_ALLOWED_ORIGINS` | CORS allowed origins | `*` |
| `DEFAULT_LOCALE` | Default patient locale | - |

## Development

```bash
# Format code
uv run black .
uv run isort .

# Lint
uv run ruff check .

# Run tests
uv run pytest src/tests/ -v
```

## Production Deployment

```bash
docker build -t medassist-ai .
docker run -d \
  -p 7000:7000 \
  -e OPENAI_API_KEY=your_key \
  -e API_KEY_SECRET=your_secret \
  -e DATABASE_URI=your_db_url \
  --name medassist-ai \
  medassist-ai
```
