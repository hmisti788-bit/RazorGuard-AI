"""FastAPI application for RazorGuard AI fraud predictions."""

from contextlib import asynccontextmanager
import sqlite3

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.database.database import (
    get_analytics,
    initialize_database,
    insert_prediction,
    list_predictions,
)
from backend.schemas.transaction import (
    AnalyticsResponse,
    PredictionResponse,
    TransactionFeatures,
    TransactionRecord,
)
from backend.services.predictor import FraudPredictor


try:
    predictor = FraudPredictor()
except (FileNotFoundError, KeyError, OSError, ImportError) as error:
    predictor = None
    MODEL_LOAD_ERROR = str(error)
else:
    MODEL_LOAD_ERROR = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(title="RazorGuard AI API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    if predictor is None:
        raise HTTPException(status_code=503, detail=f"Model unavailable: {MODEL_LOAD_ERROR}")
    return {"status": "ok", "model": "loaded"}


@app.post("/predict", response_model=PredictionResponse)
def predict(transaction: TransactionFeatures) -> PredictionResponse:
    if predictor is None:
        raise HTTPException(status_code=503, detail=f"Model unavailable: {MODEL_LOAD_ERROR}")
    try:
        features, result = predictor.predict(transaction)
        insert_prediction(features, result)
        return PredictionResponse(**result)
    except (KeyError, ValueError, TypeError) as error:
        raise HTTPException(status_code=422, detail=f"Invalid transaction: {error}") from error
    except (OSError, sqlite3.Error) as error:
        raise HTTPException(status_code=500, detail="Unable to save prediction audit record") from error


@app.get("/transactions", response_model=list[TransactionRecord])
def transactions(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[dict]:
    try:
        return list_predictions(limit, offset)
    except (OSError, sqlite3.Error) as error:
        raise HTTPException(status_code=500, detail="Unable to read transaction audit records") from error


@app.get("/analytics", response_model=AnalyticsResponse)
def analytics() -> dict:
    try:
        return get_analytics()
    except (OSError, sqlite3.Error) as error:
        raise HTTPException(status_code=500, detail="Unable to calculate analytics") from error