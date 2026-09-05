"""Model loading and fraud prediction logic."""

import pickle
import uuid
from pathlib import Path
from typing import Any

import pandas as pd

from backend.database.database import utc_now
from backend.schemas.transaction import TransactionFeatures


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = PROJECT_ROOT / "ml" / "models" / "fraud_model.pkl"


class FraudPredictor:
    def __init__(self, model_path: Path = MODEL_PATH) -> None:
        if not model_path.exists():
            raise FileNotFoundError(f"Fraud model not found at {model_path}")
        with model_path.open("rb") as model_file:
            self.artifact: dict[str, Any] = pickle.load(model_file)
        self.pipeline = self.artifact["pipeline"]
        self.feature_columns = self.artifact["feature_columns"]
        self.threshold = float(self.artifact.get("decision_threshold", 0.5))

    def predict(self, transaction: TransactionFeatures) -> tuple[dict[str, Any], dict[str, Any]]:
        data = transaction.model_dump()
        transaction_id = data.pop("transaction_id", None) or f"TXN-{uuid.uuid4().hex[:12].upper()}"
        features = pd.DataFrame([{column: data[column] for column in self.feature_columns}])
        probability = float(self.pipeline.predict_proba(features)[0, 1])
        risk_level = self._risk_level(probability)
        result = {
            "transaction_id": transaction_id,
            "fraud_probability": round(probability, 6),
            "risk_score": round(probability * 100, 2),
            "risk_level": risk_level,
            "reasons": self._reasons(data, probability),
            "recommended_action": self._recommended_action(risk_level),
            "created_at": utc_now(),
        }
        return data, result

    def _risk_level(self, probability: float) -> str:
        if probability >= self.threshold:
            return "High Risk"
        if probability >= self.threshold * 0.5:
            return "Suspicious"
        return "Safe"

    @staticmethod
    def _reasons(data: dict[str, Any], probability: float) -> list[str]:
        reasons: list[str] = []
        if data["recipient_is_new"]:
            reasons.append("Recipient is new")
        if data["device_changed"]:
            reasons.append("Device changed")
        if data["location_changed"]:
            reasons.append("Location changed")
        if data["previous_failed_transactions"]:
            reasons.append("Previous failed transactions detected")
        if data["hour"] <= 5 or data["hour"] >= 23:
            reasons.append("Transaction occurs at an unusual hour")
        if data["transaction_frequency"] > 8:
            reasons.append("Unusually high transaction frequency")
        if not reasons:
            reasons.append("No individual high-risk signal detected")
        if probability >= 0.5:
            reasons.append("Model assigns elevated fraud probability")
        return reasons

    @staticmethod
    def _recommended_action(risk_level: str) -> str:
        return {
            "Safe": "Approve transaction",
            "Suspicious": "Require additional verification",
            "High Risk": "Hold transaction for manual review",
        }[risk_level]