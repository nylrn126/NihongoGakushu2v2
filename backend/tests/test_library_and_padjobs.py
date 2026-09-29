"""Iteration 7: library aggregate endpoints, weak-items, bulk pad job, extended progress."""

import os
import time
import uuid

import pytest
import requests


BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
ADMIN_EMAIL = "mpdigitech.id@gmail.com"
ADMIN_PASSWORD = "Admin@2026"


# ---------- fixtures ----------
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
    email = f"TEST_lib_{uuid.uuid4().hex[:10]}@example.com"
    r = s.post(f"{BASE_URL}/api/auth/register",
               json={"email": email, "password": "LearnerPass123!", "name": "LibTester"},
               timeout=15)
    assert r.status_code == 200, r.text
    return s


# ---------- library/kanji ----------
def test_library_kanji_all_vs_book_filter():
    r_all = requests.get(f"{BASE_URL}/api/library/kanji", timeout=15)
    assert r_all.status_code == 200
    all_data = r_all.json()
    assert "total" in all_data and "cards" in all_data
    assert all_data["total"] == len(all_data["cards"])
    total_all = all_data["total"]

    r1 = requests.get(f"{BASE_URL}/api/library/kanji", params={"book": 1}, timeout=15)
    r2 = requests.get(f"{BASE_URL}/api/library/kanji", params={"book": 2}, timeout=15)
    assert r1.status_code == 200 and r2.status_code == 200
    b1 = r1.json()["total"]
    b2 = r2.json()["total"]
    # Sum of book-filtered should be <= total (chapters missing 'book' field allowed)
    assert b1 + b2 <= total_all
    # And book filter should be strict subset when set
    assert b1 < total_all or b2 < total_all
    # Assert card shape
    if all_data["cards"]:
        c = all_data["cards"][0]
        assert "character" in c and "meaning" in c and "chapter_number" in c


def test_library_kotoba_all_vs_book_filter():
    r_all = requests.get(f"{BASE_URL}/api/library/kotoba", timeout=15)
    assert r_all.status_code == 200
    data = r_all.json()
    assert data["total"] == len(data["cards"])
    total_all = data["total"]
    r1 = requests.get(f"{BASE_URL}/api/library/kotoba", params={"book": 1}, timeout=15).json()
    r2 = requests.get(f"{BASE_URL}/api/library/kotoba", params={"book": 2}, timeout=15).json()
    assert r1["total"] + r2["total"] <= total_all


# ---------- library/quiz per type ----------
@pytest.mark.parametrize("qtype", ["bunpo", "susun", "kanji", "kotoba", "campuran"])
def test_library_quiz_types_no_answer_leak(qtype):
    params = {"type": qtype, "book": 1, "limit": 10}
    r = requests.get(f"{BASE_URL}/api/library/quiz", params=params, timeout=20)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["type"] == qtype
    qs = body["questions"]
    assert len(qs) > 0, f"no {qtype} questions returned"
    if qtype != "campuran":
        assert len(qs) <= 10
    for q in qs:
        # No answer leak
        assert "answer_index" not in q
        assert "correct_order" not in q
        assert "correct" not in q
        assert "id" in q and "|" in q["id"]
        if qtype == "susun":
            assert "tokens" in q
        else:
            # bunpo/kanji/kotoba/campuran-items all carry options
            if q.get("kind") != "susun":
                assert "options" in q and isinstance(q["options"], list) and len(q["options"]) >= 2


def test_library_quiz_campuran_mixes_kinds():
    r = requests.get(f"{BASE_URL}/api/library/quiz",
                     params={"type": "campuran", "book": 1, "limit": 15}, timeout=20)
    assert r.status_code == 200
    kinds = {q.get("kind") for q in r.json()["questions"]}
    # Should have at least 2 different kinds
    assert len(kinds & {"bunpo", "kanji", "kotoba"}) >= 2, f"campuran kinds={kinds}"


