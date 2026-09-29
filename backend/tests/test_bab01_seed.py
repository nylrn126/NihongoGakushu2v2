"""Bab 1 seed regression tests (iteration 9).

Verifies the newly added Minna no Nihongo Bab 1 content is present, well-formed
and integrates with library endpoints, admin visibility and learner quiz flow.
Idempotency of seed_chapters() is implicitly verified because backend is already
running when this test executes (no duplicates should exist).
"""

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
    email = f"TEST_bab01_{uuid.uuid4().hex[:10]}@example.com"
    r = s.post(f"{BASE_URL}/api/auth/register",
               json={"email": email, "password": "LearnerPass123!", "name": "Bab1"},
               timeout=15)
    assert r.status_code == 200, r.text
    return s


# ---------- 50 chapters incl. bab 1 ----------
def test_public_chapters_include_bab1():
    r = requests.get(f"{BASE_URL}/api/chapters", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 50
    nums = sorted(c["number"] for c in data)
    assert nums == list(range(1, 51))
    bab1 = next(c for c in data if c["number"] == 1)
    assert bab1["book"] == 1
    assert bab1["title"]
    assert bab1["title_translation"]
    # counts sanity
    counts = bab1["counts"]
    assert counts["bunpo"] == 5
    assert counts["kotoba"] == 20
    assert counts["kanji"] == 5
    assert counts["quiz_bunpo"] == 5
    assert counts["quiz_susun"] == 4
    assert counts["kaiwa_lines"] >= 6


# ---------- Bab 1 detail (learner view, answers stripped) ----------
def test_bab1_detail_shape_and_no_answer_leak():
    r = requests.get(f"{BASE_URL}/api/chapters/1", timeout=15)
    assert r.status_code == 200
    ch = r.json()
    assert ch["number"] == 1
    content = ch["content"]
    assert len(content["bunpo"]) == 5
    assert len(content["kotoba"]) == 20
    assert len(content["kanji"]) == 5
    assert len(content["quiz_bunpo"]) == 5
    assert len(content["quiz_susun"]) == 4
    # Kaiwa
    kaiwa = content.get("kaiwa") or {}
    assert len(kaiwa.get("dialog", [])) >= 6
    # Kanji has jukugo
    for k in content["kanji"]:
        assert "jukugo" in k
        assert isinstance(k["jukugo"], list)
        assert len(k["jukugo"]) >= 1
    # Answer leak checks
    for q in content["quiz_bunpo"]:
        assert "answer_index" not in q
        assert "explanation" not in q
    for q in content["quiz_susun"]:
        assert "correct_order" not in q
        assert "tokens" in q


# ---------- Admin detail exposes answer_index ----------
def test_admin_bab1_detail_has_answers(admin_session):
    r = admin_session.get(f"{BASE_URL}/api/admin/chapters/1", timeout=15)
    assert r.status_code == 200
    ch = r.json()
    qb = ch["content"]["quiz_bunpo"]
    assert len(qb) == 5
    for q in qb:
        assert "answer_index" in q
        assert isinstance(q["answer_index"], int)
    # admin susun should include correct_order
    for q in ch["content"]["quiz_susun"]:
        assert "correct_order" in q


def test_admin_chapters_count_50(admin_session):
    r = admin_session.get(f"{BASE_URL}/api/admin/chapters", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 50
    nums = sorted(c["number"] for c in data)
    assert nums[0] == 1


# ---------- Library counts include bab 1 additions ----------
def test_library_kotoba_book1_includes_bab1():
    r = requests.get(f"{BASE_URL}/api/library/kotoba",
                     params={"book": 1}, timeout=15)
    assert r.status_code == 200
    body = r.json()
    items = body.get("items") or body.get("kotoba") or []
    # Filter to bab 1 items when possible
    bab1_items = [x for x in items if x.get("chapter_number") == 1]
    assert len(bab1_items) >= 20, f"expected >=20 bab1 kotoba, got {len(bab1_items)}"


def test_library_kanji_book1_includes_bab1():
    r = requests.get(f"{BASE_URL}/api/library/kanji",
                     params={"book": 1}, timeout=15)
    assert r.status_code == 200
    body = r.json()
    items = body.get("items") or body.get("kanji") or []
    bab1_items = [x for x in items if x.get("chapter_number") == 1]
    assert len(bab1_items) >= 5
    chars = {x.get("char") or x.get("kanji") for x in bab1_items}
    # At least the 5 kanji we authored
    expected = {"私", "人", "学", "生", "先"}
    assert expected.issubset(chars), f"missing kanji: {expected - chars}"


# ---------- Library quiz pool includes bab 1 ----------
def test_library_quiz_bunpo_pool_includes_bab1():
    # Sample multiple times because limit=5 randomises; bab 1 chapter has 5/total qs.
    seen_chapter1 = False
    for _ in range(15):
        r = requests.get(f"{BASE_URL}/api/library/quiz",
                         params={"type": "bunpo", "book": 1, "limit": 5}, timeout=15)
        assert r.status_code == 200
        for q in r.json()["questions"]:
            qid = q.get("id", "")
            # id shape looks like "bunpo|<chapter>|<qref>"
            parts = qid.split("|")
            if len(parts) >= 2 and parts[1] == "1":
                seen_chapter1 = True
                break
        if seen_chapter1:
            break
    assert seen_chapter1, "bab 1 bunpo questions never appeared in library quiz pool"


def test_library_quiz_susun_pool_includes_bab1():
    seen_chapter1 = False
    for _ in range(15):
        r = requests.get(f"{BASE_URL}/api/library/quiz",
                         params={"type": "susun", "book": 1, "limit": 5}, timeout=15)
        assert r.status_code == 200
        for q in r.json()["questions"]:
            parts = q.get("id", "").split("|")
            if len(parts) >= 2 and parts[1] == "1":
                seen_chapter1 = True
                # verify token shape as segment objects
                for t in q["tokens"]:
                    assert isinstance(t, dict) and "text" in t
                break
        if seen_chapter1:
            break
    assert seen_chapter1, "bab 1 susun questions never appeared in library quiz pool"


def test_library_quiz_kanji_pool_includes_bab1():
    seen_chars = set()
    expected = {"私", "人", "学", "生", "先"}
    for _ in range(20):
        r = requests.get(f"{BASE_URL}/api/library/quiz",
                         params={"type": "kanji", "book": 1, "limit": 5}, timeout=15)
        assert r.status_code == 200
        for q in r.json()["questions"]:
            # stem or prompt should include the kanji char
            for ch in expected:
                blob = str(q)
                if ch in blob:
                    seen_chars.add(ch)
        if expected.issubset(seen_chars):
            break
    assert seen_chars, "no bab1 kanji encountered in kanji quiz pool"


# ---------- Quiz submission on Bab 1 with idempotency ----------
def test_bab1_quiz_submission_grades_and_is_idempotent(learner_session, admin_session):
    admin_ch = admin_session.get(f"{BASE_URL}/api/admin/chapters/1", timeout=15).json()
    answers = {q["id"]: q["answer_index"] for q in admin_ch["content"]["quiz_bunpo"]}
    op_id = f"op-{uuid.uuid4().hex}"
    payload = {"quiz_kind": "bunpo", "answers": answers, "operation_id": op_id}
    r1 = learner_session.post(f"{BASE_URL}/api/chapters/1/quiz",
                              json=payload, timeout=15)
    assert r1.status_code == 200, r1.text
    b1 = r1.json()
    assert b1["total"] == 5
    assert b1["correct"] == 5
    assert b1["score"] == 100
    # Idempotency: same op_id must return same attempt
    r2 = learner_session.post(f"{BASE_URL}/api/chapters/1/quiz",
                              json=payload, timeout=15)
    assert r2.status_code == 200
    assert r2.json()["id"] == b1["id"]


# ---------- Seed idempotency (implicit; only one bab1 doc exists) ----------
def test_only_one_bab1_document():
    r = requests.get(f"{BASE_URL}/api/chapters", timeout=15)
    data = r.json()
    bab1s = [c for c in data if c["number"] == 1]
    assert len(bab1s) == 1
