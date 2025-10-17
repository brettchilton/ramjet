# Full-Stack Application Template

A modern web application template with authentication, AI agent integration, and MCP (Model Context Protocol) servers for extensible functionality.

## 🚀 Quick Start

```bash
# Clone repository
git clone <repository-url>
cd app

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your settings

# Start all services
docker-compose up -d

# Access the application
open http://localhost:5179

# Create an account
open http://localhost:5179/auth/registration
```

## 📋 Features

### MCP Servers
- **Excel MCP**: Advanced Excel file manipulation, analysis, and reporting

### Core Platform
- **Dual Authentication System**: Simple JWT for development, Ory Kratos for production
- **AI Agent Integration**: OpenAI-powered workflows and analysis
- **Cloud Storage**: Digital Ocean Spaces integration
- **Role-Based Access**: Customizable user roles and permissions
- **Extensible Architecture**: Ready for your custom features

## 🏗️ Architecture

### Services

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 5179 | React/TypeScript application |
| Backend API | 8006 | FastAPI REST API |
| Ory Kratos | 4433/4434 | Identity & user management (production) |
| PostgreSQL | 5435 | Primary database |
| Adminer | 8085 | Database GUI |

### MCP Servers

| Server | Port | Description |
|--------|------|-------------|
| Excel MCP | 9105 | Excel file manipulation and analysis |

### Tech Stack

**Backend**
- Python 3.11+ with FastAPI
- SQLAlchemy ORM with Alembic migrations
- Dual auth: Simple JWT (dev) / Ory Kratos (prod)
- OpenAI integration for AI analysis
- Boto3 for Digital Ocean Spaces

**Frontend**
- React 18 with TypeScript
- Vite for fast development
- TanStack Router for routing
- Material-UI components
- Axios for API calls

**Infrastructure**
- Docker & Docker Compose
- PostgreSQL (dual database setup)
- Redis for caching
- Digital Ocean Spaces for file storage

## 🔧 Configuration

### Required Environment Variables

```bash
# Database
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_DB=annie_defect

# Authentication
SECRET_KEY=your-secret-key-change-this-in-production  # JWT secret
VITE_USE_SIMPLE_AUTH=true  # Use simple auth (set to false for Kratos in production)

# Ory Kratos (Production Auth)
KRATOS_COOKIE_SECRET=your-32-char-secret-here
KRATOS_CIPHER_SECRET=32-CHAR-LONG-SECRET-CHANGE-ME!!!

# Digital Ocean Spaces (Optional)
DO_SPACES_ENDPOINT=https://syd1.digitaloceanspaces.com
DO_SPACES_BUCKET=your-bucket
DO_SPACES_KEY=your-key
DO_SPACES_SECRET=your-secret

# Frontend
VITE_API_URL=http://localhost:8006

# Development
DEBUG=true  # Enable synchronous processing
LOG_LEVEL=DEBUG  # Verbose logging
```

## 🤖 MCP Servers

### Quick Start

```bash
# Start all MCP servers
./scripts/start-servers.sh

# Test server health
./scripts/test-servers.sh

# Stop MCP servers
./scripts/stop-servers.sh
```

### Operating Modes

**STDIO Mode (Default)**
- Direct process communication
- Lower latency
- Best for local development with MCP clients

**SSE Mode**
- HTTP Server-Sent Events
- Network accessible
- For web applications and remote access

```bash
# Start in SSE mode
./scripts/start-servers.sh sse
```

### Environment

No external API keys are required for the Excel MCP.

```bash
# MCP Server Ports
EXCEL_MCP_PORT=9105
```

### Claude Desktop Integration

Add to your Claude Desktop config file:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "excel-mcp": {
      "command": "docker",
      "args": ["exec", "-i", "eezy_peezy_excel_mcp", "/entrypoint.sh"]
    }
  }
}
```

## 🚦 Development Workflow

### Starting Services

```bash
# Start core application services
docker-compose up -d backend frontend db redis hydra

# Start MCP servers
./scripts/start-servers.sh

# Start everything
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f eezy_peezy_excel_mcp

# Restart specific service
docker-compose restart eezy_peezy_backend
```

### Database Migrations

```bash
# Run migrations
docker exec backend alembic upgrade head

