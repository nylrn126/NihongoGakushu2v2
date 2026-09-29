import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api, errorText } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const FILTERS = [
  { id: "all", label: "Semua" },
  { id: "kotoba", label: "Kotoba" },
  { id: "kanji", label: "Kanji" },
  { id: "bunpo", label: "Bunpo" },
  { id: "susun", label: "Susun Kata" },
];
const QUALITY = [
  { q: 0, label: "Lupa", cls: "again", hint: "Ulang segera" },
  { q: 3, label: "Ingat", cls: "good", hint: "+ beberapa hari" },
  { q: 5, label: "Hafal", cls: "easy", hint: "Interval panjang" },
];

export default function KartuPage() {
  const { user } = useAuth();
  const [mode, setMode] = useState("due"); // due | weak
  const [filter, setFilter] = useState("all");
  const [cards, setCards] = useState([]);
  const [idx, setIdx] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState("");

  const load = async () => {
    if (!user) return;
    setLoading(true);
    try {
      const path = mode === "due" ? "/library/due-cards?limit=50" : "/library/weak-items?limit=50";
      const r = await api.get(path);
      setCards(r.data.cards || []);
      setIdx(0); setFlipped(false);
    } catch { setCards([]); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [user, mode]);

  const visible = useMemo(() => cards.filter((c) => filter === "all" || c.kind === filter), [cards, filter]);
  const card = visible[idx];

  useEffect(() => { setIdx(0); setFlipped(false); }, [filter]);

  const review = async (quality) => {
    if (!card) return;
    try {
      await api.post("/library/review", { card_id: card.id, quality });
      const remaining = visible.filter((_, i) => i !== idx);
      setCards(cards.filter((c) => c.id !== card.id));
      setNotice(quality >= 5 ? "Kartu naik interval — hebat!" : quality >= 3 ? "Kartu akan muncul lagi beberapa hari lagi." : "Kartu akan muncul lagi besok.");
      setFlipped(false);
      if (idx >= remaining.length && idx > 0) setIdx(idx - 1);
      setTimeout(() => setNotice(""), 2000);
    } catch (e) { setNotice(errorText(e)); }
  };

  if (!user) {
    return (
      <main className="page">
        <div className="cta-band" data-testid="kartu-guest">
          <div>
            <h3>Masuk untuk melihat kartu ulangan</h3>
            <p>Kata dan kanji yang sering salah muncul di sini agar bisa dihafal ulang.</p>
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
          <div className="eyebrow">KARTU HAFALAN · SM-2</div>
          <h1>Ulangi yang perlu diingat</h1>
          <p className="muted">Kartu yang lupa muncul lebih sering; kartu yang hafal muncul lebih jarang.</p>
        </div>
        <div className="page-head-actions">
          <div className="pill-tabs">
            <button className={mode === "due" ? "active" : ""} onClick={() => setMode("due")} data-testid="kartu-mode-due">Jatuh tempo</button>
            <button className={mode === "weak" ? "active" : ""} onClick={() => setMode("weak")} data-testid="kartu-mode-weak">Sering salah</button>
          </div>
        </div>
      </section>

      <div className="pill-tabs pill-tabs-wrap" data-testid="kartu-filter">
        {FILTERS.map((f) => (
          <button key={f.id} className={filter === f.id ? "active" : ""} onClick={() => setFilter(f.id)} data-testid={`kartu-filter-${f.id}`}>{f.label}</button>
        ))}
      </div>

      {notice && <div className="notice" data-testid="kartu-notice">{notice}</div>}
      {loading && <div className="empty-state" data-testid="kartu-loading">Memuat kartu…</div>}
      {!loading && !visible.length && (
        <div className="empty-state" data-testid="kartu-empty">
          {mode === "due" ? "Tidak ada kartu jatuh tempo. Semua terjaga!" : "Belum ada kartu — kerjakan quiz dulu."}
        </div>
      )}

      {card && (
        <div className="flashcard-wrap" data-testid="kartu-flashcard">
          <button className={`flashcard kartu-fc ${flipped ? "flipped" : ""}`} onClick={() => setFlipped(!flipped)}>
            <div className="fc-meta">
              <small className="chip small">{card.kind}</small>
              {card.sr && <small className="chip small">rep {card.sr.reps} · ease {card.sr.ease}</small>}
              {card.wrong_count && <small className="wrong-count">salah {card.wrong_count}×</small>}
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

          <div className="sm2-actions" data-testid="sm2-actions">
            {QUALITY.map((q) => (
              <button key={q.q} className={`sm2-btn ${q.cls}`} onClick={() => review(q.q)} disabled={!flipped}
                      data-testid={`sm2-${q.cls}`}>
                <b>{q.label}</b><small>{q.hint}</small>
              </button>
            ))}
          </div>

          <div className="flashcard-nav">
            <span className="muted">Kartu {idx + 1} dari {visible.length}</span>
            <div>
              <button className="tiny-btn" onClick={() => { setFlipped(false); setIdx((idx - 1 + visible.length) % visible.length); }} data-testid="kartu-prev">← Sebelum</button>
              <button className="tiny-btn" onClick={() => { setFlipped(false); setIdx((idx + 1) % visible.length); }} data-testid="kartu-next">Lewati →</button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
