import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { Item } from "../api/types";
import Html from "./Html";
import ItemText from "./ItemText";
import SpecimenPicker from "./SpecimenPicker";
import ImagePicker from "./ImagePicker";

type Tab = "text" | "specimens" | "images";

export default function ItemPanel({ itemId, pubId }: { itemId: number; pubId: number }) {
  const { t } = useTranslation();
  const [tab, setTab] = useState<Tab>("text");
  const item = useQuery({ queryKey: ["item", itemId], queryFn: () => api.get<Item>(`/items/${itemId}`) });

  if (item.isLoading) return <div className="center muted">{t("common.loading")}</div>;
  if (item.error || !item.data) return <div className="error">{t("common.error", { msg: (item.error as Error)?.message })}</div>;
  const it = item.data;

  return (
    <div className="item-panel">
      <div className="item-head">
        <h2><Html html={it.usage_text || it.name_html || it.scientific_name} /></h2>
        {it.common_names && <div className="muted">{it.common_names.split("|").join("、")}</div>}
        <div className="small muted">
          {it.rank && `${it.rank[0]} / ${it.rank[1]} · `}name_id {it.name_id}
        </div>
      </div>
      <nav className="tabs" role="tablist">
        {(["text", "specimens", "images"] as Tab[]).map((x) => (
          <button key={x} role="tab" aria-selected={tab === x} className={`tab ${tab === x ? "on" : ""}`} onClick={() => setTab(x)}>
            {t(`tabs.${x}`)}
            {x === "specimens" && <span className="tab-n">{it.specimens.length}</span>}
            {x === "images" && <span className="tab-n">{it.images.length}</span>}
          </button>
        ))}
      </nav>
      {tab === "text" && <ItemText item={it} pubId={pubId} />}
      {tab === "specimens" && <SpecimenPicker item={it} pubId={pubId} />}
      {tab === "images" && <ImagePicker item={it} pubId={pubId} />}
    </div>
  );
}
