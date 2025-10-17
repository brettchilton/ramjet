# Backend Structure Guide

## Overview

The backend follows a modular architecture organized under the `app/` directory. This structure promotes clean separation of concerns, maintainability, and scalability.

## Directory Structure

```
backend/
├── app/                      # Main application code
│   ├── __init__.py
│   ├── main.py              # FastAPI app initialization
│   ├── api/                 # API endpoints/routes
│   ├── core/                # Core functionality
│   ├── services/            # Business logic
│   ├── agents/              # AI agent implementations
│   └── scripts/             # Application-specific scripts
├── migrations/              # Database migrations (Alembic)
├── sandbox/                 # Development templates
├── scripts/                 # Standalone utility scripts
├── data/                    # Local data storage
├── alembic.ini             # Alembic configuration
├── requirements.txt        # Python dependencies
├── dockerfile              # Docker configuration
└── .env                    # Environment variables
```

## Module Descriptions

### `app/main.py`
The entry point of the FastAPI application. Handles:
- FastAPI app initialization
- CORS middleware configuration
- Router includes
- Root endpoints
- Startup/shutdown events

### `app/api/`
Contains all API endpoint definitions organized by resource:
- `auth.py` - Authentication endpoints (login, register, password reset)
- `upload.py` - File upload and processing endpoints
- Future: Add your own API endpoints here

### `app/core/`
Core application components:
- `database.py` - Database connection and session management
- `models.py` - SQLAlchemy ORM models (includes password_hash field for users)
- `auth.py` - JWT authentication, password hashing, and token validation
- `user_sync.py` - User-tenant synchronization logic

### `app/services/`
Business logic layer (currently empty, for future use):
- Data processing services
- External API integrations
- Complex business operations

### `app/agents/`
AI agent implementations using OpenAI Agents SDK:
- Example agent workflows included
  - `agent_definitions.py` - Agent definitions with instructions and handoffs
  - `models.py` - Structured output data models
  - `workflow.py` - Workflow orchestrator classes
  - `example.py` - Example usage of agent workflows

### `app/scripts/`
Application-specific scripts (currently empty, for future use):
- Data migration scripts
- Batch processing utilities

## Import Patterns

### Within the app directory
```python
# From app/api/endpoints.py
from app.core.database import get_db
from app.core.models import User, YourModel
from app.core.auth import get_current_user
from app.services.your_service import YourService
```

### From external modules
```python
# Standard imports
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

# From agents subdirectory
from app.agents.your_agent.workflow import your_workflow_function
```

## Adding New Components

### 1. New API Endpoint
Create a new file in `app/api/`:
```python
# app/api/your_resource.py
from fastapi import APIRouter, Depends
from app.core.database import get_db
from app.core.auth import get_current_user

router = APIRouter(prefix="/your-resource", tags=["your-resource"])

@router.get("/")
async def list_items(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Implementation
```

Then include in `app/main.py`:
```python
from app.api import your_resource
app.include_router(your_resource.router)
```

### 2. New Service
Create in `app/services/`:
```python
# app/services/your_service.py
from app.core.models import YourModel
from app.core.database import get_db

class YourService:
    def __init__(self, db_session):
        self.db = db_session
    
    def process_data(self, data_id: str):
        # Implementation
```

### 3. New Agent
Create in appropriate subdirectory under `app/agents/`:
```python
# app/agents/your_workflow/your_agent.py
from agents import Agent
from app.agents.your_workflow.models import YourOutputModel

your_agent = Agent(
    name="YourAgent",
    instructions="...",
    output_type=YourOutputModel
)
```

## Configuration Files

### Files that remain in backend root:
- `alembic.ini` - Alembic needs this in root
- `requirements.txt` - Standard Python convention
- `dockerfile` - Docker build configuration
- `.env` - Environment variables (git-ignored)

### Migration files:
- `migrations/` - Contains all database migrations
- Don't move this directory - Alembic expects it here

## Environment Variables

The application uses environment variables for configuration:
```bash
# Database
DB_HOST=db
POSTGRES_USER=username
POSTGRES_PASSWORD=password
POSTGRES_DB=app_database

# Authentication
SECRET_KEY=your-jwt-secret-key

# Redis (for password reset codes)
REDIS_HOST=redis
REDIS_PORT=6379

# Storage
DO_SPACES_BUCKET=bucket-name
DO_SPACES_KEY=access-key
DO_SPACES_SECRET=secret-key

# AI
OPENAI_API_KEY=your-api-key
```

## Docker Considerations

The dockerfile has been updated to run the app from the new location:
```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

## Development Workflow

1. **Local Development**: Code changes in `app/` auto-reload due to volume mounting
2. **Database Changes**: Create migrations with `alembic revision -m "description"`
3. **New Dependencies**: Add to `requirements.txt` and rebuild container
4. **Templates**: Keep reusable code templates in `sandbox/`

## Testing Structure (Future)

```
backend/
├── tests/
│   ├── unit/
│   │   ├── test_models.py
│   │   └── test_services.py
│   ├── integration/
│   │   └── test_api.py
│   └── conftest.py
```

## Best Practices

1. **Separation of Concerns**: Keep API logic in `api/`, business logic in `services/`
2. **Dependency Injection**: Use FastAPI's `Depends()` for database sessions and auth
3. **Type Hints**: Use Python type hints for better IDE support and documentation
4. **Modular Imports**: Use absolute imports starting with `app.`
5. **Configuration**: Keep settings in environment variables, not hardcoded

## Common Tasks

### Adding a new database model
1. Add model class to `app/core/models.py`
2. Create migration: `docker exec backend alembic revision --autogenerate -m "Add new model"`
3. Apply migration: `docker exec backend alembic upgrade head`

### Adding a protected endpoint
```python
from app.core.auth import get_current_user

@router.post("/protected")
async def protected_endpoint(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Basic auth - user available
    user_email = current_user.email
    # Implementation
```

### Using AI agents
```python
from app.agents.your_workflow.workflow import your_workflow_function

async def process_with_ai(input_data):
    result = await your_workflow_function(input_data)
    return result
```