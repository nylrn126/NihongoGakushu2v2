import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, errorText } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function AuthPage({ mode }) {
  const { setUser } = useAuth();
  const navigate = useNavigate();
  const register = mode === "register";
  const [form, setForm] = useState({ email: "", password: "", name: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [temporary, setTemporary] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const r = await api.post(`/auth/${register ? "register" : "login"}`, form);
      setUser(r.data);
      navigate(r.data.role === "admin" ? "/admin" : "/dashboard");
    } catch (x) {
      setError(errorText(x));
    } finally {
      setBusy(false);
    }
  };

  const reset = async () => {
    if (!form.email) return setError("Isi email dulu.");
    try {
      const r = await api.post("/auth/forgot-password", { email: form.email });
      setTemporary(r.data.temporary_password);
    } catch (x) {
      setError(errorText(x));
    }
  };

  return (
    <main className="auth-page">
      <div className="auth-art">
        <span className="large-kanji">学</span>
        <p>Sedikit tiap hari.<br/><em>Datang lagi besok.</em></p>
      </div>
      <section className="auth-panel">
        <div className="eyebrow">{register ? "Mulai berlatih" : "Selamat datang kembali"}</div>
        <h1>{register ? "Jadikan Jepang bagian dari harimu." : "Lanjutkan progresmu."}</h1>
        <p className="muted">Materi Minna no Nihongo 1 &amp; 2, kosakata, kanji, dan quiz.</p>
        <form onSubmit={submit} data-testid={`${mode}-form`}>
          {register && (
            <label>Nama
              <input data-testid="register-name-input" value={form.name}
                     onChange={(e) => setForm({ ...form, name: e.target.value })}
                     placeholder="Nama panggilan" />
            </label>
          )}
          <label>Email
            <input data-testid={`${mode}-email-input`} type="email" required
                   value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
                   placeholder="kamu@example.com" />
          </label>
          <label>Password
            <input data-testid={`${mode}-password-input`} type="password" required
                   value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })}
                   placeholder="Minimal 8 karakter" />
          </label>
          {error && <div className="error" data-testid="auth-error">{error}</div>}
          <button className="primary-button wide" disabled={busy} data-testid={`${mode}-submit-button`}>
            {busy ? "Memproses…" : register ? "Buat akun" : "Masuk"}
          </button>
        </form>
        {!register && (
          <button className="quiet-link" onClick={reset} data-testid="forgot-password-button">
            Lupa password?
          </button>
        )}
        {temporary && (
          <div className="temporary-box" data-testid="temporary-password-popup">
            <b>Password sementara</b>
            <strong>{temporary}</strong>
            <span>Pakai untuk masuk, lalu ganti password segera di dashboard.</span>
          </div>
        )}
        <p className="switch-copy">
          {register ? "Sudah punya akun?" : "Baru di Gakushu?"}{" "}
          <Link to={register ? "/login" : "/register"} data-testid="auth-switch-link">
            {register ? "Masuk" : "Buat akun"}
          </Link>
        </p>
      </section>
    </main>
  );
}
