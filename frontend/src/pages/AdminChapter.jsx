import React, { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, errorText } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Ruby } from "@/components/Ruby";
import FuriganaSegmentEditor from "@/components/FuriganaSegmentEditor";

const TABS = [
  { id: "bunpo", label: "Bunpou" },
  { id: "kotoba", label: "Kotoba" },
  { id: "kanji", label: "Kanji" },
  { id: "kaiwa", label: "Kaiwa" },
  { id: "quiz_bunpo", label: "Quiz PG" },
  { id: "quiz_susun", label: "Quiz Susun" },
];

export default function AdminChapter() {
  const { user } = useAuth();
  const { number } = useParams();
  const navigate = useNavigate();
  const [chapter, setChapter] = useState(null);
  const [tab, setTab] = useState("bunpo");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [saving, setSaving] = useState(false);
  const [busy, setBusy] = useState(null);

  const load = () => api.get(`/admin/chapters/${number}`).then((r) => setChapter(r.data)).catch((e) => setError(errorText(e)));
  useEffect(() => { load(); }, [number]);

  if (!user || user.role !== "admin") return <main className="loading"><div className="error">Halaman khusus admin.</div></main>;
  if (error) return <main className="loading"><div className="error" data-testid="admin-detail-error">{error}</div></main>;
  if (!chapter) return <main className="loading" data-testid="admin-detail-loading">Memuat bab…</main>;

  const updateMeta = async (patch) => {
    setSaving(true);
    setNotice("");
    try {
      const r = await api.put(`/admin/chapters/${number}`, patch);
      setChapter(r.data);
      setNotice("Perubahan tersimpan");
    } catch (e) { setError(errorText(e)); }
    finally { setSaving(false); }
  };

  const updateContentField = async (field, value) => {
    await updateMeta({ content: { [field]: value } });
  };

  const doAction = async (label, fn) => {
    setBusy(label);
    setNotice("");
    try {
      const r = await fn();
      setNotice(r?.data?.message || "Berhasil");
      await load();
    } catch (e) { setError(errorText(e)); }
    finally { setBusy(null); }
  };

  const content = chapter.content || {};

  return (
    <main className="page admin-page">
      <Link to="/admin" className="back-link" data-testid="back-to-admin">← Kembali ke daftar</Link>
      <section className="admin-header">
        <div>
          <div className="eyebrow">EDITOR BAB {chapter.number} · {chapter.book_label}</div>
          <input
            className="admin-title-input"
            value={chapter.title}
            onChange={(e) => setChapter({ ...chapter, title: e.target.value })}
            onBlur={(e) => e.target.value !== chapter.title && updateMeta({ title: e.target.value })}
            data-testid="admin-title-input"
          />
          <input
            className="admin-subtitle-input"
            value={chapter.title_translation}
            onChange={(e) => setChapter({ ...chapter, title_translation: e.target.value })}
            onBlur={(e) => updateMeta({ title_translation: e.target.value })}
            data-testid="admin-subtitle-input"
          />
        </div>
        <div className="admin-header-actions">
          <span className={`status-pill ${chapter.published ? "pub" : "unpub"}`}>
            {chapter.published ? "Terbit" : "Draft"}
          </span>
          <button className="tiny-btn" disabled={busy === "publish"}
                  onClick={() => doAction("publish", () => api.post(`/admin/chapters/${number}/publish`))}
                  data-testid="admin-detail-publish">
            {chapter.published ? "Sembunyikan" : "Terbitkan"}
          </button>
          {(content.quiz_bunpo || []).length < 15 && (
            <button className="tiny-btn accent" disabled={busy === "pad"}
                    onClick={() => doAction("pad", () => api.post(`/admin/chapters/${number}/pad-quiz`))}
                    data-testid="admin-detail-pad">
              {busy === "pad" ? "AI generate…" : "Pad Quiz → 15"}
            </button>
          )}
          <button className="tiny-btn" disabled={busy === "reset"}
                  onClick={() => doAction("reset", () => api.post(`/admin/chapters/${number}/reset`))}
                  data-testid="admin-detail-reset">
            Reset dari sumber
          </button>
        </div>
      </section>

      {saving && <div className="notice" data-testid="admin-saving">Menyimpan…</div>}
      {notice && <div className="notice" data-testid="admin-detail-notice">{notice}</div>}

      <div className="tab-bar admin-tabs">
        {TABS.map((t) => {
          const count = t.id === "kaiwa" ? (content.kaiwa?.dialog?.length || 0) : (content[t.id]?.length || 0);
          return (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`tab-btn ${tab === t.id ? "active" : ""}`}
              data-testid={`admin-tab-${t.id}`}
            >
              <b>{t.label}</b><small>{count} entri</small>
            </button>
          );
        })}
      </div>

      <div className="tab-panel">
        {tab === "bunpo" && <BunpoEditor items={content.bunpo || []} onSave={(v) => updateContentField("bunpo", v)} />}
        {tab === "kotoba" && <KotobaEditor items={content.kotoba || []} onSave={(v) => updateContentField("kotoba", v)} />}
        {tab === "kanji" && <KanjiEditor items={content.kanji || []} onSave={(v) => updateContentField("kanji", v)} />}
        {tab === "kaiwa" && <KaiwaEditor data={content.kaiwa} onSave={(v) => updateContentField("kaiwa", v)} />}
        {tab === "quiz_bunpo" && <QuizBunpoEditor items={content.quiz_bunpo || []} onSave={(v) => updateContentField("quiz_bunpo", v)} />}
        {tab === "quiz_susun" && <QuizSusunEditor items={content.quiz_susun || []} onSave={(v) => updateContentField("quiz_susun", v)} />}
      </div>
    </main>
  );
}

