"""LLM-powered quiz auto-generation to pad quiz_bunpo up to 15 questions."""
import json
import logging
import os
import re
import uuid
from typing import Any

from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

MODEL_PROVIDER = "openai"
MODEL_NAME = "gpt-5.4-mini"

_JSON_BLOCK = re.compile(r"\[.*\]", re.DOTALL)


def _segments_to_plain(segments: list[dict] | None) -> str:
    if not segments:
        return ""
    parts = []
    for seg in segments:
        text = seg.get("text", "")
        reading = seg.get("reading")
        parts.append(f"{text}({reading})" if reading else text)
    return "".join(parts)


def _bunpo_summary(bunpo: list[dict]) -> str:
    lines = []
    for point in bunpo[:6]:
        lines.append(f"- {point.get('judul', '')}: {point.get('rumus', '')}")
        keterangan = point.get("keterangan") or []
        if keterangan:
            lines.append(f"  • {keterangan[0]}")
    return "\n".join(lines)


def _existing_examples(quiz_bunpo: list[dict], limit: int = 3) -> str:
    out = []
    for q in quiz_bunpo[:limit]:
        stem = q.get("question_text") or _segments_to_plain(q.get("question_segments"))
        options = q.get("options") or []
        idx = q.get("answer_index", 0)
        out.append(
            f"- STEM: {stem}\n  OPTIONS: {options}\n  ANSWER_INDEX: {idx}\n  RUMUS: {q.get('rumus','')}\n  EXPLANATION: {q.get('explanation','')}"
        )
    return "\n".join(out)


async def generate_extra_bunpo_questions(chapter: dict, need: int) -> list[dict]:
    """Ask the LLM for `need` new multiple-choice quiz items grounded in the chapter."""
    if need <= 0:
        return []
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise RuntimeError("EMERGENT_LLM_KEY not configured")

    content = chapter.get("content") or {}
    bunpo = content.get("bunpo", [])
    existing = content.get("quiz_bunpo", [])

    system_msg = (
        "Anda adalah editor materi Minna no Nihongo. Tugas: buat soal pilihan ganda "
        "grammar (Bunpo) Bahasa Jepang tambahan yang konsisten dengan bab yang diberikan. "
        "SETIAP jawaban HARUS pilihan yang benar-benar bisa diverifikasi dari materi bab. "
        "Balas HANYA dalam format JSON array valid, tanpa markdown fence."
    )

    user_prompt = (
        f"Bab {chapter['number']} — {chapter['title']} ({chapter['title_translation']}).\n\n"
        f"Materi Bunpo yang tersedia:\n{_bunpo_summary(bunpo)}\n\n"
        f"Contoh soal yang sudah ada:\n{_existing_examples(existing)}\n\n"
        f"Buat {need} soal BARU (tidak boleh duplikat contoh di atas). Setiap objek JSON harus punya kunci:\n"
        '- "question_text" (string, stem kalimat Jepang dengan penanda ＿＿ atau pertanyaan Bahasa Indonesia)\n'
        '- "options" (array 4 string; opsi jawaban singkat, romaji/hiragana/kanji dibolehkan)\n'
        '- "answer_index" (integer 0-3, indeks jawaban benar)\n'
        '- "rumus" (string singkat, pola grammar utama)\n'
        '- "explanation" (string, penjelasan singkat Bahasa Indonesia)\n\n'
        f"Balas HANYA JSON array berisi {need} objek."
    )

    chat = LlmChat(
        api_key=api_key,
        session_id=f"quiz-pad-{chapter['number']}-{uuid.uuid4().hex[:8]}",
        system_message=system_msg,
    ).with_model(MODEL_PROVIDER, MODEL_NAME)

    reply = await chat.send_message(UserMessage(text=user_prompt))
    return _parse_questions(reply, need)


def _parse_questions(reply: str, need: int) -> list[dict]:
    if not reply:
        return []
    text = reply.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    match = _JSON_BLOCK.search(text)
    if not match:
        logger.warning("LLM returned no JSON block: %s", text[:200])
        return []
    try:
        items = json.loads(match.group(0))
    except json.JSONDecodeError as e:
        logger.warning("LLM JSON parse failed: %s; raw=%s", e, text[:200])
        return []
    normalized: list[dict] = []
    for raw in items[:need]:
        if not isinstance(raw, dict):
            continue
        options = raw.get("options") or []
        if not isinstance(options, list) or len(options) < 2:
            continue
        answer = raw.get("answer_index")
        try:
            answer = int(answer)
        except (TypeError, ValueError):
            continue
        if not (0 <= answer < len(options)):
            continue
        normalized.append(
            {
                "id": f"gen-{uuid.uuid4().hex[:10]}",
                "question_segments": None,
                "question_text": str(raw.get("question_text", "")).strip() or "(soal tanpa teks)",
                "options": [str(o) for o in options],
                "answer_index": answer,
                "correct_segments": None,
                "highlight_text": None,
                "rumus": str(raw.get("rumus", "")).strip(),
                "explanation": str(raw.get("explanation", "")).strip(),
                "generated": True,
            }
        )
    return normalized
