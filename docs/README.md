# Ramjet Plastics — Order Automation Platform

A web application that automates order processing for Ramjet Plastics. Monitors a Gmail inbox for customer purchase orders, extracts order data using AI (Anthropic Claude), enriches it with product specs from a database, generates Office Order and Works Order forms, and presents them for review/approval.

## Quick Start

```bash
# Clone repository
git clone <repository-url>
cd ramjet

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your settings (database credentials, Gmail OAuth, Anthropic API key)

# Start development environment (Simple Auth - no Kratos)
./start-dev.sh

# OR manually:
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Enable PostgreSQL UUID extension (first time only)
docker-compose exec db psql -U postgres -d ${POSTGRES_DB} -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"

# Run database migrations (first time only)
docker-compose exec backend alembic upgrade head

# Seed product database (first time only)
docker-compose exec backend python scripts/seed_products.py

# Access the application
open http://localhost:5179
```

## Features

### Order Automation
- **Email Monitoring**: Gmail API polling for incoming customer purchase orders
- **AI Extraction**: Anthropic Claude extracts structured order data from emails and PDF attachments
- **Product Enrichment**: Automatic lookup of manufacturing specs, materials, packaging from product database
- **Form Generation**: Auto-generates Office Order and Works Order Excel spreadsheets
- **Review Workflow**: Dashboard for reviewing, editing, approving, or rejecting extracted orders

### Core Platform
- **Dual Authentication System**: Simple JWT for development, Ory Kratos for production
- **MCP Servers**: Excel MCP for advanced spreadsheet manipulation
- **Cloud Storage**: Digital Ocean Spaces integration
- **Role-Based Access**: Customizable user roles and permissions

## Architecture

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
| Excel MCP | 9100 | Excel file manipulation and analysis |

### Tech Stack

**Backend**
- Python 3.11+ with FastAPI
- SQLAlchemy ORM with Alembic migrations
- Dual auth: Simple JWT (dev) / Ory Kratos (prod)
- Anthropic Claude API for order data extraction
- Gmail API for email monitoring
- Boto3 for Digital Ocean Spaces

**Frontend**
- React 18 with TypeScript
- Vite for fast development
- TanStack Router for routing
- TanStack Query for data fetching
- shadcn/ui + Tailwind CSS for components

**Infrastructure**
- Docker & Docker Compose
- PostgreSQL (single database with optional Kratos DB)
- Digital Ocean Spaces for file storage (optional)

## Configuration

### Required Environment Variables

