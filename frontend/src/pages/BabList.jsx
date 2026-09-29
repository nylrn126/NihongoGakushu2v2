import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";

export default function BabList() {
  const [chapters, setChapters] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [book, setBook] = useState("all");

  useEffect(() => {
    api.get("/chapters")
      .then((r) => setChapters(r.data))
      .catch(() => setError("Gagal memuat bab."))
      .finally(() => setLoading(false));
  }, []);

  const filtered = chapters.filter((c) => book === "all" || String(c.book) === book);

  return (
    <main className="page bab-page">
      <section className="page-head">
        <div>
          <div className="eyebrow">MATERI · MINNA NO NIHONGO</div>
          <h1>Semua Bab</h1>
          <p className="muted">Pilih bab untuk membaca pola kalimat, kosakata, kanji, dan percakapan.</p>
        </div>
        <div className="pill-tabs" data-testid="book-filter">
          <button className={book === "all" ? "active" : ""} onClick={() => setBook("all")} data-testid="filter-all">Semua</button>
          <button className={book === "1" ? "active" : ""} onClick={() => setBook("1")} data-testid="filter-book-1">Minna 1</button>
          <button className={book === "2" ? "active" : ""} onClick={() => setBook("2")} data-testid="filter-book-2">Minna 2</button>
        </div>
      </section>
      {loading && <div className="empty-state" data-testid="bab-loading">Memuat bab…</div>}
      {error && <div className="error">{error}</div>}
      <div className="chapter-grid" data-testid="chapter-grid">
        {filtered.map((c) => (
          <Link to={`/bab/${c.number}`} className="chapter-mini" key={c.number} data-testid={`chapter-card-${c.number}`}>
            <div className="mini-top">
              <span className="mini-num">{String(c.number).padStart(2, "0")}</span>
              <span className="mini-book">MN {c.book}</span>
            </div>
            <h3 className="ja-title">{c.title}</h3>
            <p>{c.title_translation}</p>
            <div className="mini-footer">
              <span>{c.counts.kotoba} kata</span>
              <span>{c.counts.kanji} kanji</span>
              <span>{c.counts.quiz_bunpo} soal</span>
            </div>
          </Link>
        ))}
      </div>
    </main>
  );
}
