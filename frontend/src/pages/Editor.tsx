import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, download } from "../api/client";
import type { ItemSummary, Publication } from "../api/types";
import Html from "../components/Html";
import { SortableList } from "../components/Sortable";
import ItemPanel from "../components/ItemPanel";
import Preview from "../components/Preview";
import PubSettings from "../components/PubSettings";
import KeysEditor from "../components/KeysEditor";

const EXPORTS = [
  ["docx", "Word (.docx)"], ["pdf", "PDF"], ["pdf2", "PDF — journal"], ["pdf3", "PDF — journal compact"],
  ["json", "JSON"],
] as const;

export default function Editor() {
  const { t } = useTranslation();
  const { pubId, itemId } = useParams();
  const nav = useNavigate();
  const qc = useQueryClient();
  const [filter, setFilter] = useState("");
  const [panel, setPanel] = useState<"none" | "preview" | "settings" | "keys">("none");
  const [msg, setMsg] = useState("");
  const [exportOpen, setExportOpen] = useState(false);
  const key = ["publication", Number(pubId)];

  const pub = useQuery({ queryKey: key, queryFn: () => api.get<Publication>(`/publications/${pubId}`) });

  const sync = useMutation({
    mutationFn: () => api.post<Record<string, number>>(`/publications/${pubId}/sync`),
    onSuccess: (c) => {
      setMsg(t("editor.synced", c));
      qc.invalidateQueries({ queryKey: key });
      qc.invalidateQueries({ queryKey: ["item"] });
      qc.invalidateQueries({ queryKey: ["preview"] });
    },
    onError: (e) => setMsg((e as Error).message),
  });
  const status = useMutation({
    mutationFn: (s: string) => api.patch<Publication>(`/publications/${pubId}`, { status: s }),
    onSuccess: (p) => qc.setQueryData(key, p),
  });
  const order = useMutation({
    mutationFn: (ids: number[]) => api.put<Publication>(`/publications/${pubId}/items/order`, { ids }),
    onSuccess: (p) => { qc.setQueryData(key, p); qc.invalidateQueries({ queryKey: ["preview"] }); },
  });

  const items = pub.data?.items || [];
  const shown = useMemo(() => {
    const f = filter.trim().toLowerCase();
    return f ? items.filter((i) => `${i.scientific_name} ${i.common_names || ""}`.toLowerCase().includes(f)) : items;
  }, [items, filter]);

  if (pub.isLoading) return <div className="center muted">{t("common.loading")}</div>;
  if (pub.error || !pub.data) return <div className="center error">{t("common.error", { msg: (pub.error as Error)?.message })}</div>;
  const p = pub.data;
  const current = itemId ? Number(itemId) : null;

  const reorder = (next: ItemSummary[]) => {
    qc.setQueryData<Publication>(key, { ...p, items: next });
    order.mutate(next.map((i) => i.id));
  };
  const doExport = async (fmt: string) => {
    setExportOpen(false);
    try { await download(`/publications/${p.id}/export?format=${fmt}`, `biotaeditor.${fmt}`); }
    catch (e) { setMsg((e as Error).message); }
  };

  return (
    <div className={`editor ${panel !== "none" ? "with-side" : ""}`}>
      <div className="editor-head">
        <Link to="/" className="muted small">← {t("editor.back")}</Link>
        <h1 className="pub-h1">{p.title}</h1>
        <span className="muted small hide-sm">{p.author} · ns {p.namespace_id}</span>
        <div className="spacer" />
        <select value={p.status} onChange={(e) => status.mutate(e.target.value)} aria-label="status">
          {["draft", "review", "done"].map((s) => <option key={s} value={s}>{t(`status.${s}`)}</option>)}
        </select>
        <button className="btn" onClick={() => sync.mutate()} disabled={sync.isPending}>
          ⟳ {sync.isPending ? t("editor.syncing") : t("editor.sync")}
        </button>
        <button className={`btn ${panel === "settings" ? "on" : ""}`} onClick={() => setPanel(panel === "settings" ? "none" : "settings")}>
          {t("editor.literatures")}
        </button>
        <button className={`btn ${panel === "keys" ? "on" : ""}`} onClick={() => setPanel(panel === "keys" ? "none" : "keys")}>
          {t("editor.keys")}
        </button>
        <button className={`btn ${panel === "preview" ? "on" : ""}`} onClick={() => setPanel(panel === "preview" ? "none" : "preview")}>
          {panel === "preview" ? t("editor.hidePreview") : t("editor.preview")}
        </button>
        <div className="popover-wrap">
          <button className="btn primary" onClick={() => setExportOpen(!exportOpen)}>⇩ {t("editor.export")}</button>
          {exportOpen && (
            <div className="popover right">
              {EXPORTS.map(([f, label]) => (
                <button key={f} className="menu-item" onClick={() => doExport(f)}>{label}</button>
              ))}
            </div>
          )}
        </div>
      </div>
      {msg && <div className="flash" onClick={() => setMsg("")}>{msg} ✕</div>}

      <aside className="names">
        <input className="filter" placeholder={t("editor.filter")} value={filter} onChange={(e) => setFilter(e.target.value)} />
        {filter ? (
          <div>{shown.map((i) => <NameRow key={i.id} i={i} on={i.id === current} onClick={() => nav(`/p/${p.id}/i/${i.id}`)} />)}</div>
        ) : (
          <SortableList items={items} getId={(i) => String(i.id)} onChange={reorder}
            render={(i, _n, handle) => (
              <NameRow i={i} on={i.id === current} handle={handle} onClick={() => nav(`/p/${p.id}/i/${i.id}`)} />
            )} />
        )}
      </aside>

      <main className="item-main">
        {current ? <ItemPanel itemId={current} pubId={p.id} /> : <div className="center muted">{t("editor.pick")}</div>}
      </main>

      {panel !== "none" && (
        <aside className="side">
          {panel === "preview" && <Preview pubId={p.id} />}
          {panel === "settings" && <PubSettings pub={p} />}
          {panel === "keys" && <KeysEditor pub={p} />}
        </aside>
      )}
    </div>
  );
}

function NameRow({ i, on, onClick, handle }: { i: ItemSummary; on: boolean; onClick: () => void; handle?: React.ReactNode }) {
  const { i18n } = useTranslation();
  const species = (i.rank_id || 0) >= 34;
  return (
    <div className={`name-row ${on ? "on" : ""} ${species ? "" : "higher"}`}>
      {handle}
      <button className="name-btn" onClick={onClick}>
        <span className="name-sci">
          {!species && i.rank && <span className="rank">{i18n.language === "zh" ? i.rank[1] : i.rank[0]} </span>}
          <Html html={i.name_html || i.scientific_name} />
        </span>
        {i.common_names && <span className="name-common">{i.common_names.split("|")[0]}</span>}
      </button>
      <span className="counts" title="specimens · images">
        <span className={i.n_specimens ? "c on" : "c"}>⊞{i.n_specimens}</span>
        <span className={i.n_images ? "c on" : "c"}>▣{i.n_images}</span>
      </span>
    </div>
  );
}
