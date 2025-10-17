# Database Setup Guide

This guide will help you set up the database for your application.

## Quick Start

1. **Start the database container:**
   ```bash
   docker-compose up -d db
   ```

2. **Run database migrations:**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

3. **Start all services:**
   ```bash
   docker-compose up -d
   ```

4. **Test the connection:**
   - Basic test: http://localhost:8006/
   - Database test: http://localhost:8006/db_test
   - ORM test: http://localhost:8006/orm_test
   - API Documentation: http://localhost:8006/docs

## Database Schema

The database now has a simplified schema with only the `users` table:

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    mobile VARCHAR(20),
    hydra_subject VARCHAR(255) UNIQUE,
    role VARCHAR(50) DEFAULT 'inspector',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_user_hydra_subject ON users(hydra_subject);
CREATE INDEX idx_user_active ON users(is_active);
```

### Key Points:
- **No password storage in users table** - Authentication is handled by auth system
- **kratos_identity_id** - Links users to Kratos identity (when using Kratos)
- **Simplified structure** - Removed all tenant-related tables
- **UUID primary keys** - Using PostgreSQL's uuid-ossp extension

## Database Access

- **Adminer (Web UI):** http://localhost:8085
  - Server: `db`
  - Username: `postgres` (from .env)
  - Password: (from .env)
  - Database: `app_database`

- **Direct PostgreSQL connection:**
  - Host: `localhost`
  - Port: `5435`
  - Database: `app_database`
  - Username: `postgres`
  - Password: (from .env)

## Kratos Database

Kratos uses a separate database within the same PostgreSQL instance:
- Database name: `kratos`
- Must be created manually before first run
- Contains identity data and session information

## Complete Database Reset

To completely wipe and rebuild the database:

```bash
# Stop all containers and remove volumes
docker-compose down -v

# Start fresh
docker-compose up -d db
sleep 5

# Create Kratos database (if using production auth)
docker exec app_postgres psql -U postgres -d app_database -c "CREATE DATABASE kratos;"

# Run migrations
docker-compose exec kratos kratos migrate sql -e --yes
docker-compose exec backend alembic upgrade head

# Start all services
docker-compose up -d
```

## Migrations

### Create a new migration:
```bash
docker-compose exec backend alembic revision -m "description_of_changes"
```

### Apply migrations:
```bash
docker-compose exec backend alembic upgrade head
```

### Rollback migrations:
```bash
docker-compose exec backend alembic downgrade -1
```

### View migration history:
```bash
docker-compose exec backend alembic history
```

## Troubleshooting

**Database connection issues:**
- Make sure Docker containers are running: `docker ps`
- Check logs: `docker logs app_postgres`
- Verify .env file has correct credentials

**Migration issues:**
- Check current version: `docker-compose exec backend alembic current`
- Reset if needed: `docker-compose exec backend alembic downgrade base`
- Re-run migrations: `docker-compose exec backend alembic upgrade head`

**Kratos database missing:**
- Create manually: `docker exec app_postgres psql -U postgres -d app_database -c "CREATE DATABASE kratos;"`
- Run migrations: `docker-compose exec kratos kratos migrate sql -e --yes`

**Port conflicts:**
- Database is on port 5435 (not 5432) to avoid conflicts
- Backend is on port 8006
- Frontend is on port 5179
- Adminer is on port 8085
- Kratos public: 4433
- Kratos admin: 4434