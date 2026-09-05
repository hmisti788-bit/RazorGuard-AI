"""Generate a realistic synthetic payment transaction dataset."""

from pathlib import Path

import numpy as np
import pandas as pd


RANDOM_SEED = 42
TRANSACTION_COUNT = 12_000


def generate_transactions(
    transaction_count: int = TRANSACTION_COUNT,
    random_seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """Create synthetic transactions with a probabilistic, multi-feature fraud signal."""
    rng = np.random.default_rng(random_seed)

    transaction_types = rng.choice(
        ["purchase", "transfer", "withdrawal", "subscription"],
        size=transaction_count,
        p=[0.62, 0.16, 0.12, 0.10],
    )
    type_baselines = {
        "purchase": 65.0,
        "transfer": 240.0,
        "withdrawal": 120.0,
        "subscription": 35.0,
    }
    baseline_amount = np.array([type_baselines[item] for item in transaction_types])

    average_amount = np.round(
        np.clip(rng.lognormal(np.log(baseline_amount), 0.45), 5, 2_500), 2
    )
    amount = np.round(
        np.clip(average_amount * rng.lognormal(0, 0.55, transaction_count), 1, 5_000), 2
    )
    hour = rng.integers(0, 24, transaction_count)
    transaction_frequency = np.clip(rng.poisson(4, transaction_count) + 1, 1, 30)
    account_age_days = np.clip(rng.gamma(3.0, 180, transaction_count).astype(int) + 1, 1, 3_000)
    previous_failed_transactions = np.clip(rng.poisson(0.45, transaction_count), 0, 8)

    recipient_is_new = rng.binomial(1, 0.14, transaction_count)
    device_changed = rng.binomial(1, 0.08, transaction_count)
    location_changed = rng.binomial(1, 0.10, transaction_count)

    amount_deviation = np.abs(np.log1p(amount) - np.log1p(average_amount))
    unusual_hour = ((hour <= 5) | (hour >= 23)).astype(int)
    frequency_pressure = np.maximum(transaction_frequency - 8, 0)

    fraud_score = (
        -4.4
        + 1.20 * amount_deviation
        + 1.60 * recipient_is_new
        + 1.50 * device_changed
        + 1.40 * location_changed
        + 0.45 * previous_failed_transactions
        + 0.55 * unusual_hour
        + 0.12 * frequency_pressure
        - 0.00020 * account_age_days
        + 0.35 * (transaction_types == "transfer")
        + rng.normal(0, 0.30, transaction_count)
    )
    fraud_probability = 1 / (1 + np.exp(-fraud_score))
    fraud = rng.binomial(1, fraud_probability)

    return pd.DataFrame(
        {
            "transaction_id": [f"TXN-{index:07d}" for index in range(1, transaction_count + 1)],
            "amount": amount,
            "hour": hour,
            "transaction_frequency": transaction_frequency,
            "average_amount": average_amount,
            "recipient_is_new": recipient_is_new,
            "device_changed": device_changed,
            "location_changed": location_changed,
            "transaction_type": transaction_types,
            "account_age_days": account_age_days,
            "previous_failed_transactions": previous_failed_transactions,
            "fraud": fraud,
        }
    )


def main() -> None:
    output_path = Path(__file__).parent / "data" / "transactions.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    transactions = generate_transactions()
    transactions.to_csv(output_path, index=False)

    fraud_count = int(transactions["fraud"].sum())
    genuine_count = len(transactions) - fraud_count
    print(f"Transactions generated: {len(transactions):,}")
    print(f"Genuine transactions: {genuine_count:,}")
    print(f"Fraudulent transactions: {fraud_count:,}")
    print(f"Fraud percentage: {transactions['fraud'].mean() * 100:.2f}%")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()
