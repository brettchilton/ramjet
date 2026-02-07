# Ramjet Plastics - Order Automation System

Automated order processing system for Ramjet Plastics. Monitors email, extracts customer orders using AI, auto-generates Office Orders and Works Orders, and presents them to Sharon for approval.

## Quick Start

### Prerequisites
- Docker 24.0+
- Python 3.11+ (for local development)
- Office 365 email account
- Anthropic API key

### Setup

1. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

2. **Initialize Database**
   ```bash
   python database/seed_demo_data.py
   ```

3. **Run with Docker**
   ```bash
   docker-compose up -d
   ```

4. **Access Web UI**
   ```
   http://localhost:5000
   ```

## Project Structure

```
ramjet-automation/
├── IMPLEMENTATION_PLAN.md     ← Complete implementation guide
├── database/                   ← Product database
│   ├── schema.sql             ← Database schema
│   ├── seed_demo_data.py      ← Demo data generator
│   ├── ramjet_products.db     ← SQLite database
│   └── product_lookup.py      ← Query helper functions
├── templates/                  ← Excel templates
├── examples/                   ← Sample customer orders
└── docs/                       ← Documentation
```

## Current Status

✅ **Phase 0: Planning & Database**
- [x] Database schema designed
- [x] Demo data with 57 products (7 real + 50 mock)
- [x] Product lookup utilities
- [x] Implementation plan documented

⏳ **Phase 1: Email & LLM** (In Progress)
- [ ] Email monitor
- [ ] PDF extraction
- [ ] Claude API integration

## Key Files

- **IMPLEMENTATION_PLAN.md** - Complete 7-phase implementation roadmap
- **database/ramjet_products.db** - Product master database ready for use
- **database/product_lookup.py** - Helper functions for database queries
- **examples/*.pdf** - Real customer orders for testing

## Database

The system uses SQLite with a complete product master database including:

- **57 products** with full specifications
- **Manufacturing data**: moulds, cycle times, cavities, weights
- **Material data**: grades, colours, suppliers, additives
- **Packaging data**: bags, cartons, pallets
- **Pricing data**: unit costs per product/colour

### Query Examples

```python
from database.product_lookup import get_product_full_specs, calculate_material_requirements

# Get complete product specs
specs = get_product_full_specs('LOCAP2', 'Black')

# Calculate materials for an order
materials = calculate_material_requirements('LOCAP2', 'Black', 1000)
```

## Development

### Local Development
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run Tests
```bash
pytest tests/
```

## Documentation

- **IMPLEMENTATION_PLAN.md** - Complete project roadmap and architecture
- **docs/SETUP.md** - Deployment instructions (TBD)
- **docs/USER_GUIDE.md** - User guide for Sharon (TBD)
- **docs/API_REFERENCE.md** - Code documentation (TBD)

## Support

- **Developer**: Brett
- **Primary User**: Sharon
- **Stakeholder**: Grant (grant@ramjetplastics.com)

## License

Proprietary - Ramjet Plastics Pty Ltd
