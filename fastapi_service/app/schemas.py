from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Status(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class PaymentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")  # rejects unexpected fields such as cvv / card_number

    card_id: int = Field(gt=0)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="INR", pattern=r"^[A-Za-z]{3}$")
    description: str = Field(default="", max_length=255)

    @field_validator("currency")
    @classmethod
    def upper(cls, v: str) -> str:
        return v.upper()

    @field_validator("description")
    @classmethod
    def strip(cls, v: str) -> str:
        return v.strip()


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reference: str
    card_id: int | None
    amount: Decimal
    currency: str
    description: str
    status: Status
    failure_reason: str
    created_at: datetime
    updated_at: datetime
