import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/lib/auth";

export default function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const onLogout = async () => { await logout(); navigate("/"); };
  return (
    <header className="topbar">
      <Link className="brand" to="/" data-testid="brand-home">
        <span className="brand-mark">学</span>
        <span><b>Gakushu</b><small>Nihongo 2</small></span>
      </Link>
      <nav data-testid="main-navigation">
        <Link to="/" data-testid="chapters-nav">Bab</Link>
        {user && <Link to="/dashboard" data-testid="dashboard-nav">Progres saya</Link>}
        {user?.role === "admin" && <Link to="/admin" data-testid="admin-nav">Admin</Link>}
      </nav>
      <div className="top-actions">
        {user ? (
          <>
            <span className="avatar" data-testid="user-avatar">{(user.name || user.email)?.slice(0, 1).toUpperCase()}</span>
            <button className="text-button" onClick={onLogout} data-testid="logout-button">Keluar</button>
          </>
        ) : (
          <Link className="outline-button" to="/login" data-testid="login-nav">Masuk</Link>
        )}
      </div>
    </header>
  );
}
