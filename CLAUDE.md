# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Environment Setup

**Python Environment:**
- Uses Python 3.13 with Pipenv for dependency management
- Install dependencies: `pipenv install`
- Activate environment: `pipenv shell`
- Install dev dependencies: `pipenv install --dev`

**Database Setup:**
- PostgreSQL with pgvector extension (for vector operations)
- Run services: `docker-compose up -d` (starts PostgreSQL, Redis, Loki, Grafana, MinIO, OpenTelemetry Collector)
- Database migrations: `alembic upgrade head`

**Application Launch:**
- Start FastAPI server: `uvicorn main:app --reload`
- Background tasks: `celery -A celery_app worker --loglevel=info`
- Scheduled tasks: `celery -A celery_app beat --loglevel=info`

**Code Quality:**
- Format code: `black .`
- No explicit linting command found - verify with project maintainer

## Architecture Overview

**Core Application:**
- FastAPI web framework with CORS middleware
- OpenTelemetry instrumentation for observability
- Application title: "Morpheus @ HTEC" - skill matrix validation system

**Database Design:**
- Primary entities: Users, Skills, Grades, UserSkills (junction table)
- Hierarchical skills system (parent-child relationships)
- Notification system with chat UUID tracking
- MatrixChat for skill validation sessions with time spans
- Runnable* tables for LangGraph state management

**AI/ML Components:**
- LangGraph-based conversational agents in `/agents/`
- OpenAI integration for language models
- Guidance agent for skill validation conversations
- Reasoner agent for processing and classification
- Welcome agent for user onboarding

**Background Processing:**
- Celery with Redis broker for async tasks
- Scheduled matrix validations via cron jobs
- Task definitions in `tasks.py`

**API Structure:**
- Modular routers in `/routers/` directory
- Each router handles specific domain (users, skills, grades, matrix_chats, etc.)
- DTOs organized by type: request, response, inner (internal data structures)

**Infrastructure:**
- Docker Compose with PostgreSQL, Redis, Grafana, Loki, MinIO
- OpenTelemetry for distributed tracing
- MinIO for object storage
- Grafana + Loki for logging and monitoring

**Key Workflows:**
- Users populate skill matrices with grades
- Automated validation via conversational AI agents
- Notification system for reminders and updates
- Matrix chat sessions track skill validation progress
- Analytics router provides usage insights

## File Organization

- `/agents/` - LangGraph-based AI agents
- `/db/` - Database models and connection management
- `/dto/` - Data transfer objects (request/response/inner)
- `/routers/` - FastAPI route handlers
- `/service/` - Business logic and filtering
- `/tools/` - Custom tools for agents
- `/utils/` - Common utility functions
- `/notebooks/` - Jupyter notebooks for experimentation
- `/alembic/` - Database migration scripts