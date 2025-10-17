# 🚀 FIRST TIME SETUP GUIDE

Welcome! This guide will walk you through setting up this full-stack application template from scratch.

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Docker Desktop** (Docker & Docker Compose)
- **Node.js 18+** (for local frontend development)
- **Python 3.11+** (for local backend development)
- **Git** (for version control)

## 🔧 Initial Setup Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd mono_repo_shadcn
```

### 2. Set Up Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Open .env in your editor and configure the following:
```

**Essential variables to configure:**

```bash
# Database (can keep defaults for local development)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-secure-password-here
POSTGRES_DB=app_database

# Authentication - IMPORTANT: Generate secure secrets!
SECRET_KEY=generate-a-secure-secret-key-here
JWT_SECRET_KEY=generate-another-secure-key-here

# For production auth (Kratos) - Generate 32 character secrets
KRATOS_COOKIE_SECRET=generate-32-char-secret-here
KRATOS_CIPHER_SECRET=generate-32-char-secret-here

# OpenAI (Optional - for AI agent features)
OPENAI_API_KEY=your-openai-api-key-if-using-ai-features
```

**Generate secure secrets:**
```bash
# Generate secure random secrets
echo "SECRET_KEY=$(openssl rand -base64 32)"
echo "JWT_SECRET_KEY=$(openssl rand -base64 32)"
echo "KRATOS_COOKIE_SECRET=$(openssl rand -base64 32 | head -c 32)"
echo "KRATOS_CIPHER_SECRET=$(openssl rand -base64 32 | head -c 32)"
```

### 3. Start Docker Services

```bash
# Start all services in the background
docker-compose up -d

# Check that all services are running
docker-compose ps

# View logs if needed
docker-compose logs -f
```

### 4. Initialize the Database

```bash
# Run database migrations to create tables
docker-compose exec backend alembic upgrade head

# If using Kratos (production auth), create its database
docker exec eezy_peezy_postgres psql -U postgres -c "CREATE DATABASE kratos;"
docker-compose exec kratos kratos migrate sql -e --yes
```

### 5. Verify Services Are Running

Check that these URLs are accessible:

- **Frontend**: http://localhost:5179
- **Backend API**: http://localhost:8006/docs
- **Database UI (Adminer)**: http://localhost:8085
- **Email Testing (Mailslurper)**: http://localhost:8086

**Complete Port Reference:**

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 5179 | React development server |
| Backend API | 8006 | FastAPI application |
| PostgreSQL | 5435 | Database (non-standard to avoid conflicts) |
| Adminer | 8085 | Database web UI |
| Mailslurper | 8086 / 2500 | Email testing (UI / SMTP) |
| Redis | 6379 | Session/cache storage |
| Kratos Public | 4433 | Identity service public API |
| Kratos Admin | 4434 | Identity service admin API |

## 🎯 Quick Start - Create Your First Account

### Development Mode (Default - Simple Auth)

1. Navigate to: http://localhost:5179/auth/registration
2. Fill in the registration form:
   - Email: your-email@example.com
   - Password: choose-a-secure-password
   - First Name: Your Name
   - Last Name: Your Surname
   - Mobile (optional): Your phone number
3. Click "Register"
4. You'll be automatically logged in and redirected to the dashboard

### Production Mode (Kratos Auth)

If you've set `VITE_USE_SIMPLE_AUTH=false`:

1. Navigate to: http://localhost:5179/auth/registration
2. Complete the Kratos registration flow
3. Check email (or Mailslurper) for verification
4. Login at: http://localhost:5179/auth/login

## 🛠️ Development Workflow

### Frontend Development

```bash
# For hot-reload development
cd frontend
npm install
npm run dev

# Access at http://localhost:5179
```

### Backend Development

```bash
# For hot-reload development
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8006

# API docs at http://localhost:8006/docs
```

### Working with the Database

