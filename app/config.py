from dataclasses import dataclass
import os
from dotenv import load_dotenv

@dataclass
class Config:
    bearer_token: str
    target_username: str
    user_id: int | None
    discord_webhook_url: str

    poll_interval_seconds: int
    exclude_replies: bool
    exclude_retweets: bool
    catch_up_on_first_run: bool
    state_file: str
    max_results: int

    include_translation: bool
    translate_provider: str      # none|free（保留未來付費）
    embed_domain: str

    fake_mode: str               # off|record|replay
    fake_dir: str
    fake_path: str

def _bool(env: str, default: str = "false") -> bool:
    return os.getenv(env, default).strip().lower() == "true"

def load_config() -> Config:
    load_dotenv()

    bearer = os.getenv("BEARER_TOKEN", "").strip()
    user = os.getenv("TARGET_USERNAME", "").strip()
    webhook = os.getenv("DISCORD_WEBHOOK_URL", "").strip()

    if not bearer:
        raise SystemExit("環境變數 BEARER_TOKEN 未設定")
    if not user:
        raise SystemExit("環境變數 TARGET_USERNAME 未設定")
    if not webhook:
        raise SystemExit("環境變數 DISCORD_WEBHOOK_URL 未設定")

    # USER_ID 可選
    uid_env = os.getenv("USER_ID", "").strip()
    uid = int(uid_env) if uid_env.isdigit() else None

    mr = max(5, min(100, int(os.getenv("MAX_RESULTS", "10"))))

    # FAKE 路徑
    fake_dir = os.getenv("FAKE_DIR", "fake_data").strip()
    fake_file = os.getenv("FAKE_FILE", f"fake_{user}.json").strip()
    os.makedirs(fake_dir, exist_ok=True)
    fake_path = os.path.join(fake_dir, fake_file)

    return Config(
        bearer_token=bearer,
        target_username=user,
        user_id=uid,
        discord_webhook_url=webhook,

        poll_interval_seconds=int(os.getenv("POLL_INTERVAL_SECONDS", "60")),
        exclude_replies=_bool("EXCLUDE_REPLIES", "true"),
        exclude_retweets=_bool("EXCLUDE_RETWEETS", "true"),
        catch_up_on_first_run=_bool("CATCH_UP_ON_FIRST_RUN", "false"),
        state_file=os.getenv("STATE_FILE", "state.json"),
        max_results=mr,

        include_translation=_bool("INCLUDE_TRANSLATION", "true"),
        translate_provider=os.getenv("TRANSLATE_PROVIDER", "none").strip().lower(),
        embed_domain=os.getenv("EMBED_DOMAIN", "twitter.com").strip(),

        fake_mode=os.getenv("FAKE_MODE", "off").strip().lower(),
        fake_dir=fake_dir,
        fake_path=fake_path,
    )
