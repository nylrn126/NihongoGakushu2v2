# Gakushu Nihongo 2 — PRD

## Problem Statement (original, Bahasa Indonesia)
Web app PWA untuk belajar bahasa Jepang dengan seluruh akun baru dan seluruh data aplikasi dikonsolidasikan ke satu MongoDB Atlas, sambil mempertahankan fitur inti repository dan membuka ruang revisi UI/fitur. Pengguna umum otodidak berbasis Minna no Nihongo 1 & 2. Frontend/PWA Vercel; FastAPI Render; MongoDB Atlas.

## User Personas
1. **Learner** — otodidak Bahasa Jepang yang mengikuti Minna no Nihongo 1 & 2. Butuh materi grammar, kosakata, kanji, percakapan, quiz, flashcard, dan progres tersimpan.
2. **Admin/Editor** — memelihara konten (CRUD bab, publish/unpublish, extend quiz via AI).

## Core Requirements (static)
- Registrasi/login berbasis email+password dengan HttpOnly cookie session + JWT.
- Password hashing bcrypt, reset (temporary), forced change, IP+email lockout 5 percobaan/15 menit.
- MongoDB tunggal (collections: users, sessions, chapters, progress, attempts, login_attempts).
- 49 bab Minna no Nihongo 1 & 2 (nomor 2–50) diimpor dari repo asli LTZ24/GakushuNihongo2.
- Setiap bab menyimpan: bunpo, kotoba, kanji, kaiwa, quiz_bunpo, quiz_susun (dengan furigana segments).
- Quiz submission idempotent via operation_id (unique compound index).
- Progress per user per chapter+section; ringkasan dashboard.
- Admin route diproteksi backend (role check); CRUD chapter + toggle publish + LLM auto-pad quiz ke 15 soal + reset dari sumber.

## What's Been Implemented
### 2026-02-09
- Auth stack: register/login/logout/refresh/forgot/change-password dengan HttpOnly cookies (JWT HS256), lockout, forced password change.
- Chapters (49 bab) diseed dari `seed_data/*.py` DSL; endpoint publik `/api/chapters` & `/api/chapters/{n}` (menghilangkan `answer_index`).
- Quiz endpoint `/api/chapters/{n}/quiz` (idempotent, grade bunpo/susun, tulis progress bila skor ≥ 60).
- Progress endpoint `/api/progress` menghitung ringkasan + 30 riwayat percobaan.
- Admin CRUD: list, detail, PUT partial (title, translation, content merge, published), toggle publish, reset dari sumber.
- Admin LLM pad-quiz: GPT-5.4-mini via Emergent Universal Key menambah soal grammar hingga ≥15.
- Frontend Bahasa Indonesia: Home (Book 1 & Book 2 grid), ChapterDetail 6-tab (Bunpou/Kotoba/Kanji/Kaiwa/Quiz/Flashcard) + rendering furigana `<ruby>`, AuthPage, Dashboard, Admin summary table + tabbed editor.
- 13/13 backend regression tests lolos (iteration_6).

## Prioritized Backlog
### P1
- Full editor untuk `question_segments` (rich furigana) selain `question_text`.
- Editor detail untuk quiz susun kata.
- Bulk "Pad all quizzes → 15" admin action dengan progress bar.
- Object storage untuk audio/gambar kanji (Emergent Object Storage).
- Streak tracking N-hari.

### P2
- Content versioning untuk auto-reseed jika DSL sumber di-bump.
- Real email password reset (Resend).
- Offline PWA sync queue dengan konflik resolution.
- Audit log admin actions.
- Bahasa UI toggle (ID/EN/JP).
