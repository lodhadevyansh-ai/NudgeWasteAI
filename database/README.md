# NudgeWasteAI Database Package

The `database` directory is a self-contained, modular Python package providing MongoDB persistence, connection lifecycle management, data-access collection abstractions, Pydantic document schemas, indexing scripts, and seed utilities for the **NudgeWasteAI** platform.

---

## 1. Package Architecture

```text
database/
├── collections/             # Data-access collection abstraction modules
│   ├── analytics.py         # Aggregation pipelines for dashboards & reporting
│   ├── credits.py           # Swachh Credits transaction logs & duplicate checks
│   ├── disposals.py         # Disposal event records & history queries
│   ├── nudges.py            # Micro-nudge guidance persistence
│   ├── predictions.py      # Classification prediction event records
│   ├── rewards.py           # Municipal rewards catalog & redemption vouchers
│   ├── users.py             # User accounts & credit balance atomic updates
│   └── waste.py             # Statutory waste stream category definitions
├── config/                  # Configuration settings
│   ├── collections_config.py# Centralized collection name constants & enum
│   └── database_config.py   # Pydantic-settings database configuration
├── connection/              # MongoDB connection pool & health ping
│   ├── health.py            # Diagnostic ping & credential URI sanitizer
│   └── mongodb.py           # Shared MongoDBManager singleton connection pool
├── indexes/                 # Collection index creation definitions
│   ├── analytics_indexes.py
│   ├── credits_indexes.py   # Unique & partial index definitions
│   ├── disposals_indexes.py # History & analytics compound indexes
│   ├── nudges_indexes.py
│   ├── predictions_indexes.py
│   ├── rewards_indexes.py
│   ├── users_indexes.py     # Unique email & user ID indexes
│   └── waste_indexes.py
├── schemas/                 # Pydantic document persistence models
│   ├── analytics_schema.py
│   ├── credit_schema.py
│   ├── disposal_schema.py
│   ├── nudge_schema.py
│   ├── prediction_schema.py
│   ├── reward_schema.py
│   ├── user_schema.py
│   └── waste_schema.py
├── scripts/                 # Maintenance CLI execution scripts
│   ├── create_indexes.py    # Standalone idempotent index creator
│   ├── health_check.py      # Diagnostic CLI health ping script
│   ├── reset_database.py    # Safe development DB reset script
│   └── setup_database.py    # Database initialization & setup script
├── seed/                    # Reference data seed modules
│   ├── rewards_seed.py      # Municipal incentive catalog seed
│   ├── users_seed.py        # Demo user seed module
│   ├── waste_seed.py        # Statutory waste streams seed
│   └── run_seed.py          # Master seed execution runner
├── tests/                   # Pytest unit & integration test suites
│   ├── test_collections.py  # Data-access collection unit tests
│   ├── test_config.py       # Config validation unit tests
│   ├── test_connection.py   # Connection pool & ping unit tests
│   ├── test_indexes.py      # Index creation & repeatability tests
│   ├── test_schemas.py      # Document schema validation tests
│   └── test_seed.py         # Seed idempotency & reset safeguard tests
├── .env.example             # Environment configuration template
├── pyproject.toml           # Package installation manifest
├── requirements.txt         # Package dependencies
└── README.md                # Component documentation
```

---

## 2. Prerequisites & Installation

### Prerequisites
- Python 3.10+
- MongoDB 6.0+ (Local instance `mongodb://localhost:27017` or MongoDB Atlas URI)

### Package Installation
Install the database package in editable mode within your Python virtual environment:

```powershell
.venv\Scripts\pip.exe install -e database
```

---

## 3. Environment Variables Configuration

Create or update `.env` in the root workspace directory or set environment variables:

```env
# MongoDB Database Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=nudgewaste_db
MONGODB_TIMEOUT_MS=1500
MONGODB_MAX_POOL_SIZE=50
```

---

## 4. Setup, Index Creation, & Seeding

### Full Database Setup
Initialize MongoDB connection, build all required indexes, and seed baseline reference data:

```powershell
.venv\Scripts\python.exe -m database.scripts.setup_database
```

### Standalone Index Creation
Create or verify all collection indexes idempotently:

```powershell
.venv\Scripts\python.exe -m database.scripts.create_indexes
```

### Standalone Reference Seeding
Seed baseline statutory waste categories, municipal rewards, and demo user:

```powershell
.venv\Scripts\python.exe -m database.seed.run_seed
```

---

## 5. Health Check Diagnostics

Run the database health diagnostic script to verify connection and latency without exposing URI credentials:

```powershell
.venv\Scripts\python.exe -m database.scripts.health_check
```

Sample Output:
```json
{
  "status": "healthy",
  "is_connected": true,
  "database_name": "nudgewaste_db",
  "sanitized_uri": "mongodb://localhost:27017",
  "latency_ms": 1.25,
  "error": null
}
```

---

## 6. Running Automated Tests

Run the complete database test suite:

```powershell
.venv\Scripts\python.exe -m pytest database/tests
```

Run both backend and database test suites together:

```powershell
.venv\Scripts\python.exe -m pytest database/tests backend/tests
```

---

## 7. Safety & Maintenance Scripts

### Database Reset Safeguards
To reset a development or test database:

```powershell
.venv\Scripts\python.exe -m database.scripts.reset_database --confirm-reset
```

> **Safety Safeguard:** The reset script will raise a `PermissionError` and terminate immediately if:
> 1. `--confirm-reset` flag is omitted.
> 2. `MONGODB_DB_NAME` contains `_prod` or `production`.

---

## 8. Troubleshooting

- **Index Name Conflicts (`IndexOptionsConflict`):** The index creation functions use `safe_create_index()` to catch code 85 error and reuse pre-existing index structures gracefully.
- **Duplicate Null Keys in Credit Transactions:** `credits_indexes.py` uses `partialFilterExpression={"disposal_id": {"$type": "string"}}` to ensure string disposal IDs are unique while permitting multiple reward redemptions where `disposal_id` is null.
- **Import Errors:** Ensure `database` is installed in editable mode (`pip install -e database`) or run python modules from the repository root using `.venv\Scripts\python.exe -m <module_name>`.
