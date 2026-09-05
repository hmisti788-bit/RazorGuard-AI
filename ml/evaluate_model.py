"""Evaluate the saved RazorGuard fraud model on a held-out test split."""

from pathlib import Path
import pickle

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split


RANDOM_SEED = 42


def main() -> None:
    project_root = Path(__file__).parents[1]
    data_path = project_root / "ml" / "data" / "transactions.csv"
    model_path = project_root / "ml" / "models" / "fraud_model.pkl"

    transactions = pd.read_csv(data_path)
    with model_path.open("rb") as model_file:
        artifact = pickle.load(model_file)

    features = transactions[artifact["feature_columns"]]
    target = transactions[artifact["target_column"]]
    _, test_features, _, test_target = train_test_split(
        features,
        target,
        test_size=0.20,
        stratify=target,
        random_state=RANDOM_SEED,
    )

    probabilities = artifact["pipeline"].predict_proba(test_features)[:, 1]
    threshold = artifact.get("decision_threshold", 0.5)
    predictions = (probabilities >= threshold).astype(int)
    matrix = confusion_matrix(test_target, predictions, labels=[0, 1])
    false_positives = int(matrix[0, 1])
    false_negatives = int(matrix[1, 0])

    print("Evaluation on held-out test set")
    print(f"Accuracy: {accuracy_score(test_target, predictions):.4f}")
    print(f"Precision: {precision_score(test_target, predictions, zero_division=0):.4f}")
    print(f"Recall: {recall_score(test_target, predictions, zero_division=0):.4f}")
    print(f"F1-score: {f1_score(test_target, predictions, zero_division=0):.4f}")
    print(f"Decision threshold: {threshold:.2f}")
    print(f"Fraud percentage (full dataset): {target.mean() * 100:.2f}%")
    print(f"Fraud percentage (held-out test set): {test_target.mean() * 100:.2f}%")
    print("Confusion matrix [genuine, fraudulent]:")
    print(matrix)
    print("Classification report:")
    print(classification_report(test_target, predictions, target_names=["genuine", "fraudulent"], zero_division=0))
    print(f"False Positives: {false_positives}")
    print(f"False Negatives: {false_negatives}")
    print("False positives can inconvenience genuine customers and cause unnecessary declines or reviews.")
    print("False negatives allow fraudulent payments through, creating financial and trust losses.")


if __name__ == "__main__":
    main()
