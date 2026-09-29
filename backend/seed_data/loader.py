"""Import Minna no Nihongo chapters from seed_data DSL into MongoDB."""
from seed_data.bab01 import CHAPTERS as C0
from seed_data.bab02_09 import CHAPTERS as C1
from seed_data.bab10_17 import CHAPTERS as C2
from seed_data.bab18_25 import CHAPTERS as C3
from seed_data.bab26_30 import CHAPTERS as C4
from seed_data.bab31_35 import CHAPTERS as C5
from seed_data.bab36_40 import CHAPTERS as C6
from seed_data.bab41_45 import CHAPTERS as C7
from seed_data.bab46_50 import CHAPTERS as C8

ALL_CHAPTERS = C0 + C1 + C2 + C3 + C4 + C5 + C6 + C7 + C8


def chapter_summary(chapter: dict) -> dict:
    content = chapter.get("content") or {}
    return {
        "number": chapter["number"],
        "book": chapter["book"],
        "book_label": f"Minna no Nihongo {chapter['book']}",
        "title": chapter["title"],
        "title_translation": chapter["title_translation"],
        "has_content": chapter.get("has_content", True),
        "counts": {
            "bunpo": len(content.get("bunpo", [])),
            "kotoba": len(content.get("kotoba", [])),
            "kanji": len(content.get("kanji", [])),
            "quiz_bunpo": len(content.get("quiz_bunpo", [])),
            "quiz_susun": len(content.get("quiz_susun", [])),
            "kaiwa_lines": len((content.get("kaiwa") or {}).get("dialog", [])),
        },
    }
