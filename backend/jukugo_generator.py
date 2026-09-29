"""LLM-powered jukugo/example generator for kanji cards."""
import json
import logging
import os
import re
import uuid

from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

MODEL_PROVIDER = "openai"
MODEL_NAME = "gpt-5.4-mini"
_JSON_BLOCK = re.compile(r"\[.*\]", re.DOTALL)


async def generate_extra_jukugo(kanji_doc: dict, need: int) -> list[dict]:
    """Ask the LLM for `need` new example words for a kanji: {word, kana, meaning, segments}."""
    if need <= 0:
        return []
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise RuntimeError("EMERGENT_LLM_KEY not configured")

    existing = kanji_doc.get("jukugo") or []
    existing_words = [j.get("word", "") for j in existing]

    system_msg = (
        "Anda editor kamus Bahasa Jepang. Buat contoh kata majemuk/kalimat pendek "
        "yang mengandung kanji yang diberikan, sesuai level Minna no Nihongo. "
        "Balas HANYA JSON array valid, tanpa markdown fence."
    )
    user_prompt = (
        f"Kanji: {kanji_doc['character']}\n"
        f"Arti: {kanji_doc.get('meaning','')}\n"
        f"Onyomi: {kanji_doc.get('onyomi','')}  |  Kunyomi: {kanji_doc.get('kunyomi','')}\n"
        f"Contoh yang SUDAH ADA (jangan diulang): {existing_words}\n\n"
        f"Buat {need} contoh BARU. Setiap objek JSON harus punya field:\n"
        '- "word" (string, penulisan asli Jepang, WAJIB mengandung kanji tersebut)\n'
        '- "kana" (string, semua kana/hiragana pengucapan)\n'
        '- "meaning" (string, arti Bahasa Indonesia)\n\n'
        f"Balas HANYA JSON array {need} objek."
    )

    chat = LlmChat(
        api_key=api_key,
        session_id=f"juk-{kanji_doc.get('id','x')}-{uuid.uuid4().hex[:6]}",
        system_message=system_msg,
    ).with_model(MODEL_PROVIDER, MODEL_NAME)

    reply = await chat.send_message(UserMessage(text=user_prompt))
    return _parse_jukugo(reply, need)


def _parse_jukugo(reply: str, need: int) -> list[dict]:
    if not reply:
        return []
    text = reply.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    match = _JSON_BLOCK.search(text)
    if not match:
        return []
    try:
        items = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    out = []
    for raw in items[:need]:
        if not isinstance(raw, dict):
            continue
        word = str(raw.get("word", "")).strip()
        kana = str(raw.get("kana", "")).strip()
        meaning = str(raw.get("meaning", "")).strip()
        if not word or not meaning:
            continue
        out.append({
            "word": word,
            "kana": kana,
            "meaning": meaning,
            "segments": [{"text": word, "reading": kana or None}],
            "generated": True,
        })
    return out