// ---------------- Editors ----------------

function EditorFrame({ title, count, onAdd, onSave, dirty, children }) {
  return (
    <div className="editor-frame">
      <div className="editor-frame-head">
        <b>{title}</b>
        <span className="muted">{count} entri</span>
        <div className="ef-actions">
          {onAdd && <button className="tiny-btn" onClick={onAdd} data-testid={`editor-add-${title}`}>+ Tambah</button>}
          <button className="tiny-btn accent" disabled={!dirty} onClick={onSave} data-testid={`editor-save-${title}`}>Simpan {title}</button>
        </div>
      </div>
      {children}
    </div>
  );
}

function useDraft(items) {
  const [draft, setDraft] = useState(items);
  useEffect(() => { setDraft(items); }, [items]);
  const dirty = JSON.stringify(draft) !== JSON.stringify(items);
  return [draft, setDraft, dirty];
}

function BunpoEditor({ items, onSave }) {
  const [draft, setDraft, dirty] = useDraft(items);
  const update = (i, patch) => setDraft(draft.map((d, idx) => idx === i ? { ...d, ...patch } : d));
  const remove = (i) => setDraft(draft.filter((_, idx) => idx !== i));
  const add = () => setDraft([...draft, { id: `new-${Date.now()}`, judul: "Pola baru", rumus: "", keterangan: [], penjelasan: "", contoh: [] }]);
  return (
    <EditorFrame title="Bunpou" count={draft.length} onAdd={add} onSave={() => onSave(draft)} dirty={dirty}>
      {draft.map((b, i) => (
        <div className="editor-row" key={b.id || i} data-testid={`edit-bunpo-${i}`}>
          <input className="ef-input" value={b.judul} onChange={(e) => update(i, { judul: e.target.value })} placeholder="Judul pola" />
          <input className="ef-input" value={b.rumus} onChange={(e) => update(i, { rumus: e.target.value })} placeholder="Rumus" />
          <textarea className="ef-input" rows={2} value={b.penjelasan} onChange={(e) => update(i, { penjelasan: e.target.value })} placeholder="Penjelasan Bahasa Indonesia" />
          <button className="tiny-btn danger" onClick={() => remove(i)} data-testid={`edit-bunpo-remove-${i}`}>Hapus</button>
        </div>
      ))}
    </EditorFrame>
  );
}

