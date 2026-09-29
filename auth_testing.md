# Gakushu Nihongo 2 authentication test contract

1. `POST /api/auth/register` with a new email returns a learner and sets HttpOnly `access_token` and `refresh_token` cookies.
2. `GET /api/auth/me` with those cookies returns the same learner without `password_hash`.
3. `POST /api/auth/refresh` rotates the refresh session and keeps the learner signed in.
4. `POST /api/auth/logout` clears both cookies.
5. `POST /api/auth/login` rejects incorrect credentials and accepts the seeded admin.
6. `POST /api/auth/forgot-password` returns a one-time temporary password for an existing account; the next password change must use it.
7. `POST /api/auth/change-password` clears `must_change_password` and accepts the new password on the next login.

Seeded admin: `editor@gakushu.local` / `GakushuEditor2026!` (role: admin)