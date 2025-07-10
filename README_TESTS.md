# Test Suite Documentation

## Overview

Comprehensive test suite for the Morpheus application using FastAPI TestClient and testcontainers for database isolation.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Test configuration and fixtures
├── test_analytics.py        # Analytics router tests
├── test_configs.py          # Configuration router tests
├── test_grades.py           # Grades router tests
├── test_matrix.py           # Matrix router tests
├── test_matrix_chats.py     # Matrix chats router tests
├── test_notifications.py   # Notifications router tests
├── test_profile.py          # Profile router tests
├── test_skills.py           # Skills router tests
├── test_testing.py          # Testing router tests
├── test_users.py            # Users router tests
└── test_integration.py      # Integration tests
```

## Features

- **Testcontainers Integration**: Isolated PostgreSQL and Redis containers for each test session
- **FastAPI TestClient**: HTTP client for testing API endpoints
- **Async Support**: Full async/await support with pytest-asyncio
- **Authentication Testing**: Mock authentication for different user roles
- **Database Fixtures**: Pre-populated test data for consistent testing
- **Integration Tests**: End-to-end workflow testing

## Running Tests

### Quick Start
```bash
python run_tests.py
```

### Manual Setup
```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_users.py -v

# Run with coverage
pytest tests/ --cov=routers --cov-report=html
```

## Test Categories

### Unit Tests
- Individual router endpoint testing
- Authentication and authorization
- Request/response validation
- Error handling

### Integration Tests
- Multi-router workflows
- Database transaction testing
- User journey scenarios
- Admin workflow testing

## Fixtures

### Database Fixtures
- `postgres_container`: PostgreSQL testcontainer
- `redis_container`: Redis testcontainer
- `test_engine`: SQLAlchemy async engine
- `test_session`: Database session with rollback

### Data Fixtures
- `test_user`: Regular user account
- `admin_user`: Admin user account
- `test_grade`: Sample grade record
- `test_skill`: Sample skill record
- `test_config`: Sample configuration

### Authentication Fixtures
- `auth_headers`: Basic auth headers for regular user
- `admin_auth_headers`: Basic auth headers for admin user
- `mock_current_user`: Mock current user dependency
- `mock_admin_user`: Mock admin user dependency

## Test Coverage

### Analytics Router (`/api/v1/analytics`)
- ✅ Unauthorized access
- ✅ Non-admin forbidden access
- ✅ Admin access success

### Configs Router (`/api/v1/configuration`)
- ✅ Get configurations
- ✅ Update configurations
- ✅ Admin-only access control

### Grades Router (`/api/v1/grades`)
- ✅ CRUD operations
- ✅ Authentication required
- ✅ Not found handling

### Matrix Router (`/api/v1/users/{user_id}/matrix`)
- ✅ Get user matrix
- ✅ Get matrix by skill
- ✅ Populate matrix
- ✅ Delete matrix entries

### Matrix Chats Router (`/api/v1/matrix-chats`)
- ✅ Get user chats
- ✅ Get chat info
- ✅ Message posting restrictions
- ✅ Completed chat protection

### Notifications Router (`/api/v1/users/{user_id}/notifications`)
- ✅ List notifications
- ✅ Mark notification status
- ✅ Create notifications
- ✅ User/admin filtering

### Profile Router (`/api/v1/profile`)
- ✅ Get current user profile
- ✅ Update profile
- ✅ Authentication required

### Skills Router (`/api/v1/skills`)
- ✅ CRUD operations
- ✅ Admin-only access
- ✅ Hierarchical relationships

### Testing Router (`/api/v1/testing`)
- ✅ Get testing chats
- ✅ Create test models
- ✅ Reasoning workflows
- ✅ AI service integration

### Users Router (`/api/v1/users`)
- ✅ CRUD operations
- ✅ User selection
- ✅ Authentication patterns
- ✅ File upload endpoints

## Environment Variables

Set these for testing:
```bash
TESTING=1
LOG_LEVEL=WARNING
```

## Dependencies

- `pytest`: Test framework
- `pytest-asyncio`: Async test support
- `testcontainers`: Container-based testing
- `httpx`: HTTP client for FastAPI TestClient

## Notes

- Tests use isolated database containers for each session
- Authentication is mocked for consistent testing
- Some endpoints may return 500 due to external AI service dependencies
- Integration tests cover complete user workflows
- All routers have comprehensive test coverage