"""Request and response schemas for transaction risk predictions."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TransactionFeatures(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transaction_id: str | None = Field(default=None, min_length=1, max_length=80)
    amount: float = Field(gt=0, le=500000)
    hour: int = Field(ge=0, le=23)
    transaction_frequency: int = Field(ge=1, le=30)
    average_amount: float = Field(gt=0, le=500000)
    recipient_is_new: int = Field(ge=0, le=1)
    device_changed: int = Field(ge=0, le=1)
    location_changed: int = Field(ge=0, le=1)
    transaction_type: Literal["purchase", "transfer", "withdrawal", "subscription"]
    account_age_days: int = Field(ge=1, le=3000)
    previous_failed_transactions: int = Field(ge=0, le=8)


class PredictionResponse(BaseModel):
    transaction_id: str
    fraud_probability: float = Field(ge=0, le=1)
    risk_score: float = Field(ge=0, le=100)
    risk_level: Literal["Safe", "Suspicious", "High Risk"]
    reasons: list[str]
    recommended_action: str
    created_at: datetime


class TransactionRecord(PredictionResponse):
    id: int
    amount: float
    transaction_type: str


class AnalyticsResponse(BaseModel):
    total_predictions: int
    average_risk_score: float
    safe_count: int
    suspicious_count: int
    high_risk_count: int