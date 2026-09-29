import React, { useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "@/lib/auth";

const LINKS = [
  { to: "/", label: "Beranda", end: true },
  { to: "/bab", label: "Bab" },
  { to: "/quiz", label: "Quiz" },
  { to: "/kanji", label: "Kanji" },
  { to: "/kartu", label: "Kartu" },
  { to: "/progres", label: "Progres", auth: true },
];

export default function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const close = () => setOpen(false);
  const onLogout = async () => { close(); await logout(); navigate("/"); };
  const displayName = user?.name || user?.email;

  return (
    <header className="topbar">
      <Link className="brand" to="/" data-testid="brand-home" onClick={close}>
        <span className="brand-mark">学</span>
        <span><b>Gakushu</b><small>Nihongo 2</small></span>
      </Link>
      <button className="hamburger" aria-label="Menu" onClick={() => setOpen(!open)} data-testid="mobile-menu-toggle">
        <span/><span/><span/>
      </button>
      <nav className={`topnav ${open ? "open" : ""}`} data-testid="main-navigation">
        {LINKS.filter((l) => !l.auth || user).map((l) => (
          <NavLink key={l.to} to={l.to} end={l.end} onClick={close}
                   className={({ isActive }) => `topnav-link ${isActive ? "active" : ""}`}
                   data-testid={`nav-${l.label.toLowerCase()}`}>
            {l.label}
          </NavLink>
        ))}
        {user?.role === "admin" && (
          <NavLink to="/admin" onClick={close}
                   className={({ isActive }) => `topnav-link admin ${isActive ? "active" : ""}`}
                   data-testid="nav-admin">Admin</NavLink>
        )}
      </nav>
      <div className="top-actions">
        {user ? (
          <>
            <span className="avatar hide-sm" data-testid="user-avatar">{displayName?.slice(0, 1).toUpperCase()}</span>
            <span className="user-name hide-sm">{displayName}</span>
            <button className="icon-btn" onClick={onLogout} data-testid="logout-button" aria-label="Keluar">↩</button>
          </>
        ) : (
          <Link className="outline-button small" to="/login" data-testid="login-nav">Masuk</Link>
        )}
      </div>
    </header>
  );
}
