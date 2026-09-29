import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const FILTERS = [
  { id: "all", label: "Semua" },
  { id: "kotoba", label: "Kotoba" },
  { id: "kanji", label: "Kanji" },
  { id: "bunpo", label: "Bunpo" },
  { id: "susun", label: "Susun Kata" },
];

export default function KartuPage() {
  const { user } = useAuth();
  const [filter, setFilter] = useState("all");
  const [cards, setCards] = useState([]);
  const [idx, setIdx] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    setLoading(true);
    api.get("/library/weak-items?limit=50").then((r) => setCards(r.data.cards || [])).finally(() => setLoading(false));
  }, [user]);

  const visible = useMemo(
    () => cards.filter((c) => filter === "all" || c.kind === filter),
    [cards, filter]
  );
  const card = visible[idx];

  useEffect(() => { setIdx(0); setFlipped(false); }, [filter]);

  if (!user) {
    return (
      <main className="page">
        <div className="cta-band" data-testid="kartu-guest">
          <div>
            <h3>Masuk untuk melihat kartu ulangan</h3>
            <p>Kata dan kanji yang paling sering kamu jawab salah akan muncul di sini agar bisa dihafal ulang.</p>
          </div>
          <Link className="primary-button" to="/login">Masuk<span>→</span></Link>
        </div>
      </main>
    );
  }

  return (
    <main className="page kartu-page">
      <section className="page-head compact">
        <div>
          <div className="eyebrow">KARTU HAFALAN</div>
          <h1>Ulangi yang sering salah</h1>
          <p className="muted">Kata dan kanji yang paling sering kamu jawab salah muncul lebih dulu.</p>
        </div>
        <div className="page-head-actions">
          <Link to="/quiz" className="tiny-btn accent" data-testid="kartu-quiz-link">Kuis Dari Kartu Ini</Link>
        </div>
      </section>

      <div className="pill-tabs pill-tabs-wrap" data-testid="kartu-filter">
        {FILTERS.map((f) => (
          <button key={f.id} className={filter === f.id ? "active" : ""} onClick={() => setFilter(f.id)} data-testid={`kartu-filter-${f.id}`}>{f.label}</button>
        ))}
      </div>

      {loading && <div className="empty-state" data-testid="kartu-loading">Memuat kartu…</div>}
      {!loading && !visible.length && (
        <div className="empty-state" data-testid="kartu-empty">Belum ada — kerjakan quiz dulu, kartu yang salah akan muncul di sini.</div>
      )}

      {card && (
        <div className="flashcard-wrap" data-testid="kartu-flashcard">
          <button className={`flashcard kartu-fc ${flipped ? "flipped" : ""}`} onClick={() => setFlipped(!flipped)}>
            <div className="fc-meta">
              <small className="chip small">{card.kind}</small>
              <small className="wrong-count">salah {card.wrong_count}×</small>
            </div>
            {flipped ? (
              <div className="fc-back">
                <b>{card.back}</b>
                {card.extra && <small className="muted">{card.extra}</small>}
              </div>
            ) : (
              <div className="fc-front">
                <strong className={card.kind === "kanji" ? "kanji-huge" : "ja-title"}>{card.front}</strong>
                <small className="muted">Ketuk kartu untuk melihat jawaban</small>
              </div>
            )}
          </button>
          <div className="flashcard-nav">
            <span className="muted">Kartu {idx + 1} dari {visible.length}</span>
            <div>
              <button className="tiny-btn" onClick={() => { setFlipped(false); setIdx((idx - 1 + visible.length) % visible.length); }} data-testid="kartu-prev">← Sebelum</button>
              <button className="tiny-btn accent" onClick={() => { setFlipped(false); setIdx((idx + 1) % visible.length); }} data-testid="kartu-next">Berikutnya →</button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
