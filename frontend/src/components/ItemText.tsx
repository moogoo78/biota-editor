import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../api/client";
import type { Item, TextField } from "../api/types";
import Html from "./Html";
import { useItemSave } from "./useItemSave";

const FIELDS: TextField[] = ["common_names", "description", "distribution", "note"];

export default function ItemText({ item, pubId }: { item: Item; pubId: number }) {
  const { t } = useTranslation();
  const [draft, setDraft] = useState<Record<TextField, string>>(() => pick(item));
  useEffect(() => setDraft(pick(item)), [item]);
  const save = useItemSave(item.id, pubId, (patch: Partial<Record<TextField, string>>) => api.patch<Item>(`/items/${item.id}`, patch));
  const revert = useItemSave(item.id, pubId, (fields: TextField[]) => api.post<Item>(`/items/${item.id}/revert`, { fields }));

  const dirty = FIELDS.filter((f) => draft[f] !== (item[f] || ""));

  return (
    <div className="item-text">
      <section>
        <h3>{t("text.synonyms")}</h3>
        {item.synonyms.length === 0 && <div className="muted small">{t("text.noSynonyms")}</div>}
        <ul className="syn-list">{item.synonyms.map((s) => <li key={s.id}><Html html={s.usage_text} /></li>)}</ul>
      </section>
      {FIELDS.map((f) => (
        <section key={f}>
          <div className="row between">
            <h3>{t(`text.${f}`)}</h3>
            {item.edited_fields.includes(f) && (
              <span className="small">
                <span className="pill warn">{t("text.edited")}</span>{" "}
                <button className="link" onClick={() => revert.mutate([f])}>{t("text.revert")}</button>
              </span>
            )}
          </div>
          {f === "common_names" ? (
            <input value={draft[f]} onChange={(e) => setDraft({ ...draft, [f]: e.target.value })} />
          ) : (
            <textarea rows={f === "description" ? 8 : 3} value={draft[f]} onChange={(e) => setDraft({ ...draft, [f]: e.target.value })} />
          )}
        </section>
      ))}
      <div className="sticky-actions">
        <button className="btn primary" disabled={!dirty.length || save.isPending}
          onClick={() => save.mutate(Object.fromEntries(dirty.map((f) => [f, draft[f]])))}>
          {save.isPending ? t("common.loading") : t("editor.save")}
        </button>
        {dirty.length > 0 && <button className="btn ghost" onClick={() => setDraft(pick(item))}>{t("editor.cancel")}</button>}
        {save.isSuccess && !dirty.length && <span className="muted small">{t("editor.saved")}</span>}
        {save.error && <span className="error small">{(save.error as Error).message}</span>}
      </div>
    </div>
  );
}

function pick(item: Item): Record<TextField, string> {
  return Object.fromEntries(FIELDS.map((f) => [f, item[f] || ""])) as Record<TextField, string>;
}
