# KosherPay Backend

Backend service for **KosherPay** — a digital payments platform with REST APIs, IVR integration (Yemot), JWT-based authentication, and PostgreSQL transaction processing.

---

## Table of Contents
- [Overview](#overview)
- [Core Features](#core-features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Local Setup](#local-setup)
- [Environment Variables](#environment-variables)
- [Running the Service](#running-the-service)
- [API Overview](#api-overview)
- [Authentication & Authorization](#authentication--authorization)
- [IVR (Yemot) Flow](#ivr-yemot-flow)
- [Health & Observability](#health--observability)
- [Security Notes](#security-notes)
- [Troubleshooting](#troubleshooting)
- [Production Considerations](#production-considerations)

---

## Overview
KosherPay Backend provides the server-side capabilities for account onboarding and payment operations:
- User account creation and login.
- Wallet operations (balance, deposit, withdrawal, transfer).
- Payment request lifecycle (create, list, approve, reject).
- User profile management.
- Admin visibility endpoints.
- IVR-compatible flows for telephony interactions.

The project follows a layered architecture to separate HTTP transport concerns, business logic, and data-access responsibilities.

---

## Core Features
- **Modular API surface** across `web`, `admin`, and `ivr` routes.
- **JWT authentication** with strict token type enforcement.
- **Role-based authorization** for protected admin operations.
- **Transactional PostgreSQL operations** via `psycopg`.
- **Brute-force mitigation** through failed-login tracking and temporary lockouts.
- **IVR session persistence** via Redis (with in-memory fallback in development).

---

## Architecture
The codebase is organized into clear layers:

1. **Routes (`routes/`)**  
   FastAPI endpoints, request parsing, and HTTP-level response mapping.

2. **Domain Services (`domain/`)**  
   Business rules for auth, wallet actions, payment requests, and profile updates.

3. **Repositories (`repositories/`)**  
   SQL queries and PostgreSQL persistence operations.

4. **Infrastructure (`auth/`, `db/`, `ivr/`)**  
   JWT handling, password hashing, DB connection management, Redis/session utilities, and IVR helpers.

---

## Project Structure
```text
KosherPayBackend/
├── app.py
├── requirements.txt
├── auth/
├── db/
├── domain/
├── ivr/
├── repositories/
├── routes/
└── schemas/
```

---

## Technology Stack
- Python 3.11+
- FastAPI
- Uvicorn
- PostgreSQL + psycopg v3
- PyJWT
- bcrypt
- Redis (production-required for IVR session durability)
- python-dotenv

---

## Prerequisites
Before running locally, ensure:
- Python is installed.
- PostgreSQL is available and initialized with the required schema.
- Redis is available (recommended for local parity; required in production).
- A valid `.env` file is configured.

> Note: This repository currently does not include migration files. Database tables must already exist (e.g. `users`, `user_phones`, `user_auth`, `wallets`, `transactions`, `payment_requests`, `bank_accounts`).

---

## Local Setup
1. Clone the repository:
```bash
git clone https://github.com/YochiRozental/KosherPayBackend.git
cd KosherPayBackend
```

1. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate
```

1. Install dependencies:
```bash
pip install -r requirements.txt
```

1. Create a `.env` file using the template below.

---

## Environment Variables
Example `.env`:

```env
# App
ENV=dev
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=kosherpay
DB_USER=postgres
DB_PASSWORD=postgres

# JWT
JWT_SECRET=replace-with-a-strong-secret
JWT_ISSUER=kosherpay
JWT_ALGORITHM=HS256
JWT_ACCESS_TTL_MIN=30
JWT_REFRESH_TTL_DAYS=14

# Auth lock policy
AUTH_MAX_FAILED=5
AUTH_LOCK_MINUTES=15

# Redis
REDIS_URL=redis://localhost:6379/0
```

Important:
- `JWT_SECRET` is mandatory; the application fails fast if missing.
- In `ENV=prod`, Redis connectivity is required.
- PostgreSQL connection uses `sslmode=require`.

---

## Running the Service
Start the API server:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Quick health check:

```bash
curl http://localhost:8000/
```

Interactive docs:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## API Overview
### Web API (`/api/web`)
- `POST /open_account`
- `POST /login`
- `GET /balance`
- `GET /history`
- `POST /deposit`
- `POST /withdraw`
- `POST /transfer`
- `POST /request_payment`
- `GET /payment_requests`
- `GET /payment_requests_sent`
- `POST /payment_requests/{req_id}/approve`
- `POST /payment_requests/{req_id}/reject`
- `GET /me`
- `PUT /me`

### Admin API (`/api/admin`)
- `GET /users` (admin-only)

### IVR API (`/ivr`)
- `GET /api?action=...`
  - user existence checks
  - account opening
  - login
  - balance retrieval
  - transfers
  - payment requests (send/approve/reject)
  - transaction history retrieval
  - profile edits

---

## Authentication & Authorization
1. Authenticate via `POST /api/web/login`.
2. Receive:
   - `access_token`
   - `refresh_token`
   - basic user payload
3. Send protected requests with:
   ```http
   Authorization: Bearer <access_token>
   ```
4. Admin routes enforce `role == "admin"`.

---

## IVR (Yemot) Flow
The IVR integration supports stateful menu-driven interactions through session keys:
- Authentication-aware flows.
- Multi-step input collection (phone, amount, dates, etc.).
- Action-specific cleanup of session values.
- Redis-backed session persistence (or in-memory fallback in development).

---

## Health & Observability
- `GET /` — service health.
- `GET /api/web/db-health` — DB connectivity check (`SELECT 1`).
- Global exception handler returns a consistent 500 response payload.
- Logging level is controlled via `LOG_LEVEL`.

---

## Security Notes
- Secret codes are stored as bcrypt hashes.
- JWT validation enforces issuer, expiry, and token type.
- Failed login attempts trigger temporary account lockout.
- Sensitive values should be managed through environment variables / secret managers.
- CORS should be restricted to trusted origins in production.

---

## Troubleshooting
- **Application fails at startup**
  - Verify `JWT_SECRET` is set.
  - Verify all DB credentials are set.

- **Database connection errors**
  - Verify PostgreSQL host/port/user/password.
  - Confirm SSL requirements are compatible (`sslmode=require`).

- **401 on protected routes**
  - Confirm Bearer token is valid and unexpired.

- **IVR state inconsistencies in local dev**
  - In-memory fallback does not persist across process restarts.

---

## Production Considerations
Recommended hardening for production deployments:
- Run behind a secure reverse proxy with TLS termination.
- Use managed, highly available Redis.
- Add rate limiting for authentication and financial operations.
- Implement audit logging for financial state transitions.
- Introduce CI checks (tests, linting, static analysis).
- Manage database schema changes with structured migrations (e.g., Alembic).