function KotobaEditor({ items, onSave }) {
  const [draft, setDraft, dirty] = useDraft(items);
  const update = (i, patch) => setDraft(draft.map((d, idx) => idx === i ? { ...d, ...patch } : d));
  const remove = (i) => setDraft(draft.filter((_, idx) => idx !== i));
  const add = () => setDraft([...draft, { id: `new-${Date.now()}`, word: "", kana: "", romaji: "", meaning: "", word_type: "Kata Benda", segments: [{ text: "", reading: null }], example: { segments: [], translation: "" } }]);
  return (
    <EditorFrame title="Kotoba" count={draft.length} onAdd={add} onSave={() => onSave(draft)} dirty={dirty}>
      {draft.map((k, i) => (
        <div className="editor-row" key={k.id || i} data-testid={`edit-kotoba-${i}`}>
          <div className="editor-row inline">
            <input className="ef-input" value={k.word} onChange={(e) => update(i, { word: e.target.value })} placeholder="Kata (kanji/kana)" />
            <input className="ef-input" value={k.kana} onChange={(e) => update(i, { kana: e.target.value })} placeholder="Kana" />
            <input className="ef-input" value={k.romaji} onChange={(e) => update(i, { romaji: e.target.value })} placeholder="Romaji" />
            <input className="ef-input" value={k.meaning} onChange={(e) => update(i, { meaning: e.target.value })} placeholder="Arti" />
            <input className="ef-input" value={k.word_type} onChange={(e) => update(i, { word_type: e.target.value })} placeholder="Jenis" />
            <button className="tiny-btn danger" onClick={() => remove(i)}>Hapus</button>
          </div>
          <details>
            <summary className="muted small" style={{ cursor: "pointer", padding: "6px 0" }}>Edit furigana (segments)</summary>
            <FuriganaSegmentEditor
              value={k.segments || []}
              onChange={(v) => update(i, { segments: v })}
              testid={`kotoba-furi-${i}`}
            />
          </details>
        </div>
      ))}
    </EditorFrame>
  );
}

function KanjiEditor({ items, onSave }) {
  const [draft, setDraft, dirty] = useDraft(items);
  const update = (i, patch) => setDraft(draft.map((d, idx) => idx === i ? { ...d, ...patch } : d));
  const remove = (i) => setDraft(draft.filter((_, idx) => idx !== i));
  const add = () => setDraft([...draft, { id: `new-${Date.now()}`, character: "", onyomi: "", kunyomi: "", meaning: "", stroke_count: 1, jukugo: [] }]);
  return (
    <EditorFrame title="Kanji" count={draft.length} onAdd={add} onSave={() => onSave(draft)} dirty={dirty}>
      {draft.map((k, i) => (
        <div className="editor-row inline" key={k.id || i} data-testid={`edit-kanji-${i}`}>
          <input className="ef-input ja-title" style={{ width: 70 }} value={k.character} onChange={(e) => update(i, { character: e.target.value })} placeholder="漢" />
          <input className="ef-input" value={k.onyomi} onChange={(e) => update(i, { onyomi: e.target.value })} placeholder="Onyomi" />
          <input className="ef-input" value={k.kunyomi} onChange={(e) => update(i, { kunyomi: e.target.value })} placeholder="Kunyomi" />
          <input className="ef-input" value={k.meaning} onChange={(e) => update(i, { meaning: e.target.value })} placeholder="Arti" />
          <input className="ef-input" type="number" style={{ width: 80 }} value={k.stroke_count} onChange={(e) => update(i, { stroke_count: Number(e.target.value) })} placeholder="Coretan" />
          <button className="tiny-btn danger" onClick={() => remove(i)}>Hapus</button>
        </div>
      ))}
    </EditorFrame>
  );
}

