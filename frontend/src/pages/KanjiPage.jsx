import React, { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import KanjiStroke from "@/components/KanjiStroke";
import { Ruby } from "@/components/Ruby";

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
          <p className="muted">Pilih cakupan, ketuk kartu untuk membalik. Ikon ↻ memutar ulang animasi goresan.</p>
        </div>
        <div className="pill-tabs" data-testid="kanji-scope">
          <button className={book === "1" ? "active" : ""} onClick={() => setBook("1")} data-testid="kanji-book-1">Minna 1</button>
          <button className={book === "2" ? "active" : ""} onClick={() => setBook("2")} data-testid="kanji-book-2">Minna 2</button>
          <button className={book === "all" ? "active" : ""} onClick={() => setBook("all")} data-testid="kanji-book-all">Semua Bab</button>
        </div>
      </section>
      <div className="chip-band">
        <span className="chip"><i className="mi mi-list" /> {cards.length} kanji</span>
      </div>

      {loading && <div className="empty-state" data-testid="kanji-loading">Memuat kanji…</div>}
      {!loading && !cards.length && <div className="empty-state">Belum ada kanji untuk cakupan ini.</div>}

      {card && (
        <div className="kanji-page-card" data-testid="kanji-flashcard">
          <div className="kanji-hero">
            <div className="kanji-hero-meta">
              <span className="chip">Bab {card.chapter_number}</span>
              <span className="chip small">{card.stroke_count} goresan</span>
            </div>
            <KanjiStroke character={card.character} size={260} />
            <div className="kanji-hero-info">
              <div><small>音</small><b>{card.onyomi || "—"}</b></div>
              <div><small>訓</small><b>{card.kunyomi || "—"}</b></div>
              <div><small>意味</small><b>{card.meaning}</b></div>
            </div>
          </div>
          <div className="kanji-examples" data-testid="kanji-examples">
            <div className="content-label">CONTOH ( 4 kata + arti )</div>
            <ul className="kanji-example-list">
              {(card.jukugo || []).slice(0, 4).map((j, i) => (
                <li key={i} data-testid={`kanji-example-${i}`}>
                  <Ruby segments={j.segments && j.segments.length ? j.segments : [{ text: j.word, reading: j.kana || null }]} />
                  <small className="hira">{j.kana}</small>
                  <span>{j.meaning}</span>
                </li>
              ))}
              {(card.jukugo || []).length < 4 && Array.from({ length: 4 - (card.jukugo || []).length }).map((_, i) => (
                <li key={`empty-${i}`} className="muted small placeholder">Belum ada contoh · minta admin melengkapi</li>
              ))}
            </ul>
          </div>
          <div className="flashcard-nav">
            <span className="muted">Kartu {idx + 1} dari {cards.length}</span>
            <div>
              <button className="tiny-btn" onClick={() => setIdx((idx - 1 + cards.length) % cards.length)} data-testid="kanji-prev">← Sebelum</button>
              <button className="tiny-btn accent" onClick={() => setIdx((idx + 1) % cards.length)} data-testid="kanji-next">Berikutnya →</button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
