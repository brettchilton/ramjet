# Ramjet Plastics — Project Overview

## What This Project Does

An order automation platform for Ramjet Plastics. The system monitors a Gmail inbox for customer purchase orders, uses AI to extract order data, enriches it with product specifications from the database, generates Office Order and Works Order forms, and presents everything to Sharon for review and approval.

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
- Ory Kratos - Identity and access management

**Frontend**:
- React 18 + TypeScript
- Vite - Lightning-fast build tool
- TanStack Router/Query - Type-safe routing and data fetching
- shadcn/ui + Tailwind CSS - Modern component library
- Dark mode support

**AI/ML Stack**:
- Anthropic Claude API - Order data extraction from emails and PDFs
- Pandas - Data processing

**Infrastructure**:
- Docker Compose - Complete development environment
- MCP Servers - External data integration (Excel processing)

## System Architecture

```
ramjet/
├── frontend/                 # React SPA
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/          # shadcn/ui components
│   │   │   ├── orders/      # Order automation components
│   │   │   └── Layout/      # App layout components
│   │   ├── routes/          # Page components
│   │   ├── hooks/           # Custom React hooks (useOrders, useUnifiedAuth)
│   │   ├── contexts/        # Auth & state management
│   │   ├── services/        # API clients (kratosService, orderService)
│   │   └── types/           # TypeScript interfaces
│   └── ...
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/            # API endpoints (orders, products, system, auth)
│   │   ├── core/           # Core functionality (auth, models, database)
│   │   ├── services/       # Business logic (gmail, extraction, enrichment, form generation)
│   │   ├── schemas/        # Pydantic schemas (orders, products, emails)
│   │   └── agents/         # AI agent definitions
│   ├── scripts/            # Utility scripts (gmail_oauth_setup, seed_products)
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
- **Order Automation**: End-to-end email-to-form pipeline
  - Gmail inbox monitoring via Gmail API
  - AI-powered order extraction (Anthropic Claude)
  - Product database enrichment
  - Office Order + Works Order Excel generation
  - Review/approval dashboard
- **User Authentication**: Dual auth system (Kratos/Simple)
- **User Management**: Registration, profile, settings
- **Modern UI**: shadcn/ui components with Tailwind
- **Dark Mode**: System-wide theme support
- **API Security**: JWT tokens with automatic refresh

## Docker Services

The application runs as a set of Docker containers:

```yaml
# Core Services
db          # PostgreSQL (port 5435) — container: eezy_peezy_postgres
backend     # FastAPI API (port 8006)
frontend    # React app (port 5179)
kratos      # Identity service (ports 4433/4434)

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
cd ramjet

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Setup Kratos database (if using production auth)
docker exec eezy_peezy_postgres psql -U postgres -c "CREATE DATABASE kratos;"
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
- `/api/orders/*` - Order processing, review, approval
- `/api/products/*` - Product database lookup
- `/api/system/*` - System status, email monitoring

## Environment Configuration

Critical environment variables:

```bash
# Database
DATABASE_URL=postgresql://user:pass@db:5432/${POSTGRES_DB}

# Authentication
KRATOS_PUBLIC_URL=http://kratos:4433
KRATOS_ADMIN_URL=http://kratos:4434
JWT_SECRET_KEY=your-secret-key

# Frontend
VITE_API_URL=http://localhost:8006
VITE_USE_SIMPLE_AUTH=false  # Use Kratos in production

# AI Services
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Gmail API
GMAIL_DELEGATED_USER=catchment@ramjetplastics.com
GMAIL_CREDENTIALS_FILE=client_secret.json
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
- [Feature Overview](./FEATURE_OVERVIEW.md) - Order automation feature details

---
*Last updated after order automation implementation*
