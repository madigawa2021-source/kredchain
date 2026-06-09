import pandas as pd
import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

# -------------------------
# Load training features
# -------------------------
df = pd.read_csv("training_data.csv")

FEATURES = [
    "F1","F2","F3","F4","F5",
    "F6","F7","F8","F9","F10",
    "F11","F12","F13","F14"
]

# -------------------------
# Generate labels using algorithm
# -------------------------
from scorer import compute_score

def score_row(row):
    features = {
        "F1 account_age_days":        float(row["F1"]),
        "F2 oldest_utxo_age_days":    float(row["F2"]),
        "F3 active_months_ratio":     float(row["F3"]),
        "F4 tx_frequency_weekly_std": float(row["F4"]),
        "F5 monthly_volume_cv":       float(row["F5"]),
        "F6 avg_utxo_age_days":       float(row["F6"]),
        "F7 script_type_score":       float(row["F7"]),
        "F8 counterparty_diversity":  float(row["F8"]),
        "F9 utxo_count":              float(row["F9"]),
        "F10 total_tx_count":         float(row["F10"]),
        "F11 incoming_outgoing_ratio":float(row["F11"]),
        "F12 recency_score":          float(row["F12"]),
        "F13 avg_tx_value_sats":      float(row["F13"]),
        "F14 address_reuse_score":    float(row["F14"]),
        "utxo_data_available": float(row["F2"]) > 0,
    }
    result = compute_score(features)
    
    # explicitly return the algorithm score, not AI score
    return float(result["ai"]["algorithm_score"])

print("Generating scores for training data...")
df["target_score"] = df.apply(score_row, axis=1)

print(f"Score distribution:")
print(df["target_score"].describe())

# -------------------------
# Train regression model
# -------------------------
X = df[FEATURES]
y = df["target_score"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = GradientBoostingRegressor(
    n_estimators=300,
    max_depth=4,
    learning_rate=0.05,
    random_state=42,
)

model.fit(X_train, y_train)

# -------------------------
# Evaluate
# -------------------------
preds = model.predict(X_test)
mae = mean_absolute_error(y_test, preds)
r2 = r2_score(y_test, preds)

print(f"\nModel Performance:")
print(f"Mean Absolute Error: {mae:.2f} points")
print(f"R² Score: {r2:.4f}")
print(f"(R² of 1.0 = perfect, 0.0 = random)")

# -------------------------
# Feature importance
# -------------------------
print(f"\nFeature Importance (what AI learned):")
importances = model.feature_importances_
for feat, imp in sorted(zip(FEATURES, importances), key=lambda x: -x[1]):
    bar = "█" * int(imp * 50)
    print(f"  {feat:<6} {bar} {imp:.4f}")

joblib.dump(model, "kredchain_model.pkl")
print(f"\nAI scoring model saved to kredchain_model.pkl")