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
RETRAIN_EVERY = 50  # retrain every 10 new addresses




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
                "training_samples": 306,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, str(e))