```bash
# Database
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_DB=your_database_name

# Authentication
SECRET_KEY=your-secret-key-change-this-in-production  # JWT secret
VITE_USE_SIMPLE_AUTH=true  # Use simple auth (set to false for Kratos in production)

# Ory Kratos (Production Auth)
KRATOS_COOKIE_SECRET=your-32-char-secret-here
KRATOS_CIPHER_SECRET=32-CHAR-LONG-SECRET-CHANGE-ME!!!

# Anthropic API (for order extraction)
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Gmail API (for email monitoring)
GMAIL_DELEGATED_USER=catchment@ramjetplastics.com
GMAIL_CREDENTIALS_FILE=client_secret.json

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

## MCP Servers

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

## Development Workflow

### Starting Services

```bash
# Start development environment (Simple Auth - recommended)
./start-dev.sh
# OR manually: docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Start production environment (with Kratos)
./start-prod.sh
# OR manually: docker-compose --profile production up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart specific service
docker-compose restart backend
```

### Database Migrations

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Create new migration (auto-generate from models)
docker-compose exec backend alembic revision --autogenerate -m "description"

# Create blank migration
docker-compose exec backend alembic revision -m "description"
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

## Project Structure

```
ramjet/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI application
│   │   ├── api/
│   │   │   ├── auth_simple.py     # Simple JWT auth
│   │   │   ├── auth_kratos.py     # Kratos integration
│   │   │   ├── auth_simplified.py # Simplified auth wrapper
│   │   │   ├── orders.py          # Order processing endpoints
│   │   │   ├── products.py        # Product lookup endpoints
│   │   │   └── system.py          # System/email endpoints
│   │   ├── services/
│   │   │   ├── gmail_service.py          # Gmail API integration
│   │   │   ├── extraction_service.py     # Claude AI data extraction
│   │   │   ├── enrichment_service.py     # Product database enrichment
│   │   │   └── form_generation_service.py # Excel form generation
│   │   ├── schemas/
│   │   │   ├── order_schemas.py    # Order Pydantic models
│   │   │   ├── product_schemas.py  # Product Pydantic models
│   │   │   └── email_schemas.py    # Email Pydantic models
│   │   ├── core/
│   │   │   ├── auth.py           # Authentication logic
│   │   │   ├── models.py         # SQLAlchemy models
│   │   │   └── database.py       # Database setup
│   │   └── migrations/           # Alembic migrations
│   └── scripts/
│       ├── gmail_oauth_setup.py  # Gmail OAuth credential setup
│       └── seed_products.py      # Seed product database
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/               # shadcn/ui components
│   │   │   ├── orders/           # Order automation components
│   │   │   └── Layout/           # App layout components
│   │   ├── contexts/
│   │   │   ├── SimpleAuthContext.tsx  # JWT auth context
│   │   │   └── AuthContext.tsx        # Kratos auth context
│   │   ├── hooks/
│   │   │   ├── useUnifiedAuth.tsx     # Unified auth hook
│   │   │   └── useOrders.ts           # Order data hooks
│   │   ├── services/
│   │   │   ├── kratosService.ts       # Kratos API client
│   │   │   └── orderService.ts        # Order API client
│   │   ├── types/
│   │   │   └── orders.ts              # Order TypeScript interfaces
│   │   ├── routes/                    # Page components
│   │   └── utils/
│   │       └── apiClient.ts           # API client
│   └── package.json
├── kratos/                      # Kratos configuration
├── mcp-servers/                 # MCP server implementations
│   └── excel/                   # Excel processing MCP
├── docker-compose.yml           # Main service orchestration
├── docker-compose.dev.yml       # Development overrides (skips Kratos)
├── start-dev.sh                 # Quick start for development
├── start-prod.sh                # Quick start for production
├── .env                         # Environment variables
└── docs/                        # Documentation
```

## Data Flow

1. **Email Arrival**: Customer PO email arrives in Gmail catchment inbox
2. **Polling**: Gmail service polls for new unprocessed emails
3. **Extraction**: Anthropic Claude extracts structured order data (customer, PO#, line items, quantities)
4. **Enrichment**: Product database lookup adds manufacturing specs, materials, packaging info
5. **Form Generation**: Office Order and Works Order Excel forms are auto-generated
6. **Review**: Sharon reviews extracted data and generated forms on the dashboard
7. **Approval**: Approved orders produce downloadable .xlsx files; rejected orders are flagged with a reason

## Security

- **Dual Authentication**:
  - Development: Simple JWT with bcrypt passwords
  - Production: Ory Kratos with session management
- **Password Security**: Bcrypt hashing with salt
- **Token Management**: JWT with 7-day expiry (dev)
- **Session Security**: HTTP-only cookies (prod)
- **CORS**: Configured for frontend origin

## API Documentation

### Key Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/auth/register` | Create account (dev) | No |
| POST | `/auth/login` | Login (dev) | No |
| GET | `/auth/me` | Current user info | Yes |
| POST | `/auth/logout` | Logout | Yes |
| GET | `/api/orders/` | List orders | Yes |
| POST | `/api/orders/process-pending` | Process new emails | Yes |
| GET | `/api/orders/{id}` | Get order details | Yes |
| POST | `/api/orders/{id}/approve` | Approve order | Yes |
| POST | `/api/orders/{id}/reject` | Reject order | Yes |
| GET | `/api/products/` | List products | Yes |
| GET | `/api/system/monitor-status` | Email monitor status | Yes |

Full API documentation available at http://localhost:8006/docs

## Testing

```bash
# Test authentication
curl http://localhost:8006/auth/me \
  -H "Authorization: Bearer $TOKEN"

# Run backend tests
docker-compose exec backend pytest
```

## Troubleshooting

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

**Database Connection Failed**
- Verify PostgreSQL is running
- Check credentials in .env
- Ensure database exists

## Documentation

- [Authentication & Multi-Tenancy](docs/AUTHENTICATION.md)
- [Database Schema](docs/DATABASE_SETUP.md)
- [Project Overview](docs/PROJECT_OVERVIEW.md)
- [Feature Overview](docs/FEATURE_OVERVIEW.md)

## Production Deployment

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
VITE_API_URL=https://api.yourdomain.com
VITE_USE_SIMPLE_AUTH=false
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Check [Troubleshooting](#troubleshooting) section
- Review logs: `docker-compose logs`
- Open GitHub issue with details
