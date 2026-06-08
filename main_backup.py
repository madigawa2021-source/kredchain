from features import compute_features


WEIGHTS = {
    "F1": 0.15,
    "F2": 0.15,
    "F3": 0.10,
    "F4": 0.15,
    "F5": 0.10,
    "F6": 0.10,
    "F7": 0.05,
    "F8": 0.15,
    "F9": 0.05,
}


FEATURE_MAP = {
    "F1": "F1 account_age_days",
    "F2": "F2 oldest_utxo_age_days",
    "F3": "F3 active_months_ratio",
    "F4": "F4 tx_frequency_weekly_std",
    "F5": "F5 monthly_volume_cv",
    "F6": "F6 avg_utxo_age_days",
    "F7": "F7 script_type_score",
    "F8": "F8 counterparty_diversity",
    "F9": "F9 utxo_count",
}


def clamp01(value):
    return max(0.0, min(1.0, value))


def normalize_features(features):

    normalized = {}

    normalized["F1"] = clamp01(
        features["F1 account_age_days"] / 1825
    )

    normalized["F2"] = clamp01(
        features["F2 oldest_utxo_age_days"] / 1095
    )

    normalized["F3"] = clamp01(
        features["F3 active_months_ratio"]
    )

    normalized["F4"] = max(
        0.0,
        1 - (
            features["F4 tx_frequency_weekly_std"]
            / 20
        )
    )

    normalized["F5"] = max(
        0.0,
        1 - (
            features["F5 monthly_volume_cv"]
            / 2
        )
    )

    normalized["F6"] = clamp01(
        features["F6 avg_utxo_age_days"] / 730
    )

    normalized["F7"] = clamp01(
        features["F7 script_type_score"]
    )

    normalized["F8"] = clamp01(
        features["F8 counterparty_diversity"] / 50
    )

    normalized["F9"] = (
        1.0
        if features["F9 utxo_count"] >= 1
        else 0.0
    )

    return normalized


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

    normalized = normalize_features(features)

    breakdown = {}

    final_score = 0

    for fid in FEATURE_MAP:

        raw_value = features[
            FEATURE_MAP[fid]
        ]

        normalized_value = normalized[fid]

        weight = WEIGHTS[fid]

        contribution = (
            normalized_value
            * weight
            * 100
        )

        breakdown[fid] = {
            "feature_name":
                FEATURE_MAP[fid],
            "raw":
                raw_value,
            "normalized":
                round(
                    normalized_value,
                    4
                ),
            "weight":
                weight,
            "contribution":
                round(
                    contribution,
                    2
                ),
        }

        final_score += contribution

    final_score = round(
        final_score,
        1
    )

    tier = get_tier(
        final_score
    )

    return {
        "score":
            final_score,
        "tier":
            tier,
        "breakdown":
            breakdown,
    }


def print_score_report(features):

    result = compute_score(
        features
    )

    print(
        "\nKredChain Score Breakdown\n"
    )

    print(
        f"{'Feature':<32}"
        f"{'Raw':>12}"
        f"{'Norm':>12}"
        f"{'Weight':>12}"
        f"{'Contribution':>15}"
    )

    print("-" * 83)

    for fid, data in result[
        "breakdown"
    ].items():

        print(
            f"{fid:<32}"
            f"{str(data['raw'])[:10]:>12}"
            f"{data['normalized']:>12.3f}"
            f"{data['weight']:>12.2f}"
            f"{data['contribution']:>15.2f}"
        )

    print("\n" + "=" * 83)

    print(
        f"FINAL SCORE: "
        f"{result['score']}/100"
    )

    print(
        f"TIER: "
        f"{result['tier']}"
    )


def main():

    features = compute_features()

    print_score_report(
        features
    )


if __name__ == "__main__":
    main()