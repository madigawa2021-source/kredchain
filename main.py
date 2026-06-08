from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from features import compute_features
from scorer import compute_score

app = FastAPI(title="KredChain API", version="1.1.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "service": "KredChain",
        "status": "running",
        "version": "1.1.1"
    }


@app.get("/analyze/{address}")
def analyze(address: str):

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

            # IMPORTANT: UI uses this
            "ai": result["ai"],

            "metadata": {
                "analyzed_at": datetime.utcnow().isoformat(),
                "data_source": "mempool.space",
                "model_version": "1.1.1",
                "utxo_data_available": features.get(
                    "utxo_data_available", False
                )
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, str(e))