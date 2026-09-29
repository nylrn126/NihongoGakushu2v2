import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, errorText } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Ruby, plainText } from "@/components/Ruby";

const TABS = [
  { id: "bunpo", label: "Bunpou", subtitle: "Tata bahasa" },
  { id: "kotoba", label: "Kotoba", subtitle: "Kosakata" },
  { id: "kanji", label: "Kanji", subtitle: "Aksara Han" },
  { id: "kaiwa", label: "Kaiwa", subtitle: "Percakapan" },
  { id: "quiz", label: "Quiz", subtitle: "Latihan" },
  { id: "flashcard", label: "Flashcard", subtitle: "Ulang cepat" },
];

export default function ChapterDetail() {
  const { number } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [chapter, setChapter] = useState(null);
  const [error, setError] = useState("");
  const [tab, setTab] = useState("bunpo");

  useEffect(() => {
    setChapter(null);
    api.get(`/chapters/${number}`)
      .then((r) => setChapter(r.data))
      .catch(() => setError("Bab ini belum tersedia."));
  }, [number]);

  if (error) return <main className="loading"><div className="error" data-testid="chapter-error">{error}</div></main>;
  if (!chapter) return <main className="loading" data-testid="chapter-loading">Memuat bab…</main>;
  const content = chapter.content || {};
  const accent = chapter.number % 3 === 0 ? "teal" : chapter.number % 3 === 1 ? "vermilion" : "indigo";

  return (
    <main className="page lesson-page" data-testid={`chapter-page-${chapter.number}`}>
      <Link to="/" className="back-link" data-testid="back-to-chapters">← Semua bab</Link>
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
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`tab-btn ${tab === t.id ? "active" : ""}`}
            data-testid={`tab-${t.id}`}
          >
            <b>{t.label}</b>
            <small>{t.subtitle}</small>
          </button>
        ))}
      </div>

      <div className="tab-panel" data-testid={`tab-panel-${tab}`}>
        {tab === "bunpo" && <BunpoView items={content.bunpo || []} />}
        {tab === "kotoba" && <KotobaView items={content.kotoba || []} />}
        {tab === "kanji" && <KanjiView items={content.kanji || []} />}
        {tab === "kaiwa" && <KaiwaView data={content.kaiwa} />}
        {tab === "quiz" && (
          <QuizView
            number={chapter.number}
            questions={content.quiz_bunpo || []}
            requireLogin={!user}
            onLogin={() => navigate("/login")}
          />
        )}
        {tab === "flashcard" && <FlashcardView kotoba={content.kotoba || []} kanji={content.kanji || []} />}
      </div>
    </main>
  );
}