# Create new migration
docker exec backend alembic revision -m "description"
```

### Authentication Setup

**Development Mode (Default)**:
1. Navigate to http://localhost:5179/simple-register
2. Create account with email and password
3. Login at http://localhost:5179/simple-login
4. JWT tokens stored in localStorage

**Production Mode (Ory Kratos)**:
1. Set `VITE_USE_SIMPLE_AUTH=false` in .env
2. Configure Kratos (see docs/AUTHENTICATION.md)
3. Use Kratos flows for registration/login
4. Session cookies for authentication

## 📁 Project Structure

```
eezy-peezy/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI application
│   │   ├── api/
│   │   │   ├── auth_simple.py     # Simple JWT auth
│   │   │   ├── auth_kratos.py     # Kratos integration
│   │   │   └── buildings.py       # Building/defect APIs
│   │   ├── core/
│   │   │   ├── auth.py           # Authentication logic
│   │   │   ├── models.py         # SQLAlchemy models
│   │   │   └── database.py       # Database setup
│   │   └── migrations/           # Alembic migrations
├── frontend/
│   ├── src/
│   │   ├── contexts/
│   │   │   ├── SimpleAuthContext.tsx  # JWT auth context
│   │   │   └── AuthContext.tsx        # Kratos auth context
│   │   ├── hooks/
│   │   │   └── useUnifiedAuth.tsx     # Unified auth hook
│   │   ├── routes/                    # Page components
│   │   └── utils/
│   │       └── apiClient.ts           # API client
│   └── package.json
├── kratos/                      # Kratos configuration
├── docker-compose.yml           # Service orchestration
├── .env                        # Environment variables
└── docs/                       # Documentation
```

## 📊 Data Flow

1. **Authentication**: User logs in (JWT in dev, Kratos in prod)
2. **Upload**: Inspector uploads defect photos
3. **Categorize**: Assign to building/room/component
4. **AI Analysis**: OpenAI analyzes defect severity
5. **Report**: Generate inspection reports
6. **Track**: Monitor defect resolution status

## 🔐 Security

- **Dual Authentication**: 
  - Development: Simple JWT with bcrypt passwords
  - Production: Ory Kratos with session management
- **Password Security**: Bcrypt hashing with salt
- **Token Management**: JWT with 7-day expiry (dev)
- **Session Security**: HTTP-only cookies (prod)
- **Role-Based Access**: Inspector, Admin, Viewer roles
- **CORS**: Configured for frontend origin

## 📝 API Documentation

### Key Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/auth/register` | Create account (dev) | ❌ |
| POST | `/auth/login` | Login (dev) | ❌ |
| GET | `/auth/me` | Current user info | ✅ |
| POST | `/auth/logout` | Logout | ✅ |
| GET | `/api/buildings` | List buildings | ✅ |
| POST | `/api/defects` | Create defect | ✅ |
| GET | `/api/admin/users` | List all users | Admin |

Full API documentation available at http://localhost:8006/docs

## 🧪 Testing

```bash
# Test authentication
curl http://localhost:8006/api/me \
  -H "Authorization: Bearer $TOKEN"

# Test file upload (use frontend)
# 1. Login at http://localhost:5179
# 2. Upload test-data.zip
# 3. Check processing in logs
```

## 🐛 Troubleshooting

### Common Issues

**MCP Servers Won't Start**
```bash
# Check logs
docker-compose logs eezy_peezy_excel_mcp

# Rebuild images
docker-compose build --no-cache excel-mcp

# Verify API keys
cat .env | grep API_KEY
```

**API Authentication Errors**
- Verify API keys are set in `.env`
- Check container environment: `docker exec eezy_peezy_excel_mcp env`
- Ensure API keys are valid and not expired

**Port Conflicts**
```bash
# Check what's using the Excel MCP port
lsof -i :9105

# Modify ports in .env if needed
```

**401 Unauthorized**
- Token not sent or expired
- Check authentication service is running
- Verify frontend includes token

**403 No Tenant Assigned**
- User needs tenant assignment
- Check `/api/tenants/available`
- Assign via API or admin panel

**Database Connection Failed**
- Verify PostgreSQL is running
- Check credentials in .env
- Ensure database exists

## 📚 Documentation

- [Authentication & Multi-Tenancy](docs/AUTHENTICATION.md)
- [Database Schema](docs/DATABASE_SETUP.md)
- [Project Overview](docs/PROJECT_OVERVIEW.md)

## 🚢 Production Deployment

### Prerequisites
- Configure SSL/HTTPS
- Set secure passwords
- Use external PostgreSQL
- Configure backup strategy
- Set up monitoring

### Environment Changes
```bash
DEBUG=false
LOG_LEVEL=INFO
# Add production URLs
KEYCLOAK_URL=https://auth.yourdomain.com
VITE_API_URL=https://api.yourdomain.com
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

For issues and questions:
- Check [Troubleshooting](#-troubleshooting) section
- Review logs: `docker-compose logs`
- Open GitHub issue with details
