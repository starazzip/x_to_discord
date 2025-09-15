from datetime import datetime, timezone, timedelta
from typing import Any
from app.config import Config
from app.translate_ultra import translate_en_to_zh_tw_ultra

def _format_tw_time(dt: datetime) -> str:
    taipei = timezone(timedelta(hours=8))
    return dt.astimezone(taipei).strftime("%Y-%m-%d %H:%M:%S") + " UTC+8"

def _get_full_text(t) -> str:
    nt = getattr(t, "note_tweet", None)
    if isinstance(nt, dict) and "text" in nt and nt["text"]:
        return nt["text"]
    return t.text or ""

def build_discord_message(cfg: Config, username: str, tweet: Any) -> str:
    url = f"https://{cfg.embed_domain}/{username}/status/{tweet.id}"

    dt = tweet.created_at
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except Exception:
            dt = datetime.now(timezone.utc)
    created_at = _format_tw_time(dt)

    original = _get_full_text(tweet)

    if cfg.include_translation:
        if cfg.include_translation and getattr(tweet, "lang", "en") == "en":
            translated = translate_en_to_zh_tw_ultra(original)
        else:
            translated = ""
        return (
            "--------------------------------\n\n"
            f"推文（{created_at}）:\n{original}\n\n"
            f"翻譯: {translated}\n\n"
            f"網址: {url}\n\n"
        )
    else:
        return (
            "--------------------------------\n\n"
            f"推文（{created_at}）:\n{original}\n\n"
            f"日期: {created_at}\n\n"
            f"網址: {url}\n\n"
        )
