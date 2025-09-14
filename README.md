# x_to_discord

把指定 **X（Twitter）** 使用者的貼文，自動轉發到 **Discord** 頻道。  
支援速率限制處理、首啟動錨點（不補發歷史）、假資料錄製/回放、以及「免費、穩定、輕量化」翻譯（預設 ultra 模式：MyMemory + 本地快取，選配 LibreTranslate 與 OpenCC 簡→繁）。

---

## 目錄
- [專案介紹](#專案介紹)
- [專案結構](#專案結構)
- [環境需求](#環境需求)
- [安裝與執行](#安裝與執行)
- [.env 參數](#env-參數)
- [翻譯（Ultra 模式）](#翻譯ultra-模式)
- [常見問題](#常見問題)
- [授權](#授權)

---

## 專案介紹

- 監看單一 X 帳號（`TARGET_USERNAME` 或 `USER_ID`），以 Tweepy v2 取得新貼文並貼到 Discord Webhook。
- **限流保護**：
  - X：`wait_on_rate_limit=True`，遇到 429 會安全退避。
  - Discord：Webhook 回 429 會依 `Retry-After` 自動重試，並在大量貼文時做輕微節流。
- **首次啟動**：預設不補發歷史，只記錄最新一則做為錨點（避免第一次就狂刷頻道）。
- **狀態持久化**：以 `state.json` 保存 `last_seen_id`；重啟不重複貼。
- **假資料（FAKE）**：
  - `record`：抓到的新推文會寫入 `fake_data/*.json`。
  - `replay`：完全不打 X API，依 JSON 模擬回傳（依 `since_id` 過濾，新到舊）。
- **翻譯**（可選）：預設 **ultra** 模式（免費、穩定、輕量），只對英文貼文翻成繁中；失敗時回傳原文不阻塞流程。

> 倉庫中可見的主要檔案／目錄：`app/`、`fake_data/`、`.env.example`、`main.py`、`pyproject.toml`、`state.json`、`translations_cache.json`。

---

## 專案結構

```
x_to_discord/
├─ app/                     # 模組化程式（config、x_client、formatter、discord_sender、translate_* 等）
├─ fake_data/               # FAKE 模式錄製資料（JSON）
├─ .env.example             # 環境變數範例
├─ main.py                  # 程式進入點
├─ pyproject.toml           # 專案設定/依賴（PEP 621 / Poetry / uv 皆可使用）
├─ state.json               # 上次處理到的推文 ID（程式運行時產生/更新）
└─ translations_cache.json  # 翻譯快取（Ultra 模式使用；可刪）
```

---

## 環境需求

- Python **3.10+**
- 依賴（最小化）：
  - `tweepy`、`requests`、`python-dotenv`
  - （選配）`opencc-python-reimplemented`（若需簡→繁）

---

## 安裝與執行

### 1) 取得原始碼
```bash
git clone https://github.com/starazzip/x_to_discord.git
cd x_to_discord
```

### 2) 安裝依賴（使用 Poetry）

如未安裝 Poetry：

```bash
# 推薦方式
pipx install poetry

# 或使用 pip（使用者範圍安裝）
pip install --user poetry
```

建立／指定虛擬環境（可選；不指定則自動）

```bash
poetry env use python3.11   # 依你的 Python 版本調整
```

安裝專案依賴（讀取 `pyproject.toml`）

```bash
poetry install
```

### 3) 設定環境變數
```bash
cp .env.example .env
# 編輯 .env，填入 BEARER_TOKEN、TARGET_USERNAME、DISCORD_WEBHOOK_URL 等
```

### 4) 執行
```bash
poetry run python main.py
```

或先進入虛擬環境再執行：
```bash
poetry shell
python main.py
```

---

## .env 參數

```dotenv
# --- 必要 ---
BEARER_TOKEN=你的X_BEARER_TOKEN
TARGET_USERNAME=目標帳號（例如 elonmusk）
# 可選：若已知 user id，可填此欄以略過查詢
USER_ID=

DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxxx/xxxx

# --- 輪詢與行為 ---
POLL_INTERVAL_SECONDS=60
EXCLUDE_REPLIES=true
EXCLUDE_RETWEETS=true
CATCH_UP_ON_FIRST_RUN=false
STATE_FILE=state.json
MAX_RESULTS=10                 # 5..100（X v2 限制）

# --- 翻譯（Ultra 模式） ---
INCLUDE_TRANSLATION=true
TRANSLATE_PROVIDER=ultra       # ultra | none
ULTRA_PROVIDER_ORDER=mymemory,libre
FREE_TRANSLATE_ENDPOINT=       # 若你有 LibreTranslate 端點，可填；不填也可用
FREE_TRANSLATE_API_KEY=
OPENCC_ENABLED=true            # 若不需要簡→繁，設為 false 並可不安裝 opencc

# --- 連結網域（通常 twitter.com 比較容易觸發 Discord 卡片預覽） ---
EMBED_DOMAIN=twitter.com

# --- 假資料（FAKE） ---
FAKE_MODE=off                  # off | record | replay
FAKE_DIR=fake_data
FAKE_FILE=fake_${TARGET_USERNAME}.json
TRANSLATE_CACHE_FILE=translations_cache.json
TRANSLATE_CACHE_TTL_SEC=15552000  # 180 天
```

---

## 翻譯（Ultra 模式）

- **預設使用 MyMemory（免費、無金鑰）**，搭配 **本地快取**（`translations_cache.json`）。
- **僅對英文貼文**送翻譯請求，節省額度、降低失敗率。
- 若 `.env` 提供 `FREE_TRANSLATE_ENDPOINT`，則 **LibreTranslate** 作為備援（多數節點回簡體，可搭配 `OPENCC_ENABLED=true` 自動轉繁）。
- 翻譯失敗或超時時，會直接返回原文，不影響主流程。

---

## 常見問題

- **X 回 401/403**：檢查 `BEARER_TOKEN` 是否有效、權限是否為 Read，或帳號是否受限。  
- **429 Too Many Requests（X）**：拉長 `POLL_INTERVAL_SECONDS` 或降低 `MAX_RESULTS`。  
- **429（Discord）**：已依 `Retry-After` 重試；如仍頻繁遇到，增加每則訊息間隔（程式內已加 0.8s 微節流）。  
- **FAKE 無資料**：先用 `FAKE_MODE=record` 跑一段時間收集；之後切 `replay` 就能離線測試。  
- **要改時區或訊息格式**：修改 `app/formatter.py`。

---

## 授權

以原倉庫設定為準；若未標註，預設保留作者所有權利。
