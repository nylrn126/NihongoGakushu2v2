import React from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import "@/App.css";
import "@/app-extras.css";
import { AuthProvider, useAuth } from "@/lib/auth";
import Header from "@/components/Header";
import Home from "@/pages/Home";
import AuthPage from "@/pages/AuthPage";
import ChapterDetail from "@/pages/ChapterDetail";
import Dashboard from "@/pages/Dashboard";
import Admin from "@/pages/Admin";
import AdminChapter from "@/pages/AdminChapter";

function Protected({ children, adminOnly = false }) {
  const { user, checking } = useAuth();
  if (checking) return <div className="loading" data-testid="app-loading">Memuat Gakushu…</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (adminOnly && user.role !== "admin") return <Navigate to="/dashboard" replace />;
  return children;
}

function Shell() {
  const { checking } = useAuth();
  if (checking) return <div className="loading" data-testid="app-loading">Memuat Gakushu…</div>;
  return (
    <BrowserRouter>
      <Header />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<AuthPage mode="login" />} />
        <Route path="/register" element={<AuthPage mode="register" />} />
        <Route path="/chapters/:number" element={<ChapterDetail />} />
        <Route path="/dashboard" element={<Protected><Dashboard /></Protected>} />
        <Route path="/admin" element={<Protected adminOnly><Admin /></Protected>} />
        <Route path="/admin/chapters/:number" element={<Protected adminOnly><AdminChapter /></Protected>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <footer className="footer">学習 · Sedikit demi sedikit setiap hari</footer>
    </BrowserRouter>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Shell />
    </AuthProvider>
  );
}
