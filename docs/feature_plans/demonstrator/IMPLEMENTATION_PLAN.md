# Ramjet Plastics - Order Automation Implementation Plan

**Version:** 1.0  
**Date:** February 7, 2026  
**Status:** Ready for Development

---

## Executive Summary

This plan outlines the implementation of an automated order processing system for Ramjet Plastics. The system will monitor email inboxes, extract order data using AI (Claude Sonnet 4.5), populate internal forms automatically, and present them to Sharon for approval before distribution.

**Goal:** Eliminate manual re-keying of customer orders, reducing admin time from 10-20 minutes per order to ~2 minutes for review/approval.

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Technology Stack](#technology-stack)
3. [Database Design](#database-design)
4. [Implementation Phases](#implementation-phases)
5. [File Structure](#file-structure)
6. [Development Roadmap](#development-roadmap)
7. [Testing Strategy](#testing-strategy)
8. [Deployment Plan](#deployment-plan)
9. [Future Enhancements](#future-enhancements)

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ STAGE 1: EMAIL INTAKE                                       │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Email Catchment Inbox (catchment@ramjetplastics.com)   │ │
│ │ - Customers forward POs here                            │ │
│ │ - Zero disruption to current customer process          │ │
│ └─────────────────────────────────────────────────────────┘ │
│                          ↓                                   │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Email Monitor (Python + IMAP)                           │ │
│ │ - Polls inbox every 60 seconds                          │ │
│ │ - Downloads email body + PDF attachments                │ │
│ │ - Marks processed emails as read                        │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGE 2: DATA EXTRACTION (LLM)                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Claude Sonnet 4.5 (via Anthropic API)                   │ │
│ │ - Extract: Customer, PO#, Products, Qty, Dates, Notes  │ │
│ │ - Parse PDF attachments (text + tables)                │ │
│ │ - Confidence scoring for each field                    │ │
│ │ - Handle variations in PO formats                      │ │
│ └─────────────────────────────────────────────────────────┘ │
│                          ↓                                   │
│        Returns structured JSON with extracted data          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGE 3: DATA ENRICHMENT                                    │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Product Database Lookup (SQLite)                        │ │
│ │ - Query product master data by code                    │ │
│ │ - Retrieve 30+ fields per product:                     │ │
│ │   • Manufacturing specs (mould, cycle time, etc.)      │ │
│ │   • Material specs (grades, colours, additives)        │ │
│ │   • Packaging specs (bags, cartons, pallets)           │ │
│ │ - Get pricing information                              │ │
│ │ - Check stock levels (if available)                    │ │
│ └─────────────────────────────────────────────────────────┘ │
│                          ↓                                   │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Calculations Engine                                     │ │
│ │ - Qty to Produce = Order Qty - Stock On Hand          │ │
│ │ - Material Required = (Weight × Qty × 1.05) kg        │ │
│ │ - Bags Needed = ROUNDUP(Qty / Qty per Bag)            │ │
│ │ - Cartons Needed = ROUNDUP(Qty / Qty per Carton)      │ │
│ │ - Running Time = (Cycle Time × Qty / Cavities) hrs    │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGE 4: FORM GENERATION                                    │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Excel Template Population (openpyxl)                    │ │
│ │                                                         │ │
│ │ 1. Office Order Form (F-21):                           │ │
│ │    - Customer, Date, Order No                          │ │
│ │    - Line items with products, qty, prices             │ │
│ │    - Special instructions                              │ │
│ │    - WO/F20 checkboxes                                 │ │
│ │                                                         │ │
│ │ 2. Works Orders (one per manufacturing item):          │ │
│ │    - Header: Date, WO#, Part#, Qty, Due Date          │ │
│ │    - Product specs (from database)                     │ │
│ │    - Material specs (from database)                    │ │
│ │    - Packaging specs (from database)                   │ │
│ │    - Calculated fields (materials, bags, cartons)      │ │
│ │                                                         │ │
│ │ 3. F20 Forms (packing/dispatch):                       │ │
│ │    - TBD - need template                               │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGE 5: APPROVAL WORKFLOW                                  │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Web UI (Flask + Bootstrap)                              │ │
│ │                                                         │ │
│ │ Dashboard:                                              │ │
│ │ - List of pending orders                               │ │
│ │ - Show extracted data + confidence scores              │ │
│ │ - Preview generated forms (Excel rendered as HTML)     │ │
│ │                                                         │ │
│ │ Review Screen:                                          │ │
│ │ - Side-by-side: Original email vs. Generated forms     │ │
│ │ - Editable fields (if corrections needed)              │ │
│ │ - Buttons: [Approve] [Edit] [Reject]                   │ │
│ │                                                         │ │
│ │ Actions:                                                │ │
│ │ - Approve → Save to network folder / Email to dept     │ │
│ │ - Edit → Modify data, regenerate forms                 │ │
│ │ - Reject → Flag for manual processing                  │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGE 6: DISTRIBUTION                                       │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Output Handler                                          │ │
│ │                                                         │ │
│ │ Option A: Network Folder                                │ │
│ │ - Save Office Order to: \\server\orders\               │ │
│ │ - Save Works Orders to: \\server\production\           │ │
│ │ - Save F20s to: \\server\dispatch\                     │ │
│ │                                                         │ │
│ │ Option B: Email Distribution                            │ │
│ │ - Office Order → Sharon                                 │ │
│ │ - Works Orders → Production Manager                     │ │
│ │ - F20s → Dispatch                                       │ │
│ │                                                         │ │
│ │ Option C: Both                                          │ │
│ │ - Save AND email                                        │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Core Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Runtime** | Docker + Python 3.11 | Isolated environment, easy deployment |
| **Email Monitoring** | `imaplib` | Connect to Office 365 via IMAP |
| **PDF Parsing** | `PyPDF2`, `pdfplumber` | Extract text from PDF attachments |
| **LLM Integration** | Anthropic API (Claude Sonnet 4.5) | Extract structured data from emails |
| **Database** | SQLite 3 | Product master data |
| **Excel Generation** | `openpyxl` | Populate Office Order & Works Order templates |
| **Web UI** | Flask + Bootstrap 5 | Approval workflow interface |
| **Scheduling** | `schedule` library | Poll email inbox every 60s |
| **Logging** | Python `logging` | Audit trail of all operations |

### Python Dependencies
```
anthropic>=0.18.0
openpyxl>=3.1.0
PyPDF2>=3.0.0
pdfplumber>=0.10.0
flask>=3.0.0
schedule>=1.2.0
python-dotenv>=1.0.0
```

---

## Database Design

See `database/schema.sql` for complete schema.

### Core Tables

**products** - Product catalog
- product_code (PK)
- product_description
- customer_name
- is_active

**manufacturing_specs** - Production specifications
- product_code (FK)
- mould_no
- cycle_time_seconds
- shot_weight_grams
- num_cavities
- product_weight_grams
- estimated_running_time_hours
- machine_minimum_requirements

**packaging_specs** - Packaging requirements
- product_code (FK)
- qty_per_bag
- bag_size
- qty_per_carton
- carton_size
- cartons_per_pallet
- cartons_per_layer

**material_specs** - Material specifications (per product + colour)
- product_code (FK)
- colour
- material_grade
- material_type
- colour_no
- colour_supplier
- mb_add_rate
- additive
- additive_add_rate
- additive_supplier

**pricing** - Pricing data
- product_code (FK)
- customer_name (NULL = default)
- unit_price
- currency
- effective_date

**stock** - Inventory levels (optional for Phase 1)
- product_code (FK)
- qty_on_hand
- qty_allocated
- qty_available (computed)
- last_updated

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
**Goal:** Prove email parsing + LLM extraction works

**Deliverables:**
- ✅ Docker container with Python environment
- ✅ Email monitor connecting to Office 365
- ✅ LLM integration extracting order data
- ✅ Database with real + mock products
- ✅ Basic logging

**Success Criteria:**
- Can successfully extract data from 2 real customer emails
- Structured JSON output with 90%+ accuracy
- Logs all operations

---

### Phase 2: Office Order Form Automation (Week 3)
**Goal:** Auto-generate Office Order Forms from emails

**Deliverables:**
- ✅ Product lookup from database
- ✅ Pricing calculation
- ✅ Office Order Form template population
- ✅ Excel file generation
- ✅ Basic validation (missing products, invalid data)

**Success Criteria:**
- Generate accurate Office Order Form for Shape Aluminium order
- Generate accurate Office Order Form for Cleber order
- Handle missing products gracefully

---

### Phase 3: Works Order Automation (Week 4)
**Goal:** Auto-generate Works Orders with full specs

**Deliverables:**
- ✅ Material calculations (base material, masterbatch, additives)
- ✅ Packaging calculations (bags, cartons)
- ✅ Works Order template population
- ✅ One Works Order per manufacturing item

**Success Criteria:**
- Works Order has all 30+ fields populated correctly
- Material calculations match manual calculations
- Packaging quantities correct

---

### Phase 4: Web UI & Approval Workflow (Week 5-6)
**Goal:** Sharon can review and approve generated forms

**Deliverables:**
- ✅ Flask web application
- ✅ Dashboard showing pending orders
- ✅ Preview of generated forms
- ✅ Edit capability for corrections
- ✅ Approve/Reject workflow
- ✅ Confidence score display

**Success Criteria:**
- Sharon can log in and see pending orders
- Can preview all generated forms
- Can edit fields if extraction was wrong
- Can approve and save to network folder

---

### Phase 5: Production Deployment (Week 7)
**Goal:** Run in production with real orders

**Deliverables:**
- ✅ Production Docker deployment
- ✅ Email credentials configured
- ✅ Network folder access configured
- ✅ Error handling & monitoring
- ✅ Documentation for Sharon

**Success Criteria:**
- Process 10 real orders end-to-end
- <1% error rate requiring manual intervention
- Sharon comfortable using the system

---

## File Structure

```
ramjet-automation/
├── README.md
├── IMPLEMENTATION_PLAN.md          ← This file
├── .env.example                     ← Environment variables template
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
│
├── database/
│   ├── schema.sql                   ← Database schema
│   ├── seed_demo_data.py           ← Populate with demo products
│   ├── ramjet_products.db          ← SQLite database (gitignored)
│   └── product_lookup.py           ← Helper functions for queries
│
├── templates/                       ← Excel templates
│   ├── OFFICE_ORDER_FORM.xls
│   ├── WORKS_ORDER_FORM_MASTER.xls
│   └── F20_TEMPLATE.xls            ← TBD
│
├── examples/                        ← Sample customer orders for testing
│   ├── cleber_po0020.pdf
│   ├── shape_aluminium_po12022.pdf
│   └── sample_emails.txt
│
├── src/
│   ├── __init__.py
│   │
│   ├── email_monitor.py            ← Email polling & download
│   ├── llm_extractor.py            ← Claude API integration
│   ├── product_enrichment.py      ← Database lookups & calculations
│   ├── form_generator.py          ← Excel template population
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── order.py               ← Order data model
│   │   └── product.py             ← Product data model
│   │
│   ├── web/
│   │   ├── __init__.py
│   │   ├── app.py                 ← Flask application
│   │   ├── routes.py              ← Web routes
│   │   └── templates/
│   │       ├── base.html
│   │       ├── dashboard.html
│   │       └── review.html
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py              ← Logging configuration
│       ├── config.py              ← App configuration
│       └── validators.py          ← Data validation
│
├── tests/
│   ├── test_email_monitor.py
│   ├── test_llm_extractor.py
│   ├── test_product_enrichment.py
│   └── test_form_generator.py
│
├── docs/
│   ├── USER_GUIDE.md              ← Guide for Sharon
│   ├── SETUP.md                   ← Deployment instructions
│   └── API_REFERENCE.md           ← Code documentation
│
└── logs/                           ← Application logs (gitignored)
    ├── app.log
    └── errors.log
```

---

## Development Roadmap

### Sprint 1: Email & LLM (Week 1-2)
- [x] Set up Docker environment
- [x] Create database schema & demo data
- [ ] Implement email monitor (IMAP connection)
- [ ] Implement PDF text extraction
- [ ] Integrate Claude API for extraction
- [ ] Test with 2 real customer emails
- [ ] Logging infrastructure

### Sprint 2: Office Order Forms (Week 3)
- [ ] Product database queries
- [ ] Pricing lookups
- [ ] Office Order template mapping
- [ ] Excel file generation (openpyxl)
- [ ] Validation & error handling
- [ ] Test with 5 different order types

### Sprint 3: Works Orders (Week 4)
- [ ] Material calculation functions
- [ ] Packaging calculation functions
- [ ] Works Order template mapping
- [ ] Multi-item order handling
- [ ] Test with Cleber order (5 products)
- [ ] Test with Shape order (2 products)

### Sprint 4: Web UI (Week 5-6)
- [ ] Flask app skeleton
- [ ] Dashboard page (list pending orders)
- [ ] Review page (preview forms)
- [ ] Edit functionality
- [ ] Approve/Reject workflow
- [ ] File save/distribution
- [ ] User authentication (basic)

### Sprint 5: Production (Week 7)
- [ ] Production deployment to Docker
- [ ] Real email account configuration
- [ ] Network folder permissions
- [ ] Error monitoring & alerts
- [ ] User acceptance testing with Sharon
- [ ] Documentation & training
- [ ] Go-live!

---

## Testing Strategy

### Unit Tests
- Email parsing functions
- LLM extraction with mocked API
- Database queries
- Calculation functions
- Excel template population

### Integration Tests
- End-to-end: Email → Generated Forms
- Database lookups with real data
- File system operations
- Web UI workflows

### User Acceptance Testing
- Sharon processes 10 test orders
- Verify accuracy of generated forms
- Measure time savings
- Collect feedback on UI/UX

### Test Data
- 2 real customer emails (Cleber, Shape Aluminium)
- 10 synthetic test emails covering edge cases:
  - Multiple products
  - Unknown products
  - Missing information
  - Different PO formats
  - Large quantities
  - Rush orders

---

## Deployment Plan

### Environment Setup

**1. Docker Host Requirements:**
- Ubuntu 20.04+ or Windows Server 2019+
- Docker 24.0+
- 2GB RAM minimum
- 10GB disk space

**2. Environment Variables (.env file):**
```bash
# Email Configuration
EMAIL_SERVER=outlook.office365.com
EMAIL_PORT=993
EMAIL_USER=catchment@ramjetplastics.com
EMAIL_PASSWORD=<secure-password>
EMAIL_FOLDER=INBOX

# Anthropic API
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Database
DATABASE_PATH=/app/database/ramjet_products.db

# Output Paths
OUTPUT_FOLDER=/mnt/network/ramjet/orders
NETWORK_SHARE_USER=<username>
NETWORK_SHARE_PASSWORD=<password>

# Web UI
FLASK_SECRET_KEY=<random-secure-key>
ADMIN_PASSWORD=<secure-password>

# Logging
LOG_LEVEL=INFO
LOG_FILE=/app/logs/app.log
```

**3. Network Access:**
- Port 5000 (web UI) - internal network only
- Port 993 (IMAP) - outbound to Office 365
- HTTPS 443 (Anthropic API) - outbound

**4. File Permissions:**
- Read: Excel templates directory
- Read: Database directory
- Write: Output folder (network share)
- Write: Logs directory

### Deployment Steps

**1. Clone Repository:**
```bash
git clone https://github.com/your-org/ramjet-automation
cd ramjet-automation
```

**2. Configure Environment:**
```bash
cp .env.example .env
nano .env  # Edit with actual credentials
```

**3. Build & Start:**
```bash
docker-compose up -d
```

**4. Verify Database:**
```bash
docker exec ramjet-automation python database/seed_demo_data.py
```

**5. Test Email Connection:**
```bash
docker exec ramjet-automation python -m src.email_monitor --test
```

**6. Access Web UI:**
```
http://<server-ip>:5000
Login: admin / <ADMIN_PASSWORD from .env>
```

---

## Future Enhancements (Post-Phase 5)

### Stage 2: Operational Visibility
- Dashboard showing orders in progress
- Real-time workload view (machine utilization)
- Stock level integration with MYOB
- Material allocation against confirmed orders
- Production planning & scheduling

### Stage 3: End-to-End Integration
- Auto-trigger F20 when Works Order completed
- Link to dispatch system
- Invoice generation from completed orders
- Payment status tracking
- Customer portal for order status

### Potential Integrations
- MYOB API (customer data, invoicing)
- SMS notifications for rush orders
- Mobile app for shop floor
- QR codes on Works Orders for tracking
- Barcode scanning for stock management

---

## Risk Assessment & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| LLM extraction errors | Medium | Medium | Human approval workflow, confidence scores |
| Email connection fails | High | Low | Retry logic, error alerts, fallback to manual |
| Unknown products | Medium | Medium | Search similar products, flag for Sharon |
| Network folder access issues | Medium | Low | Email fallback, local save option |
| Database corruption | High | Low | Daily backups, transaction logging |
| Excel template changes | Medium | Low | Version control templates, validation |

---

## Success Metrics

### Phase 1 (Immediate)
- ✅ 90%+ accuracy in data extraction
- ✅ Process 1 order end-to-end without errors
- ✅ All 30+ Works Order fields populated

### Phase 2 (1 Month)
- ⏱️ Reduce order processing time from 15 min → 2 min
- 📊 Process 50+ orders successfully
- 🎯 <5% rejection rate (requiring manual handling)
- 😊 Sharon satisfaction score 8/10+

### Phase 3 (3 Months)
- 📈 100+ orders processed
- ⚡ <1 minute average review time
- 🔍 Zero transcription errors
- 💰 ROI: 10+ hours/week saved

---

## Support & Maintenance

### Monitoring
- Daily log review (automated email digest)
- Weekly metrics report (orders processed, errors, time saved)
- Monthly review meeting with Grant & Sharon

### Maintenance Tasks
- Weekly: Review flagged/rejected orders
- Monthly: Database backup verification
- Quarterly: Product database updates
- Annually: Security review, dependency updates

### Contact
- Developer: Brett (brett@example.com)
- Primary User: Sharon
- Stakeholder: Grant (grant@ramjetplastics.com)

---

## Appendix

### A. Database Query Examples
See `database/product_lookup.py` for helper functions.

### B. LLM Prompt Templates
See `src/llm_extractor.py` for extraction prompts.

### C. Excel Template Cell Mappings
See `src/form_generator.py` for field mappings.

### D. Sample Customer Emails
See `examples/` directory.

---

**Document Version:** 1.0  
**Last Updated:** February 7, 2026  
**Next Review:** Start of Phase 2
