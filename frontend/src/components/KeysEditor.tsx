import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import type { IdKey, KeyEntry, Publication } from "../api/types";

export default function KeysEditor({ pub }: { pub: Publication }) {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const keys = useQuery({ queryKey: ["keys", pub.id], queryFn: () => api.get<IdKey[]>(`/publications/${pub.id}/keys`) });
  const create = useMutation({
    mutationFn: () => api.post<IdKey>(`/publications/${pub.id}/keys`, { title: "", entries: [] }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["keys", pub.id] }),
  });
  return (
    <div className="settings">
      <div className="row between">
        <h3>{t("editor.keys")}</h3>
        <button className="btn" onClick={() => create.mutate()}>＋ {t("keys.new")}</button>
      </div>
      {keys.data?.length === 0 && <div className="muted small">{t("keys.empty")}</div>}
      {keys.data?.map((k) => <KeyForm key={k.id} k={k} pub={pub} />)}
    </div>
  );
}

function KeyForm({ k, pub }: { k: IdKey; pub: Publication }) {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const [title, setTitle] = useState(k.title || "");
  const [entries, setEntries] = useState<KeyEntry[]>(k.entries);
  useEffect(() => { setTitle(k.title || ""); setEntries(k.entries); }, [k]);
  const done = () => { qc.invalidateQueries({ queryKey: ["keys", pub.id] }); qc.invalidateQueries({ queryKey: ["preview", pub.id] }); };
  const save = useMutation({ mutationFn: () => api.put<IdKey>(`/keys/${k.id}`, { title, entries }), onSuccess: done });
  const del = useMutation({ mutationFn: () => api.del(`/keys/${k.id}`), onSuccess: done });
  const set = (i: number, patch: Partial<KeyEntry>) => setEntries(entries.map((e, j) => (j === i ? { ...e, ...patch } : e)));
  const species = pub.items.filter((i) => (i.rank_id || 0) >= 34);

  return (
    <div className="card key-card">
      <input placeholder={t("keys.title")} value={title} onChange={(e) => setTitle(e.target.value)} />
      <table className="key-table">
        <thead><tr><th>{t("keys.number")}</th><th>{t("keys.indent")}</th><th>{t("keys.description")}</th><th>{t("keys.goto")}</th><th>{t("keys.result")}</th><th /></tr></thead>
        <tbody>
          {entries.map((e, i) => (
            <tr key={i}>
              <td><input type="number" min={1} value={e.number} onChange={(x) => set(i, { number: Number(x.target.value) })} /></td>
              <td><input type="number" min={0} max={8} value={e.indent_level} onChange={(x) => set(i, { indent_level: Number(x.target.value) })} /></td>
              <td><textarea rows={2} value={e.description} onChange={(x) => set(i, { description: x.target.value })} /></td>
              <td><input type="number" min={1} value={e.result_couplet ?? ""} onChange={(x) => set(i, { result_couplet: x.target.value ? Number(x.target.value) : null, result_item_id: null })} /></td>
              <td>
                <select value={e.result_item_id ?? ""} onChange={(x) => set(i, { result_item_id: x.target.value ? Number(x.target.value) : null, result_couplet: null })}>
                  <option value="">—</option>
                  {species.map((s) => <option key={s.id} value={s.id}>{s.scientific_name}</option>)}
                </select>
              </td>
              <td><button className="btn ghost small danger" onClick={() => setEntries(entries.filter((_, j) => j !== i))}>✕</button></td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="row gap">
        <button className="btn" onClick={() => {
          const last = entries[entries.length - 1];
          setEntries([...entries, { number: last ? last.number + (entries.length % 2 === 0 ? 1 : 0) : 1, indent_level: last?.indent_level ?? 0, description: "", result_couplet: null, result_item_id: null }]);
        }}>＋ {t("keys.addEntry")}</button>
        <div className="spacer" />
        <button className="btn ghost danger" onClick={() => del.mutate()}>{t("keys.delete")}</button>
        <button className="btn primary" disabled={save.isPending} onClick={() => save.mutate()}>{t("editor.save")}</button>
      </div>
      {save.error && <div className="error small">{(save.error as Error).message}</div>}
    </div>
  );
}
