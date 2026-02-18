# Authentication Documentation

This application uses a dual authentication system that automatically switches between development and production modes.

## Overview

The application supports two authentication modes:

1. **Simple JWT Authentication** (Development - Default)
   - Fast and easy for local development
   - No external dependencies
   - JWT tokens stored in localStorage
   - Works seamlessly across different ports

2. **Ory Kratos** (Production)
   - Enterprise-grade identity management
   - Session-based authentication
   - Advanced security features
   - Email verification, account recovery, MFA support

## Architecture

### Automatic Mode Selection
The frontend automatically selects the authentication mode based on environment:
```typescript
// In development or when VITE_USE_SIMPLE_AUTH=true
const useSimpleAuth = import.meta.env.VITE_USE_SIMPLE_AUTH === 'true' || import.meta.env.DEV;
```

### Unified Auth Hook
Components use a unified interface regardless of auth mode:
```typescript
import { useUnifiedAuth } from '../hooks/useUnifiedAuth';

const { user, isAuthenticated, loading, logout } = useUnifiedAuth();
```

## Development Authentication (Simple JWT)

### How It Works

1. **Registration**: Users create accounts with email/password
2. **Password Storage**: Passwords hashed with bcrypt in PostgreSQL
3. **Login**: Returns JWT token valid for 7 days
4. **Token Storage**: Stored in localStorage
5. **API Calls**: Token sent in Authorization header

### Backend Endpoints

```bash
# Register new user
POST /auth/register
Body: {
  "email": "user@example.com",
  "password": "secure-password",
  "first_name": "John",
  "last_name": "Doe",
  "mobile": "0400000000",  # optional
  "role": "warehouse"      # default: warehouse
}
Response: {
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "warehouse"
  }
}

# Login
POST /auth/login
Body: {
  "email": "user@example.com",
  "password": "secure-password"
}
Response: {
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": { ... }
}

# Get current user
GET /auth/me
Headers: {
  "Authorization": "Bearer eyJ..."
}
Response: {
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "mobile": "0400000000",
  "role": "warehouse",
  "is_active": true
}

# Logout (client-side only)
POST /auth/logout
# Simply removes token from localStorage
```

### Frontend Implementation

Context: `src/contexts/SimpleAuthContext.tsx`
```typescript
// Login example
const { login } = useAuth();
await login(email, password);

// The context handles:
// - API call to /auth/login
// - Token storage in localStorage
// - User state management
// - Automatic token inclusion in API requests via apiClient
```

## Production Authentication (Ory Kratos)

### Configuration

Kratos is configured via `kratos/kratos.yml`:

```yaml
session:
  cookie:
    name: app_kratos_session
    same_site: Lax
    path: /
  lifespan: 24h

selfservice:
  flows:
    login:
      ui_url: http://localhost:5179/auth/login
      after:
        default_browser_return_url: http://localhost:5179/dashboard
    
    registration:
      ui_url: http://localhost:5179/auth/registration
      after:
        default_browser_return_url: http://localhost:5179/dashboard
    
    recovery:
      ui_url: http://localhost:5179/auth/recovery
    
    verification:
      ui_url: http://localhost:5179/auth/verification
```

### Identity Schema

User identities are defined in `kratos/identity.schema.json`:
```json
{
  "properties": {
    "traits": {
      "properties": {
        "email": {
          "type": "string",
          "format": "email",
          "ory.sh/kratos": {
            "credentials": {
              "password": {
                "identifier": true
              }
            },
            "recovery": {
              "via": "email"
            },
            "verification": {
              "via": "email"
            }
          }
        },
        "first_name": { "type": "string" },
        "last_name": { "type": "string" },
        "mobile": { "type": "string" },
        "role": {
          "type": "string",
          "default": "warehouse",
          "enum": ["warehouse", "admin"]
        }
      }
    }
  }
}
```

### Kratos Flows

1. **Registration Flow**
   - User visits `/auth/registration`
   - Frontend fetches flow from Kratos
   - Dynamic form rendered via `KratosFlow.tsx`
   - On submit, identity created in Kratos
   - Webhook syncs user to backend database

2. **Login Flow**
   - User visits `/auth/login`
   - Credentials validated by Kratos
   - Session cookie set
   - Frontend redirects to dashboard

3. **Recovery Flow**
   - User requests password reset
   - Email sent with recovery link
   - New password set via recovery UI

### Frontend Implementation

Hook: `src/hooks/useKratos.tsx`
```typescript
// Initialize flow
const { initFlow, submitFlow, session } = useKratos();
const flow = await initFlow('login');

// Render dynamic form
<KratosFlow flow={flow} onSubmit={submitFlow} />

// Check authentication
if (session?.active) {
  // User is authenticated
}
```

## Backend Integration

### JWT Validation (Simple Auth)
```python
# In app/core/auth.py
def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    user_id = payload.get("sub")
    # Fetch and return user
```

### Kratos Session Validation
```python
# In app/api/auth_kratos.py
async def validate_kratos_session(cookie: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{KRATOS_PUBLIC_URL}/sessions/whoami",
            cookies={"app_kratos_session": cookie}
        )
    return response.json()
```

### Dual Mode Support
The backend supports both authentication methods simultaneously:
- `/auth/simple/*` - Simple JWT endpoints
- `/auth/kratos/*` - Kratos integration endpoints
- API endpoints accept both JWT tokens and Kratos sessions

## Frontend Routes

### Auth Pages (shadcn/ui components)
- `/auth/login` - Login form
- `/auth/registration` - Sign up form
- `/auth/recovery` - Password reset
- `/auth/verification` - Email verification
- `/auth/error` - Error handling

### Protected Routes
- `/dashboard` - Main application
- `/settings` - User settings
- Uses `AuthGuard` component for protection

## Security Considerations

### Simple Auth
- Passwords hashed with bcrypt (12 rounds)
- JWT tokens expire after 7 days
- Tokens include user ID and email
- No refresh token mechanism (intentional for simplicity)

### Kratos
- Industry-standard security
- CSRF protection
- Session management
- Account enumeration protection
- Brute force protection
- Secure password requirements

## Switching Between Modes

### Development to Production
1. Set `VITE_USE_SIMPLE_AUTH=false` in `.env`
2. Ensure Kratos is running
3. Frontend automatically uses Kratos

### Production to Development
1. Set `VITE_USE_SIMPLE_AUTH=true` or use development mode
2. Frontend automatically uses Simple Auth
3. No Kratos required

## Common Issues & Solutions

### CORS Errors
**Simple Auth**: Backend allows localhost:5179
**Kratos**: Configure allowed_origins in kratos.yml

### Session Expiration
**Simple Auth**: Re-login required after 7 days
**Kratos**: Configurable session lifetime

### Password Reset
**Simple Auth**: Not implemented (dev only)
**Kratos**: Full recovery flow with email

### Cookie Issues
**Kratos**: Ensure same_site and domain settings match your deployment

## Testing Authentication

### Simple Auth Test
```bash
# Register
curl -X POST http://localhost:8006/auth/simple/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123","first_name":"Test","last_name":"User"}'

# Login
curl -X POST http://localhost:8006/auth/simple/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

### Kratos Test
```bash
# Check Kratos health
curl http://localhost:4434/health/ready

# Initialize registration flow
curl http://localhost:4433/self-service/registration/browser
```

## Migration Path

When moving from development to production:

1. Export users from Simple Auth
2. Import identities into Kratos
3. Users must reset passwords
4. Update environment variables
5. Deploy with Kratos infrastructure

---
*Last updated after implementing dual authentication system*