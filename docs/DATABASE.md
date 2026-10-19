# NAKSHA Database Guide (PostgreSQL + PostGIS)

This document provides exact PowerShell commands to manage the PostgreSQL + PostGIS database environment for NAKSHA on Windows.

---

## 1. Quick Start (Docker Desktop)

Ensure Docker Desktop is running.

### Start Database Service
Start the PostgreSQL container in background:
```powershell
docker compose up -d
```
Verify the container is healthy:
```powershell
docker compose ps
```

### Stop Database Service
Stop containers without losing persisted data:
```powershell
docker compose down
```

### Reset Database (Wipe Volume and Re-initialize)
Stops the container, deletes the Docker volume (`naksha_pgdata`), and restarts afresh with `docker/init-test-db.sh`:
```powershell
docker compose down -v
docker compose up -d
```

---

## 2. Interactive psql Shell

### Connect to Primary Application Database (`naksha`)
```powershell
docker compose exec -it db psql -U naksha_dev -d naksha
```

### Connect to Test Database (`naksha_test`)
```powershell
docker compose exec -it db psql -U naksha_dev -d naksha_test
```

### Verify PostGIS Extension
Inside psql, run:
```sql
SELECT postgis_full_version();
```

---

## 3. Database Connection URLs

Configure these in your `.env` or set as environment variables:

| Variable | Description | Value |
|---|---|---|
| `NAKSHA_DATABASE_URL` | Main Application Database | `postgresql+psycopg://naksha_dev:naksha_dev_pw@localhost:5432/naksha` |
| `NAKSHA_TEST_DATABASE_URL` | Automated Test Database | `postgresql+psycopg://naksha_dev:naksha_dev_pw@localhost:5432/naksha_test` |
| `NAKSHA_LEDGER_PRIVATE_KEY` | Ed25519 32-byte hex signing key for Trust Ledger | Required in production (generate via `python -m naksha.cli generate-ledger-key`) |

> **Note**: If `NAKSHA_DATABASE_URL` is omitted, NAKSHA defaults to SQLite (`sqlite:///naksha_spatial.db`), keeping local offline development fully functional without Docker.

---

## 4. Alembic Migrations

Alembic targets `NAKSHA_DATABASE_URL` by default. To target the dedicated test database, pass `-x db=test`.

### Run Migrations Against Main Database
```powershell
$env:NAKSHA_DATABASE_URL="postgresql+psycopg://naksha_dev:naksha_dev_pw@localhost:5432/naksha"
alembic upgrade head
```

### Run Migrations Against Test Database
```powershell
$env:NAKSHA_TEST_DATABASE_URL="postgresql+psycopg://naksha_dev:naksha_dev_pw@localhost:5432/naksha_test"
alembic -x db=test upgrade head
```

### Downgrade Database
```powershell
# Downgrade to base on test DB
alembic -x db=test downgrade base
```

---

## 5. Running Tests

Run all unit and integration tests (Postgres tests automatically skipped if Postgres is unreachable):
```powershell
pytest -q
```

Run tests with PostgreSQL + PostGIS enabled:
```powershell
$env:NAKSHA_TEST_DATABASE_URL="postgresql+psycopg://naksha_dev:naksha_dev_pw@localhost:5432/naksha_test"
pytest -q -m postgres
```
