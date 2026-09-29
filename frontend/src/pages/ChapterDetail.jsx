import React, { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "@/lib/api";
import { Ruby } from "@/components/Ruby";

const TABS = [
  { id: "bunpo", label: "Bunpou", subtitle: "Tata bahasa" },
  { id: "kotoba", label: "Kotoba", subtitle: "Kosakata" },
  { id: "kanji", label: "Kanji", subtitle: "Aksara" },
  { id: "kaiwa", label: "Kaiwa", subtitle: "Percakapan" },
];

export default function ChapterDetail() {
  const { number } = useParams();
  const [chapter, setChapter] = useState(null);
  const [error, setError] = useState("");
  const [tab, setTab] = useState("bunpo");

  useEffect(() => {
    setChapter(null);
    api.get(`/chapters/${number}`).then((r) => setChapter(r.data)).catch(() => setError("Bab tidak tersedia."));
  }, [number]);

  if (error) return <main className="loading"><div className="error" data-testid="chapter-error">{error}</div></main>;
  if (!chapter) return <main className="loading" data-testid="chapter-loading">Memuat bab…</main>;
  const content = chapter.content || {};
  const accent = chapter.number % 3 === 0 ? "teal" : chapter.number % 3 === 1 ? "vermilion" : "indigo";

  return (
    <main className="page lesson-page" data-testid={`chapter-page-${chapter.number}`}>
      <div className="page-actions">
        <Link to="/bab" className="back-link" data-testid="back-to-chapters">← Semua bab</Link>
        <Link to={`/quiz?bab=${chapter.number}`} className="tiny-btn accent" data-testid="chapter-take-quiz">Ambil quiz bab ini →</Link>
      </div>
      <section className="lesson-hero">
        <div>
          <div className="eyebrow">{chapter.book_label} · BAB {chapter.number}</div>
          <h1 className="ja-title">{chapter.title}</h1>
          <p>{chapter.title_translation}</p>
        </div>
        <div className={`lesson-seal ${accent}`}>{chapter.number}</div>
      </section>

      <div className="tab-bar" data-testid="tab-bar">
        {TABS.map((t) => (
          <button key={t.id} onClick={() => setTab(t.id)}
                  className={`tab-btn ${tab === t.id ? "active" : ""}`}
                  data-testid={`tab-${t.id}`}>
            <b>{t.label}</b><small>{t.subtitle}</small>
          </button>
        ))}
      </div>

      <div className="tab-panel" data-testid={`tab-panel-${tab}`}>
        {tab === "bunpo" && <BunpoView items={content.bunpo || []} />}
        {tab === "kotoba" && <KotobaView items={content.kotoba || []} />}
        {tab === "kanji" && <KanjiView items={content.kanji || []} />}
        {tab === "kaiwa" && <KaiwaView data={content.kaiwa} />}
      </div>
    </main>
  );
}

function BunpoView({ items }) {
  if (!items.length) return <div className="empty-state">Belum ada tata bahasa untuk bab ini.</div>;
  return (
    <div className="bunpo-list">
      {items.map((b) => (
        <article className="bunpo-card" key={b.id} data-testid={`bunpo-${b.id}`}>
          <div className="content-label">POLA</div>
          <h3>{b.judul}</h3>
          <div className="rumus">{b.rumus}</div>
          {b.keterangan?.length > 0 && <ul className="keterangan">{b.keterangan.map((k, i) => <li key={i}>{k}</li>)}</ul>}
          <p className="muted">{b.penjelasan}</p>
          {b.contoh?.length > 0 && (
            <div className="contoh-block">
              <div className="content-label">CONTOH</div>
              {b.contoh.map((ex, i) => (
                <div className="contoh-row" key={i}>
                  <Ruby segments={ex.segments} />
                  <span>{ex.translation}</span>
                </div>
              ))}
            </div>
          )}
        </article>
      ))}
    </div>
  );
}

function KotobaView({ items }) {
  if (!items.length) return <div className="empty-state">Belum ada kosakata.</div>;
  return (
    <div className="kotoba-grid">
      {items.map((k) => (
        <div className="kotoba-card" key={k.id} data-testid={`kotoba-${k.id}`}>
          <div className="kotoba-head">
            <Ruby segments={k.segments} size="lg" />
            <span className="badge">{k.word_type}</span>
          </div>
          <div className="kotoba-meta">
            <span>{k.romaji}</span>
            <b>{k.meaning}</b>
          </div>
          {k.example && (
            <div className="contoh-row">
              <Ruby segments={k.example.segments} size="sm" />
              <span>{k.example.translation}</span>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function KanjiView({ items }) {
  if (!items.length) return <div className="empty-state">Bab ini belum memuat kanji baru.</div>;
  return (
    <div className="kanji-grid">
      {items.map((k) => (
        <div className="kanji-card" key={k.id} data-testid={`kanji-${k.character}`}>
          <div className="kanji-face">{k.character}</div>
          <div className="kanji-body">
            <div className="kanji-row"><small>音</small><b>{k.onyomi || "—"}</b></div>
            <div className="kanji-row"><small>訓</small><b>{k.kunyomi || "—"}</b></div>
            <div className="kanji-row"><small>意味</small><b>{k.meaning}</b></div>
            <div className="kanji-row"><small>画</small><b>{k.stroke_count} coretan</b></div>
            {k.jukugo?.length > 0 && (
              <div className="jukugo-list">
                {k.jukugo.map((j, i) => (
                  <div className="jukugo-row" key={i}>
                    <Ruby segments={j.segments} size="sm" />
                    <span>{j.meaning}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

function KaiwaView({ data }) {
  if (!data || !data.dialog?.length) return <div className="empty-state">Belum ada percakapan.</div>;
  return (
    <div className="kaiwa-panel">
      <h3>{data.judul}</h3>
      <p className="muted">{data.latar}</p>
      <div className="dialog">
        {data.dialog.map((line, i) => (
          <div className="dialog-line" key={i} data-testid={`kaiwa-line-${i}`}>
            <div className="speaker"><b>{line.speaker}</b><small>{line.speaker_reading}</small></div>
            <div className="speech">
              <Ruby segments={line.segments} />
              <span>{line.translation}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
