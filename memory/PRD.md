# Gakushu Nihongo 2 — Product Record

## Original problem statement
Rebuild the Gakushu Nihongo 2 Japanese-learning PWA with new accounts, MongoDB-backed learning content and progress, and a responsive learner experience. The first release is the core learner flow: registration/login, public lessons, lesson detail, quiz, progress dashboard, and PWA shell.

## Architecture decisions
- React with the existing CRA/Craco toolchain, React Router, Axios, and the repository's current CSS entry points.
- FastAPI with Motor and the configured MongoDB connection only.
- HttpOnly access/refresh cookies with refresh-session rotation; passwords hashed with bcrypt.
- Lesson, quiz, progress, and attempt documents use stable string IDs. Quiz attempts use a unique user/operation compound index for idempotency.
- PWA shell uses a manifest and versioned service worker; the API remains network-first.

## User personas
- New Japanese learner following Minna no Nihongo.
- Returning learner who wants a quick daily continuation point.
- Future content editor/admin (seeded role and account; admin CRUD is outside this first slice).

## Core requirements (static)
- Public lessons and lesson details with vocabulary and quiz.
- New account registration, login, logout, refresh, temporary password reset, forced password change.
- User progress, quiz score history, and resume position stored in MongoDB.
- Responsive, mobile-first learner UI with loading, empty, and error states.
- Installable PWA shell and offline shell fallback.

## Implemented — 2026-02-14
- Replaced the starter API with auth, lesson, quiz, and progress endpoints.
- Seeded three starter lessons and added MongoDB indexes.
- Replaced the starter screen with a Japanese-learning path, auth screens, lesson view, quiz flow, and dashboard.
- Added PWA manifest, service worker, install metadata, and session-aware navigation.
- Added failed-login lockout and startup admin-password reconciliation.

## Prioritized backlog
- P0: Verify API and browser flows against the running preview.
- P1: Add protected admin/editor CRUD for lessons, quizzes, vocabulary, and publish state.
- P1: Add offline lesson download and queued progress sync with conflict timestamps.
- P2: Add object-storage media metadata and audio playback.
- P2: Add production email delivery for password reset instead of in-app temporary-password display.