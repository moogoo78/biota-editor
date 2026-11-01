import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import type { PublicationSummary } from "../api/types";

interface Available { namespace_id: number; publication_id: number | null }
interface ImportOut { publication_id: number; status: string; counts: Record<string, number> }

export default function Publications() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const [showImport, setShowImport] = useState(false);
  const pubs = useQuery({ queryKey: ["publications"], queryFn: () => api.get<PublicationSummary[]>("/publications") });
  const del = useMutation({
    mutationFn: (id: number) => api.del(`/publications/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["publications"] }),
  });

  return (
    <main className="page">
      <div className="row between">
        <h1>{t("pubs.title")}</h1>
        <button className="btn primary" onClick={() => setShowImport(true)}>＋ {t("pubs.import")}</button>
      </div>
      {showImport && <ImportDialog onClose={() => setShowImport(false)} />}
      {pubs.isLoading && <p className="muted">{t("common.loading")}</p>}
      {pubs.error && <p className="error">{t("common.error", { msg: (pubs.error as Error).message })}</p>}
      {pubs.data?.length === 0 && <p className="muted">{t("pubs.empty")}</p>}
      <div className="pub-grid">
        {pubs.data?.map((p) => (
          <div className="card pub-card" key={p.id}>
            <Link to={`/p/${p.id}`} className="pub-title">{p.title || `#${p.namespace_id}`}</Link>
            <div className="muted small">{p.author}</div>
            <div className="row small gap">
              <span className={`pill status-${p.status}`}>{t(`status.${p.status}`)}</span>
              <span className="muted">{t("pubs.items", { n: p.n_items })}</span>
              <span className="muted">ns {p.namespace_id}</span>
            </div>
            {p.synced_at && (
              <div className="muted small">{t("pubs.synced", { at: new Date(p.synced_at + "Z").toLocaleString() })}</div>
            )}
            <div className="row gap">
              <Link className="btn" to={`/p/${p.id}`}>{t("pubs.open")}</Link>
              <button className="btn ghost danger" onClick={() => { if (confirm(t("pubs.confirmDelete"))) del.mutate(p.id); }}>
                {t("pubs.delete")}
              </button>
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}

function ImportDialog({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation();
  const nav = useNavigate();
  const qc = useQueryClient();
  const [nsId, setNsId] = useState("");
  const avail = useQuery({ queryKey: ["available"], queryFn: () => api.get<Available[]>("/namespaces/available"), retry: 0 });
  const imp = useMutation({
    mutationFn: (namespace_id: number) => api.post<ImportOut>("/publications/import", { namespace_id }),
    onSuccess: (r) => {
      qc.invalidateQueries({ queryKey: ["publications"] });
      nav(`/p/${r.publication_id}`);
    },
  });
  const submit = (e: FormEvent) => { e.preventDefault(); if (nsId) imp.mutate(Number(nsId)); };

  return (
    <div className="modal-bg" onClick={onClose}>
      <form className="card modal" onClick={(e) => e.stopPropagation()} onSubmit={submit}>
        <h2>{t("pubs.import")}</h2>
        <div className="muted small">{t("pubs.available")}</div>
        {avail.isLoading && <div className="muted small">{t("common.loading")}</div>}
        {avail.error && <div className="muted small">{t("pubs.loadAvailable")}</div>}
        <div className="chips">
          {avail.data?.map((a) => (
            <button type="button" key={a.namespace_id} className={`chip ${String(a.namespace_id) === nsId ? "on" : ""}`}
              onClick={() => setNsId(String(a.namespace_id))}>
              {a.namespace_id}{a.publication_id ? ` · ${t("pubs.imported")}` : ""}
            </button>
          ))}
        </div>
        <label>{t("pubs.namespaceId")}
          <input inputMode="numeric" pattern="[0-9]+" required value={nsId} onChange={(e) => setNsId(e.target.value)} />
        </label>
        {imp.error && <div className="error">{(imp.error as Error).message}</div>}
        <div className="row gap end">
          <button type="button" className="btn ghost" onClick={onClose}>{t("editor.cancel")}</button>
          <button className="btn primary" disabled={imp.isPending}>{imp.isPending ? t("common.loading") : t("pubs.import")}</button>
        </div>
      </form>
    </div>
  );
}