function BunpoView({ items }) {
  if (!items.length) return <div className="empty-state">Belum ada materi tata bahasa untuk bab ini.</div>;
  return (
    <div className="bunpo-list">
      {items.map((b) => (
        <article className="bunpo-card" key={b.id} data-testid={`bunpo-${b.id}`}>
          <div className="content-label">POLA</div>
          <h3>{b.judul}</h3>
          <div className="rumus">{b.rumus}</div>
          {b.keterangan?.length > 0 && (
            <ul className="keterangan">
              {b.keterangan.map((k, i) => <li key={i}>{k}</li>)}
            </ul>
          )}
          <p className="muted">{b.penjelasan}</p>
          <div className="contoh-block">
            <div className="content-label">CONTOH</div>
            {b.contoh?.map((ex, i) => (
              <div className="contoh-row" key={i}>
                <Ruby segments={ex.segments} />
                <span>{ex.translation}</span>
              </div>
            ))}
          </div>
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

function QuizView({ number, questions, requireLogin, onLogin }) {
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const operationId = useMemo(() => `ch${number}-${Date.now()}`, [number]);

  if (!questions.length) return <div className="empty-state">Belum ada soal untuk bab ini.</div>;

  const submit = async () => {
    if (requireLogin) return onLogin();
    setError("");
    setBusy(true);
    try {
      const r = await api.post(`/chapters/${number}/quiz`, {
        quiz_kind: "bunpo",
        answers,
        operation_id: operationId,
      });
      setResult(r.data);
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="quiz-panel">
      <div className="content-label">LATIHAN GRAMMAR</div>
      <h2>Uji pemahamanmu ({questions.length} soal)</h2>
      {questions.map((q, idx) => {
        const item = result?.items?.find((it) => it.id === q.id);
        return (
          <div className="question" key={q.id} data-testid={`quiz-question-${q.id}`}>
            <b>
              {idx + 1}.{" "}
              {q.question_text ? q.question_text : q.question_segments ? <Ruby segments={q.question_segments} size="sm" /> : "(soal)"}
            </b>
            <div className="options">
              {q.options.map((opt, i) => {
                const picked = answers[q.id] === i;
                const graded = result ? (item?.correct_index === i ? "correct" : picked ? "wrong" : "") : picked ? "selected" : "";
                return (
                  <button
                    key={i}
                    className={graded}
                    disabled={!!result}
                    onClick={() => setAnswers({ ...answers, [q.id]: i })}
                    data-testid={`quiz-option-${q.id}-${i}`}
                  >
                    {opt}
                  </button>
                );
              })}
            </div>
            {item?.explanation && (
              <p className="muted quiz-explain" data-testid={`quiz-explain-${q.id}`}>{item.explanation}</p>
            )}
          </div>
        );
      })}
      {error && <div className="error" data-testid="quiz-error">{error}</div>}
      {result ? (
        <div className="result" data-testid="quiz-result">
          <strong>{result.score}%</strong>
          <span>{result.score >= 80 ? "すごい! Luar biasa." : result.score >= 60 ? "Bagus! Ulangi bagian yang salah." : "Terus latihan — kamu bisa!"}</span>
        </div>
      ) : (
        <button className="primary-button wide" onClick={submit} disabled={busy} data-testid="submit-quiz-button">
          {busy ? "Memeriksa…" : "Selesai"} <span>→</span>
        </button>
      )}
    </div>
  );
}

function FlashcardView({ kotoba, kanji }) {
  const cards = useMemo(() => {
    const list = [
      ...kotoba.map((k) => ({ kind: "kotoba", key: k.id, front: k.word, front_read: k.kana, back: k.meaning, extra: k.romaji })),
      ...kanji.map((k) => ({ kind: "kanji", key: k.id, front: k.character, front_read: `${k.onyomi} / ${k.kunyomi}`, back: k.meaning, extra: `${k.stroke_count} coretan` })),
    ];
    return list;
  }, [kotoba, kanji]);
  const [idx, setIdx] = useState(0);
  const [flipped, setFlipped] = useState(false);
  if (!cards.length) return <div className="empty-state">Belum ada kartu.</div>;
  const card = cards[idx];
  const next = () => { setFlipped(false); setIdx((idx + 1) % cards.length); };
  const prev = () => { setFlipped(false); setIdx((idx - 1 + cards.length) % cards.length); };
  return (
    <div className="flashcard-wrap">
      <div className="flashcard-meta">
        <span>{card.kind === "kotoba" ? "Kosakata" : "Kanji"}</span>
        <span>{idx + 1} / {cards.length}</span>
      </div>
      <button className={`flashcard ${flipped ? "flipped" : ""}`} onClick={() => setFlipped(!flipped)} data-testid={`flashcard-${card.key}`}>
        {flipped ? (
          <div className="fc-back">
            <b>{card.back}</b>
            <small>{card.extra}</small>
          </div>
        ) : (
          <div className="fc-front">
            <strong>{card.front}</strong>
            <small>{card.front_read}</small>
          </div>
        )}
      </button>
      <div className="flashcard-nav">
        <button onClick={prev} data-testid="flashcard-prev">← Sebelumnya</button>
        <button onClick={() => setFlipped(!flipped)} data-testid="flashcard-flip">Balik kartu</button>
        <button onClick={next} data-testid="flashcard-next">Berikutnya →</button>
      </div>
    </div>
  );
}
