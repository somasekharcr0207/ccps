# Credit Card Payment System - Backend

Django (auth, cards, transactions, admin) + FastAPI (payment processing) on a shared MySQL database.
**No real payment gateway is used. No CVV or full card number is ever stored.**

## Architecture
```
React  --JWT-->  Django :8000  (auth, cards, history, admin, CSV)   \
       --JWT-->  FastAPI :8001 (make payment: PENDING -> SUCCESS/FAILED) --> MySQL :3306
```
Django issues JWTs (HS256). FastAPI verifies the same token with the shared `JWT_SIGNING_KEY`.
Django owns the schema (migrations); FastAPI reads `users`/`cards` and writes `transactions`.

## Setup (local, Windows PowerShell)
```powershell
# 1. MySQL: create DB
mysql -u root -p -e "CREATE DATABASE ccps CHARACTER SET utf8mb4; CREATE USER 'ccps_user'@'%' IDENTIFIED BY 'ccps_pass'; GRANT ALL ON ccps.* TO 'ccps_user'@'%';"

# 2. Django
cd django_backend
python -m venv venv ; .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env          # edit secrets
python manage.py makemigrations accounts cards transactions adminpanel
python manage.py migrate
python manage.py seed_demo      # admin / demo users
python manage.py runserver 8000

# 3. FastAPI (new terminal)
cd fastapi_service
python -m venv venv ; .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env          # JWT_SIGNING_KEY MUST equal Django's
uvicorn app.main:app --port 8001 --reload
```
Commit the generated `*/migrations/0001_initial.py` files to Git.

## Docker
```bash
docker compose up --build
docker compose exec django python manage.py makemigrations accounts cards transactions adminpanel  # first time only, then commit
docker compose exec django python manage.py migrate
docker compose exec django python manage.py seed_demo
```
Add a `frontend/Dockerfile` (Node build -> nginx) and uncomment the `frontend` service in `docker-compose.yml`.

## API docs
- Django Swagger: http://localhost:8000/api/docs/  (ReDoc `/api/redoc/`, schema `/api/schema/`)
- FastAPI Swagger: http://localhost:8001/docs
- Postman: `postman/CCPS.postman_collection.json`

| Module | Method & path | Auth |
|---|---|---|
| Auth | POST `/api/auth/register/` `/login/` `/refresh/` `/logout/`, GET `/me/` | public / JWT |
| Cards | GET,POST `/api/cards/`, GET,DELETE `/api/cards/{id}/` | JWT (own cards) |
| Payments (FastAPI) | POST `/payments`, GET `/payments`, GET `/payments/{reference}` | JWT |
| Transactions | GET `/api/transactions/?status=&min_amount=&max_amount=&date_from=&date_to=` | JWT (own) |
| Export | GET `/api/transactions/admin/export/` (same filters, CSV) | Admin |
| Admin | `/api/admin/users/`, `users/{id}/` (PATCH is_active), `cards/`, `transactions/`, `daily-summary/`, `logs/` | Admin |

Django admin site: `/django-admin/`.

## Database schema
See `db/schema.sql` - tables `users`, `cards`, `transactions`, `admin_logs` (plus Django/JWT blacklist tables).

## Security
- Passwords hashed with PBKDF2-SHA256 + Django password validators
- JWT access (30 min) + rotating refresh with blacklist on logout
- Card number and CVV are validated (Luhn, format) then discarded; only brand, masked number, last4, expiry stored
- FastAPI request model rejects unknown fields (`cvv`, `card_number`) with 422
- Serializer/Pydantic validation everywhere; ORM only (parameterised queries) -> SQL injection safe
- Users can only access their own cards/transactions; admin endpoints require `is_staff`
- CSV export escapes spreadsheet-formula injection; admin actions recorded in `admin_logs`
- Secrets from environment, CORS restricted, login/register throttled

## Tests
```powershell
cd django_backend
$env:DB_ENGINE="sqlite"
coverage run manage.py test ; coverage report

cd ..\fastapi_service
pytest          # coverage printed automatically
```

## Demo credentials
Created by `seed_demo`: admin `admin` / `Admin@12345`, user `demo` / `Demo@12345`
(override with `ADMIN_PASSWORD`, `DEMO_USER_PASSWORD`; change before any real deployment).

## Database dump
```bash
mysqldump -u ccps_user -p --no-tablespaces ccps > db/ccps_dump.sql
```
