"""Simple English to Traditional Chinese translation helper."""

import os
import re
from typing import List, Optional

import requests

DEFAULT_CHAR_LIMIT = 400
SENTENCE_ENDINGS = frozenset(".!?") | frozenset({chr(0x3002), chr(0xFF01), chr(0xFF1F)})


def _segment_sentences(text: str) -> List[str]:
    sentences: List[str] = []
    length = len(text)
    start = 0
    while start < length:
        end = start
        while end < length and text[end] not in SENTENCE_ENDINGS:
            end += 1
        while end < length and text[end] in SENTENCE_ENDINGS:
            end += 1
        while end < length and text[end].isspace():
            end += 1
        if end == start:
            end = min(start + 1, length)
        sentences.append(text[start:end])
        start = end
    return sentences


def _split_by_tokens(segment: str, limit: int) -> List[str]:
    tokens = re.findall(r"\S+|\s+", segment)
    chunks: List[str] = []
    current = ""

    def flush() -> None:
        nonlocal current
        if current:
            chunks.append(current)
            current = ""

    for token in tokens:
        if len(current) + len(token) <= limit:
            current += token
            continue
        flush()
        if len(token) <= limit:
            current = token
            continue
        for start in range(0, len(token), limit):
            chunks.append(token[start:start + limit])
    flush()
    return chunks


def _split_into_chunks(text: str, limit: int) -> List[str]:
    if not text:
        return []
    if limit <= 0:
        return [text]

    chunks: List[str] = []
    current = ""
    for sentence in _segment_sentences(text):
        if not sentence:
            continue
        if len(sentence) > limit:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_split_by_tokens(sentence, limit))
            continue
        if len(current) + len(sentence) <= limit:
            current += sentence
            continue
        if current:
            chunks.append(current)
        current = sentence
    if current:
        chunks.append(current)
    return chunks


def _resolve_limit() -> int:
    try:
        limit = int(os.getenv("ULTRA_FREE_LIMIT", str(DEFAULT_CHAR_LIMIT)))
    except ValueError:
        limit = DEFAULT_CHAR_LIMIT
    limit = max(1, limit)
    return min(limit, DEFAULT_CHAR_LIMIT)


def _via_mymemory(text: str) -> Optional[str]:
    try:
        response = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": text, "langpair": "en|zh-TW"},
            timeout=12,
        )
        response.raise_for_status()
        payload = response.json()
        return (payload.get("responseData") or {}).get("translatedText")
    except Exception:
        return None


def _via_libre(text: str) -> Optional[str]:
    endpoint = os.getenv("FREE_TRANSLATE_ENDPOINT", "").strip()
    if not endpoint:
        return None
    try:
        data = {"q": text, "source": "en", "target": "zh", "format": "text"}
        api_key = os.getenv("FREE_TRANSLATE_API_KEY", "").strip()
        if api_key:
            data["api_key"] = api_key
        response = requests.post(endpoint, data=data, timeout=12)
        response.raise_for_status()
        payload = response.json()
        return payload.get("translatedText") or payload.get("translation")
    except Exception:
        return None


def _translate_once(text: str) -> Optional[str]:
    order_env = os.getenv("ULTRA_PROVIDER_ORDER", "mymemory,libre")
    providers = [name.strip().lower() for name in order_env.split(",") if name.strip()]
    tried = set()
    for provider in providers:
        if provider in tried:
            continue
        tried.add(provider)
        if provider == "mymemory":
            result = _via_mymemory(text)
        elif provider == "libre":
            result = _via_libre(text)
        else:
            continue
        if result:
            return result
    return None


def translate_en_to_zh_tw_ultra(text: str) -> str:
    """Translate English text to Traditional Chinese within the 400 character limit."""
    if not text or not text.strip():
        return text

    limit = _resolve_limit()

    if len(text) <= limit:
        translated = _translate_once(text)
        return translated if translated else text

    output: List[str] = []
    for chunk in _split_into_chunks(text, limit):
        if not chunk.strip():
            output.append(chunk)
            continue
        translated = _translate_once(chunk)
        output.append(translated if translated else chunk)
    return "".join(output) if output else text