# Gakushu Nihongo 2 — PRD

## Problem Statement (Bahasa Indonesia)
Web app PWA untuk belajar Bahasa Jepang berdasarkan Minna no Nihongo 1 & 2. Data terkonsolidasi di satu MongoDB. Frontend Bahasa Indonesia. Nav dipisah per fitur; content editor dengan furigana; AI padding quiz.

## User Personas
1. **Learner** — otodidak Minna no Nihongo 1 & 2. Butuh materi Bunpou/Kotoba/Kanji/Kaiwa, quiz lintas bab, kartu ulangan (weak items), progres + streak.
2. **Admin/Editor** — memelihara materi, publish/unpublish, AI-pad quiz, edit furigana.

## Core Requirements
- Auth email+password dengan HttpOnly cookie session + JWT + bcrypt + IP lockout.
- MongoDB tunggal (users, sessions, chapters, progress, attempts).
- 49 bab (Minna 1 nomor 2–25; Minna 2 nomor 26–50) diimpor dari repo asli.
- Setiap bab: bunpo, kotoba (dengan segments furigana), kanji (dengan jukugo), kaiwa, quiz_bunpo, quiz_susun.
- Nav utama 6 halaman: **Beranda / Bab / Quiz / Kanji / Kartu / Progres** (+ Admin untuk role admin).
- Quiz lintas-bab agregat: Bunpo, Kanji, Kotoba, Susun Kata, Campuran (filter by book / bab).
- Idempotency: unique(user_id, operation_id) di collection `attempts`.
- Progress: streak (hari beruntun), best_score, average_score, total_sessions.
- Kartu Hafalan: ulang item yang paling sering salah (top-20 by wrong_count).
- Admin CRUD chapter + publish toggle + LLM-pad quiz per-bab + Pad-Semua bulk job + Furigana segment editor.
- Mobile-first: hamburger nav, layout 1-col ≤760px, hero + card padding proporsional.

## What's Been Implemented
### 2026-02-09 — Iteration 6
- Auth stack + 49 chapters seeded + admin CRUD + single-chapter LLM pad + reset.

### 2026-02-09 — Iteration 7
- Nav restructure 6 halaman terpisah (Beranda/Bab/Quiz/Kanji/Kartu/Progres) sesuai referensi screenshot user.
- Beranda: hero card + Menu Bab/Menu Quiz tiles + statistik + riwayat + CTA guest.
- Bab list dengan filter Minna 1 / Minna 2 / Semua.
- ChapterDetail dipangkas jadi 4 tab (Bunpou/Kotoba/Kanji/Kaiwa) — quiz + flashcard pindah ke halaman dedikasi.
- Quiz page: pilih jenis (5 tipe) + cakupan (buku / bab spesifik) + play + hasil dengan penjelasan.
- Kanji page: flashcard reviewer dengan filter book/bab.
- Kartu page: weak-items dari attempts.items yang salah, di-group by frequency.
- Progres page: streak, best, average, riwayat skor + kanji sering salah.
- Backend: /api/library/{kanji,kotoba,quiz} + POST /api/library/quiz/attempt + /api/library/weak-items + streak/best/avg di /api/progress.
- Admin: FuriganaSegmentEditor untuk kotoba segments + tombol "Perlengkapi semua quiz ke 15" dengan progress polling (in-memory job).
- Mobile responsive: hamburger nav, hero heading di-scale-down, menu tile 1-col, stat tiles 2-col, chapter grid 2-col di small screen.
- 27/27 backend tests lolos (13 lama + 14 baru).

## Prioritized Backlog
### P1
- Full Furigana editor untuk kaiwa dialog lines + kanji jukugo (saat ini hanya kotoba).
- Audio pengucapan onyomi/kunyomi per kanji (butuh Emergent Object Storage + TTS integration).
- Editor quiz susun kata (drag-and-drop segments).
- Konsistensi campuran quiz: pastikan mix 5+5+5 tetap ada 15 setelah shuffle.

### P2
- Move PAD_JOBS ke Mongo agar tahan restart & multi-worker.
- Real email password reset (Resend integration).
- Offline PWA sync queue.
- Audit log admin actions.
- Bahasa UI toggle (ID/EN/JP).
- Spaced repetition (SM-2) untuk Kartu, bukan hanya top-wrong.
