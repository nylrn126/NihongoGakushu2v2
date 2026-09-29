import React, { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api, errorText } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Ruby } from "@/components/Ruby";

const TYPES = [
  { id: "bunpo", label: "Bunpo" },
  { id: "kanji", label: "Kanji" },
  { id: "kotoba", label: "Kotoba" },
  { id: "campuran", label: "Campuran" },
  { id: "susun", label: "Susun Kata" },
];

export default function QuizPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const babParam = params.get("bab");
  const [type, setType] = useState(params.get("type") || "bunpo");
  const [book, setBook] = useState(params.get("book") || "1");
  const [bab, setBab] = useState(babParam || "");
  const [state, setState] = useState("setup"); // setup | play | result
  const [session, setSession] = useState(null);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const startQuiz = async () => {
    setError(""); setBusy(true); setAnswers({}); setResult(null);
    try {
      const query = new URLSearchParams({ type, limit: "15" });
      if (bab) query.set("bab", bab);
      else if (book) query.set("book", book);
      const r = await api.get(`/library/quiz?${query}`);
      if (!r.data.questions?.length) {
        setError("Tidak ada soal untuk pilihan ini.");
      } else {
        setSession(r.data);
        setState("play");
      }
    } catch (e) { setError(errorText(e)); }
    finally { setBusy(false); }
  };

  const submit = async () => {
    if (!user) { navigate("/login"); return; }
    setBusy(true); setError("");
    try {
      const items = session.questions.map((q) => ({ id: q.id, picked: answers[q.id] }));
      const r = await api.post("/library/quiz/attempt", {
        type: session.type, book: bab ? null : Number(book) || null, items,
      });
      setResult(r.data);
      setState("result");
    } catch (e) { setError(errorText(e)); }
    finally { setBusy(false); }
  };

  const restart = () => { setState("setup"); setSession(null); setAnswers({}); setResult(null); };

  return (
    <main className="page quiz-page">
      <section className="page-head">
        <div>
          <div className="eyebrow">LATIHAN INTERAKTIF</div>
          <h1>Quiz</h1>
          <p className="muted">Uji pemahaman lintas bab. Pilih jenis dan cakupan.</p>
        </div>
      </section>

      {state === "setup" && (
        <div className="quiz-setup" data-testid="quiz-setup">
          <div className="setup-block">
            <label>Jenis Quiz</label>
            <div className="pill-tabs pill-tabs-wrap" data-testid="quiz-type-tabs">
              {TYPES.map((t) => (
                <button key={t.id} className={type === t.id ? "active" : ""}
                        onClick={() => setType(t.id)} data-testid={`type-${t.id}`}>
                  {t.label}
                </button>
              ))}
            </div>
          </div>
          <div className="setup-block">
            <label>Cakupan Buku</label>
            <div className="pill-tabs" data-testid="quiz-book-tabs">
              <button className={book === "1" && !bab ? "active" : ""} onClick={() => { setBook("1"); setBab(""); }} data-testid="scope-book-1">Minna 1 (Bab 1–25)</button>
              <button className={book === "2" && !bab ? "active" : ""} onClick={() => { setBook("2"); setBab(""); }} data-testid="scope-book-2">Minna 2 (Bab 26–50)</button>
              <button className={!book && !bab ? "active" : ""} onClick={() => { setBook(""); setBab(""); }} data-testid="scope-all">Semua Bab</button>
            </div>
          </div>
          <div className="setup-block">
            <label>Atau pilih bab tertentu (opsional)</label>
            <input className="ef-input" placeholder="Nomor bab, mis. 26" value={bab}
                   onChange={(e) => setBab(e.target.value.replace(/\D/g, ""))}
                   data-testid="scope-bab-input" />
          </div>
          {error && <div className="error" data-testid="quiz-setup-error">{error}</div>}
          <button className="primary-button wide" disabled={busy} onClick={startQuiz} data-testid="start-quiz-button">
            {busy ? "Menyiapkan…" : "Mulai Quiz"} <span>→</span>
          </button>
        </div>
      )}

      {state === "play" && session && (
        <QuizPlay session={session} answers={answers} setAnswers={setAnswers}
                  onSubmit={submit} busy={busy} error={error} onCancel={restart} />
      )}

      {state === "result" && result && (
        <QuizResult result={result} session={session} onRestart={restart} onRetake={startQuiz} />
      )}
    </main>
  );
}

