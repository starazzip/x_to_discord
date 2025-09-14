from app.config import Config, load_config
from app.state_store import load_state, save_state
from app.discord_sender import post_discord
from app.formatter import build_discord_message
from app.x_client import new_client, get_user_id, fetch_new_tweets
import time

def main():
    cfg: Config = load_config()
    client = new_client(cfg)

    # 允許以 USER_ID 直接覆寫，否則以 username 查 ID
    user_id = cfg.user_id or get_user_id(client, cfg.target_username)
    if not user_id:
        raise SystemExit(f"找不到使用者：{cfg.target_username}")

    state = load_state(cfg.state_file)
    last_seen_id = state.get(str(user_id))

    # 首次啟動，預設不補發歷史
    if last_seen_id is None and not cfg.catch_up_on_first_run:
        latest = fetch_new_tweets(client, cfg, user_id, since_id=None)
        if latest:
            newest_id = str(latest[0].id)
            last_seen_id = newest_id
            state[str(user_id)] = last_seen_id
            save_state(cfg.state_file, state)
            print(f"[Init] 設定基準 last_seen_id={last_seen_id}（不補發歷史）")
        else:
            print("[Init] 沒有抓到任何貼文，等待下一輪")

    try:
        while True:
            tweets = fetch_new_tweets(client, cfg, user_id, since_id=last_seen_id)
            if tweets:
                for t in reversed(tweets):  # 時間正序轉發
                    msg = build_discord_message(cfg, cfg.target_username, t)
                    post_discord(cfg.discord_webhook_url, msg)
                    last_seen_id = str(t.id)
                    state[str(user_id)] = last_seen_id
                    save_state(cfg.state_file, state)
                    time.sleep(0.8)  # 輕微節流
            time.sleep(cfg.poll_interval_seconds)
    except KeyboardInterrupt:
        print("\n收到中斷，正在安全退出…")
        if last_seen_id is not None:
            state[str(user_id)] = last_seen_id
            save_state(cfg.state_file, state)
        print("完成。")

if __name__ == "__main__":
    main()
