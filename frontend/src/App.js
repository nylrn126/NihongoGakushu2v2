import React from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import "@/App.css";
import "@/app-extras.css";
import "@/app-v2.css";
import { AuthProvider, useAuth } from "@/lib/auth";
import Header from "@/components/Header";
import Beranda from "@/pages/Beranda";
import BabList from "@/pages/BabList";
import ChapterDetail from "@/pages/ChapterDetail";
import QuizPage from "@/pages/QuizPage";
import KanjiPage from "@/pages/KanjiPage";
import KartuPage from "@/pages/KartuPage";
import Progres from "@/pages/Progres";
import AuthPage from "@/pages/AuthPage";
import Admin from "@/pages/Admin";
import AdminChapter from "@/pages/AdminChapter";

function Protected({ children, adminOnly = false }) {
  const { user, checking } = useAuth();
  if (checking) return <div className="loading" data-testid="app-loading">Memuat Gakushu…</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (adminOnly && user.role !== "admin") return <Navigate to="/" replace />;
  return children;
}

function Shell() {
  const { checking } = useAuth();
  if (checking) return <div className="loading" data-testid="app-loading">Memuat Gakushu…</div>;
  return (
    <BrowserRouter>
      <Header />
      <Routes>
        <Route path="/" element={<Beranda />} />
        <Route path="/bab" element={<BabList />} />
        <Route path="/bab/:number" element={<ChapterDetail />} />
        <Route path="/quiz" element={<QuizPage />} />
        <Route path="/kanji" element={<KanjiPage />} />
        <Route path="/kartu" element={<KartuPage />} />
        <Route path="/progres" element={<Protected><Progres /></Protected>} />
        <Route path="/login" element={<AuthPage mode="login" />} />
        <Route path="/register" element={<AuthPage mode="register" />} />
        <Route path="/admin" element={<Protected adminOnly><Admin /></Protected>} />
        <Route path="/admin/chapters/:number" element={<Protected adminOnly><AdminChapter /></Protected>} />
        {/* Legacy redirects */}
        <Route path="/chapters/:number" element={<Navigate to={window.location.pathname.replace('/chapters/', '/bab/')} replace />} />
        <Route path="/dashboard" element={<Navigate to="/progres" replace />} />
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
