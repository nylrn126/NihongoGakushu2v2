import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const accents = ["vermilion", "indigo", "teal"];

export default function Home() {
  const { user } = useAuth();
  const [chapters, setChapters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/chapters")
      .then((r) => setChapters(r.data))
      .catch(() => setError("Gagal memuat daftar bab. Coba refresh."))
      .finally(() => setLoading(false));
  }, []);

  const book1 = chapters.filter((c) => c.book === 1);
  const book2 = chapters.filter((c) => c.book === 2);

  return (
    <main className="page">
      <section className="intro">
        <div>
          <div className="eyebrow">MINNA NO NIHONGO · 1 &amp; 2</div>
          <h1>Bahasa Jepang<br/><em>setiap hari</em>, sedikit demi sedikit.</h1>
          <p>Materi Minna no Nihongo 1 &amp; 2 lengkap: tata bahasa, kosakata, kanji, percakapan, dan latihan. Cocok untuk otodidak yang ingin konsisten.</p>
          <Link className="primary-button" to={user ? "/dashboard" : "/register"} data-testid="start-learning-button">
            {user ? "Lanjut belajar" : "Mulai belajar"}<span>→</span>
          </Link>
        </div>
        <div className="intro-stamp">
          <span>毎日</span>
          <small>ma i ni chi<br/>every day</small>
        </div>
      </section>

      {error && <div className="error" data-testid="chapters-error">{error}</div>}
      {loading && <div className="empty-state" data-testid="chapters-loading">Memuat bab…</div>}

      {!loading && book1.length > 0 && (
        <BookSection title="Minna no Nihongo 1" subtitle="Bab 1 – 25 · Fondasi" chapters={book1} testid="minna-1-section" />
      )}
      {!loading && book2.length > 0 && (
        <BookSection title="Minna no Nihongo 2" subtitle="Bab 26 – 50 · Lanjutan" chapters={book2} testid="minna-2-section" />
      )}
    </main>
  );
}

function BookSection({ title, subtitle, chapters, testid }) {
  return (
    <section className="lesson-section" data-testid={testid}>
      <div className="section-heading">
        <div>
          <div className="eyebrow">{subtitle}</div>
          <h2>{title}</h2>
        </div>
        <span className="lesson-count" data-testid={`${testid}-count`}>{chapters.length} bab</span>
      </div>
      <div className="lesson-grid">
        {chapters.map((c, i) => (
          <Link
            to={`/chapters/${c.number}`}
            className={`lesson-card ${i === 0 ? "featured" : ""}`}
            key={c.number}
            data-testid={`chapter-card-${c.number}`}
          >
            <div className="lesson-top">
              <span className={`lesson-number ${accents[i % accents.length]}`}>{String(c.number).padStart(2, "0")}</span>
              <span className="duration">{c.counts.kotoba} kata · {c.counts.kanji} kanji</span>
            </div>
            <div>
              <h3 className="ja-title">{c.title}</h3>
              <p>{c.title_translation}</p>
            </div>
            <div className="lesson-footer">
              <span>{c.counts.bunpo} pola · {c.counts.quiz_bunpo} soal</span>
              <span className="arrow">↗</span>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