# ---------- library quiz attempt: grading + idempotency + weak-items population ----------
def test_library_attempt_grading_and_idempotency_and_weak_items(admin_session, learner_session):
    # Fetch quiz items (kanji is easiest to answer correctly with admin lookup)
    r = requests.get(f"{BASE_URL}/api/library/quiz",
                     params={"type": "kanji", "book": 1, "limit": 5}, timeout=15)
    assert r.status_code == 200
    questions = r.json()["questions"]
    assert len(questions) >= 3

    # Use admin to find true meaning per character
    items = []
    correct_expected = 0
    for idx, q in enumerate(questions):
        # id like kanji|<ch>|<char>
        _, chn, char = q["id"].split("|", 2)
        ch = admin_session.get(f"{BASE_URL}/api/admin/chapters/{chn}", timeout=15).json()
        k = next(x for x in ch["content"]["kanji"] if x["character"] == char)
        true_meaning = k["meaning"]
        if idx == 0:
            # deliberately wrong
            wrong = next((o for o in q["options"] if o != true_meaning), q["options"][0])
            items.append({"id": q["id"], "picked": wrong})
        else:
            items.append({"id": q["id"], "picked": true_meaning})
            correct_expected += 1

    op_id = f"op-{uuid.uuid4().hex}"
    payload = {"type": "kanji", "book": 1, "items": items, "operation_id": op_id}
    r1 = learner_session.post(f"{BASE_URL}/api/library/quiz/attempt", json=payload, timeout=20)
    assert r1.status_code == 200, r1.text
    body1 = r1.json()
    assert body1["correct"] == correct_expected
    assert body1["total"] == len(items)
    assert body1["score"] == round(correct_expected / len(items) * 100)
    # items[] contain correct_value + is_correct
    assert len(body1["items"]) == len(items)
    wrong_items = [i for i in body1["items"] if not i["is_correct"]]
    assert len(wrong_items) >= 1
    for it in body1["items"]:
        assert "correct_value" in it and "is_correct" in it

    # Idempotency: resubmit → same id
    r2 = learner_session.post(f"{BASE_URL}/api/library/quiz/attempt", json=payload, timeout=20)
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["id"] == body1["id"], "duplicate operation_id must not create new attempt"

    # Weak-items should now include our deliberately-wrong kanji
    time.sleep(0.5)
    wi = learner_session.get(f"{BASE_URL}/api/library/weak-items", timeout=15)
    assert wi.status_code == 200
    wi_body = wi.json()
    cards = wi_body["cards"] if isinstance(wi_body, dict) else wi_body
    assert isinstance(cards, list)
    assert any(c.get("wrong_count", 0) > 0 for c in cards), f"no weak items after wrong answer: {wi_body}"


# ---------- extended progress fields ----------
def test_progress_has_extended_fields(learner_session):
    r = learner_session.get(f"{BASE_URL}/api/progress", timeout=15)
    assert r.status_code == 200
    body = r.json()
    for field in ("streak", "best_score", "average_score", "total_sessions",
                  "completed", "total_chapters", "progress", "attempts"):
        assert field in body, f"missing field {field}"
    assert isinstance(body["streak"], int)
    assert isinstance(body["best_score"], int)
    assert isinstance(body["average_score"], int)
    assert isinstance(body["total_sessions"], int)
    # Since learner just submitted an attempt, sessions >= 1
    assert body["total_sessions"] >= 1


# ---------- admin gating for new endpoints ----------
def test_weak_items_requires_auth():
    r = requests.get(f"{BASE_URL}/api/library/weak-items", timeout=15)
    assert r.status_code == 401


def test_learner_forbidden_from_pad_all(learner_session):
    r = learner_session.post(f"{BASE_URL}/api/admin/pad-all-quizzes", timeout=15)
    assert r.status_code == 403


# ---------- bulk pad job: verify launches and reports progress ----------
def test_admin_pad_all_launches_job(admin_session):
    r = admin_session.post(f"{BASE_URL}/api/admin/pad-all-quizzes", timeout=20)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "job_id" in body
    assert "total" in body
    assert "targets" in body and isinstance(body["targets"], list)
    assert body["total"] == len(body["targets"])

    job_id = body["job_id"]

    # Poll status endpoint shape
    s = admin_session.get(f"{BASE_URL}/api/admin/pad-jobs/{job_id}", timeout=15)
    assert s.status_code == 200
    js = s.json()
    for f in ("total", "done", "progress", "finished"):
        assert f in js, f"missing {f} in job status"
    assert isinstance(js["progress"], list)
    assert isinstance(js["finished"], bool)

    # If there are targets, wait briefly and confirm 'done' or 'progress' advances (best-effort, don't fail whole test)
    if body["total"] > 0:
        advanced = False
        deadline = time.time() + 35
        while time.time() < deadline:
            js2 = admin_session.get(f"{BASE_URL}/api/admin/pad-jobs/{job_id}", timeout=15).json()
            if js2["done"] >= 1 or len(js2["progress"]) >= 1 or js2["finished"]:
                advanced = True
                break
            time.sleep(3)
        # We don't hard-fail here since LLM may be slow / no targets; just log via assert message
        assert advanced or body["total"] == 0, "pad job did not advance within 35s"

    # Unknown job → 404
    bad = admin_session.get(f"{BASE_URL}/api/admin/pad-jobs/does-not-exist", timeout=15)
    assert bad.status_code == 404


# ---------- backward compat: original /api/chapters/{n}/quiz still works ----------
def test_chapter_quiz_still_works(learner_session):
    detail = requests.get(f"{BASE_URL}/api/chapters/2", timeout=15).json()
    qids = [q["id"] for q in detail["content"]["quiz_bunpo"]]
    assert len(qids) > 0
    payload = {"quiz_kind": "bunpo", "answers": {qids[0]: 0},
               "operation_id": f"op-{uuid.uuid4().hex}"}
    r = learner_session.post(f"{BASE_URL}/api/chapters/2/quiz", json=payload, timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert "score" in body and "correct" in body and "total" in body
