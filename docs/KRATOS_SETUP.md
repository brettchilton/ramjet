# Ory Kratos Integration Guide

This document describes how Ory Kratos has been integrated into the application to handle user identity management, authentication, and account recovery.

## Overview

Ory Kratos provides identity management for the application, including:
- User registration and profile management
- Password-based authentication
- Account recovery (forgot password)
- Email verification
- Session management
- Account settings management

## Architecture

```
┌─────────────┐     ┌────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Kratos   │────▶│   Backend   │
│  (React)    │     │  (Identity) │     │  (FastAPI)  │
└─────────────┘     └────────────┘     └─────────────┘
                           │                    │
                           └────────────────────┘
                              Webhook Sync
```

## Setup Instructions

### 1. Database Setup

Create the Kratos database (only needed for production mode):
```bash
docker-compose exec db psql -U postgres -c "CREATE DATABASE kratos;"
```

### 2. Run Database Migrations

The `users` table already includes `kratos_identity_id` column. Run migrations if needed:
```bash
docker-compose exec backend alembic upgrade head
```

### 3. Start Services

**Development mode (Simple Auth - no Kratos):**
```bash
./start-dev.sh
```

**Production mode (with Kratos):**
```bash
./start-prod.sh
# OR: docker-compose --profile production up -d
```

Kratos will be available on:
- Public API: http://localhost:4433
- Admin API: http://localhost:4434

### 4. Environment Variables

Add these to your `.env` file:
```bash
# Ory Kratos Configuration
KRATOS_COOKIE_SECRET=your-32-char-cookie-secret
KRATOS_CIPHER_SECRET=your-32-char-cipher-secret
KRATOS_WEBHOOK_SECRET=your-webhook-secret
```

Generate secure secrets:
```bash
echo "KRATOS_COOKIE_SECRET=$(openssl rand -base64 32)"
echo "KRATOS_CIPHER_SECRET=$(openssl rand -base64 32)"
echo "KRATOS_WEBHOOK_SECRET=$(openssl rand -base64 32)"
```

## Frontend Routes

The following authentication routes have been created:

- `/auth/login` - User login with Kratos
- `/auth/registration` - New user registration
- `/auth/recovery` - Password recovery
- `/auth/verification` - Email verification
- `/auth/error` - Error handling
- `/dashboard` - Protected dashboard
- `/settings` - Account settings

## Backend Integration

### New Endpoints

The backend provides these Kratos-related endpoints:

- `POST /auth/kratos/webhook` - Webhook endpoint for Kratos events
- `GET /auth/kratos/session` - Check current Kratos session
- `POST /auth/kratos/logout` - Logout from Kratos
- `GET /auth/kratos/flows/{flow_type}` - Get flow status

### User Model Updates

The User model now includes:
- `kratos_identity_id` - Links to Kratos identity

### Authentication Flow

1. User visits `/auth/registration` or `/auth/login`
2. Frontend initializes Kratos flow
3. User completes the flow (registration/login)
4. Kratos creates session and calls webhook
5. Backend syncs user data and issues JWT
6. Frontend receives session and JWT token

## Configuration Files

### kratos/kratos.yml

Main Kratos configuration with:
- Database connection
- UI URLs pointing to frontend
- Identity schema configuration
- Session settings
- Webhook configuration

### kratos/identity.schema.json

Defines user traits:
- email (required, used for login)
- first_name (required)
- last_name (required)
- mobile (optional)
- role (enum: warehouse, admin)

### kratos/webhooks.jsonnet

Webhook logic to sync Kratos identities with backend database after registration.

## Development Workflow

### Testing Registration

1. Navigate to http://localhost:5179/auth/registration
2. Fill in the registration form
3. Submit to create account
4. Check that user appears in both Kratos and application database

### Testing Login

1. Navigate to http://localhost:5179/auth/login
2. Enter email and password
3. Submit to login
4. Should redirect to dashboard

### Testing Recovery

1. Navigate to http://localhost:5179/auth/recovery
2. Enter email address
3. Check console/logs for recovery code (in dev mode)
4. Enter code to reset password

## Production Considerations

1. **Secrets**: Generate all new secrets for production
2. **HTTPS**: Enable HTTPS for all endpoints
3. **Email**: Configure proper SMTP settings in kratos.yml
4. **CORS**: Update CORS settings for your domain
5. **Sessions**: Configure appropriate session lifetimes
6. **Webhooks**: Secure webhook endpoint with proper authentication

## Troubleshooting

### Kratos won't start
- Check if Postgres is running
- Verify kratos database exists
- Check logs: `docker logs eezy_peezy_kratos`

### Registration fails
- Check webhook logs in backend
- Verify webhook secret matches
- Check Kratos logs for errors

### Session issues
- Clear browser cookies
- Check session cookie domain settings
- Verify frontend and backend URLs

### Database sync issues
- Check if kratos_identity_id column exists in users table
- Verify webhook is being called
- Check backend logs for webhook processing

## Migration from Existing Auth

To migrate existing users to Kratos:

1. Export user data from current system
2. Use Kratos Admin API to create identities
3. Update users table with kratos_identity_id
4. Users will need to reset passwords on first login

## Security Notes

1. Kratos handles all password storage and validation
2. No passwords are stored in the application database
3. Sessions are managed by Kratos with secure cookies
4. CSRF protection is built into Kratos flows
5. Email verification is required for new accounts