function KaiwaEditor({ data, onSave }) {
  const initial = data || { judul: "", latar: "", dialog: [] };
  const [draft, setDraft] = useState(initial);
  useEffect(() => { setDraft(data || { judul: "", latar: "", dialog: [] }); }, [data]);
  const dirty = JSON.stringify(draft) !== JSON.stringify(initial);
  const upd = (patch) => setDraft({ ...draft, ...patch });
  const updLine = (i, patch) => setDraft({ ...draft, dialog: draft.dialog.map((l, idx) => idx === i ? { ...l, ...patch } : l) });
  const addLine = () => setDraft({ ...draft, dialog: [...(draft.dialog || []), { speaker: "", speaker_reading: "", segments: [{ text: "", reading: null }], translation: "" }] });
  const removeLine = (i) => setDraft({ ...draft, dialog: draft.dialog.filter((_, idx) => idx !== i) });
  return (
    <EditorFrame title="Kaiwa" count={(draft.dialog || []).length} onAdd={addLine} onSave={() => onSave(draft)} dirty={dirty}>
      <input className="ef-input" value={draft.judul || ""} onChange={(e) => upd({ judul: e.target.value })} placeholder="Judul percakapan" />
      <input className="ef-input" value={draft.latar || ""} onChange={(e) => upd({ latar: e.target.value })} placeholder="Latar (setting)" />
      {(draft.dialog || []).map((line, i) => (
        <div className="editor-row inline" key={i} data-testid={`edit-kaiwa-${i}`}>
          <input className="ef-input" value={line.speaker} onChange={(e) => updLine(i, { speaker: e.target.value })} placeholder="Pembicara" style={{ width: 100 }} />
          <input className="ef-input" value={line.speaker_reading} onChange={(e) => updLine(i, { speaker_reading: e.target.value })} placeholder="Bacaan" style={{ width: 100 }} />
          <input className="ef-input" value={line.translation} onChange={(e) => updLine(i, { translation: e.target.value })} placeholder="Terjemahan Bahasa Indonesia" />
          <button className="tiny-btn danger" onClick={() => removeLine(i)}>Hapus</button>
        </div>
      ))}
    </EditorFrame>
  );
}

function QuizBunpoEditor({ items, onSave }) {
  const [draft, setDraft, dirty] = useDraft(items);
  const update = (i, patch) => setDraft(draft.map((d, idx) => idx === i ? { ...d, ...patch } : d));
  const updateOpt = (i, oi, v) => update(i, { options: draft[i].options.map((o, k) => k === oi ? v : o) });
  const remove = (i) => setDraft(draft.filter((_, idx) => idx !== i));
  const add = () => setDraft([...draft, { id: `new-${Date.now()}`, question_text: "", options: ["", "", "", ""], answer_index: 0, rumus: "", explanation: "" }]);
  return (
    <EditorFrame title="Quiz PG" count={draft.length} onAdd={add} onSave={() => onSave(draft)} dirty={dirty}>
      {draft.length < 15 && <p className="muted small">Quiz saat ini {draft.length} soal. Idealnya ≥ 15 (klik "Pad Quiz → 15" di atas untuk auto-generate).</p>}
      {draft.map((q, i) => (
        <div className="editor-row" key={q.id || i} data-testid={`edit-quiz-bunpo-${i}`}>
          <textarea className="ef-input" rows={2} value={q.question_text || ""} onChange={(e) => update(i, { question_text: e.target.value })} placeholder="Soal (pakai ＿＿ untuk rumpang)" />
          {(q.options || []).map((opt, oi) => (
            <div className="option-row" key={oi}>
              <input type="radio" checked={q.answer_index === oi} onChange={() => update(i, { answer_index: oi })} />
              <input className="ef-input" value={opt} onChange={(e) => updateOpt(i, oi, e.target.value)} placeholder={`Pilihan ${oi + 1}`} />
            </div>
          ))}
          <textarea className="ef-input" rows={2} value={q.explanation || ""} onChange={(e) => update(i, { explanation: e.target.value })} placeholder="Penjelasan" />
          {q.generated && <span className="badge">AI-generated</span>}
          <button className="tiny-btn danger" onClick={() => remove(i)}>Hapus soal</button>
        </div>
      ))}
    </EditorFrame>
  );
}

function QuizSusunEditor({ items, onSave }) {
  const [draft, setDraft, dirty] = useDraft(items);
  const remove = (i) => setDraft(draft.filter((_, idx) => idx !== i));
  return (
    <EditorFrame title="Quiz Susun" count={draft.length} onSave={() => onSave(draft)} dirty={dirty}>
      <p className="muted small">Untuk editing detail soal susun kata, gunakan reset dari sumber. Di sini tersedia hapus per soal.</p>
      {draft.map((q, i) => (
        <div className="editor-row inline" key={q.id || i} data-testid={`edit-quiz-susun-${i}`}>
          <span className="muted">#{i + 1}</span>
          <span>{q.translation}</span>
          <span className="ja-title">{(q.correct_order || []).map((s) => s.text).join("")}</span>
          <button className="tiny-btn danger" onClick={() => remove(i)}>Hapus</button>
        </div>
      ))}
    </EditorFrame>
  );
}
