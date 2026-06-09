from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
import joblib
import threading

from features import compute_features
from scorer import compute_score, get_tier

app = FastAPI(title="KredChain API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TRAINING_FILE = "training_data.csv"
MODEL_FILE = "kredchain_model.pkl"
RETRAIN_EVERY = 10  # retrain every 10 new addresses

new_samples_count = 0


def append_to_training(features, algorithm_score):
    """Add new address to training data."""
    row = {
        "address": "live",
        "F1":  features["F1 account_age_days"],
        "F2":  features["F2 oldest_utxo_age_days"],
        "F3":  features["F3 active_months_ratio"],
        "F4":  features["F4 tx_frequency_weekly_std"],
        "F5":  features["F5 monthly_volume_cv"],
        "F6":  features["F6 avg_utxo_age_days"],
        "F7":  features["F7 script_type_score"],
        "F8":  features["F8 counterparty_diversity"],
        "F9":  features["F9 utxo_count"],
        "F10": features["F10 total_tx_count"],
        "F11": features["F11 incoming_outgoing_ratio"],
        "F12": features["F12 recency_score"],
        "F13": features["F13 avg_tx_value_sats"],
        "F14": features["F14 address_reuse_score"],
        "target_score": algorithm_score,
    }

    df_new = pd.DataFrame([row])

    if os.path.exists(TRAINING_FILE):
        df_existing = pd.read_csv(TRAINING_FILE)
        df_combined = pd.concat(
            [df_existing, df_new],
            ignore_index=True
        )
    else:
        df_combined = df_new

    df_combined.to_csv(TRAINING_FILE, index=False)
    return len(df_combined)


def retrain_model():
    """Retrain model on updated training data."""
    try:
        from sklearn.ensemble import GradientBoostingRegressor

        FEATURES = [
            "F1","F2","F3","F4","F5",
            "F6","F7","F8","F9","F10",
            "F11","F12","F13","F14"
        ]

        df = pd.read_csv(TRAINING_FILE)

        if "target_score" not in df.columns:
            print("[RETRAIN] No target_score column found")
            return

        df = df.dropna(subset=FEATURES + ["target_score"])

        if len(df) < 20:
            print(f"[RETRAIN] Not enough data: {len(df)} rows")
            return

        X = df[FEATURES]
        y = df["target_score"]

        model = GradientBoostingRegressor(
            n_estimators=300,
            max_depth=4,
            learning_rate=0.05,
            random_state=42,
        )

        model.fit(X, y)
        joblib.dump(model, MODEL_FILE)

        print(f"[RETRAIN] Model retrained on {len(df)} samples")

    except Exception as e:
        print(f"[RETRAIN] Failed: {e}")


def background_retrain():
    """Run retraining in background thread so API doesn't block."""
    thread = threading.Thread(target=retrain_model)
    thread.daemon = True
    thread.start()


@app.get("/")
def root():
    return {
        "service": "KredChain",
        "status": "running",
        "version": "2.0.0"
    }


@app.get("/analyze/{address}")
def analyze(address: str):
    global new_samples_count

    try:
        if len(address) < 26:
            raise HTTPException(400, "Invalid Bitcoin address")

        features = compute_features(address)
        result = compute_score(features)

        # --- Self-retraining pipeline ---
        algorithm_score = result["ai"].get(
            "algorithm_score",
            result["score"]
        )

        total_samples = append_to_training(
            features,
            algorithm_score
        )

        new_samples_count += 1

        retrain_triggered = False
        if new_samples_count >= RETRAIN_EVERY:
            new_samples_count = 0
            retrain_triggered = True
            background_retrain()
            print(f"[RETRAIN] Triggered after {total_samples} total samples")

        return {
            "address": address,
            "score": result["score"],
            "tier": result["tier"],
            "features": result["features"],
            "ai": result["ai"],
            "metadata": {
                "analyzed_at": datetime.utcnow().isoformat(),
                "data_source": "mempool.space",
                "model_version": "2.0.0",
                "utxo_data_available": features.get(
                    "utxo_data_available", False
                ),
                "training_samples": total_samples,
                "retrain_triggered": retrain_triggered,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, str(e))