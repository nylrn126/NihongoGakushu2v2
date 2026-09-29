import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api, errorText } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Ruby } from "@/components/Ruby";

const TABS = ["bunpo", "kotoba", "kanji", "kaiwa", "quiz_bunpo", "quiz_susun"];
const TAB_LABEL = {
  bunpo: "Bunpou", kotoba: "Kotoba", kanji: "Kanji",
  kaiwa: "Kaiwa", quiz_bunpo: "Quiz PG", quiz_susun: "Quiz Susun",
};

export default function Admin() {
  const { user } = useAuth();
  if (!user || user.role !== "admin") {
    return <main className="loading"><div className="error" data-testid="admin-forbidden">Halaman ini khusus admin.</div></main>;
  }
  return <AdminList />;
}

function AdminList() {
  const [chapters, setChapters] = useState([]);
  const [busy, setBusy] = useState(null);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const load = () => api.get("/admin/chapters").then((r) => setChapters(r.data)).catch((e) => setError(errorText(e)));
  useEffect(() => { load(); }, []);

  const togglePublish = async (n) => {
    setBusy(`pub-${n}`);
    try {
      await api.post(`/admin/chapters/${n}/publish`);
      await load();
    } catch (e) { setError(errorText(e)); }
    finally { setBusy(null); }
  };

  const padQuiz = async (n) => {
    setBusy(`pad-${n}`);
    setNotice("");
    try {
      const r = await api.post(`/admin/chapters/${n}/pad-quiz`);
      setNotice(`Bab ${n}: ${r.data.message}`);
      await load();
    } catch (e) { setError(errorText(e)); }
    finally { setBusy(null); }
  };

  return (
    <main className="page admin-page">
      <section className="dashboard-head">
        <div>
          <div className="eyebrow">RUANG EDITOR</div>
          <h1>Kelola Materi</h1>
          <p className="muted">Ringkasan semua bab Minna no Nihongo 1 &amp; 2. Klik bab untuk mengedit isi.</p>
        </div>
      </section>
      {notice && <div className="notice" data-testid="admin-notice">{notice}</div>}
      {error && <div className="error" data-testid="admin-error">{error}</div>}
      <div className="admin-table-wrap">
        <table className="admin-table" data-testid="admin-chapters-table">
          <thead>
            <tr>
              <th>Bab</th><th>Buku</th><th>Judul</th>
              <th>Bunpo</th><th>Kotoba</th><th>Kanji</th>
              <th>Quiz PG</th><th>Quiz Susun</th>
              <th>Status</th><th>Aksi</th>
            </tr>
          </thead>
          <tbody>
            {chapters.map((c) => (
              <tr key={c.number} data-testid={`admin-row-${c.number}`}>
                <td><b>{c.number}</b></td>
                <td>{c.book_label}</td>
                <td className="ja-cell">
                  <span className="ja-title">{c.title}</span>
                  <small>{c.title_translation}</small>
                </td>
                <td>{c.counts.bunpo}</td>
                <td>{c.counts.kotoba}</td>
                <td>{c.counts.kanji}</td>
                <td className={c.counts.quiz_bunpo < 15 ? "warn" : "ok"}>{c.counts.quiz_bunpo}</td>
                <td>{c.counts.quiz_susun}</td>
                <td>
                  <span className={`status-pill ${c.published ? "pub" : "unpub"}`}>
                    {c.published ? "Terbit" : "Draft"}
                  </span>
                </td>
                <td className="admin-actions">
                  <button className="tiny-btn" onClick={() => navigate(`/admin/chapters/${c.number}`)} data-testid={`admin-edit-${c.number}`}>Edit</button>
                  <button className="tiny-btn" disabled={busy === `pub-${c.number}`} onClick={() => togglePublish(c.number)} data-testid={`admin-publish-${c.number}`}>
                    {c.published ? "Sembunyikan" : "Terbitkan"}
                  </button>
                  {c.counts.quiz_bunpo < 15 && (
                    <button className="tiny-btn accent" disabled={busy === `pad-${c.number}`} onClick={() => padQuiz(c.number)} data-testid={`admin-pad-${c.number}`}>
                      {busy === `pad-${c.number}` ? "AI…" : `Pad → 15`}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}
