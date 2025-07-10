# Morpheus @ HTEC

An AI-powered skill matrix validation and guidance system that helps engineers assess and validate their technical expertise levels through intelligent conversations.

## Overview

Morpheus is a FastAPI-based application that uses AI agents to guide engineers through skill assessment conversations, validate their expertise claims, and provide personalized feedback. The system employs multiple specialized agents working together to ensure accurate skill matrix population.

## Key Features

- **AI-Powered Skill Assessment**: Multi-agent system for validating user expertise through conversational interfaces
- **Intelligent Guidance**: Provides contextual guidance and feedback based on user responses
- **Skill Matrix Management**: Tracks and manages user skills across different expertise levels
- **Automated Notifications**: Reminds users to complete their skill assessments
- **Real-time Chat Interface**: Interactive conversations for skill validation
- **Analytics & Monitoring**: Comprehensive observability with OpenTelemetry, Jaeger, and Grafana

## Architecture

### Core Components

- **Supervisor Agent**: Orchestrates the conversation flow and determines next steps
- **Guidance Agent**: Provides educational content and skill-specific guidance
- **Discrepancy Agent**: Identifies inconsistencies in user skill claims
- **Feedback Agent**: Offers constructive feedback on user responses
- **Grading Agent**: Evaluates and confirms user expertise levels

### Tech Stack

- **Backend**: FastAPI with Python 3.13
- **Database**: PostgreSQL with pgvector for embeddings
- **AI/ML**: LangChain, LangGraph, OpenAI
- **Caching**: Redis
- **Task Queue**: Celery
- **Observability**: OpenTelemetry, Jaeger, Grafana, Loki
- **Storage**: MinIO for file storage

## Expertise Levels

The system recognizes 7 levels of expertise:

1. **Not Informed**: No prior knowledge
2. **Informed Basics**: Basic concept understanding
3. **Informed in Details**: Deep strategic understanding
4. **Practice and Lab Examples**: Practical application ability
5. **Production Maintenance**: Production environment maintenance
6. **Production from Scratch**: Full system setup capability
7. **Educator/Expert**: Teaching and thought leadership level

## Getting Started

### Prerequisites

- Python 3.13
- Docker and Docker Compose
- OpenAI API key

### Installation

1. Clone the repository
2. Install dependencies: `pipenv install`
3. Set up environment variables in `.env`
4. Start services: `docker-compose up -d`
5. Run migrations: `alembic upgrade head`
6. Start the application: `python main.py`

### API Access

- **Main API**: http://localhost:8000
- **Grafana Dashboard**: http://localhost:3000
- **Jaeger UI**: http://localhost:16686
- **MinIO Console**: http://localhost:9001

## Usage

Users interact with the system through chat interfaces where AI agents guide them through skill assessment conversations, validate their expertise claims, and provide personalized learning recommendations.