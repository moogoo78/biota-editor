import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import type { Literature, Publication } from "../api/types";
import { SortableList } from "./Sortable";

let uid = 0;
type Row = Literature & { _k: string };
const rows = (p: Publication): Row[] => p.literatures.map((l) => ({ ...l, _k: `l${uid++}` }));

export default function PubSettings({ pub }: { pub: Publication }) {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const [title, setTitle] = useState(pub.title);
  const [author, setAuthor] = useState(pub.author);
  const [lits, setLits] = useState<Row[]>(() => rows(pub));
  useEffect(() => { setTitle(pub.title); setAuthor(pub.author); setLits(rows(pub)); }, [pub.id, pub.synced_at]); // eslint-disable-line

  const save = useMutation({
    mutationFn: async () => {
      await api.put(`/publications/${pub.id}/literatures`,
        lits.filter((l) => l.citation.trim()).map((l) => ({ reference_id: l.reference_id, citation: l.citation })));
      return api.patch<Publication>(`/publications/${pub.id}`, { title, author });
    },
    onSuccess: (p) => {
      qc.setQueryData(["publication", pub.id], p);
      qc.invalidateQueries({ queryKey: ["preview", pub.id] });
      qc.invalidateQueries({ queryKey: ["publications"] });
    },
  });

  return (
    <div className="settings">
      <label>{t("editor.title")}<input value={title} onChange={(e) => setTitle(e.target.value)} /></label>
      <label>{t("editor.author")}<input value={author} onChange={(e) => setAuthor(e.target.value)} /></label>
      <h3>{t("editor.literatures")}</h3>
      <SortableList items={lits} getId={(l) => l._k} onChange={setLits}
        render={(l, i, handle) => (
          <div className="pick-row">
            {handle}
            <textarea className="grow" rows={2} value={l.citation}
              onChange={(e) => setLits(lits.map((x, j) => (j === i ? { ...x, citation: e.target.value } : x)))} />
            <button className="btn ghost small danger" onClick={() => setLits(lits.filter((_, j) => j !== i))}>✕</button>
          </div>
        )} />
      <div className="row gap">
        <button className="btn" onClick={() => setLits([...lits, { reference_id: null, citation: "", _k: `l${uid++}` }])}>＋ {t("editor.addLit")}</button>
        <div className="spacer" />
        <button className="btn primary" disabled={save.isPending} onClick={() => save.mutate()}>{t("editor.save")}</button>
      </div>
      {save.isSuccess && <div className="muted small">{t("editor.saved")}</div>}
      {save.error && <div className="error small">{(save.error as Error).message}</div>}
    </div>
  );
}
