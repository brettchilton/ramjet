# Development Guide

This guide covers the development workflow for the application.

## Prerequisites

- Docker Desktop installed and running
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)
- Git for version control
- VS Code or similar editor

## Quick Start

### 1. Clone and Setup
```bash
git clone <repository-url>
cd app

# Copy environment template
cp .env.example .env

# Edit .env with your settings
# Minimal required: DATABASE_URL, JWT_SECRET_KEY
```

### 2. Start Docker Services
```bash
# Start all services
docker-compose up -d

# Check service health
docker-compose ps

# View logs
docker-compose logs -f
```

### 3. Initialize Database
```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Create Kratos database (if using Kratos)
docker exec app_postgres psql -U postgres -c "CREATE DATABASE kratos;"
docker-compose exec kratos kratos migrate sql -e --yes
```

### 4. Access Application
- Frontend: http://localhost:5179
- API Docs: http://localhost:8006/docs
- Database UI: http://localhost:8085 (Adminer)
- Email UI: http://localhost:8086 (Mailslurper)

## Development Workflows

### Frontend Development

The frontend uses Vite for fast hot-module replacement:

```bash
cd frontend
npm install
npm run dev
```

Key commands:
- `npm run dev` - Start development server with HMR
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript compiler

### Backend Development

For backend development with hot-reload:

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run with hot-reload
uvicorn app.main:app --reload --port 8006
```

Key commands:
- `alembic revision -m "description"` - Create new migration
- `alembic upgrade head` - Apply migrations
- `alembic downgrade -1` - Rollback one migration
- `pytest` - Run tests (when implemented)

### Database Management

#### Using Adminer (Web UI)
1. Visit http://localhost:8085
2. Login with:
   - System: PostgreSQL
   - Server: db
   - Username: postgres
   - Password: postgres
   - Database: app_database

#### Using psql (CLI)
```bash
# Connect to database
docker exec -it app_postgres psql -U postgres -d app_database

# Common commands
\dt              # List tables
\d users         # Describe table
\q               # Quit
```

#### Creating Migrations
```bash
# Generate migration from model changes
docker-compose exec backend alembic revision --autogenerate -m "Add new field"

# Or create empty migration
docker-compose exec backend alembic revision -m "Custom migration"

# Apply migration
docker-compose exec backend alembic upgrade head
```

## UI Development with shadcn/ui

### Adding New Components
```bash
cd frontend
npx shadcn@latest add <component-name>

# Examples:
npx shadcn@latest add button
npx shadcn@latest add card
npx shadcn@latest add form
```

### Component Structure
```tsx
// Use shadcn components
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

// Combine with Tailwind classes
<Card className="w-full max-w-md mx-auto">
  <CardHeader>
    <CardTitle>My Component</CardTitle>
  </CardHeader>
  <CardContent>
    <Button className="w-full">Click me</Button>
  </CardContent>
</Card>
```

### Styling Guidelines
- Use Tailwind utility classes
- Extend with custom CSS only when necessary
- Follow shadcn's composition patterns
- Maintain consistent spacing with Tailwind's scale

## Authentication Development

### Simple Auth (Development)
```typescript
// Frontend
import { useUnifiedAuth } from '@/hooks/useUnifiedAuth';

const { login, user, isAuthenticated } = useUnifiedAuth();

// Backend
from app.api.auth_simple import router as simple_auth_router
app.include_router(simple_auth_router, prefix="/auth/simple")
```

### Kratos (Production)
```typescript
// Frontend
import { useKratos } from '@/hooks/useKratos';

const { initFlow, submitFlow } = useKratos();

// Backend webhook
@router.post("/auth/kratos/webhook")
async def handle_kratos_webhook(request: Request):
    # Sync user data
```

## API Development

### Creating New Endpoints
```python
# In app/api/my_feature.py
from fastapi import APIRouter, Depends
from app.core.auth import get_current_user

router = APIRouter(prefix="/api/v1/my-feature", tags=["my-feature"])

