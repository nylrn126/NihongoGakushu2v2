"""Backend regression tests for Gakushu Nihongo v2 (chapters model).

Covers: public chapters, admin-only chapter management, quiz submission
idempotency, progress tracking, auth end-to-end with HttpOnly cookies,
brute-force lockout, and LLM-based quiz padding.
"""

import os
import uuid

import pytest
import requests


BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
ADMIN_EMAIL = "mpdigitech.id@gmail.com"
ADMIN_PASSWORD = "Admin@2026"


# ---------- fixtures ----------
@pytest.fixture(scope="session")
def admin_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login",
               json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    assert r.json()["role"] == "admin"
    return s


@pytest.fixture(scope="session")
def learner_session():
    s = requests.Session()
    email = f"TEST_learner_{uuid.uuid4().hex[:10]}@example.com"
    r = s.post(f"{BASE_URL}/api/auth/register",
               json={"email": email, "password": "LearnerPass123!", "name": "Test Learner"},
               timeout=15)
    assert r.status_code == 200, r.text
    return s


# ---------- public chapters ----------
def test_public_chapters_list():
    r = requests.get(f"{BASE_URL}/api/chapters", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 50, f"expected 50 published chapters, got {len(data)}"
    numbers = sorted(c["number"] for c in data)
    assert numbers[0] == 1 and numbers[-1] == 50
    for ch in data:
        assert "counts" in ch and "quiz_bunpo" in ch["counts"]
        assert "content" not in ch  # summary only
        assert "answer_index" not in str(ch)


def test_public_chapter_detail_strips_answers():
    r = requests.get(f"{BASE_URL}/api/chapters/2", timeout=15)
    assert r.status_code == 200
    ch = r.json()
    assert ch["number"] == 2
    assert "content" in ch
    for q in ch["content"].get("quiz_bunpo", []):
        assert "answer_index" not in q, "learner detail must not leak answer_index"
        assert "explanation" not in q
    for q in ch["content"].get("quiz_susun", []):
        assert "correct_order" not in q


# ---------- auth ----------
def test_admin_login_returns_admin_role():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login",
               json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200
    assert r.json()["role"] == "admin"
    assert s.cookies.get("access_token") and s.cookies.get("refresh_token")


def test_auth_end_to_end_cookies(learner_session):
    # register done in fixture; verify cookies present
    assert learner_session.cookies.get("access_token")
    me = learner_session.get(f"{BASE_URL}/api/auth/me", timeout=15)
    assert me.status_code == 200
    email = me.json()["email"]
    # logout
    lo = learner_session.post(f"{BASE_URL}/api/auth/logout", timeout=15)
    assert lo.status_code == 200
    # me should fail
    me2 = requests.get(f"{BASE_URL}/api/auth/me",
                       cookies={}, timeout=15)
    assert me2.status_code == 401
    # login again
    r = learner_session.post(f"{BASE_URL}/api/auth/login",
                             json={"email": email, "password": "LearnerPass123!"}, timeout=15)
    assert r.status_code == 200
    # forgot password
    fp = requests.post(f"{BASE_URL}/api/auth/forgot-password",
                       json={"email": email}, timeout=15)
    assert fp.status_code == 200
    assert "temporary_password" in fp.json()
    # re-login with new temporary sets learner_session cookies back
    temp = fp.json()["temporary_password"]
    r2 = learner_session.post(f"{BASE_URL}/api/auth/login",
                              json={"email": email, "password": temp}, timeout=15)
    assert r2.status_code == 200
    # change password back so remaining tests using learner_session work
    ch = learner_session.post(f"{BASE_URL}/api/auth/change-password",
                              json={"current_password": temp,
                                    "new_password": "LearnerPass123!"}, timeout=15)
    assert ch.status_code == 200
    # log back in with original password
    r3 = learner_session.post(f"{BASE_URL}/api/auth/login",
                              json={"email": email, "password": "LearnerPass123!"}, timeout=15)
    assert r3.status_code == 200


def test_login_lockout_after_5_failures():
    email = f"TEST_lock_{uuid.uuid4().hex[:8]}@example.com"
    reg = requests.post(f"{BASE_URL}/api/auth/register",
                        json={"email": email, "password": "GoodPass123!"}, timeout=15)
    assert reg.status_code == 200
    s = requests.Session()
    for _ in range(5):
        r = s.post(f"{BASE_URL}/api/auth/login",
                   json={"email": email, "password": "WrongPass999!"}, timeout=15)
        assert r.status_code == 401
    r6 = s.post(f"{BASE_URL}/api/auth/login",
                json={"email": email, "password": "GoodPass123!"}, timeout=15)
    assert r6.status_code == 429, f"expected 429 after 5 fails, got {r6.status_code}"


# ---------- admin gating ----------
def test_learner_forbidden_from_admin(learner_session):
    r = learner_session.get(f"{BASE_URL}/api/admin/chapters", timeout=15)
    assert r.status_code == 403


def test_admin_chapters_summary(admin_session):
    r = admin_session.get(f"{BASE_URL}/api/admin/chapters", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 50
    assert all("counts" in c for c in data)
    assert all("content" not in c for c in data)


def test_admin_chapter_detail_includes_answers(admin_session):
    r = admin_session.get(f"{BASE_URL}/api/admin/chapters/26", timeout=15)
    assert r.status_code == 200
    ch = r.json()
    qb = ch["content"]["quiz_bunpo"]
    assert len(qb) > 0
    assert "answer_index" in qb[0], "admin detail must expose answer_index"


def test_admin_update_and_restore_chapter(admin_session):
    orig = admin_session.get(f"{BASE_URL}/api/admin/chapters/26", timeout=15).json()
    original_title_tr = orig["title_translation"]
    up = admin_session.put(f"{BASE_URL}/api/admin/chapters/26",
                           json={"title_translation": "Test updated"}, timeout=15)
    assert up.status_code == 200
    assert up.json()["title_translation"] == "Test updated"
    # verify via GET
    g = admin_session.get(f"{BASE_URL}/api/admin/chapters/26", timeout=15).json()
    assert g["title_translation"] == "Test updated"
    # restore via reset
    rst = admin_session.post(f"{BASE_URL}/api/admin/chapters/26/reset", timeout=30)
    assert rst.status_code == 200
    assert rst.json()["title_translation"] == original_title_tr


def test_admin_publish_toggle(admin_session):
    r1 = admin_session.post(f"{BASE_URL}/api/admin/chapters/2/publish", timeout=15)
    assert r1.status_code == 200
    state1 = r1.json()["published"]
    r2 = admin_session.post(f"{BASE_URL}/api/admin/chapters/2/publish", timeout=15)
    assert r2.status_code == 200
    assert r2.json()["published"] != state1  # toggled back


# ---------- LLM padding ----------
def test_admin_pad_quiz_chapter_27(admin_session):
    # Verify starting count
    before = admin_session.get(f"{BASE_URL}/api/admin/chapters/27", timeout=15).json()
    before_count = len(before["content"]["quiz_bunpo"])
    assert before_count < 15, f"chapter 27 already has {before_count} questions"
    r = admin_session.post(f"{BASE_URL}/api/admin/chapters/27/pad-quiz", timeout=90)
    assert r.status_code == 200, f"pad-quiz failed: {r.status_code} {r.text}"
    body = r.json()
    assert body["generated"] > 0
    assert body["quiz_padded"] is True
    assert body["quiz_bunpo"] == 15
    # verify persisted
    after = admin_session.get(f"{BASE_URL}/api/admin/chapters/27", timeout=15).json()
    assert len(after["content"]["quiz_bunpo"]) == 15
    # reset back to original
    rst = admin_session.post(f"{BASE_URL}/api/admin/chapters/27/reset", timeout=30)
    assert rst.status_code == 200
    reset_body = rst.json()
    assert len(reset_body["content"]["quiz_bunpo"]) == before_count


# ---------- quiz submission ----------
def test_quiz_submission_idempotent_and_scores(learner_session):
    # chapter 2, q1 (qb2-1) correct answer_index is 0
    op_id = f"op-{uuid.uuid4().hex}"
    # get chapter detail to know all question ids
    detail = requests.get(f"{BASE_URL}/api/chapters/2", timeout=15).json()
    qids = [q["id"] for q in detail["content"]["quiz_bunpo"]]
    answers = {qids[0]: 0}  # only q1 answered correctly; rest unanswered → wrong
    payload = {"quiz_kind": "bunpo", "answers": answers, "operation_id": op_id}
    r1 = learner_session.post(f"{BASE_URL}/api/chapters/2/quiz", json=payload, timeout=15)
    assert r1.status_code == 200, r1.text
    body1 = r1.json()
    total = body1["total"]
    assert body1["correct"] == 1
    assert body1["score"] == round(1 / total * 100)
    r2 = learner_session.post(f"{BASE_URL}/api/chapters/2/quiz", json=payload, timeout=15)
    assert r2.status_code == 200
    assert r2.json()["id"] == body1["id"], "duplicate op_id must not create new attempt"


def test_progress_after_passing_quiz(learner_session):
    # Answer all questions correctly on chapter 2 by using admin detail to fetch answer_index
    admin = requests.Session()
    admin.post(f"{BASE_URL}/api/auth/login",
               json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    admin_ch = admin.get(f"{BASE_URL}/api/admin/chapters/2", timeout=15).json()
    answers = {q["id"]: q["answer_index"] for q in admin_ch["content"]["quiz_bunpo"]}
    payload = {"quiz_kind": "bunpo", "answers": answers,
               "operation_id": f"op-{uuid.uuid4().hex}"}
    r = learner_session.post(f"{BASE_URL}/api/chapters/2/quiz", json=payload, timeout=15)
    assert r.status_code == 200
    assert r.json()["score"] == 100
    prog = learner_session.get(f"{BASE_URL}/api/progress", timeout=15)
    assert prog.status_code == 200
    assert prog.json()["completed"] >= 1
