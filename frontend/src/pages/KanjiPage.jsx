import React, { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";

export default function KanjiPage() {
  const [book, setBook] = useState("1");
  const [data, setData] = useState(null);
  const [idx, setIdx] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true); setIdx(0); setFlipped(false);
    const q = book === "all" ? "" : `?book=${book}`;
    api.get(`/library/kanji${q}`).then((r) => setData(r.data)).finally(() => setLoading(false));
  }, [book]);

  const cards = data?.cards || [];
  const card = cards[idx];

  return (
    <main className="page kanji-page">
      <section className="page-head compact">
        <div>
          <div className="eyebrow">FLASHCARD KANJI</div>
          <h1>Hafalkan kanji per bab</h1>
          <p className="muted">Pilih cakupan, lalu ketuk kartu untuk melihat bacaan dan arti.</p>
        </div>
        <div className="pill-tabs" data-testid="kanji-scope">
          <button className={book === "1" ? "active" : ""} onClick={() => setBook("1")} data-testid="kanji-book-1">Minna 1 (Bab 1–25)</button>
          <button className={book === "2" ? "active" : ""} onClick={() => setBook("2")} data-testid="kanji-book-2">Minna 2 (Bab 26–50)</button>
          <button className={book === "all" ? "active" : ""} onClick={() => setBook("all")} data-testid="kanji-book-all">Semua Bab</button>
        </div>
      </section>
      <div className="chip-band">
        <span className="chip"><i className="mi mi-list" /> {cards.length} kanji</span>
      </div>

      {loading && <div className="empty-state" data-testid="kanji-loading">Memuat kanji…</div>}
      {!loading && !cards.length && <div className="empty-state">Belum ada kanji untuk cakupan ini.</div>}

      {card && (
        <div className="flashcard-wrap" data-testid="kanji-flashcard">
          <button className={`flashcard kanji-fc ${flipped ? "flipped" : ""}`} onClick={() => setFlipped(!flipped)} data-testid={`flashcard-${card.character}`}>
            <div className="fc-meta"><small>Bab {card.chapter_number}</small><small>{card.stroke_count} goresan</small></div>
            {flipped ? (
              <div className="fc-back">
                <b>{card.meaning}</b>
                <small>音 {card.onyomi || "—"} · 訓 {card.kunyomi || "—"}</small>
                {card.jukugo?.length > 0 && (
                  <ul className="jukugo-inline">
                    {card.jukugo.slice(0, 3).map((j, i) => (
                      <li key={i}><b>{j.segments?.map((s) => s.text).join("") || j.word}</b> · {j.meaning}</li>
                    ))}
                  </ul>
                )}
              </div>
            ) : (
              <div className="fc-front">
                <strong className="kanji-huge">{card.character}</strong>
                <small className="muted">Ketuk untuk melihat bacaan &amp; arti</small>
              </div>
            )}
          </button>
          <div className="flashcard-nav">
            <span className="muted">Kartu {idx + 1} dari {cards.length}</span>
            <div>
              <button className="tiny-btn" onClick={() => { setFlipped(false); setIdx((idx - 1 + cards.length) % cards.length); }} data-testid="kanji-prev">← Acak</button>
              <button className="tiny-btn accent" onClick={() => { setFlipped(false); setIdx((idx + 1) % cards.length); }} data-testid="kanji-next">Berikutnya →</button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
