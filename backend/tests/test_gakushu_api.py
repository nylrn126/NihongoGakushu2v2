import os
import uuid

import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")


def test_public_lessons_and_detail():
    response = requests.get(f"{BASE_URL}/api/lessons", timeout=15)
    assert response.status_code == 200
    lessons = response.json()
    assert len(lessons) >= 3
    assert all("quiz" not in lesson and "vocabulary" not in lesson for lesson in lessons)
    detail = requests.get(f"{BASE_URL}/api/lessons/{lessons[0]['id']}", timeout=15)
    assert detail.status_code == 200
    assert detail.json()["vocabulary"] and detail.json()["quiz"]


def test_registration_cookie_refresh_quiz_progress_logout():
    session = requests.Session()
    email = f"test_{uuid.uuid4().hex[:12]}@example.com"
    register = session.post(
        f"{BASE_URL}/api/auth/register",
        json={"email": email, "password": "ValidPass123!", "name": "Regression User"},
        timeout=15,
    )
    assert register.status_code == 200
    assert register.json()["email"] == email
    assert "password_hash" not in register.json()
    assert session.cookies.get("access_token") and session.cookies.get("refresh_token")
    me = session.get(f"{BASE_URL}/api/auth/me", timeout=15)
    assert me.status_code == 200 and me.json()["email"] == email
    old_refresh = session.cookies.get("refresh_token")
    refreshed = session.post(f"{BASE_URL}/api/auth/refresh", timeout=15)
    assert refreshed.status_code == 200
    assert session.cookies.get("refresh_token") != old_refresh
    detail = requests.get(f"{BASE_URL}/api/lessons/lesson-01", timeout=15).json()
    answers = {question["id"]: question["answer"] for question in detail["quiz"]}
    payload = {"answers": answers, "operation_id": f"op-{uuid.uuid4().hex}"}
    quiz = session.post(f"{BASE_URL}/api/lessons/lesson-01/quiz", json=payload, timeout=15)
    assert quiz.status_code == 200 and quiz.json()["score"] == 100
    repeat = session.post(f"{BASE_URL}/api/lessons/lesson-01/quiz", json=payload, timeout=15)
    assert repeat.status_code == 200 and repeat.json()["id"] == quiz.json()["id"]
    progress = session.put(f"{BASE_URL}/api/progress", json={"lesson_id": "lesson-01", "completed": True}, timeout=15)
    assert progress.status_code == 200
    dashboard = session.get(f"{BASE_URL}/api/progress", timeout=15)
    assert dashboard.status_code == 200 and dashboard.json()["completed"] >= 1
    logout = session.post(f"{BASE_URL}/api/auth/logout", timeout=15)
    assert logout.status_code == 200
    assert session.get(f"{BASE_URL}/api/auth/me", timeout=15).status_code == 401