@router.get("/")
async def list_items(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Implementation
    pass

# Register in main.py
from app.api import my_feature
app.include_router(my_feature.router)
```

### Frontend API Calls
```typescript
// Using apiClient (auto-handles auth)
import { apiClient } from '@/utils/apiClient';

const response = await apiClient.get('/api/v1/my-feature');
const data = await apiClient.post('/api/v1/my-feature', { 
  name: 'New Item' 
});
```

## Testing

### Manual Testing Checklist
- [ ] User registration flow
- [ ] Login/logout functionality
- [ ] Protected route access
- [ ] API authentication
- [ ] Form validation
- [ ] Error handling
- [ ] Dark mode toggle

### API Testing with Swagger
1. Visit http://localhost:8006/docs
2. Click "Authorize" button
3. Use token from login response
4. Test endpoints interactively

### Database Testing
```sql
-- Check users
SELECT * FROM users;

-- Check user with specific email
SELECT * FROM users WHERE email = 'test@example.com';

-- Count users by role
SELECT role, COUNT(*) FROM users GROUP BY role;
```

## Common Development Tasks

### Reset Database
```bash
# Drop all tables
docker-compose exec backend alembic downgrade base

# Recreate tables
docker-compose exec backend alembic upgrade head
```

### Clear Docker Volumes
```bash
# Stop services
docker-compose down

# Remove volumes (WARNING: Deletes all data)
docker-compose down -v

# Restart fresh
docker-compose up -d
```

### Update Dependencies

Frontend:
```bash
cd frontend
npm update
npm audit fix
```

Backend:
```bash
cd backend
pip install --upgrade -r requirements.txt
```

### Debug Container Issues
```bash
# View logs
docker-compose logs <service-name>

# Enter container shell
docker-compose exec <service-name> sh

# Rebuild specific service
docker-compose build <service-name>
docker-compose up -d <service-name>
```

## Environment Variables

### Development Defaults
```env
# Database
DATABASE_URL=postgresql://postgres:postgres@db:5432/app_database

# Auth
JWT_SECRET_KEY=dev-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_DAYS=7

# Frontend
VITE_API_URL=http://localhost:8006
VITE_USE_SIMPLE_AUTH=true

# Kratos (if using)
KRATOS_PUBLIC_URL=http://kratos:4433
KRATOS_ADMIN_URL=http://kratos:4434
```

### Adding New Variables
1. Add to `.env` file
2. Update `.env.example`
3. For frontend: prefix with `VITE_`
4. For backend: add to `app/core/config.py`
5. Update docker-compose.yml if needed

## Troubleshooting

### Frontend Not Loading
```bash
# Check if running
docker-compose ps frontend

# View logs
docker-compose logs frontend

# Restart
docker-compose restart frontend
```

### Backend API Errors
```bash
# Check logs
docker-compose logs backend

# Common fixes:
# - Check DATABASE_URL
# - Verify migrations ran
# - Check import paths
```

### Database Connection Issues
```bash
# Verify PostgreSQL is running
docker-compose ps db

# Test connection
docker exec eezy_peezy_postgres psql -U postgres -c "\l"
```

### Port Conflicts
If ports are already in use:
1. Change ports in docker-compose.yml
2. Update .env variables
3. Restart services

## Best Practices

### Code Style
- **Frontend**: ESLint + Prettier configuration
- **Backend**: Black + isort for Python
- **Commits**: Conventional commits (feat:, fix:, docs:)

### Component Development
1. Start with shadcn/ui components
2. Extend with Tailwind classes
3. Extract reusable components
4. Add TypeScript types
5. Document props

### API Development
1. Use proper HTTP methods
2. Return consistent responses
3. Handle errors gracefully
4. Add OpenAPI documentation
5. Validate inputs with Pydantic

### Database Changes
1. Always use migrations
2. Test rollback capability
3. Backup before major changes
4. Keep migrations small
5. Document schema changes

## VS Code Extensions

Recommended extensions:
- Python
- Pylance
- ESLint
- Prettier
- Tailwind CSS IntelliSense
- Docker
- Thunder Client (API testing)
- Prisma (for database viewing)

## Performance Tips

### Frontend
- Use React.memo for expensive components
- Implement lazy loading for routes
- Optimize bundle size with dynamic imports
- Use TanStack Query for server state

### Backend
- Add database indexes for frequent queries
- Use Redis for caching
- Implement pagination for large datasets
- Optimize N+1 queries with joins

### Docker
- Use .dockerignore to reduce build context
- Cache dependencies in separate layers
- Use multi-stage builds for production
- Monitor resource usage with `docker stats`

---
*For additional help, check other docs or open an issue*