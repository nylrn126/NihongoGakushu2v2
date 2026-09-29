import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, errorText } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function Dashboard() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [showChange, setShowChange] = useState(user?.must_change_password);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/progress").then((r) => setData(r.data)).catch((e) => setError(errorText(e)));
  }, []);

  const percent = data ? Math.round((data.completed / Math.max(data.total_chapters || 1, 1)) * 100) : 0;
  const lastAttempt = data?.attempts?.[0];

  return (
    <main className="page dashboard">
      <section className="dashboard-head">
        <div>
          <div className="eyebrow">PROGRES BELAJAR</div>
          <h1>おかえり, {user.name || user.email}.</h1>
          <p className="muted">Sedikit tiap hari, dan bahasa Jepangmu terus tumbuh.</p>
        </div>
        <div className="streak" data-testid="streak-summary">
          <strong>{percent}%</strong>
          <span>bab selesai</span>
        </div>
      </section>

      {error && <div className="error" data-testid="dashboard-error">{error}</div>}
      {showChange && <ChangePassword onDone={() => setShowChange(false)} />}

      <section className="stats-row">
        <div className="stat" data-testid="progress-summary">
          <span>Bab selesai</span>
          <b>{data?.completed || 0}<small> / {data?.total_chapters || 0}</small></b>
        </div>
        <div className="stat">
          <span>Total percobaan quiz</span>
          <b>{data?.attempts?.length || 0}</b>
          <small>3 percobaan terakhir tampil di bawah</small>
        </div>
        <div className="stat">
          <span>Rata-rata skor</span>
          <b>{data?.attempts?.length ? Math.round(data.attempts.reduce((s, a) => s + a.score, 0) / data.attempts.length) : 0}%</b>
          <small>Dari semua percobaan</small>
        </div>
      </section>

      {lastAttempt && (
        <section className="continue-band">
          <div>
            <div className="eyebrow">TERAKHIR DIKERJAKAN</div>
            <h2>Bab {lastAttempt.chapter_number}</h2>
            <p>Skor {lastAttempt.score}% · {new Date(lastAttempt.created_at).toLocaleString("id-ID")}</p>
          </div>
          <Link to={`/chapters/${lastAttempt.chapter_number}`} className="primary-button" data-testid="continue-chapter-button">
            Buka bab <span>→</span>
          </Link>
        </section>
      )}

      <section className="activity">
        <div className="section-heading">
          <div>
            <div className="eyebrow">RIWAYAT</div>
            <h2>Perjalananmu</h2>
          </div>
        </div>
        {data?.attempts?.length ? data.attempts.map((item) => (
          <div className="activity-row" key={item.id} data-testid={`activity-${item.id}`}>
            <span className="activity-dot">✓</span>
            <span>Quiz bab {item.chapter_number} ({item.quiz_kind})</span>
            <b>{item.score}%</b>
            <small>{new Date(item.created_at).toLocaleDateString("id-ID")}</small>
          </div>
        )) : (
          <div className="empty-state" data-testid="activity-empty">
            Selesaikan quiz pertamamu dan riwayatnya akan muncul di sini.
          </div>
        )}
      </section>
    </main>
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
      {error && <div className="error" data-testid="change-password-error">{error}</div>}
    </div>
  );
}
