import logging
import random
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..config import settings
from ..database import get_db
from ..models import Card, Transaction, User
from ..schemas import PaymentRequest, PaymentResponse

log = logging.getLogger("payments")
router = APIRouter(prefix="/payments", tags=["Payments"])

FAILURE_REASONS = ["Insufficient funds", "Card declined by issuer", "Suspected fraud", "Network timeout"]


def simulate_gateway() -> tuple[bool, str]:
    """Fake gateway - NO real payment provider is ever called."""
    if random.random() < settings.PAYMENT_SUCCESS_RATE:
        return True, ""
    return False, random.choice(FAILURE_REASONS)


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def make_payment(body: PaymentRequest, user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    if body.amount > settings.MAX_PAYMENT_AMOUNT:
        raise HTTPException(422, f"Amount exceeds the maximum of {settings.MAX_PAYMENT_AMOUNT}")

    card = db.scalar(select(Card).where(Card.id == body.card_id, Card.user_id == user.id))
    if card is None:
        raise HTTPException(404, "Card not found")
    today = date.today()
    if (card.expiry_year, card.expiry_month) < (today.year, today.month):
        raise HTTPException(400, "Card has expired")

    # 1) create PENDING record
    txn = Transaction(user_id=user.id, card_id=card.id, amount=body.amount, currency=body.currency,
                      description=body.description, status="PENDING")
    db.add(txn)
    db.commit()

    # 2) simulate processing, 3) set final status
    try:
        ok, reason = simulate_gateway()
    except Exception:  # pragma: no cover
        log.exception("simulation error")
        ok, reason = False, "Processing error"
    txn.status = "SUCCESS" if ok else "FAILED"
    txn.failure_reason = reason
    db.commit()
    db.refresh(txn)
    log.info("payment %s user=%s status=%s", txn.reference, user.id, txn.status)
    return txn


@router.get("/{reference}", response_model=PaymentResponse)
def get_payment(reference: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    txn = db.scalar(select(Transaction).where(Transaction.reference == reference,
                                              Transaction.user_id == user.id))
    if txn is None:
        raise HTTPException(404, "Transaction not found")
    return txn


@router.get("", response_model=list[PaymentResponse])
def recent_payments(limit: int = Query(10, ge=1, le=100), user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    stmt = (select(Transaction).where(Transaction.user_id == user.id)
            .order_by(Transaction.created_at.desc()).limit(limit))
    return list(db.scalars(stmt))
