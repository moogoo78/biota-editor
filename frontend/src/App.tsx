import { Navigate, Route, Routes } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "./auth";
import TopBar from "./components/TopBar";
import Login from "./pages/Login";
import Publications from "./pages/Publications";
import Editor from "./pages/Editor";

export default function App() {
  const { user, ready } = useAuth();
  const { t } = useTranslation();
  if (!ready) return <div className="center muted">{t("common.loading")}</div>;
  if (!user) return <Login />;
  return (
    <div className="app">
      <TopBar />
      <Routes>
        <Route path="/" element={<Publications />} />
        <Route path="/p/:pubId" element={<Editor />} />
        <Route path="/p/:pubId/i/:itemId" element={<Editor />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}
