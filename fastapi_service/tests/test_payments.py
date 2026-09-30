from app.config import settings
from app.models import Card, Transaction

from .conftest import make_token


def pay(client, auth, **over):
    body = {"card_id": 10, "amount": "150.50", "description": "Order #1"}
    body.update(over)
    return client.post("/payments", json=body, headers=auth)


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_requires_token(client, card):
    assert client.post("/payments", json={"card_id": 10, "amount": "1"}).status_code == 401


def test_rejects_bad_tokens(client, card):
    for tok in (make_token(1, key="wrong"), make_token(1, token_type="refresh"),
                make_token(1, exp_minutes=-5), make_token(999), "garbage"):
        r = client.post("/payments", json={"card_id": 10, "amount": "1"},
                        headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 401


def test_inactive_user_rejected(client, card, db, auth):
    from app.models import User
    db.get(User, 1).is_active = False
    db.commit()
    assert pay(client, auth).status_code == 401


def test_payment_success(client, card, auth, monkeypatch):
    monkeypatch.setattr(settings, "PAYMENT_SUCCESS_RATE", 1.0)
    r = pay(client, auth)
    assert r.status_code == 201
    assert r.json()["status"] == "SUCCESS"
    assert r.json()["failure_reason"] == ""


def test_payment_failure(client, card, auth, monkeypatch):
    monkeypatch.setattr(settings, "PAYMENT_SUCCESS_RATE", 0.0)
    r = pay(client, auth)
    assert r.status_code == 201
    assert r.json()["status"] == "FAILED"
    assert r.json()["failure_reason"]


def test_pending_then_final_status(client, card, auth, db, monkeypatch):
    seen = {}
    from app.routes import payments

    def fake_gateway():
        seen["status_during"] = db.query(Transaction).one().status
        return True, ""

    monkeypatch.setattr(payments, "simulate_gateway", fake_gateway)
    r = pay(client, auth)
    assert seen["status_during"] == "PENDING"
    assert r.json()["status"] == "SUCCESS"


def test_cannot_use_other_users_card(client, card, db):
    tok = {"Authorization": f"Bearer {make_token(2)}"}
    assert pay(client, tok).status_code == 404


def test_unknown_card(client, card, auth):
    assert pay(client, auth, card_id=999).status_code == 404


def test_expired_card(client, card, auth, db):
    db.get(Card, 10).expiry_year = 2020
    db.commit()
    assert pay(client, auth).status_code == 400


def test_validation(client, card, auth):
    assert pay(client, auth, amount="0").status_code == 422
    assert pay(client, auth, amount="-5").status_code == 422
    assert pay(client, auth, amount="1.999").status_code == 422
    assert pay(client, auth, currency="RUPEES").status_code == 422
    assert pay(client, auth, amount="999999").status_code == 422  # over max


def test_cvv_and_card_number_rejected(client, card, auth):
    assert pay(client, auth, cvv="123").status_code == 422
    assert pay(client, auth, card_number="4111111111111111").status_code == 422


def test_get_payment_and_list(client, card, auth):
    ref = pay(client, auth).json()["reference"]
    assert client.get(f"/payments/{ref}", headers=auth).json()["reference"] == ref
    assert len(client.get("/payments", headers=auth).json()) == 1
    other = {"Authorization": f"Bearer {make_token(2)}"}
    assert client.get(f"/payments/{ref}", headers=other).status_code == 404
