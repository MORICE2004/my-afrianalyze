# AfriEdge Database Runbook

## 1. Overview
AfriEdge utilizes PostgreSQL (>= 15) as its persistent transactional and evidence datastore. It stores:
- Users & authentication metadata (`users`)
- Saved investment portfolios & holdings (`saved_portfolios`, `portfolio_holdings`)
- Issuer universe (`companies`)
- Regulatory & annual report documents (`documents`)
- Daily pricing & turnover records (`market_prices`)
- Research run execution tracking (`research_runs`)
- Lineage-backed extraction evidence (`evidence`)

## 2. Configuration & Connection Lifecycle
Database connection string is configured via `DATABASE_URL`:
`postgresql://<USER>:<PASSWORD>@<HOST>:<PORT>/<DATABASE>?sslmode=require`

Connection pooling is managed via SQLAlchemy in `packages/database/session.py`:
- `pool_pre_ping=True`: Detects stale connections before checkout
- `pool_recycle=300`: Recycles idle connections every 5 minutes to prevent cloud gateway drops
- SSL enforcement: Required for managed cloud providers (Neon, Supabase, Cloud SQL)

## 3. Bootstrap & Migration Sequence

### Empty Database Bootstrap:
```bash
# Set environment
export DATABASE_URL="postgresql://user:pass@host:5432/afriedge?sslmode=require"

# Execute migration from clean slate
alembic upgrade head
```

### Verification Query:
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';
-- Expected: companies, documents, evidence, market_prices, portfolio_holdings, research_runs, saved_portfolios, users
```

### Rollback / Downgrade:
```bash
# Rollback single migration
alembic downgrade -1

# Rollback to clean slate
alembic downgrade base
```

## 4. Backup & Disaster Recovery Assumptions
- **Managed Automated Backups:** Continuous point-in-time recovery (PITR) with minimum 7-day retention.
- **Manual Snapshot:** Prior to major migrations:
  ```bash
  pg_dump -Fc --no-acl --no-owner -h <HOST> -U <USER> -d afriedge > backup_$(date +%Y%m%d_%H%M%S).dump
  ```
- **Restore:**
  ```bash
  pg_restore -h <HOST> -U <USER> -d afriedge --clean --if-exists backup_<TIMESTAMP>.dump
  ```
