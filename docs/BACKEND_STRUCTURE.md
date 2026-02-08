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
│   ├── services/            # Business logic (order automation)
│   ├── schemas/             # Pydantic request/response models
│   ├── agents/              # AI agent implementations
│   └── scripts/             # Application-specific scripts
├── scripts/                 # Standalone utility scripts
├── migrations/              # Database migrations (Alembic)
├── sandbox/                 # Development templates
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
- `auth_simple.py` - Simple JWT authentication (development)
- `auth_kratos.py` - Kratos integration endpoints (production)
- `auth_simplified.py` - Simplified auth wrapper endpoints
- `orders.py` - Order processing, review, approval/rejection endpoints
- `products.py` - Product database lookup endpoints
- `system.py` - System status, email monitoring, email detail endpoints

### `app/core/`
Core application components:
- `database.py` - Database connection and session management
- `models.py` - SQLAlchemy ORM models (users, orders, products, emails)
- `auth.py` - JWT authentication, password hashing, and token validation
- `user_sync.py` - User-tenant synchronization logic

### `app/services/`
Business logic layer for order automation:
- `gmail_service.py` - Gmail API integration for polling and fetching emails
- `extraction_service.py` - Anthropic Claude integration for extracting structured order data from emails/PDFs
- `enrichment_service.py` - Product database lookup, manufacturing specs, material calculations
- `form_generation_service.py` - Office Order and Works Order Excel form generation

### `app/schemas/`
Pydantic models for request/response validation:
- `order_schemas.py` - Order, line item, and approval schemas
- `product_schemas.py` - Product lookup and specification schemas
- `email_schemas.py` - Email and attachment schemas

### `app/agents/`
AI agent implementations using OpenAI Agents SDK:
- Example agent workflows included
  - `agent_definitions.py` - Agent definitions with instructions and handoffs
  - `models.py` - Structured output data models
  - `workflow.py` - Workflow orchestrator classes
  - `example.py` - Example usage of agent workflows

### `scripts/` (backend root)
Standalone utility scripts:
- `gmail_oauth_setup.py` - Set up Gmail OAuth credentials for email monitoring
- `seed_products.py` - Populate the product database with initial data
- `create_test_data.py` - Generate test data for development

## Import Patterns

### Within the app directory
```python
# From app/api/endpoints.py
from app.core.database import get_db
from app.core.models import User, Order, Product
from app.core.auth import get_current_user
from app.services.extraction_service import ExtractionService
from app.schemas.order_schemas import OrderResponse
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
POSTGRES_DB=your_database_name

# Authentication
SECRET_KEY=your-jwt-secret-key

# AI Services
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Gmail API
GMAIL_DELEGATED_USER=catchment@ramjetplastics.com
GMAIL_CREDENTIALS_FILE=client_secret.json

# Storage
DO_SPACES_BUCKET=bucket-name
DO_SPACES_KEY=access-key
DO_SPACES_SECRET=secret-key
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

## Testing Structure

```
backend/
├── tests/
│   ├── test_form_generation.py
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
