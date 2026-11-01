import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useInfiniteQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { Image, ImageCandidate, ImagePage, Item } from "../api/types";
import { SortableList } from "./Sortable";
import { useItemSave } from "./useItemSave";

const isCC = (l: string | null) => !!l && /^cc/i.test(l);

export default function ImagePicker({ item, pubId }: { item: Item; pubId: number }) {
  const { t } = useTranslation();
  const [picks, setPicks] = useState<Image[]>(item.images);
  useEffect(() => setPicks(item.images), [item]);
  const [source, setSource] = useState<"inat" | "taieol">("inat");
  const [name, setName] = useState(item.scientific_name);
  const [nameInput, setNameInput] = useState(item.scientific_name);
  useEffect(() => { setName(item.scientific_name); setNameInput(item.scientific_name); }, [item.id]); // eslint-disable-line

  const res = useInfiniteQuery({
    queryKey: ["images", item.id, source, source === "inat" ? name : ""],
    queryFn: ({ pageParam }) => api.get<ImagePage>(`/items/${item.id}/image-candidates`, { source, page: pageParam, name: source === "inat" ? name : undefined }),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.has_more ? last.page + 1 : undefined),
  });

  const save = useItemSave(item.id, pubId, (list: Image[]) => api.put<Item>(`/items/${item.id}/images`, list));
  const commit = (next: Image[]) => { setPicks(next); save.mutate(next); };
  const key = (x: { source: string; source_id: string }) => `${x.source}:${x.source_id}`;
  const picked = new Set(picks.map(key));

  const toggle = (c: ImageCandidate) => {
    if (picked.has(key(c))) commit(picks.filter((p) => key(p) !== key(c)));
    else commit([...picks, {
      source: c.source, source_id: c.source_id, url: c.url, thumb_url: c.thumb_url, link: c.link,
      attribution: c.attribution, license: c.license, caption: "",
    }]);
  };

  const rows = res.data?.pages.flatMap((p) => p.items) || [];
  const taxon = res.data?.pages[0]?.taxon_id;

  return (
    <div className="picker">
      <section className="picked">
        <h3>{t("img.picked", { n: picks.length })} {save.isPending && <span className="muted small">…</span>}</h3>
        {save.error && <div className="error small">{(save.error as Error).message}</div>}
        {picks.length === 0 && <div className="muted small">{t("img.none")}</div>}
        <SortableList items={picks} getId={key} onChange={commit} className="pick-strip" grid
          render={(p, i, handle) => (
            <figure className="pick-img">
              <div className="pick-img-top">{handle}
                <button className="btn ghost small danger" onClick={() => commit(picks.filter((x) => key(x) !== key(p)))}>✕</button>
              </div>
              <img src={p.thumb_url || p.url} alt={p.caption || item.scientific_name} loading="lazy" />
              <input placeholder={t("img.caption")} value={p.caption || ""}
                onChange={(e) => setPicks(picks.map((x, j) => (j === i ? { ...x, caption: e.target.value } : x)))}
                onBlur={() => save.mutate(picks)} />
              <figcaption className="small muted">
                <span className={`pill ${isCC(p.license) ? "" : "warn"}`}>{p.license || "?"}</span> {p.attribution}
              </figcaption>
            </figure>
          )} />
      </section>

      <section className="candidates">
        <div className="row gap wrap">
          <div className="seg">
            <button className={source === "inat" ? "on" : ""} onClick={() => setSource("inat")}>{t("img.inat")}</button>
            <button className={source === "taieol" ? "on" : ""} onClick={() => setSource("taieol")}>{t("img.taieol")}</button>
          </div>
          {source === "inat" ? (
            <form className="row gap" onSubmit={(e) => { e.preventDefault(); setName(nameInput.trim() || item.scientific_name); }}>
              <input aria-label={t("img.nameOverride")} value={nameInput} onChange={(e) => setNameInput(e.target.value)} list={`syn-${item.id}`} />
              <datalist id={`syn-${item.id}`}>{item.search_names.map((n) => <option key={n} value={n} />)}</datalist>
              <button className="btn">{t("spec.search")}</button>
            </form>
          ) : taxon ? <span className="muted small">{t("img.taxon", { id: taxon })}</span> : null}
        </div>
        {res.error && <div className="error">{t("common.error", { msg: (res.error as Error).message })}</div>}
        {res.isLoading && <div className="muted">{t("common.loading")}</div>}
        {res.data && rows.length === 0 && <div className="muted">{t("img.noResults")}</div>}
        <div className="img-grid">
          {rows.map((c) => {
            const on = picked.has(key(c));
            return (
              <figure key={key(c)} className={`cand ${on ? "on" : ""}`}>
                <button className="cand-img" onClick={() => toggle(c)} aria-pressed={on}>
                  <img src={c.thumb_url || c.url} alt={c.title} loading="lazy" />
                  <span className="cand-check">{on ? "✓" : "＋"}</span>
                </button>
                <figcaption className="small">
                  <span className={`pill ${isCC(c.license) ? "" : "warn"}`} title={isCC(c.license) ? c.license : t("img.noLicense")}>{c.license || "©"}</span>{" "}
                  <span className="muted">{c.attribution}</span>{" "}
                  {c.link && <a href={c.link} target="_blank" rel="noreferrer" title={t("img.open")}>↗</a>}
                  {(c.date || c.kind) && <div className="muted">{[c.date, c.place, c.kind].filter(Boolean).join(" · ")}</div>}
                </figcaption>
              </figure>
            );
          })}
        </div>
        {res.hasNextPage && (
          <button className="btn" disabled={res.isFetchingNextPage} onClick={() => res.fetchNextPage()}>
            {res.isFetchingNextPage ? t("common.loading") : t("img.more")}
          </button>
        )}
      </section>
    </div>
  );
}
