from dataclasses import dataclass
from datetime import datetime, timezone
import json

@dataclass
class FakeTweet:
    id: str
    text: str
    created_at: datetime

def tweets_to_dicts(tweets: list) -> list[dict]:
    out = []
    for t in tweets:
        created = t.created_at
        if isinstance(created, datetime):
            created = created.isoformat()
        out.append({"id": str(t.id), "text": t.text or "", "created_at": created})
    return out

def save_fake_tweets(path: str, items: list[dict]) -> None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            existing = json.load(f)
    except Exception:
        existing = []
    known = {str(x["id"]) for x in existing}
    new_items = [x for x in items if str(x["id"]) not in known]
    if not new_items: return
    existing.extend(new_items)
    existing.sort(key=lambda x: int(x["id"]))
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    import os; os.replace(tmp, path)

def load_fake_tweets(path: str, since_id: str | None, max_results: int) -> list[FakeTweet]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return []
    sid = int(since_id) if since_id else 0
    filtered = [x for x in data if int(x["id"]) > sid]
    filtered.sort(key=lambda x: int(x["id"]), reverse=True)
    filtered = filtered[:max_results]
    out: list[FakeTweet] = []
    for x in filtered:
        created = x.get("created_at")
        try:
            created_dt = datetime.fromisoformat(str(created).replace("Z", "+00:00"))
        except Exception:
            created_dt = datetime.now(timezone.utc)
        out.append(FakeTweet(id=str(x["id"]), text=x.get("text", ""), created_at=created_dt))
    return out
