import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function Beranda() {
  const { user } = useAuth();
  const [progress, setProgress] = useState(null);
  useEffect(() => {
    if (user) api.get("/progress").then((r) => setProgress(r.data)).catch(() => {});
  }, [user]);

  return (
    <main className="page beranda">
      <section className="hero-card" data-testid="beranda-hero">
        <div className="hero-inner">
          <span className="hero-badge">Minna no Nihongo 1 &amp; 2</span>
          <h1>Belajar Bahasa Jepang, <em>いっしょに!</em></h1>
          <p>Satu tempat untuk mempelajari Bahasa Jepang Bab 1–50. Materi mencakup tata bahasa (Bunpō), kosakata (Kotoba), Kanji, dan percakapan (Kaiwa), dilengkapi contoh penggunaan, penjelasan Bahasa Indonesia, dan latihan kuis untuk setiap materi.</p>
          <div className="hero-actions">
            <Link className="primary-button" to="/bab" data-testid="hero-cta-bab">Mulai Bab 1<span>→</span></Link>
            <Link className="outline-button" to="/quiz" data-testid="hero-cta-quiz">Coba Quiz</Link>
          </div>
        </div>
      </section>

      <section className="menu-grid" data-testid="beranda-menu-grid">
        <Link to="/bab" className="menu-tile" data-testid="menu-tile-bab">
          <div className="menu-icon"><i className="mi mi-book" /></div>
          <div>
            <h3>Menu Bab</h3>
            <p>Materi pembelajaran Bab 1–50: pola kalimat, kosakata, kanji, dan percakapan — lengkap dengan furigana di atas kanji.</p>
            <small><b>Minna no Nihongo 1</b> · Bab 1–25 &nbsp;·&nbsp; <b>Minna no Nihongo 2</b> · Bab 26–50</small>
          </div>
          <span className="menu-arrow">→</span>
        </Link>
        <Link to="/quiz" className="menu-tile" data-testid="menu-tile-quiz">
          <div className="menu-icon"><i className="mi mi-check" /></div>
          <div>
            <h3>Menu Quiz</h3>
            <p>Lima jenis latihan interaktif — Bunpo, Kanji, Kotoba, Campuran, dan Susun Kata. Pilih cakupan bab atau buku.</p>
            <small>Umpan balik instan · Hasil tersimpan sebagai statistik</small>
          </div>
          <span className="menu-arrow">→</span>
        </Link>
      </section>

      {user && progress && (
        <section className="stats-section" data-testid="beranda-stats">
          <h2 className="stats-title">Statistik Belajar {user.name || user.email}</h2>
          <div className="stat-tiles">
            <div className="stat-tile" data-testid="stat-total-sessions">
              <div className="stat-icon"><i className="mi mi-list" /></div>
              <strong>{progress.total_sessions || 0}</strong>
              <small>Total Sesi Quiz</small>
            </div>
            <div className="stat-tile" data-testid="stat-average">
              <div className="stat-icon vermilion"><i className="mi mi-target" /></div>
              <strong>{progress.average_score || 0}%</strong>
              <small>Rata-rata Skor</small>
            </div>
            <div className="stat-tile" data-testid="stat-best">
              <div className="stat-icon rose"><i className="mi mi-crown" /></div>
              <strong>{progress.best_score || 0}%</strong>
              <small>Skor Terbaik</small>
            </div>
            <div className="stat-tile" data-testid="stat-streak">
              <div className="stat-icon amber"><i className="mi mi-flame" /></div>
              <strong>{progress.streak || 0} hari</strong>
              <small>Streak Belajar</small>
            </div>
          </div>

          <h2 className="stats-title">Riwayat Quiz</h2>
          <div className="recent-list">
            {progress.attempts.slice(0, 8).map((a) => (
              <div className="recent-row" key={a.id} data-testid={`history-${a.id}`}>
                <div>
                  <b>{quizKindLabel(a.quiz_kind)}</b>
                  <span>{a.chapter_number ? `Bab ${a.chapter_number}` : "Cakupan gabungan"} · {new Date(a.created_at).toLocaleDateString("id-ID", { day: "numeric", month: "short" })}</span>
                </div>
                <div className="recent-score">{a.correct}/{a.total} · {a.score}%</div>
              </div>
            ))}
            {!progress.attempts.length && <div className="empty-state">Belum ada riwayat. Kerjakan quiz pertamamu di menu Quiz.</div>}
          </div>
        </section>
      )}

      {!user && (
        <section className="cta-band" data-testid="beranda-cta-guest">
          <div>
            <h3>Buat akun untuk menyimpan progresmu</h3>
            <p>Statistik, riwayat, dan flashcard yang sering salah akan tersimpan otomatis.</p>
          </div>
          <div className="hero-actions">
            <Link className="primary-button" to="/register" data-testid="guest-register">Daftar<span>→</span></Link>
            <Link className="outline-button" to="/login" data-testid="guest-login">Masuk</Link>
          </div>
        </section>
      )}
    </main>
  );
}

function quizKindLabel(k) {
  return ({
    bunpo: "Quiz Bunpo",
    susun: "Susun Kata",
    kanji: "Quiz Kanji",
    kotoba: "Quiz Kotoba",
    campuran: "Quiz Campuran",
  })[k] || `Quiz ${k}`;
}
