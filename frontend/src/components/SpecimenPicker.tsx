import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { Facets, Item, Occurrence, OccurrencePage, Specimen } from "../api/types";
import { SortableList } from "./Sortable";
import { useItemSave } from "./useItemSave";

const PAGE = 50;
type FacetKey = "county" | "type_status" | "dataset_name";
const FACETS: [FacetKey, string][] = [["county", "spec.county"], ["type_status", "spec.typeStatus"], ["dataset_name", "spec.dataset"]];

interface Pick { occurrence_id: string; display_text: string; record: Record<string, unknown>; link?: string | null; label: string }

const fromSaved = (s: Specimen): Pick => ({
  occurrence_id: s.occurrence_id, display_text: s.display_text, record: {}, link: s.link,
  label: [s.scientific_name, s.county, s.event_date, s.type_status].filter(Boolean).join(" · "),
});

export default function SpecimenPicker({ item, pubId }: { item: Item; pubId: number }) {
  const { t } = useTranslation();
  const [picks, setPicks] = useState<Pick[]>(() => item.specimens.map(fromSaved));
  useEffect(() => setPicks(item.specimens.map(fromSaved)), [item]);

  const [mode, setMode] = useState<"names" | "text">("names");
  const [names, setNames] = useState<string[]>(item.search_names);
  const [text, setText] = useState("");
  const [q, setQ] = useState("");
  const [sel, setSel] = useState<Record<FacetKey, string[]>>({ county: [], type_status: [], dataset_name: [] });
  const [hasMedia, setHasMedia] = useState(false);
  useEffect(() => { setNames(item.search_names); setSel({ county: [], type_status: [], dataset_name: [] }); }, [item.id]); // eslint-disable-line

  const params = {
    ...(mode === "text" ? { q } : { names }),
    county: sel.county, type_status: sel.type_status, dataset_name: sel.dataset_name, has_media: hasMedia,
  };
  const enabled = mode === "text" ? q.length > 0 : names.length > 0;

  const res = useInfiniteQuery({
    queryKey: ["specimens", item.id, params],
    queryFn: ({ pageParam }) => api.get<OccurrencePage>(`/items/${item.id}/specimen-candidates`, { ...params, limit: PAGE, offset: pageParam }),
    initialPageParam: 0,
    getNextPageParam: (last) => (last.offset + last.items.length < last.total ? last.offset + PAGE : undefined),
    enabled,
  });
  const facets = useQuery({
    queryKey: ["specimen-facets", item.id, mode === "text" ? q : names],
    queryFn: () => api.get<Facets>(`/items/${item.id}/specimen-facets`, mode === "text" ? { q } : { names }),
    enabled,
  });

  const save = useItemSave(item.id, pubId, (list: Pick[]) =>
    api.put<Item>(`/items/${item.id}/specimens`, list.map(({ occurrence_id, display_text, record }) => ({ occurrence_id, display_text, record }))));
  const commit = (next: Pick[]) => { setPicks(next); save.mutate(next); };

  const pickedIds = new Set(picks.map((p) => p.occurrence_id));
  const toggle = (o: Occurrence) => {
    if (pickedIds.has(o.id)) commit(picks.filter((p) => p.occurrence_id !== o.id));
    else commit([...picks, {
      occurrence_id: o.id, display_text: o.display_text, record: o, link: o.link,
      label: [o.scientific_name, o.county, o.standard_date, o.type_status].filter(Boolean).join(" · "),
    }]);
  };
  const toggleFacet = (k: FacetKey, v: string) =>
    setSel({ ...sel, [k]: sel[k].includes(v) ? sel[k].filter((x) => x !== v) : [...sel[k], v] });

  const rows = res.data?.pages.flatMap((p) => p.items) || [];
  const total = res.data?.pages[0]?.total ?? 0;
  const anyFilter = sel.county.length + sel.type_status.length + sel.dataset_name.length > 0 || hasMedia;

  return (
    <div className="picker">
      <section className="picked">
        <h3>{t("spec.picked", { n: picks.length })} {save.isPending && <span className="muted small">…</span>}</h3>
        {save.error && <div className="error small">{(save.error as Error).message}</div>}
        {picks.length === 0 && <div className="muted small">{t("spec.none")}</div>}
        <SortableList items={picks} getId={(p) => p.occurrence_id} onChange={commit}
          render={(p, i, handle) => (
            <div className="pick-row">
              {handle}
              <div className="grow">
                <div className="small muted">{p.label}</div>
                <input value={p.display_text} aria-label="display text"
                  onChange={(e) => setPicks(picks.map((x, j) => (j === i ? { ...x, display_text: e.target.value } : x)))}
                  onBlur={() => { if (p.display_text !== item.specimens.find((s) => s.occurrence_id === p.occurrence_id)?.display_text) save.mutate(picks); }} />
              </div>
              {p.link && <a className="btn ghost small" href={p.link} target="_blank" rel="noreferrer" title={t("spec.open")}>↗</a>}
              <button className="btn ghost small danger" onClick={() => commit(picks.filter((x) => x.occurrence_id !== p.occurrence_id))}>{t("spec.remove")}</button>
            </div>
          )} />
      </section>

      <section className="candidates">
        <h3>{t("spec.candidates")}</h3>
        <div className="row gap wrap">
          <div className="seg">
            <button className={mode === "names" ? "on" : ""} onClick={() => setMode("names")}>{t("spec.byNames")}</button>
            <button className={mode === "text" ? "on" : ""} onClick={() => setMode("text")}>{t("spec.byText")}</button>
          </div>
          {mode === "names" ? (
            <div className="chips">
              {item.search_names.map((n, i) => (
                <button key={n} className={`chip ${names.includes(n) ? "on" : ""}`} title={i === 0 ? "accepted" : "synonym"}
                  onClick={() => setNames(names.includes(n) ? names.filter((x) => x !== n) : [...names, n])}>
                  <i>{n}</i>{i > 0 && <span className="muted"> syn.</span>}
                </button>
              ))}
            </div>
          ) : (
            <form className="row gap" onSubmit={(e) => { e.preventDefault(); setQ(text.trim()); }}>
              <input value={text} placeholder="Hayata, 合歡山, TAI 12345…" onChange={(e) => setText(e.target.value)} />
              <button className="btn">{t("spec.search")}</button>
            </form>
          )}
        </div>

        {facets.data && (
          <div className="facets">
            {FACETS.map(([k, label]) => (facets.data[k]?.length ? (
              <div key={k} className="facet">
                <span className="facet-label">{t(label)}</span>
                <div className="chips">
                  {facets.data[k].slice(0, 12).map((f) => (
                    <button key={f.value} className={`chip small ${sel[k].includes(f.value) ? "on" : ""}`} onClick={() => toggleFacet(k, f.value)}>
                      {f.value} <span className="muted">{f.count}</span>
                    </button>
                  ))}
                </div>
              </div>
            ) : null))}
            <label className="small row gap"><input type="checkbox" checked={hasMedia} onChange={(e) => setHasMedia(e.target.checked)} /> {t("spec.hasMedia")}</label>
            {anyFilter && <button className="link small" onClick={() => { setSel({ county: [], type_status: [], dataset_name: [] }); setHasMedia(false); }}>{t("spec.clearFilters")}</button>}
          </div>
        )}

        {res.error && <div className="error">{t("spec.upstreamDown", { msg: (res.error as Error).message })}</div>}
        {res.isLoading && enabled && <div className="muted">{t("common.loading")}</div>}
        {res.data && <div className="muted small">{t("spec.total", { n: total })}</div>}
        {res.data && rows.length === 0 && <div className="muted">{t("spec.noResults")}</div>}

        {rows.length > 0 && (
          <div className="table-wrap">
            <table className="occ">
              <thead><tr><th /><th>Name</th><th>Collector / No.</th><th>Locality</th><th>Date</th><th>Inst. / Cat.</th><th>Type</th><th /></tr></thead>
              <tbody>
                {rows.map((o) => {
                  const on = pickedIds.has(o.id);
                  return (
                    <tr key={o.id} className={on ? "on" : ""}>
                      <td><button className={`btn small ${on ? "primary" : ""}`} onClick={() => toggle(o)}>{on ? "✓" : "＋"}</button></td>
                      <td><i>{o.scientific_name}</i></td>
                      <td>{[o.recorded_by, o.record_number].filter(Boolean).join(" ")}</td>
                      <td>{[o.county, o.locality].filter(Boolean).join(" ")}</td>
                      <td className="nowrap">{o.standard_date || o.year || ""}</td>
                      <td>{[o.institution_code, o.catalog_number].filter(Boolean).join(" ")}</td>
                      <td>{o.type_status}</td>
                      <td>
                        {o.thumbnail && <a href={o.thumbnail} target="_blank" rel="noreferrer" title="image">▣</a>}{" "}
                        <a href={o.link} target="_blank" rel="noreferrer" title={t("spec.open")}>↗</a>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        {res.hasNextPage && (
          <button className="btn" disabled={res.isFetchingNextPage} onClick={() => res.fetchNextPage()}>
            {res.isFetchingNextPage ? t("common.loading") : t("spec.more")}
          </button>
        )}
      </section>
    </div>
  );
}
