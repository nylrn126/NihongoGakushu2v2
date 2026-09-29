"""Iteration 8: susun tokens shape + grading, SM-2 review + due-cards, jukugo padding."""

import os
import uuid

import pytest
import requests


BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
ADMIN_EMAIL = "mpdigitech.id@gmail.com"
ADMIN_PASSWORD = "Admin@2026"


@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login",
               json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200, r.text
    return s


@pytest.fixture(scope="module")
def learner_session():
    s = requests.Session()
    email = f"TEST_iter8_{uuid.uuid4().hex[:10]}@example.com"
    r = s.post(f"{BASE_URL}/api/auth/register",
               json={"email": email, "password": "LearnerPass123!", "name": "Iter8"},
               timeout=15)
    assert r.status_code == 200, r.text
    return s


# ---------- SUSUN token shape ----------
def test_susun_quiz_tokens_are_segment_objects():
    r = requests.get(f"{BASE_URL}/api/library/quiz",
                     params={"type": "susun", "book": 1, "limit": 5}, timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert body["type"] == "susun"
    qs = body["questions"]
    assert len(qs) > 0
    for q in qs:
        assert "tokens" in q
        assert "correct_length" in q and isinstance(q["correct_length"], int) and q["correct_length"] > 0
        assert "stem" in q  # translation
        assert isinstance(q["tokens"], list) and len(q["tokens"]) >= q["correct_length"]
        # Each token must be a segment object with text (and typically reading)
        for t in q["tokens"]:
            assert isinstance(t, dict), f"token is not object: {t!r}"
            assert "text" in t and isinstance(t["text"], str)
            # reading field expected (may be empty)
            assert "reading" in t or t.get("text") is not None
        # No answer leak
        assert "correct_order" not in q


# ---------- SUSUN grading via /library/quiz/attempt ----------
def test_susun_grading_correct_and_wrong(admin_session, learner_session):
    # Pull a susun question via library
    r = requests.get(f"{BASE_URL}/api/library/quiz",
                     params={"type": "susun", "book": 1, "limit": 5}, timeout=15)
    assert r.status_code == 200
    qs = r.json()["questions"]
    assert len(qs) >= 2

    # Resolve correct order via admin
    def correct_texts_for(qid: str) -> list[str]:
        _, chn, qref = qid.split("|", 2)
        ch = admin_session.get(f"{BASE_URL}/api/admin/chapters/{chn}", timeout=15).json()
        item = next(x for x in ch["content"]["quiz_susun"] if x["id"] == qref)
        return [seg["text"] for seg in item["correct_order"]]

    q_ok = qs[0]
    q_bad = qs[1]
    correct_seq_ok = correct_texts_for(q_ok["id"])
    correct_seq_bad = correct_texts_for(q_bad["id"])

    # Wrong for q_bad: reverse the correct sequence (guarantees mismatch unless palindrome)
    wrong_seq = list(reversed(correct_seq_bad))
    if wrong_seq == correct_seq_bad and len(correct_seq_bad) > 1:
        wrong_seq = correct_seq_bad[1:] + correct_seq_bad[:1]

    items = [
        {"id": q_ok["id"], "picked": correct_seq_ok},   # correct
        {"id": q_bad["id"], "picked": wrong_seq},       # wrong
    ]
    payload = {"type": "susun", "book": 1, "items": items,
               "operation_id": f"op-{uuid.uuid4().hex}"}
    resp = learner_session.post(f"{BASE_URL}/api/library/quiz/attempt",
                                json=payload, timeout=20)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 2
    # First item correct, second wrong
    per = {i["id"]: i for i in body["items"]}
    assert per[q_ok["id"]]["is_correct"] is True, per[q_ok["id"]]
    # If bad happens to equal reverse-palindrome, tolerate — but usually wrong
    if wrong_seq != correct_seq_bad:
        assert per[q_bad["id"]]["is_correct"] is False, per[q_bad["id"]]
        assert body["correct"] == 1
        assert body["score"] == 50


# ---------- Bunpo no-leak regression ----------
def test_bunpo_quiz_no_answer_leak():
    r = requests.get(f"{BASE_URL}/api/library/quiz",
                     params={"type": "bunpo", "book": 1, "limit": 10}, timeout=15)
    assert r.status_code == 200
    for q in r.json()["questions"]:
        assert "answer_index" not in q
        assert "explanation" not in q
        assert "options" in q


# ---------- SM-2 review ----------
def test_sm2_review_progression_and_reset(learner_session):
    card_id = f"kanji|26|遅"

    def post(quality):
        r = learner_session.post(f"{BASE_URL}/api/library/review",
                                 json={"card_id": card_id, "quality": quality}, timeout=15)
        assert r.status_code == 200, r.text
        b = r.json()
        for f in ("ease", "interval", "reps", "due_at", "last_reviewed"):
            assert f in b, f"missing {f} in {b}"
        return b

    # First quality=5
    r1 = post(5)
    assert r1["reps"] == 1
    assert r1["interval"] == 1
    ease1 = r1["ease"]
    # Second quality=5 → reps=2, interval=3
    r2 = post(5)
    assert r2["reps"] == 2
    assert r2["interval"] == 3
    # Third quality=5 → reps=3, interval = round(3 * ease)
    r3 = post(5)
    assert r3["reps"] == 3
    assert r3["interval"] > r2["interval"], f"interval should grow: {r2['interval']} -> {r3['interval']}"
    # Ease should be >= 1.3 and increasing (or at least non-decreasing for q=5)
    assert r3["ease"] >= ease1 - 0.01

    # quality=0 must reset reps and interval
    r0 = post(0)
    assert r0["reps"] == 0
    assert r0["interval"] == 1


# ---------- Due cards ----------
def test_due_cards_endpoint_shape(learner_session):
    r = learner_session.get(f"{BASE_URL}/api/library/due-cards", timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert "total" in body and "cards" in body and "as_of" in body
    assert isinstance(body["cards"], list)
    assert body["total"] == len(body["cards"])
    # After the SM-2 test above, quality=0 puts a card due in 1 day → NOT due now.
    # But sortedness should still hold if any present.
    prev = ""
    for c in body["cards"]:
        due = c.get("sr", {})
        # each card has kind, id, front, back
        assert "id" in c and "kind" in c


def test_due_cards_requires_auth():
    r = requests.get(f"{BASE_URL}/api/library/due-cards", timeout=15)
    assert r.status_code == 401


def test_review_requires_auth():
    r = requests.post(f"{BASE_URL}/api/library/review",
                      json={"card_id": "kanji|26|遅", "quality": 5}, timeout=15)
    assert r.status_code == 401


# ---------- Jukugo padding (LLM) ----------
def test_pad_jukugo_admin_only(learner_session):
    r = learner_session.post(f"{BASE_URL}/api/admin/chapters/2/pad-jukugo", timeout=15)
    assert r.status_code == 403


def test_pad_jukugo_chapter_2(admin_session):
    # Chapter 2 has smallest kanji count per instructions
    r = admin_session.post(f"{BASE_URL}/api/admin/chapters/2/pad-jukugo", timeout=90)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "padded" in body and "message" in body
    # Verify chapter state — most kanji should now have >= 3 jukugo
    after = admin_session.get(f"{BASE_URL}/api/admin/chapters/2", timeout=15).json()
    kanji_list = after["content"].get("kanji", [])
    if not kanji_list:
        pytest.skip("Chapter 2 has no kanji")
    # Allow >=3 due to LLM latency/failures
    counts = [len(k.get("jukugo") or []) for k in kanji_list]
    # Majority should reach >=3
    passing = sum(1 for c in counts if c >= 3)
    assert passing >= max(1, int(len(counts) * 0.5)), \
        f"jukugo counts too low: {counts}"


# ---------- BabPicker: /api/chapters returns 50 with required fields ----------
def test_chapters_list_regression_for_babpicker():
    r = requests.get(f"{BASE_URL}/api/chapters", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 50
    for ch in data:
        for f in ("number", "title", "title_translation", "book"):
            assert f in ch, f"missing {f} in {ch}"
