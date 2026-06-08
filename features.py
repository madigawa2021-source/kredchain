from datetime import datetime, timezone

import numpy as np
import pandas as pd

from fetch import (
    get_address_info,
    get_address_txs,
    get_address_utxos,
)

ADDRESS = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"


def ts_to_dt(ts):
    if ts is None:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def age_days(ts):
    if ts is None:
        return None
    return (datetime.now(timezone.utc) - ts_to_dt(ts)).days


def compute_features(address=ADDRESS):

    info = get_address_info(address)
    txs = get_address_txs(address)[:25]
    utxos = get_address_utxos(address)

    utxo_data_available = len(utxos) > 0

    now = datetime.now(timezone.utc)

    # chain_stats for new features
    chain_stats = info.get("chain_stats", {})
    funded_txo_count = chain_stats.get("funded_txo_count", 0)
    funded_txo_sum = chain_stats.get("funded_txo_sum", 0)
    spent_txo_count = chain_stats.get("spent_txo_count", 0)
    total_tx_count = chain_stats.get("tx_count", 0)

    # ---------------------------------------
    # Transaction timestamps
    # ---------------------------------------

    tx_times = []
    for tx in txs:
        bt = tx.get("status", {}).get("block_time")
        if bt:
            tx_times.append(ts_to_dt(bt))
    tx_times.sort()

    # ---------------------------------------
    # UTXO ages
    # ---------------------------------------

    utxo_ages = []
    for utxo in utxos:
        bt = utxo.get("status", {}).get("block_time")
        if bt:
            utxo_ages.append(age_days(bt))

    # ---------------------------------------
    # F1 Account Age Proxy
    # ---------------------------------------

    account_age_days = max(utxo_ages) if utxo_ages else 0

    # ---------------------------------------
    # F2 Oldest UTXO Age
    # ---------------------------------------

    oldest_utxo_age_days = max(utxo_ages) if (utxo_data_available and utxo_ages) else 0

    # ---------------------------------------
    # F3 Active Months Ratio
    # ---------------------------------------

    if tx_times:
        months_active = {(d.year, d.month) for d in tx_times}
        first = tx_times[0]
        total_months = (now.year - first.year) * 12 + now.month - first.month + 1
        active_months_ratio = len(months_active) / total_months
    else:
        active_months_ratio = 0

    # ---------------------------------------
    # F4 Weekly Transaction Consistency
    # ---------------------------------------

    if tx_times:
        weekly_series = pd.Series(1, index=pd.to_datetime(tx_times))
        weekly_counts = weekly_series.resample("W").sum()
        tx_frequency_weekly_std = float(weekly_counts.std())
        if np.isnan(tx_frequency_weekly_std):
            tx_frequency_weekly_std = 0
    else:
        tx_frequency_weekly_std = 0

    # ---------------------------------------
    # F5 Monthly Volume CV
    # ---------------------------------------

    volume_rows = []
    for tx in txs:
        bt = tx.get("status", {}).get("block_time")
        if not bt:
            continue
        received = sum(out.get("value", 0) for out in tx.get("vout", []))
        volume_rows.append({"date": ts_to_dt(bt), "volume": received})

    if volume_rows:
        df = pd.DataFrame(volume_rows)
        monthly = df.set_index("date").resample("ME").sum()
        mean_vol = monthly["volume"].mean()
        std_vol = monthly["volume"].std()
        if mean_vol > 0 and not np.isnan(std_vol):
            monthly_volume_cv = float(std_vol / mean_vol)
        else:
            monthly_volume_cv = 0
    else:
        monthly_volume_cv = 0

    # ---------------------------------------
    # F6 Average UTXO Age
    # ---------------------------------------

    avg_utxo_age_days = float(np.mean(utxo_ages)) if (utxo_data_available and utxo_ages) else 0

    # ---------------------------------------
    # F7 Script Type Score
    # ---------------------------------------

    script_weights = {
        "v1_p2tr": 1.00,
        "v0_p2wpkh": 0.85,
        "v0_p2wsh": 0.75,
        "p2sh": 0.60,
        "p2pkh": 0.50,
    }

    script_types = set()
    for tx in txs:
        for out in tx.get("vout", []):
            st = out.get("scriptpubkey_type")
            if st:
                script_types.add(st)

    if script_types:
        scores = [script_weights.get(st, 0.40) for st in script_types]
        script_type_score = sum(scores) / len(scores)
    else:
        script_type_score = 0

    # ---------------------------------------
    # F8 Counterparty Diversity
    # ---------------------------------------

    counterparties = set()
    for tx in txs:
        for out in tx.get("vout", []):
            addr = out.get("scriptpubkey_address")
            if addr:
                counterparties.add(addr)

    counterparty_diversity = len(counterparties)

    # ---------------------------------------
    # F9 UTXO Count
    # ---------------------------------------

    utxo_count = len(utxos) if utxo_data_available else 0

    # ---------------------------------------
    # F10 Total Transaction Count
    # ---------------------------------------

    total_tx_count_feature = total_tx_count

    # ---------------------------------------
    # F11 Incoming/Outgoing Ratio
    # ---------------------------------------

    incoming_outgoing_ratio = funded_txo_count / (spent_txo_count + 1)

    # ---------------------------------------
    # F12 Recency Score
    # ---------------------------------------

    if tx_times:
        last_tx = max(tx_times)
        days_since_last = (now - last_tx).days
        recency_score = max(0.0, 1 - days_since_last / 365)
    else:
        recency_score = 0.0

    # ---------------------------------------
    # F13 Average Transaction Value
    # ---------------------------------------

    avg_tx_value_sats = funded_txo_sum / (funded_txo_count + 1)

    # ---------------------------------------
    # F14 Address Reuse Score
    # ---------------------------------------

    reuse_ratio = spent_txo_count / (funded_txo_count + 1)
    address_reuse_score = max(0.0, 1 - reuse_ratio)

    # ---------------------------------------
    # Final Output
    # ---------------------------------------

    features = {
        "F1 account_age_days": account_age_days,
        "F2 oldest_utxo_age_days": oldest_utxo_age_days,
        "F3 active_months_ratio": round(active_months_ratio, 4),
        "F4 tx_frequency_weekly_std": round(tx_frequency_weekly_std, 4),
        "F5 monthly_volume_cv": round(monthly_volume_cv, 4),
        "F6 avg_utxo_age_days": round(avg_utxo_age_days, 2),
        "F7 script_type_score": round(script_type_score, 4),
        "F8 counterparty_diversity": counterparty_diversity,
        "F9 utxo_count": utxo_count,
        "F10 total_tx_count": total_tx_count_feature,
        "F11 incoming_outgoing_ratio": round(incoming_outgoing_ratio, 4),
        "F12 recency_score": round(recency_score, 4),
        "F13 avg_tx_value_sats": round(avg_tx_value_sats, 2),
        "F14 address_reuse_score": round(address_reuse_score, 4),
        "utxo_data_available": utxo_data_available,
    }

    return features


if __name__ == "__main__":
    features = compute_features()
    print("\nKredChain Feature Report\n")
    for key, value in features.items():
        print(f"{key}: {value}")