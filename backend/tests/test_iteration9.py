"""Iteration 9 tests: admin susun add flow + progress total_chapters + PUT idempotency."""
import os
import uuid
import copy

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
    email = f"TEST_iter9_{uuid.uuid4().hex[:10]}@example.com"
    r = s.post(f"{BASE_URL}/api/auth/register",
               json={"email": email, "password": "LearnerPass123!", "name": "Iter9"},
               timeout=15)
    assert r.status_code == 200, r.text
    return s


def test_progress_total_chapters_is_50(learner_session):
    r = learner_session.get(f"{BASE_URL}/api/progress", timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("total_chapters") == 50, body


def test_admin_put_susun_add_and_susun_grading_and_idempotency_and_restore(admin_session, learner_session):
    # 1. Snapshot original
    r = admin_session.get(f"{BASE_URL}/api/admin/chapters/1", timeout=15)
    assert r.status_code == 200
    original_susun = copy.deepcopy(r.json()["content"]["quiz_susun"])
    assert len(original_susun) == 4

    new_item = {
        "id": "qs1-new-test",
        "translation": "Halo dunia.",
        "hint": None,
        "correct_order": [
            {"text": "こんにちは", "reading": None},
            {"text": "世界", "reading": "せかい"},
        ],
        "distractors": [],
    }
    extended = original_susun + [new_item]

    # 2. PUT with extended susun list
    put1 = admin_session.put(
        f"{BASE_URL}/api/admin/chapters/1",
        json={"content": {"quiz_susun": extended}},
        timeout=15,
    )
    assert put1.status_code == 200, put1.text

    try:
        # 3. Verify persistence via admin GET
        got = admin_session.get(f"{BASE_URL}/api/admin/chapters/1", timeout=15).json()
        susun = got["content"]["quiz_susun"]
        assert len(susun) == 5, f"expected 5, got {len(susun)}"
        new = next((s for s in susun if s["id"] == "qs1-new-test"), None)
        assert new is not None, "new susun item missing"
        assert new["translation"] == "Halo dunia."
        co = new["correct_order"]
        assert isinstance(co, list) and len(co) == 2
        # Preserved as segment objects with text and reading keys
        assert co[0]["text"] == "こんにちは"
        assert "reading" in co[0]
        assert co[1]["text"] == "世界"
        assert co[1]["reading"] == "せかい"

        # 4. PUT idempotency — same body twice, still length 5, still one qs1-new-test
        put2 = admin_session.put(
            f"{BASE_URL}/api/admin/chapters/1",
            json={"content": {"quiz_susun": extended}},
            timeout=15,
        )
        assert put2.status_code == 200
        got2 = admin_session.get(f"{BASE_URL}/api/admin/chapters/1", timeout=15).json()
        susun2 = got2["content"]["quiz_susun"]
        assert len(susun2) == 5
        assert sum(1 for s in susun2 if s["id"] == "qs1-new-test") == 1

        # 5. Susun grading with new item — correct order
        op_id_a = f"op-{uuid.uuid4().hex}"
        r_ok = learner_session.post(
            f"{BASE_URL}/api/chapters/1/quiz",
            json={
                "quiz_kind": "susun",
                "answers": {"qs1-new-test": ["こんにちは", "世界"]},
                "operation_id": op_id_a,
            },
            timeout=15,
        )
        assert r_ok.status_code == 200, r_ok.text
        body_ok = r_ok.json()
        items = body_ok.get("items") or []
        target = next((it for it in items if it.get("id") == "qs1-new-test"), None)
        assert target is not None, f"no grading item for qs1-new-test: {body_ok}"
        assert target["is_correct"] is True, target

        # 6. Susun grading — wrong order
        op_id_b = f"op-{uuid.uuid4().hex}"
        r_bad = learner_session.post(
            f"{BASE_URL}/api/chapters/1/quiz",
            json={
                "quiz_kind": "susun",
                "answers": {"qs1-new-test": ["世界", "こんにちは"]},
                "operation_id": op_id_b,
            },
            timeout=15,
        )
        assert r_bad.status_code == 200, r_bad.text
        items_b = r_bad.json().get("items") or []
        target_b = next((it for it in items_b if it.get("id") == "qs1-new-test"), None)
        assert target_b is not None
        assert target_b["is_correct"] is False, target_b
    finally:
        # 7. Cleanup — restore original 4-item susun list
        restore = admin_session.put(
            f"{BASE_URL}/api/admin/chapters/1",
            json={"content": {"quiz_susun": original_susun}},
            timeout=15,
        )
        assert restore.status_code == 200, restore.text
        final = admin_session.get(f"{BASE_URL}/api/admin/chapters/1", timeout=15).json()
        assert len(final["content"]["quiz_susun"]) == 4
