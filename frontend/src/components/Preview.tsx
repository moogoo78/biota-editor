import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { Preview as P } from "../api/types";
import Html from "./Html";

/** Renders the same generate_json() context the PDF/DOCX renderers consume. */
export default function Preview({ pubId }: { pubId: number }) {
  const { t } = useTranslation();
  const q = useQuery({ queryKey: ["preview", pubId], queryFn: () => api.get<P>(`/publications/${pubId}/preview`) });
  if (q.isLoading) return <div className="muted">{t("common.loading")}</div>;
  if (q.error || !q.data) return <div className="error">{(q.error as Error)?.message}</div>;
  return (
    <article className="preview">
      {q.data.publications.map((p, n) => (
        <div key={n}>
          {p.category?.heading && <h2 className="pv-cat"><Html html={p.category.heading} /></h2>}
          <h1 className="pv-title">{p.title}</h1>
          <div className="pv-author">{p.author}</div>
          {p.category?.description && <Html as="p" className="pv-body" html={p.category.description} />}
          {p.keys.map((k, i) => (
            <div key={i} className="pv-key">
              {k.title && <h3>{k.title}</h3>}
              {k.entries.map((e, j) => (
                <div key={j} className="pv-lead" style={{ paddingLeft: e.indentLevel * 14 }}>
                  <b>{e.number}.</b> <Html html={e.description} />
                  {e.result !== "" && <span className="pv-dots"> … {e.resultType === "item" ? <i>{e.result}</i> : e.result}</span>}
                </div>
              ))}
            </div>
          ))}
          {p.items.map((it) => (
            <section key={it.number} className="pv-item">
              <div className="pv-name"><b>{it.number}. <Html html={it.scientificName} /></b> <Html html={it.nameSuffix} /></div>
              {it.commonName && <div className="pv-common">{it.commonName}</div>}
              {it.synonyms.map((s, i) => <div key={i} className="pv-syn"><Html html={s} /></div>)}
              {it.description && <Html as="p" className="pv-body" html={it.description} />}
              {it.distribution && <Html as="p" className="pv-body" html={it.distribution} />}
              {it.specimens.length > 0 && (
                <p className="pv-spec">
                  {it.specimens.map((g) => <span key={g.county}><b>{g.region}</b>: {g.records.join("; ")}. </span>)}
                </p>
              )}
              {it.note && <Html as="p" className="pv-body" html={it.note} />}
              {it.images.length > 0 && (
                <div className="pv-figs">
                  {it.images.map((im, i) => (
                    <figure key={i}><img src={im.url} alt="" loading="lazy" /><figcaption>{im.captionText}</figcaption></figure>
                  ))}
                </div>
              )}
            </section>
          ))}
          {p.literatures.length > 0 && (
            <section className="pv-lit"><h3>{t("editor.literatures")}</h3>{p.literatures.map((l, i) => <p key={i}>{l}</p>)}</section>
          )}
        </div>
      ))}
      <div className="muted small">{q.data.generator} · {q.data.generatedAt}</div>
    </article>
  );
}
