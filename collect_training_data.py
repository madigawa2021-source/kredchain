import csv
import time

from features import compute_features

ADDRESS_FILE = "addresses.txt"
OUTPUT_FILE = "training_data.csv"

FIELDNAMES = [
    "address",
    "F1", "F2", "F3", "F4", "F5",
    "F6", "F7", "F8", "F9",
    "F10", "F11", "F12", "F13", "F14",
]


def load_addresses():
    with open(ADDRESS_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def build_row(address):
    try:
        features = compute_features(address)

        # Accept address even without UTXO data
        # F10-F14 don't need UTXOs
        return {
            "address": address,
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
        }

    except Exception as e:
        print(f"Failed {address}: {e}")
        return None


def main():
    addresses = load_addresses()
    rows = []
    total = len(addresses)

    print(f"Loaded {total} addresses")

    for i, address in enumerate(addresses, start=1):
        print(f"[{i}/{total}] {address}")
        row = build_row(address)
        if row:
            rows.append(row)
        time.sleep(2)

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved {len(rows)} rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()