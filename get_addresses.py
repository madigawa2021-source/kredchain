import time
import httpx

BASE_URL = "https://mempool.space/api"
TARGET_COUNT = 300
OUTPUT_FILE = "addresses.txt"


def get_json(url):
    try:
        with httpx.Client(timeout=30) as client:
            r = client.get(url)
            if r.status_code != 200:
                print(f"[WARN] {r.status_code}: {url}")
                return None
            return r.json()
    except Exception as e:
        print(f"[ERROR] {e}")
        return None


def load_existing():
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()


def save_addresses(collected):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for address in sorted(collected):
            f.write(address + "\n")


def main():
    # Load already collected addresses
    collected = load_existing()
    print(f"Resuming from {len(collected)} existing addresses...")

    if len(collected) >= TARGET_COUNT:
        print(f"Already have {len(collected)} addresses. Done.")
        return

    blocks = get_json(f"{BASE_URL}/blocks") or []
    print(f"Found {len(blocks)} blocks")

    for block in blocks:
        if len(collected) >= TARGET_COUNT:
            break

        block_hash = block["id"]
        print(f"\nBlock: {block_hash[:16]}...")
        time.sleep(1)

        txs = get_json(f"{BASE_URL}/block/{block_hash}/txs") or []

        for tx in txs:
            if len(collected) >= TARGET_COUNT:
                break

            for output in tx.get("vout", []):
                address = output.get("scriptpubkey_address")

                if not address or address in collected:
                    continue

                time.sleep(1)

                info = get_json(f"{BASE_URL}/address/{address}")
                if not info:
                    continue

                stats = info.get("chain_stats", {})
                tx_count = stats.get("tx_count", 0)

                if 10 <= tx_count <= 500:
                    collected.add(address)
                    # Save after every addition — no progress lost on crash
                    save_addresses(collected)
                    print(f"[{len(collected)}/{TARGET_COUNT}] {address} ({tx_count} txs)")

                if len(collected) >= TARGET_COUNT:
                    break

    print(f"\nDone. {len(collected)} addresses saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()