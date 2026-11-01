import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import type { Notification } from "../api/types";
import { useAuth } from "../auth";

export default function TopBar() {
  const { t, i18n } = useTranslation();
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const qc = useQueryClient();
  const nav = useNavigate();
  const notes = useQuery({
    queryKey: ["notifications"],
    queryFn: () => api.get<Notification[]>("/notifications"),
    refetchInterval: 60_000,
  });
  const read = useMutation({
    mutationFn: (id: number) => api.post(`/notifications/${id}/read`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });
  const unread = (notes.data || []).filter((n) => !n.read_at);

  return (
    <header className="topbar">
      <Link to="/" className="brand">🌿 {t("app.name")}</Link>
      <span className="muted small hide-sm">{t("app.tagline")}</span>
      <div className="spacer" />
      <div className="popover-wrap">
        <button className="btn ghost" onClick={() => setOpen(!open)} aria-expanded={open}>
          🔔 {unread.length > 0 && <span className="badge">{unread.length}</span>}
        </button>
        {open && (
          <div className="popover" role="dialog" aria-label={t("notif.title")}>
            <div className="popover-title">{t("notif.title")}</div>
            {(notes.data || []).length === 0 && <div className="muted small pad">{t("notif.empty")}</div>}
            {(notes.data || []).slice(0, 15).map((n) => (
              <div key={n.id} className={`notif ${n.read_at ? "read" : ""}`}>
                <button className="link" onClick={() => {
                  if (!n.read_at) read.mutate(n.id);
                  setOpen(false);
                  if (n.publication_id) nav(`/p/${n.publication_id}`);
                }}>{n.content}</button>
                <div className="muted small">{new Date(n.created_at + "Z").toLocaleString()}</div>
              </div>
            ))}
          </div>
        )}
      </div>
      <button className="btn ghost" onClick={() => i18n.changeLanguage(i18n.language === "zh" ? "en" : "zh")}>
        {i18n.language === "zh" ? "EN" : "中文"}
      </button>
      <span className="small muted hide-sm">{user?.email}</span>
      <button className="btn ghost" onClick={logout}>{t("auth.logout")}</button>
    </header>
  );
}
