# AfriEdge Security Model & Access Governance

## 1. Authentication & Session Management
- **Frontend Auth:** NextAuth.js session management with JWT tokens.
- **API Protection:** FastAPI Bearer token dependency validates user identities on stateful operations.
- **Tenant Isolation:** All saved portfolios (`saved_portfolios`) and research queries are strictly scoped to `user_id`. Cross-user data leakage is guarded at the SQL query level:
  `filter(SavedPortfolio.id == portfolio_id, SavedPortfolio.user_id == current_user.id)`.

## 2. Secrets & Credential Protection
- Zero credentials or secrets committed in Git history.
- `.env` files explicitly excluded via `.gitignore`.
- Browser bundle security: No secret (`DATABASE_URL`, `REDIS_URL`, `LLM_API_KEY`) is ever prefixed with `NEXT_PUBLIC_` or bundled in client-side code.

## 3. Input Validation & Data Sanitization
- Strict Pydantic v2 schemas on all incoming API request payloads.
- PII scrubbing implemented in `packages/security/pii_scrubber.py` to sanitize user queries before forwarding to external LLM providers.
- CORS restricted to verified origins in production.
