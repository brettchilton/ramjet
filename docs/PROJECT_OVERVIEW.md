# Full-Stack Application Template - Project Overview

## What This Template Provides

A modern full-stack application template with authentication, AI agent integration, and a scalable architecture. This template serves as a foundation for building web applications with user management, API backend, and optional AI-powered features.

## Current Architecture

### Authentication System
- **Production**: Ory Kratos for complete identity management
- **Development**: Simple JWT auth for rapid testing
- Automatic environment-based switching
- Full self-service flows (registration, login, recovery, verification)

### Technology Stack

**Backend**: 
- FastAPI - Modern Python web framework
- SQLAlchemy - ORM for database operations
- PostgreSQL - Primary database
- Alembic - Database migrations
- Redis - Session/cache storage
- Ory Kratos - Identity and access management

**Frontend**: 
- React 18 + TypeScript
- Vite - Lightning-fast build tool
- TanStack Router/Query - Type-safe routing and data fetching
- shadcn/ui + Tailwind CSS - Modern component library
- Dark mode support

**AI/ML Stack**:
- OpenAI API - GPT-4 for defect analysis
- OpenAI Agents SDK - Structured agent workflows
- Pandas - Data processing
- Redis - Agent state caching

**Infrastructure**: 
- Docker Compose - Complete development environment
- MCP Servers - External data integration
- Microservices architecture

## System Architecture

```
app/
├── frontend/                 # React SPA
│   ├── src/
│   │   ├── components/ui/    # shadcn/ui components
│   │   ├── routes/          # Page components
│   │   ├── hooks/           # Custom React hooks
│   │   ├── contexts/        # Auth & state management
│   │   └── services/        # API clients
│   └── ...
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core functionality
│   │   ├── agents/         # AI agent definitions
│   │   └── services/       # Business logic
│   └── migrations/         # Database migrations
├── kratos/                 # Identity configuration
│   ├── kratos.yml         # Main config
│   └── identity.schema.json # User schema
├── mcp-servers/           # External integrations
│   └── excel/             # Excel processing
├── docs/                  # Documentation
└── docker-compose.yml     # Service orchestration
```

## Core Features

### Current Implementation
- ✅ **User Authentication**: Dual auth system (Kratos/Simple)
- ✅ **User Management**: Registration, profile, settings
- ✅ **Role-Based Access**: Inspector, Admin, Viewer roles
- ✅ **Modern UI**: shadcn/ui components with Tailwind
- ✅ **Dark Mode**: System-wide theme support
- ✅ **API Security**: JWT tokens with automatic refresh

### Example Use Cases
- 🚧 **Data Management**: Upload and process various data types
- 🚧 **AI Integration**: GPT-4 powered analysis and processing
- 🚧 **Workflow Automation**: Intelligent task automation
- 🚧 **Report Generation**: PDF/Excel export capabilities

### Extensible Features
- 📋 Multi-tenant support
- 📋 Hierarchical data organization
- 📋 External data import
- 📋 Analytics and insights
- 📋 Bulk operations
- 📋 Mobile app support

## Docker Services

The application runs as a set of Docker containers:

```yaml
# Core Services
db          # PostgreSQL (port 5435)
backend     # FastAPI API (port 8006)
frontend    # React app (port 5179)
kratos      # Identity service (ports 4433/4434)
redis       # Cache/sessions (port 6379)

# Development Tools
adminer     # Database UI (port 8085)
mailslurper # Email testing (ports 2500/8086)

# MCP Servers (optional)
mcp-excel   # Excel processing and data manipulation
```

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Quick Start
```bash
# Clone repository
git clone <repository-url>
cd app

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Setup Kratos database (if using production auth)
docker exec app_postgres psql -U postgres -c "CREATE DATABASE kratos;"
docker-compose exec kratos kratos migrate sql -e --yes

# Access the application
open http://localhost:5179
```

### Development Workflow

**Frontend Development**:
```bash
cd frontend
npm install
npm run dev  # Hot-reload development
```

**Backend Development**:
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8006
```

## API Documentation

- **API Docs**: http://localhost:8006/docs (Swagger UI)
- **ReDoc**: http://localhost:8006/redoc (Alternative docs)

Key endpoints:
- `/auth/*` - Authentication flows
- `/api/v1/users/*` - User management
- `/api/v1/data/*` - Data operations (customizable)
- `/api/v1/reports/*` - Report generation (customizable)

## Environment Configuration

Critical environment variables:

```bash
# Database
DATABASE_URL=postgresql://user:pass@db:5432/app_database

# Authentication
KRATOS_PUBLIC_URL=http://kratos:4433
KRATOS_ADMIN_URL=http://kratos:4434
JWT_SECRET_KEY=your-secret-key

# Frontend
VITE_API_URL=http://localhost:8006
VITE_USE_SIMPLE_AUTH=false  # Use Kratos in production

# AI Services
OPENAI_API_KEY=your-openai-key

# MCP Servers (optional)
```

## Security Considerations

- All passwords hashed with bcrypt
- JWT tokens with expiration
- CORS properly configured
- SQL injection protection via SQLAlchemy
- XSS protection in React
- HTTPS required in production
- Regular security updates

## Contributing

1. Create feature branch from `main`
2. Follow existing code patterns
3. Add tests for new features
4. Update documentation
5. Submit pull request

## Support & Documentation

- [Frontend Setup](./FRONTEND_SETUP.md) - UI development guide
- [Backend Structure](./BACKEND_STRUCTURE.md) - API architecture
- [Authentication](./AUTHENTICATION.md) - Auth system details
- [Kratos Setup](./KRATOS_SETUP.md) - Identity configuration
- [Database Setup](./DATABASE_SETUP.md) - Schema and migrations
- [Development](./DEVELOPMENT.md) - Development workflow

---
*Last updated after shadcn/ui migration and Kratos integration*