**Using Adminer (Web UI)**:
1. Go to http://localhost:8085
2. Login with:
   - System: PostgreSQL
   - Server: `db`
   - Username: `postgres` (or your POSTGRES_USER)
   - Password: your POSTGRES_PASSWORD
   - Database: `app_database`

**Using psql (Command Line)**:
```bash
docker exec -it eezy_peezy_postgres psql -U postgres -d app_database
```

## 📝 Common Tasks

### Create a New Database Migration

```bash
# Auto-generate migration from model changes
docker-compose exec backend alembic revision --autogenerate -m "Description of changes"

# Apply the migration
docker-compose exec backend alembic upgrade head
```

### Add New UI Components (shadcn/ui)

```bash
cd frontend
npx shadcn@latest add button
npx shadcn@latest add card
# etc.
```

### Check Service Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Restart Services

```bash
# Restart everything
docker-compose restart

# Restart specific service
docker-compose restart backend
```

## 🔍 Troubleshooting

### Services Won't Start

```bash
# Check if ports are already in use
lsof -i :5179  # Frontend
lsof -i :8006  # Backend
lsof -i :5435  # Database

# If needed, stop everything and start fresh
docker-compose down
docker-compose up -d

# To change ports, edit docker-compose.yml:
# Example: Change frontend from 5179 to 3000
# ports:
#   - "3000:5179"
```

### Database Connection Issues

```bash
# Verify PostgreSQL is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Test connection
docker exec eezy_peezy_postgres psql -U postgres -c "\l"
```

### Authentication Issues

- **Can't login**: Check that you've run migrations
- **Registration fails**: Check backend logs for errors
- **Token errors**: Clear browser localStorage and try again

### Frontend Not Loading

```bash
# Check frontend logs
docker-compose logs frontend

# Rebuild if needed
docker-compose build frontend
docker-compose up -d frontend
```

## 📊 Architecture Overview

This template provides a modern full-stack architecture:

```
┌─────────────┐     ┌────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend  │────▶│  PostgreSQL │
│  (React)    │     │  (FastAPI) │     │  Database   │
│  Port 5179  │     │  Port 8006 │     │  Port 5435  │
└─────────────┘     └────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  External   │
                    │    APIs     │
                    │ (Optional)  │
                    └─────────────┘
```

**Key Features:**
- Modern React frontend with TypeScript and shadcn/ui components
- FastAPI backend with automatic API documentation
- Dual authentication system (Simple JWT for dev, Kratos for production)
- Database migrations with Alembic
- Docker Compose for easy development
- Optional AI agent integration with OpenAI
- MCP server architecture for extensibility

## 🎉 Next Steps

1. **Explore the API**: Visit http://localhost:8006/docs for interactive API documentation
2. **Try the UI**: Login at http://localhost:5179 to see the frontend
3. **Read the docs**: Check `/docs` folder for architecture and feature guides
4. **Customize**: Start building your own features on this foundation
5. **Optional Features**: 
   - Add OpenAI API key for AI agent capabilities
   - Configure cloud storage for file uploads
   - Enable production authentication with Kratos

## 📚 Additional Resources

- **Project Documentation**: See `/docs` folder for detailed guides
- **Authentication Guide**: `/docs/AUTHENTICATION.md` - Dual auth system explained
- **Database Setup**: `/docs/DATABASE_SETUP.md` - Schema and migration guide
- **Frontend Development**: `/docs/FRONTEND_SETUP.md` - React/TypeScript patterns
- **Backend Architecture**: `/docs/BACKEND_STRUCTURE.md` - FastAPI structure
- **Development Guide**: `/docs/DEVELOPMENT.md` - Development workflows

## 🆘 Need Help?

1. Check the logs: `docker-compose logs -f`
2. Review this guide and documentation
3. Check for existing issues in the repository
4. Create a new issue with:
   - What you're trying to do
   - What error you're seeing
   - Relevant log output

---

Happy coding! 🚀