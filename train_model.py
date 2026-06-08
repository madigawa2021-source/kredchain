import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest

print("Loading training data...")

df = pd.read_csv("training_data.csv")

print(f"Rows loaded: {len(df)}")
print(f"Columns found: {list(df.columns)}")

feature_columns = [
    "F1", "F2", "F3", "F4", "F5",
    "F6", "F7", "F8", "F9",
    "F10", "F11", "F12", "F13", "F14",
]

# Drop rows with any missing values in feature columns
df = df.dropna(subset=feature_columns)
print(f"Clean rows after dropping nulls: {len(df)}")

if len(df) < 10:
    print("[ERROR] Not enough training data. Collect more addresses first.")
    exit(1)

X = df[feature_columns]

print(f"Training Isolation Forest on {len(X)} samples, 14 features...")

model = IsolationForest(
    n_estimators=300,      # increased from 100
    contamination=0.05,    # assume 5% anomalous
    random_state=42,
    max_samples="auto",
)

model.fit(X)

joblib.dump(model, "kredchain_model.pkl")

print("Model saved to kredchain_model.pkl")
print(f"Feature count: {len(feature_columns)}")
print(f"Training samples: {len(X)}")