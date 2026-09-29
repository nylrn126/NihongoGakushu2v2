"""Mini-DSL supaya materi 25 bab bisa ditulis padat tapi tetap ber-furigana.

Format teks Jepang: token dipisah spasi, furigana ditulis "kanji|bacaan".
    S("私|わたし は 学生|がくせい です。")
Token tanpa "|" tidak diberi furigana. Reading pada teks tanpa kanji otomatis dibuang,
jadi furigana hanya pernah muncul di atas kanji.
"""

import re

_KANJI_RE = re.compile(r"[\u4e00-\u9fff]")


def seg(text: str, reading: str | None = None) -> dict:
    if reading and not _KANJI_RE.search(text):
        reading = None
    return {"text": text, "reading": reading}


def S(spec: str) -> list[dict]:
    """'私|わたし は 学生|がくせい です。' -> list[RubySegment]"""
    out: list[dict] = []
    for token in spec.split(" "):
        if not token:
            continue
        if "|" in token:
            text, reading = token.split("|", 1)
            out.append(seg(text, reading))
        else:
            out.append(seg(token))
    return out


def EX(spec: str, translation: str) -> dict:
    return {"segments": S(spec), "translation": translation}


def plain(spec: str) -> str:
    """Buang penanda furigana 'kanji|bacaan' dari teks non-ruby (rumus/keterangan).

    '読|よ みます → 読|よ む' -> '読みます → 読む' (okurigana digabung tanpa spasi).
    """
    return re.sub(r"([一-鿿]+)\|[^\s]+\s*", r"\1", spec)


def BUNPO(
    id: str, judul: str, rumus: str, keterangan: list[str], penjelasan: str,
    contoh: list[tuple[str, str]],
) -> dict:
    return {
        "id": id,
        "judul": judul,
        "rumus": plain(rumus),
        "keterangan": [plain(k) for k in keterangan],
        "penjelasan": penjelasan,
        "contoh": [EX(jp, id_) for jp, id_ in contoh],
    }


def KOTOBA(
    id: str, word: str, kana: str, romaji: str, meaning: str, word_type: str,
    example: tuple[str, str], display: str | None = None,
) -> dict:
    return {
        "id": id,
        "word": word,
        "kana": kana,
        "romaji": romaji,
        "meaning": meaning,
        "word_type": word_type,
        "segments": S(display or (f"{word}|{kana}" if _KANJI_RE.search(word) else word)),
        "example": EX(example[0], example[1]),
    }


def KANJI(
    id: str, character: str, onyomi: str, kunyomi: str, meaning: str, strokes: int,
    jukugo: list[tuple[str, str, str]],
) -> dict:
    return {
        "id": id,
        "character": character,
        "onyomi": onyomi,
        "kunyomi": kunyomi,
        "meaning": meaning,
        "stroke_count": strokes,
        "jukugo": [
            {
                "word": w,
                "kana": k,
                "meaning": m,
                "segments": S(f"{w}|{k}" if _KANJI_RE.search(w) else w),
            }
            for w, k, m in jukugo
        ],
    }


def KAIWA(judul: str, latar: str, dialog: list[tuple[str, str, str, str]]) -> dict:
    return {
        "judul": judul,
        "latar": latar,
        "dialog": [
            {
                "speaker": speaker,
                "speaker_reading": reading,
                "segments": S(jp),
                "translation": id_,
            }
            for speaker, reading, jp, id_ in dialog
        ],
    }


def QB(
    id: str, question: str, options: list[str], answer: int, correct: str, highlight: str,
    rumus: str, explanation: str,
) -> dict:
    """Soal Bunpo pilihan ganda. `question` memakai ＿＿ sebagai bagian rumpang."""
    return {
        "id": id,
        "question_segments": S(question),
        "question_text": None,
        "options": options,
        "answer_index": answer,
        "correct_segments": S(correct),
        "highlight_text": highlight,
        "rumus": plain(rumus),
        "explanation": explanation,
    }


def QB_ID(
    id: str, prompt_id: str, options: list[str], answer: int, correct: str, highlight: str,
    rumus: str, explanation: str,
) -> dict:
    """Soal Bunpo dengan stem Bahasa Indonesia (pilih kalimat Jepang yang benar)."""
    return {
        "id": id,
        "question_segments": None,
        "question_text": prompt_id,
        "options": options,
        "answer_index": answer,
        "correct_segments": S(correct),
        "highlight_text": highlight,
        "rumus": plain(rumus),
        "explanation": explanation,
    }


_PARTIKEL_STOP = {
    "は", "が", "を", "に", "へ", "で", "と", "の", "も", "か", "や", "ね", "よ",
    "から", "まで", "より", "だけ", "ぐらい", "など", "とき", "こと",
    "です", "でした", "ですか", "ください", "ましょう", "じゃありません",
    "あります", "ありません", "います", "ません", "ます", "した", "して",
}


def _merge_okurigana(segments: list[dict]) -> list[dict]:
    """Gabungkan okurigana ke blok kanji sebelumnya (安|やす + い -> 安い).

    Khusus untuk soal susun kata: tanpa ini, 安い terpecah menjadi dua blok terpisah.
    Token kana yang termasuk partikel/kopula (は, が, です, …) TIDAK digabung.
    """
    out: list[dict] = []
    for s in segments:
        prev = out[-1] if out else None
        mergeable = (
            prev is not None
            and prev.get("reading")
            and s.get("reading") is None
            and not _KANJI_RE.search(s["text"])
            and s["text"] not in _PARTIKEL_STOP
        )
        if mergeable:
            out[-1] = {"text": prev["text"] + s["text"], "reading": prev["reading"]}
        else:
            out.append(dict(s))
    return out


def QS(id: str, translation: str, correct: str, distractors: str = "") -> dict:
    """Soal susun kata: `correct` token dipisah spasi, `distractors` juga."""
    return {
        "id": id,
        "translation": translation,
        "hint": None,
        "correct_order": _merge_okurigana(S(correct)),
        "distractors": _merge_okurigana(S(distractors)) if distractors else [],
    }


def CHAPTER(
    number: int, title: str, title_translation: str, bunpo: list[dict], kotoba: list[dict],
    kanji: list[dict], kaiwa: dict, quiz_bunpo: list[dict], quiz_susun: list[dict],
) -> dict:
    return {
        "number": number,
        "book": 1 if number <= 25 else 2,
        "title": title,
        "title_translation": title_translation,
        "has_content": True,
        "content": {
            "bunpo": bunpo,
            "kotoba": kotoba,
            "kanji": kanji,
            "kaiwa": kaiwa,
            "quiz_bunpo": quiz_bunpo,
            "quiz_susun": quiz_susun,
        },
    }
