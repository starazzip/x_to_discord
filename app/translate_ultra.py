# app/translate_ultra.py
import os, re, json, time, hashlib, requests
from typing import Optional

# ---- 快取設定 ----
CACHE_FILE = os.getenv("TRANSLATE_CACHE_FILE", "translations_cache.json")
CACHE_TTL_SEC = int(os.getenv("TRANSLATE_CACHE_TTL_SEC", str(180 * 24 * 3600)))  # 180 天
os.makedirs(os.path.dirname(CACHE_FILE) or ".", exist_ok=True)

def _load_cache() -> dict:
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_cache(cache: dict) -> None:
    tmp = CACHE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    os.replace(tmp, CACHE_FILE)

_CACHE = _load_cache()

def _cache_key(text: str) -> str:
    h = hashlib.sha1(text.encode("utf-8")).hexdigest()
    return f"en2zhTW:{h}"

def _cache_get(text: str) -> Optional[str]:
    key = _cache_key(text)
    item = _CACHE.get(key)
    now = int(time.time())
    if item and (now - item.get("ts", 0) <= CACHE_TTL_SEC):
        return item.get("val")
    return None

def _cache_put(text: str, val: str) -> None:
    key = _cache_key(text)
    _CACHE[key] = {"val": val, "ts": int(time.time())}
    _save_cache(_CACHE)

# ---- 工具：保護 token ----
def _mask_tokens(text: str):
    tokens = re.findall(r'(\$[A-Za-z0-9_]+|@[A-Za-z0-9_]+|https?://\S+)', text)
    protected, placeholders = text, []
    for i, tok in enumerate(tokens):
        ph = f"[[TKN{i}]]"
        placeholders.append((ph, tok))
        protected = protected.replace(tok, ph)
    return protected, placeholders

def _unmask_tokens(text: str, placeholders):
    for ph, tok in placeholders:
        text = text.replace(ph, tok)
    return text

def _maybe_opencc_s2t(s: str) -> str:
    if os.getenv("OPENCC_ENABLED", "true").strip().lower() != "true":
        return s
    try:
        from opencc import OpenCC
        return OpenCC("s2t").convert(s)
    except Exception:
        return s

# ---- 提供者：MyMemory 免費 ----
def _via_mymemory(text: str) -> Optional[str]:
    try:
        r = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": text, "langpair": "en|zh-TW"},
            timeout=12
        )
        r.raise_for_status()
        j = r.json()
        return (j.get("responseData") or {}).get("translatedText")
    except Exception:
        return None

# ---- 提供者：LibreTranslate（選配）----
def _via_libre(text: str) -> Optional[str]:
    url = os.getenv("FREE_TRANSLATE_ENDPOINT", "").strip()
    if not url:
        return None
    try:
        data = {"q": text, "source": "en", "target": "zh", "format": "text"}
        api_key = os.getenv("FREE_TRANSLATE_API_KEY", "").strip()
        if api_key:
            data["api_key"] = api_key
        r = requests.post(url, data=data, timeout=12)
        r.raise_for_status()
        j = r.json()
        out = j.get("translatedText") or j.get("translation")
        # 多數 Libre 是簡中 → 轉繁
        return _maybe_opencc_s2t(out) if out else None
    except Exception:
        return None

# ---- 對外：英文→繁中（超輕量、可快取、穩定）----
def translate_en_to_zh_tw_ultra(text: str) -> str:
    if not text.strip():
        return text

    # 先查快取
    cached = _cache_get(text)
    if cached is not None:
        return cached

    protected, placeholders = _mask_tokens(text)

    order = [s.strip().lower() for s in os.getenv("ULTRA_PROVIDER_ORDER", "mymemory,libre").split(",") if s.strip()]
    tried = set()
    out: Optional[str] = None

    for provider in order:
        if provider in tried: 
            continue
        tried.add(provider)
        if provider == "mymemory":
            out = _via_mymemory(protected)
            if out: 
                out = _unmask_tokens(out, placeholders)
                _cache_put(text, out)
                return out
        elif provider == "libre":
            out = _via_libre(protected)
            if out:
                out = _unmask_tokens(out, placeholders)
                _cache_put(text, out)
                return out

    # 全部失敗 → 回原文（也可選擇少量標記）
    return text
