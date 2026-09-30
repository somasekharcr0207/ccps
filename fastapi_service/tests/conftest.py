import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SIGNING_KEY"] = "test-key"
os.environ["PAYMENT_SUCCESS_RATE"] = "1.0"

from datetime import datetime, timedelta, timezone  # noqa: E402

import jwt  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app import database  # noqa: E402
from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Card, User  # noqa: E402


@pytest.fixture()
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = Session()

    def override():
        yield session

    app.dependency_overrides[database.get_db] = override
    yield session
    session.close()
    app.dependency_overrides.clear()


@pytest.fixture()
def client(db):
    return TestClient(app)


def make_token(user_id, token_type="access", key=None, exp_minutes=30):
    payload = {"user_id": user_id, "token_type": token_type,
               "exp": datetime.now(timezone.utc) + timedelta(minutes=exp_minutes)}
    return jwt.encode(payload, key or settings.JWT_SIGNING_KEY, algorithm="HS256")


@pytest.fixture()
def user(db):
    u = User(id=1, username="alice", is_active=True)
    db.add(u)
    db.add(User(id=2, username="bob", is_active=True))
    db.commit()
    return u


@pytest.fixture()
def card(db, user):
    c = Card(id=10, user_id=1, card_holder_name="Alice", card_type="CREDIT", brand="VISA",
             masked_number="**** **** **** 1111", last4="1111", expiry_month=12, expiry_year=2035)
    db.add(c)
    db.commit()
    return c


@pytest.fixture()
def auth(user):
    return {"Authorization": f"Bearer {make_token(user.id)}"}
