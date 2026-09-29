import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, errorText } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function Progres() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [showChange, setShowChange] = useState(user?.must_change_password);

  useEffect(() => {
    api.get("/progress").then((r) => setData(r.data)).catch((e) => setError(errorText(e)));
  }, []);

  const percent = data ? Math.round((data.completed / Math.max(data.total_chapters || 1, 1)) * 100) : 0;
  return (
    <main className="page progres-page">
      <section className="page-head">
        <div>
          <div className="eyebrow">DASBOR PROGRES</div>
          <h1>Halo, {user.name || user.email}.</h1>
          <p className="muted">Sedikit tiap hari, dan Bahasa Jepangmu terus tumbuh.</p>
        </div>
      </section>

      {error && <div className="error">{error}</div>}
      {showChange && <ChangePassword onDone={() => setShowChange(false)} />}

      <div className="stat-tiles">
        <div className="stat-tile" data-testid="progres-sessions">
          <div className="stat-icon vermilion"><i className="mi mi-target" /></div>
          <strong>{data?.total_sessions || 0}</strong>
          <small>Sesi kuis</small>
        </div>
        <div className="stat-tile" data-testid="progres-average">
          <div className="stat-icon"><i className="mi mi-trend" /></div>
          <strong>{data?.average_score || 0}%</strong>
          <small>Rata-rata</small>
        </div>
        <div className="stat-tile" data-testid="progres-best">
          <div className="stat-icon rose"><i className="mi mi-crown" /></div>
          <strong>{data?.best_score || 0}%</strong>
          <small>Skor terbaik</small>
        </div>
        <div className="stat-tile" data-testid="progres-streak">
          <div className="stat-icon amber"><i className="mi mi-flame" /></div>
          <strong>{data?.streak || 0}</strong>
          <small>Streak hari</small>
        </div>
      </div>

      <section className="progres-band" data-testid="progres-band">
        <h3>Bab selesai</h3>
        <div className="progres-bar">
          <span style={{ width: `${percent}%` }} />
        </div>
        <div className="progres-band-meta">
          <span>{data?.completed || 0} dari {data?.total_chapters || 0} bab</span>
          <b>{percent}%</b>
        </div>
      </section>

      <section className="stats-section">
        <h2 className="stats-title">Riwayat skor terakhir</h2>
        <div className="score-history-list">
          {(data?.attempts || []).slice(0, 8).map((a) => (
            <div className="score-row" key={a.id} data-testid={`score-${a.id}`}>
              <b>{a.chapter_number ? `Bab ${a.chapter_number}` : "Cakupan"}</b>
              <div className="score-bar-wrap"><span className="score-bar" style={{ width: `${a.score}%` }} /></div>
              <span>{a.score}%</span>
            </div>
          ))}
          {!data?.attempts?.length && <div className="empty-state">Belum ada percobaan.</div>}
        </div>
      </section>

      <section className="stats-section">
        <div className="section-heading">
          <h2 className="stats-title">Kanji paling sering salah</h2>
          <Link to="/kartu" className="tiny-btn accent">Latih kartu →</Link>
        </div>
        <WeakSummary />
      </section>
    </main>
  );
}

function WeakSummary() {
  const [cards, setCards] = useState(null);
  useEffect(() => { api.get("/library/weak-items?limit=6").then((r) => setCards(r.data.cards)).catch(() => setCards([])); }, []);
  if (cards === null) return <div className="empty-state">Memuat…</div>;
  const kanji = cards.filter((c) => c.kind === "kanji");
  if (!kanji.length) return <div className="empty-state" data-testid="weak-empty">Belum ada — kerjakan kuis kanji dulu.</div>;
  return (
    <div className="weak-grid" data-testid="weak-grid">
      {kanji.slice(0, 6).map((c) => (
        <div className="weak-card" key={c.id}>
          <div className="weak-face">{c.front}</div>
          <div>
            <b>{c.back}</b>
            <small>{c.extra}</small>
          </div>
          <span className="wrong-count">salah {c.wrong_count}×</span>
        </div>
      ))}
    </div>
  );
}

function ChangePassword({ onDone }) {
  const [form, setForm] = useState({ current_password: "", new_password: "" });
  const [error, setError] = useState("");
  const submit = async (e) => {
    e.preventDefault();
    try { await api.post("/auth/change-password", form); onDone(); }
    catch (x) { setError(errorText(x)); }
  };
  return (
    <div className="change-box" data-testid="change-password-panel">
      <b>Ganti password kamu</b>
      <span>Password sementara harus diganti sebelum melanjutkan.</span>
      <form onSubmit={submit}>
        <input data-testid="current-password-input" type="password" required placeholder="Password saat ini"
               value={form.current_password} onChange={(e) => setForm({ ...form, current_password: e.target.value })} />
        <input data-testid="new-password-input" type="password" required placeholder="Password baru"
               value={form.new_password} onChange={(e) => setForm({ ...form, new_password: e.target.value })} />
        <button className="primary-button" data-testid="change-password-submit">Simpan</button>
      </form>
      {error && <div className="error">{error}</div>}
    </div>
  );
}