function QuizPlay({ session, answers, setAnswers, onSubmit, busy, error, onCancel }) {
  return (
    <div className="quiz-panel" data-testid="quiz-play">
      <div className="quiz-meta">
        <span>{typeLabel(session.type)} · {session.questions.length} soal</span>
        <button className="text-button" onClick={onCancel} data-testid="cancel-quiz">Batal</button>
      </div>
      {session.questions.map((q, idx) => (
        <div className="question" key={q.id} data-testid={`quiz-question-${idx}`}>
          <b>
            {idx + 1}.{" "}
            {q.kind === "kanji" && <span className="ja-title" style={{ fontSize: 42, marginRight: 12 }}>{q.stem}</span>}
            {q.kind === "kotoba" && <span className="ja-title" style={{ fontSize: 24, marginRight: 12 }}>{q.stem}</span>}
            {q.kind === "bunpo" && q.stem}
            {q.kind === "susun" && `Susun kalimat untuk: “${q.stem}”`}
          </b>
          {q.hint && <small className="muted"> ({q.hint})</small>}
          {q.chapter_number ? <small className="chip">Bab {q.chapter_number}</small> : null}
          {q.kind !== "susun" ? (
            <div className="options">
              {q.options.map((opt) => (
                <button key={opt} className={answers[q.id] === opt ? "selected" : ""}
                        onClick={() => setAnswers({ ...answers, [q.id]: opt })}
                        data-testid={`quiz-option-${idx}-${opt}`}>
                  {opt}
                </button>
              ))}
            </div>
          ) : (
            <SusunPicker tokens={q.tokens} value={answers[q.id] || []}
                         onChange={(v) => setAnswers({ ...answers, [q.id]: v })} qid={q.id} />
          )}
        </div>
      ))}
      {error && <div className="error">{error}</div>}
      <button className="primary-button wide" disabled={busy} onClick={onSubmit} data-testid="submit-quiz-button">
        {busy ? "Memeriksa…" : "Selesai"} <span>→</span>
      </button>
    </div>
  );
}

function SusunPicker({ tokens, value, onChange, qid }) {
  const remaining = tokens.filter((t, i) => !value.includes(`${t}#${i}`) && !value.includes(t));
  const add = (tok) => onChange([...value, tok]);
  const removeAt = (i) => onChange(value.filter((_, idx) => idx !== i));
  return (
    <div className="susun-picker">
      <div className="susun-selected">
        {value.length ? value.map((t, i) => (
          <button key={i} className="pill" onClick={() => removeAt(i)} data-testid={`susun-selected-${qid}-${i}`}>{t} ×</button>
        )) : <span className="muted">Ketuk kata untuk menyusun…</span>}
      </div>
      <div className="susun-tokens">
        {remaining.map((t, i) => (
          <button key={i} className="pill outline" onClick={() => add(t)} data-testid={`susun-token-${qid}-${i}`}>{t}</button>
        ))}
      </div>
    </div>
  );
}

function QuizResult({ result, session, onRestart, onRetake }) {
  const message = result.score >= 80 ? "すごい! Sempurna sekali." : result.score >= 60 ? "Bagus! Ulangi bagian yang salah." : "Terus latihan — kamu bisa!";
  const questionMap = useMemo(() => Object.fromEntries((session?.questions || []).map((q) => [q.id, q])), [session]);
  return (
    <div className="quiz-result-panel" data-testid="quiz-result">
      <div className="result-hero">
        <strong>{result.score}%</strong>
        <div>
          <b>{result.correct} dari {result.total} benar</b>
          <span>{message}</span>
        </div>
      </div>
      <div className="result-list">
        {result.items.map((it, i) => {
          const q = questionMap[it.id];
          return (
            <div key={it.id} className={`result-row ${it.is_correct ? "ok" : "wrong"}`} data-testid={`result-row-${i}`}>
              <span className="result-idx">{i + 1}</span>
              <div>
                <b>{q?.stem}</b>
                <small>Jawabanmu: <em>{it.picked || "—"}</em> · Benar: <em>{it.correct_value}</em></small>
                {it.explanation && <p className="muted">{it.explanation}</p>}
              </div>
              <span className="result-tag">{it.is_correct ? "✓" : "✗"}</span>
            </div>
          );
        })}
      </div>
      <div className="hero-actions">
        <button className="primary-button" onClick={onRetake} data-testid="quiz-retake">Ulang lagi<span>→</span></button>
        <button className="outline-button" onClick={onRestart} data-testid="quiz-back">Pilih quiz lain</button>
      </div>
    </div>
  );
}

const typeLabel = (t) => ({ bunpo: "Quiz Bunpo", kanji: "Quiz Kanji", kotoba: "Quiz Kotoba", campuran: "Quiz Campuran", susun: "Susun Kata" })[t] || t;
