import os
import joblib
import pandas as pd

MODEL_PATH = "kredchain_model.pkl"


def load_model():
    if not os.path.exists(MODEL_PATH):
        return None
    try:
        return joblib.load(MODEL_PATH)
    except Exception:
        return None


def get_tier(score):
    if score >= 85:
        return "TRUSTED MERCHANT"
    if score >= 70:
        return "RELIABLE"
    if score >= 50:
        return "DEVELOPING"
    if score >= 30:
        return "LIMITED HISTORY"
    return "INSUFFICIENT DATA"


def clamp01(value):
    return max(0.0, min(1.0, float(value)))


def normalize_features(features):
    return {
        "F1":  clamp01(features["F1 account_age_days"] / 1825),
        "F2":  clamp01(features["F2 oldest_utxo_age_days"] / 1095),
        "F3":  clamp01(features["F3 active_months_ratio"]),
        "F4":  max(0.0, 1 - features["F4 tx_frequency_weekly_std"] / 20),
        "F5":  max(0.0, 1 - features["F5 monthly_volume_cv"] / 2),
        "F6":  clamp01(features["F6 avg_utxo_age_days"] / 730),
        "F7":  clamp01(features["F7 script_type_score"]),
        "F8":  clamp01(features["F8 counterparty_diversity"] / 50),
        "F9":  1.0 if features["F9 utxo_count"] >= 1 else 0.0,
        "F10": clamp01(features["F10 total_tx_count"] / 1000),
        "F11": clamp01(features["F11 incoming_outgoing_ratio"] / 2.0),
        "F12": clamp01(features["F12 recency_score"]),
        "F13": clamp01(features["F13 avg_tx_value_sats"] / 10_000_000),
        "F14": clamp01(features["F14 address_reuse_score"]),
    }


WEIGHTS = {
    "F1":  0.10, "F2":  0.10, "F3":  0.08,
    "F4":  0.10, "F5":  0.07, "F6":  0.08,
    "F7":  0.03, "F8":  0.10, "F9":  0.03,
    "F10": 0.08, "F11": 0.08, "F12": 0.07,
    "F13": 0.05, "F14": 0.03,
}

FEATURE_MAP = {
    "F1":  "F1 account_age_days",
    "F2":  "F2 oldest_utxo_age_days",
    "F3":  "F3 active_months_ratio",
    "F4":  "F4 tx_frequency_weekly_std",
    "F5":  "F5 monthly_volume_cv",
    "F6":  "F6 avg_utxo_age_days",
    "F7":  "F7 script_type_score",
    "F8":  "F8 counterparty_diversity",
    "F9":  "F9 utxo_count",
    "F10": "F10 total_tx_count",
    "F11": "F11 incoming_outgoing_ratio",
    "F12": "F12 recency_score",
    "F13": "F13 avg_tx_value_sats",
    "F14": "F14 address_reuse_score",
}


def run_ai_scoring(features):
    """
    AI regression model scores the address directly from 14 features.
    Trained on algorithm-labeled data — AI does the scoring at inference time.
    """
    model = load_model()

    if model is None:
        return {
            "enabled": False,
            "ai_score": None,
            "tier": None,
        }

    X = pd.DataFrame([{
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
    }])

    try:
        ai_score = float(model.predict(X)[0])
        ai_score = round(max(0.0, min(100.0, ai_score)), 1)
    except Exception as e:
        print(f"[WARN] AI scoring failed: {e}")
        return {"enabled": False, "ai_score": None, "tier": None}

    return {
        "enabled": True,
        "ai_score": ai_score,
        "tier": get_tier(ai_score),
    }


def compute_score(features):

    # --- Feature breakdown (for UI display) ---
    normalized = normalize_features(features)
    breakdown = {}
    algorithm_score = 0

    for fid in FEATURE_MAP:
        raw = features[FEATURE_MAP[fid]]
        norm = normalized[fid]
        weight = WEIGHTS[fid]
        contribution = norm * weight * 100

        breakdown[fid] = {
            "feature_name": FEATURE_MAP[fid],
            "raw": raw,
            "normalized": round(norm, 4),
            "weight": weight,
            "contribution": round(contribution, 2),
        }

        algorithm_score += contribution

    algorithm_score = round(algorithm_score, 1)

    # --- AI scoring ---
    ai = run_ai_scoring(features)

    # AI is the primary scorer — algorithm is fallback
    if ai["enabled"] and ai["ai_score"] is not None:
        final_score = ai["ai_score"]
    else:
        final_score = algorithm_score

    return {
        "score": final_score,
        "tier": get_tier(final_score),
        "features": breakdown,
        "ai": {
            "enabled": bool(ai["enabled"]),
            "ai_score": ai.get("ai_score"),
            "algorithm_score": algorithm_score,
            "anomaly": False,  # no longer using anomaly detection
            "score": int(ai.get("ai_score") or algorithm_score),
        }
    }


def print_score_report(features):
    result = compute_score(features)

    print("\nKredChain Score Breakdown\n")
    print(f"{'Feature':<32} {'Raw':>12} {'Norm':>8} {'Weight':>8} {'Contrib':>10}")
    print("-" * 74)

    for fid, data in result["features"].items():
        print(
            f"{data['feature_name']:<32}"
            f"{str(data['raw'])[:10]:>12}"
            f"{data['normalized']:>8.3f}"
            f"{data['weight']:>8.2f}"
            f"{data['contribution']:>10.2f}"
        )

    print("=" * 74)
    print(f"ALGORITHM SCORE:  {result['ai']['algorithm_score']}/100")

    if result["ai"]["enabled"]:
        print(f"AI SCORE:         {result['ai']['ai_score']}/100")

    print(f"FINAL SCORE:      {result['score']}/100")
    print(f"TIER:             {result['tier']}")


if __name__ == "__main__":
    from features import compute_features
    features = compute_features()
    print_score_report(features)