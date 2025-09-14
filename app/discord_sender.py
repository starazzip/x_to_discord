import time, requests

def post_discord(webhook_url: str, content: str) -> None:
    """送訊息到 Discord Webhook，處理 429 速率限制重試"""
    while True:
        resp = requests.post(webhook_url, json={"content": content})
        if resp.status_code in (200, 204):
            return
        if resp.status_code == 429:
            retry_after = resp.headers.get("Retry-After") or resp.headers.get("X-RateLimit-Reset-After")
            try:
                sleep_s = float(retry_after)
                if sleep_s > 0:
                    time.sleep(sleep_s); continue
            except Exception:
                pass
            time.sleep(3); continue
        print(f"[Discord] Error {resp.status_code}: {resp.text[:500]}")
        return
