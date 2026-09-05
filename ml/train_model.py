"""Train and save the RazorGuard fraud classification pipeline."""

from pathlib import Path
import pickle

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


RANDOM_SEED = 42
VALIDATION_SEED = 43
TARGET_COLUMN = "fraud"
DROP_COLUMNS = ["transaction_id", TARGET_COLUMN]
TEST_SIZE = 0.20
VALIDATION_SIZE = 0.25
THRESHOLD_GRID = np.arange(0.10, 0.71, 0.01)
MIN_VALIDATION_PRECISION = 0.25


def build_pipeline(numeric_features: list[str]) -> Pipeline:
    categorical_features = ["transaction_type"]
    classifier = ExtraTreesClassifier(
        n_estimators=500,
        min_samples_leaf=2,
        class_weight={0: 1, 1: 3},
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )
    return Pipeline(
        steps=[
            (
                "preprocessor",
                ColumnTransformer(
                    transformers=[
                        (
                            "categorical",
                            OneHotEncoder(handle_unknown="ignore"),
                            categorical_features,
                        ),
                        ("numeric", "passthrough", numeric_features),
                    ]
                ),
            ),
            ("classifier", classifier),
        ]
    )


def select_threshold(pipeline: Pipeline, features: pd.DataFrame, target: pd.Series) -> tuple[float, float, float, float]:
    probabilities = pipeline.predict_proba(features)[:, 1]
    best_result = (0.0, 0.0, 0.0, 1.0)
    fallback_result = best_result
    for threshold in THRESHOLD_GRID:
        predictions = (probabilities >= threshold).astype(int)
        result = (
            f1_score(target, predictions, zero_division=0),
            precision_score(target, predictions, zero_division=0),
            recall_score(target, predictions, zero_division=0),
            float(threshold),
        )
        if result[:3] > fallback_result[:3]:
            fallback_result = result
        if result[1] >= MIN_VALIDATION_PRECISION and result[:3] > best_result[:3]:
            best_result = result
    return best_result if best_result[1] else fallback_result


def main() -> None:
    project_root = Path(__file__).parents[1]
    data_path = project_root / "ml" / "data" / "transactions.csv"
    model_path = project_root / "ml" / "models" / "fraud_model.pkl"

    transactions = pd.read_csv(data_path)
    features = transactions.drop(columns=DROP_COLUMNS)
    target = transactions[TARGET_COLUMN]

    train_features, test_features, train_target, test_target = train_test_split(
        features,
        target,
        test_size=TEST_SIZE,
        stratify=target,
        random_state=RANDOM_SEED,
    )
    fit_features, validation_features, fit_target, validation_target = train_test_split(
        train_features,
        train_target,
        test_size=VALIDATION_SIZE,
        stratify=train_target,
        random_state=VALIDATION_SEED,
    )
    numeric_features = [
        column for column in features.columns if column != "transaction_type"
    ]
    selection_pipeline = build_pipeline(numeric_features)
    selection_pipeline.fit(fit_features, fit_target)
    validation_f1, validation_precision, validation_recall, threshold = select_threshold(
        selection_pipeline, validation_features, validation_target
    )

    pipeline = build_pipeline(numeric_features)
    pipeline.fit(train_features, train_target)

    model_path.parent.mkdir(parents=True, exist_ok=True)
    artifact = {
        "pipeline": pipeline,
        "feature_columns": list(features.columns),
        "target_column": TARGET_COLUMN,
        "random_seed": RANDOM_SEED,
        "decision_threshold": threshold,
    }
    with model_path.open("wb") as model_file:
        pickle.dump(artifact, model_file)
    del test_features, test_target
    print(f"Training transactions: {len(train_features):,}")
    print(f"Validation-selected threshold: {threshold:.2f}")
    print(f"Validation precision floor: {MIN_VALIDATION_PRECISION:.2f}")
    print(f"Validation precision: {validation_precision:.4f}")
    print(f"Validation recall: {validation_recall:.4f}")
    print(f"Validation F1-score: {validation_f1:.4f}")
    print(f"Saved model to: {model_path}")


if __name__ == "__main__":
    main()
