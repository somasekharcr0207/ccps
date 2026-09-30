# Credit Card Payment System

Backend for a simulated credit card payment system. No real payment gateway is used.

- **Django + DRF** (port 8000): authentication, cards, transactions, admin panel
- **FastAPI** (port 8001): payment processing (PENDING, then SUCCESS or FAILED)
- **MySQL**: shared database
- **Scope note:** this submission covers the backend modules. The React frontend (Module 6) is [not included / add details here]. All features are demonstrated through Swagger.

## Credentials (seeded by `python manage.py seed_demo`)

| Role | Username | Password |
|---|---|---|
| Admin | admin | Admin@12345 |
| Normal user | demo | Demo@12345 |

## Setup (local)

Prerequisites: Python 3.12, MySQL 8.

1. Create the database and user:
```sql
   CREATE DATABASE ccps;
   CREATE USER 'ccps_user'@'%' IDENTIFIED BY 'ccps_pass';
   GRANT ALL ON *.* TO 'ccps_user'@'%';
```
   `ALL ON *.*` lets Django create its test database when running tests. Use a narrower grant in production.
2. Copy `.env.example` to `.env` in both `django_backend` and `fastapi_service`, and fill in the values.
   `JWT_SIGNING_KEY` must be identical in both files.
3. Django (terminal 1):
```powershell
   cd django_backend
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py seed_demo
   python manage.py runserver 8000
```
4. FastAPI (terminal 2):
```powershell
   cd fastapi_service
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   uvicorn app.main:app --port 8001 --reload
```

To load the provided data instead, import `db/ccps_dump.sql` into an empty `ccps` database.

## Docker

Dockerfiles for Django, FastAPI and MySQL plus `docker-compose.yml` are provided:
```
docker compose up --build
```
The verified setup path is the local setup above. [If you test Docker later, replace this sentence.]

## API documentation

- Django Swagger: http://localhost:8000/api/docs/
- FastAPI Swagger: http://localhost:8001/docs
- Postman collection: `postman/CCPS.postman_collection.json`

Typical flow: log in (`POST /api/auth/login/`), add a card (`/api/cards/`), pay through FastAPI with the same JWT, then view history with filters for date, amount and status. The CSV export and daily summary are admin-only.

## Security

- Passwords hashed with PBKDF2-SHA256
- JWT authentication on all protected routes (Django and FastAPI share the signing key)
- Only the masked card number and last 4 digits are stored. The full number and CVV are validated, then discarded and never persisted
- Input validation: Luhn check, CVV length, positive amounts, unexpected fields rejected in FastAPI
- ORM queries only, so there is no raw SQL (SQL injection protection)
- Secrets come from environment variables, and `.env` is gitignored

## Testing

```powershell
cd django_backend
coverage run manage.py test
coverage report        # 92% total
cd ..\fastapi_service
pytest --cov=app       # 13 tests, 97% coverage
```

## Database schema

Tables: users, cards, transactions and admin_logs (also in `db/schema.sql`).

```sql
-- Reference schema (MySQL 8). Django migrations are the source of truth; this mirrors them for review.
CREATE TABLE users (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  password VARCHAR(128) NOT NULL,              -- PBKDF2-SHA256 hash, never plain text
  last_login DATETIME(6) NULL,
  is_superuser TINYINT(1) NOT NULL,
  username VARCHAR(150) NOT NULL UNIQUE,
  first_name VARCHAR(150) NOT NULL,
  last_name VARCHAR(150) NOT NULL,
  email VARCHAR(254) NOT NULL UNIQUE,
  is_staff TINYINT(1) NOT NULL,
  is_active TINYINT(1) NOT NULL,
  date_joined DATETIME(6) NOT NULL
);

CREATE TABLE cards (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT NOT NULL,
  card_holder_name VARCHAR(100) NOT NULL,
  card_type VARCHAR(6) NOT NULL,               -- CREDIT | DEBIT
  brand VARCHAR(12) NOT NULL,
  masked_number VARCHAR(25) NOT NULL,          -- **** **** **** 1111
  last4 CHAR(4) NOT NULL,
  expiry_month SMALLINT UNSIGNED NOT NULL,
  expiry_year SMALLINT UNSIGNED NOT NULL,
  created_at DATETIME(6) NOT NULL,
  -- NOTE: no full card number column, no CVV column
  CONSTRAINT fk_cards_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_cards_user_last4 (user_id, last4)
);

CREATE TABLE transactions (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  reference CHAR(36) NOT NULL UNIQUE,
  user_id BIGINT NOT NULL,
  card_id BIGINT NULL,
  amount DECIMAL(12,2) NOT NULL,
  currency CHAR(3) NOT NULL,
  description VARCHAR(255) NOT NULL,
  status VARCHAR(7) NOT NULL,                  -- PENDING | SUCCESS | FAILED
  failure_reason VARCHAR(255) NOT NULL,
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  CONSTRAINT fk_txn_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_txn_card FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE SET NULL,
  INDEX idx_txn_status (status),
  INDEX idx_txn_created (created_at)
);

CREATE TABLE admin_logs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  admin_id BIGINT NULL,
  action VARCHAR(20) NOT NULL,
  details LONGTEXT NOT NULL,
  created_at DATETIME(6) NOT NULL,
  CONSTRAINT fk_log_admin FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE SET NULL
);
```

## Screenshots

See `docs/screenshots/`.

