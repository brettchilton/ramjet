# Quick Start Guide

## Local Development (Recommended)

For local development, use **Simple Auth** (no Kratos needed):

```bash
# Start development environment
./start-dev.sh

# Or manually:
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

**Services:**
- Frontend: http://localhost:5179
- Backend: http://localhost:8006
- API Docs: http://localhost:8006/docs
- Database UI: http://localhost:8085

**Authentication:**
- Uses Simple JWT authentication
- Register at: http://localhost:5179/simple-register
- Login at: http://localhost:5179/simple-login

## Production Deployment

For production with Kratos authentication:

```bash
# Start production environment
./start-prod.sh

# Or manually:
docker-compose --profile production up -d
```

**Additional Services:**
- Kratos Auth: http://localhost:4433

**Authentication:**
- Uses Ory Kratos for identity management
- Register at: http://localhost:5179/auth/registration
- Login at: http://localhost:5179/auth/login

## Common Commands

```bash
# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Restart a specific service
docker-compose restart backend

# Rebuild after code changes
docker-compose build
docker-compose up -d
```

## Database Management

```bash
# Access Adminer UI
open http://localhost:8085

# Run migrations
docker-compose exec backend alembic upgrade head

# Create new migration
docker-compose exec backend alembic revision -m "description"
```

## Switching Between Auth Modes

**Dev → Prod:**
1. Stop dev: `docker-compose down`
2. Start prod: `./start-prod.sh`
3. Set `VITE_USE_SIMPLE_AUTH=false` in `.env`

**Prod → Dev:**
1. Stop prod: `docker-compose down`
2. Start dev: `./start-dev.sh`
3. Set `VITE_USE_SIMPLE_AUTH=true` in `.env`

## Troubleshooting

**Containers crashing?**
- Check `.env` file exists and has all variables set
- View logs: `docker-compose logs <service-name>`

**Port conflicts?**
- Frontend: Change port in docker-compose.yml (default 5179)
- Backend: Change port in docker-compose.yml (default 8006)

**Database issues?**
- Reset: `docker-compose down -v` (⚠️ deletes all data)
- Rebuild: `docker-compose up -d`
