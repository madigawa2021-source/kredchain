import os
import joblib
import pandas as pd

from features import compute_features

MODEL_PATH = "kredchain_model.pkl"


def load_model():
    if not os.path.exists(MODEL_PATH):
        return None
    try:
        return joblib.load(MODEL_PATH)
    except Exception:
        return None


def run_ai_check(features):
    model = load_model()

    if model is None:
        return {"enabled": False, "anomaly": False, "score": 0}

    X = pd.DataFrame([{
        "F1": features["F1 account_age_days"],
        "F2": features["F2 oldest_utxo_age_days"],
        "F3": features["F3 active_months_ratio"],
        "F4": features["F4 tx_frequency_weekly_std"],
        "F5": features["F5 monthly_volume_cv"],
        "F6": features["F6 avg_utxo_age_days"],
        "F7": features["F7 script_type_score"],
        "F8": features["F8 counterparty_diversity"],
        "F9": features["F9 utxo_count"],
        "F10": features["F10 total_tx_count"],
        "F11": features["F11 incoming_outgoing_ratio"],
        "F12": features["F12 recency_score"],
        "F13": features["F13 avg_tx_value_sats"],
        "F14": features["F14 address_reuse_score"],
    }])

    try:
        pred = int(model.predict(X)[0])
    except Exception:
        # Model was trained on 9 features, retrain needed
        return {"enabled": False, "anomaly": False, "score": 0}

    return {
        "enabled": True,
        "anomaly": bool(pred == -1),
        "score": pred
    }


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


def compute_score(features):

    ai = run_ai_check(features)

    normalized = {
        "F1":  min(features["F1 account_age_days"] / 1825, 1.0),
        "F2":  min(features["F2 oldest_utxo_age_days"] / 1095, 1.0),
        "F3":  features["F3 active_months_ratio"],
        "F4":  max(0.0, 1 - features["F4 tx_frequency_weekly_std"] / 20),
        "F5":  max(0.0, 1 - features["F5 monthly_volume_cv"] / 2),
        "F6":  min(features["F6 avg_utxo_age_days"] / 730, 1.0),
        "F7":  features["F7 script_type_score"],
        "F8":  min(features["F8 counterparty_diversity"] / 50, 1.0),
        "F9":  1.0 if features["F9 utxo_count"] > 0 else 0.0,
        "F10": min(features["F10 total_tx_count"] / 1000, 1.0),
        "F11": min(features["F11 incoming_outgoing_ratio"] / 2.0, 1.0),
        "F12": features["F12 recency_score"],
        "F13": min(features["F13 avg_tx_value_sats"] / 10_000_000, 1.0),
        "F14": features["F14 address_reuse_score"],
    }

    weights = {
        "F1":  0.10,
        "F2":  0.10,
        "F3":  0.08,
        "F4":  0.10,
        "F5":  0.07,
        "F6":  0.08,
        "F7":  0.03,
        "F8":  0.10,
        "F9":  0.03,
        "F10": 0.08,
        "F11": 0.08,
        "F12": 0.07,
        "F13": 0.05,
        "F14": 0.03,
    }

    feature_map = {
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

    breakdown = {}
    score = 0

    for k in feature_map:
        raw = features[feature_map[k]]
        norm = normalized[k]
        weight = weights[k]
        contribution = norm * weight * 100
        score += contribution

        breakdown[k] = {
            "feature_name": feature_map[k],
            "raw": raw,
            "normalized": round(norm, 4),
            "weight": weight,
            "contribution": round(contribution, 2)
        }

    score = round(score, 1)

    if ai["enabled"] and ai["anomaly"]:
        score = round(score * 0.9, 1)

    return {
        "score": score,
        "tier": get_tier(score),
        "features": breakdown,
        "ai": {
            "enabled": bool(ai["enabled"]),
            "anomaly": bool(ai["anomaly"]),
            "score": int(ai["score"])
        }
    }


def print_score_report(features):
    result = compute_score(features)

    print("\nKredChain Score Breakdown\n")
    print(f"FINAL SCORE: {result['score']}")
    print(f"TIER: {result['tier']}")

    print(f"\n{'Feature':<30} {'Raw':>12} {'Norm':>8} {'Weight':>8} {'Contrib':>10}")
    print("-" * 72)

    for k, v in result["features"].items():
        print(f"{v['feature_name']:<30} {str(v['raw']):>12} {v['normalized']:>8.4f} {v['weight']:>8.2f} {v['contribution']:>10.2f}")

    print("-" * 72)

    if result["ai"]["enabled"]:
        status = "ANOMALOUS" if result["ai"]["anomaly"] else "NORMAL"
        print(f"\nAI Detection: {status}")


if __name__ == "__main__":
    from features import compute_features
    features = compute_features()
    print_score_report(features)