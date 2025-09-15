import time, tweepy
from typing import Optional, List, Any
from app.config import Config
from app.fake_io import load_fake_tweets, save_fake_tweets, tweets_to_dicts

def new_client(cfg: Config) -> tweepy.Client:
    return tweepy.Client(bearer_token=cfg.bearer_token, wait_on_rate_limit=True)

def get_user_id(client: tweepy.Client, username: str) -> Optional[int]:
    try:
        r = client.get_user(username=username)
        return r.data.id if r and r.data else None
    except tweepy.TweepyException as e:
        print(f"[X] get_user({username}) 失敗：{e}")
        return None

def fetch_new_tweets(client: tweepy.Client, cfg: Config, user_id: int | str,
                     since_id: Optional[str]) -> List[Any]:
    """
    抓取自上次後的新貼文；支援假資料模式：
    - FAKE_MODE=record：照常打 API，並把結果 append 到 JSON
    - FAKE_MODE=replay：不打 API，直接讀 JSON 回傳（新到舊）
    - FAKE_MODE=off：維持原本行為
    """
    if cfg.fake_mode == "replay":
        return load_fake_tweets(cfg.fake_path, since_id, cfg.max_results)

    exclude = []
    if cfg.exclude_replies:  exclude.append("replies")
    if cfg.exclude_retweets: exclude.append("retweets")

    try:
        resp = client.get_users_tweets(
            id=user_id,
            since_id=since_id,
            max_results=cfg.max_results,
            tweet_fields=["created_at", "text", "entities", "public_metrics", "note_tweet"],
            exclude=exclude if exclude else None
        )
        tweets = resp.data or []
        if cfg.fake_mode == "record" and tweets:
            save_fake_tweets(cfg.fake_path, tweets_to_dicts(tweets))
        return tweets
    except tweepy.TooManyRequests:
        print("[X] TooManyRequests：保守休息 60 秒")
        time.sleep(60)
        return []
    except tweepy.TweepyException as e:
        print(f"[X] 取得推文失敗：{e}")
        return []
