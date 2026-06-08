import time
import httpx

BASE_URL = "https://mempool.space/api"

TIMEOUT = 30  # increased from 10
MAX_RETRIES = 3


def _get(url):
    """GET with retry and exponential backoff."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with httpx.Client(timeout=TIMEOUT) as client:
                response = client.get(url)
                return response
        except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError) as e:
            wait = 2 ** attempt  # 2s, 4s, 8s
            print(f"[RETRY {attempt}/{MAX_RETRIES}] {e} — waiting {wait}s")
            time.sleep(wait)

    raise ConnectionError(f"Failed after {MAX_RETRIES} retries: {url}")


def get_address_info(address):
    start = time.time()
    response = _get(f"{BASE_URL}/address/{address}")
    response.raise_for_status()
    print(f"[INFO] address info: {time.time()-start:.2f}s")
    return response.json()


def get_address_txs(address):
    start = time.time()
    response = _get(f"{BASE_URL}/address/{address}/txs")
    response.raise_for_status()
    print(f"[INFO] txs: {time.time()-start:.2f}s")
    return response.json()


def get_address_utxos(address):
    start = time.time()

    try:
        response = _get(f"{BASE_URL}/address/{address}/utxo")
    except ConnectionError as e:
        print(f"[WARN] UTXO fetch failed: {e}")
        return []

    print(f"[INFO] utxos: {time.time()-start:.2f}s")

    if response.status_code != 200:
        print(f"[WARN] UTXO API returned {response.status_code}")
        print(response.text[:200])
        return []

    try:
        return response.json()
    except Exception:
        print("[WARN] JSON decode failed")
        return []


if __name__ == "__main__":
    address = "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kygt080"
    print(get_address_info(address))
    print(get_address_txs(address))
    print(get_address_utxos(address))