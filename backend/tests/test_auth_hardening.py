import os
import uuid

import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")


def test_admin_login_and_failed_login_lockout():
    admin = requests.Session()
    response = admin.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "editor@gakushu.local", "password": "GakushuEditor2026!", "name": ""},
        timeout=15,
    )
    assert response.status_code == 200
    assert response.json()["role"] == "admin"
    assert admin.cookies.get("access_token")

    email = f"lockout_{uuid.uuid4().hex[:12]}@example.com"
    register = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"email": email, "password": "ValidPass123!", "name": "Lockout"},
        timeout=15,
    )
    assert register.status_code == 200
    statuses = []
    for _ in range(5):
        failed = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": "WrongPass123!", "name": ""},
            timeout=15,
        )
        statuses.append(failed.status_code)
        assert failed.status_code == 401
    locked = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": "ValidPass123!", "name": ""},
        timeout=15,
    )
    print(f"lockout statuses={statuses}, followup={locked.status_code}")
    assert locked.status_code == 429


def test_forgot_password_forces_change_and_new_password_login():
    email = f"reset_{uuid.uuid4().hex[:12]}@example.com"
    session = requests.Session()
    assert session.post(
        f"{BASE_URL}/api/auth/register",
        json={"email": email, "password": "ValidPass123!", "name": "Reset"},
        timeout=15,
    ).status_code == 200
    reset = session.post(f"{BASE_URL}/api/auth/forgot-password", json={"email": email}, timeout=15)
    assert reset.status_code == 200
    temporary = reset.json()["temporary_password"]
    login = requests.Session()
    assert login.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": temporary, "name": ""},
        timeout=15,
    ).status_code == 200
    me = login.get(f"{BASE_URL}/api/auth/me", timeout=15).json()
    assert me["must_change_password"] is True
    changed = login.post(
        f"{BASE_URL}/api/auth/change-password",
        json={"current_password": temporary, "new_password": "NewValidPass123!"},
        timeout=15,
    )
    assert changed.status_code == 200
    assert login.get(f"{BASE_URL}/api/auth/me", timeout=15).json()["must_change_password"] is False