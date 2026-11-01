export interface User { id: number; email: string; name: string | null }

export interface Notification {
  id: number; content: string; publication_id: number | null; created_at: string; read_at: string | null;
}

export interface Literature { id?: number; reference_id: number | null; citation: string; sort?: number }

export interface ItemSummary {
  id: number; name_id: number | null; rank_id: number | null; rank: [string, string] | null;
  scientific_name: string; name_html: string | null; name_authors: string | null;
  common_names: string | null; sort: number; n_specimens: number; n_images: number; n_synonyms: number;
}

export interface Synonym { id: number; name_id: number | null; usage_text: string }

export interface Specimen {
  id: number; source: string; occurrence_id: string; scientific_name: string | null;
  catalog_number: string | null; recorded_by: string | null; record_number: string | null;
  locality: string | null; county: string | null; institution_code: string | null;
  dataset_name: string | null; event_date: string | null; type_status: string | null;
  display_text: string; sort: number; link: string | null;
}

export interface Image {
  id?: number; source: "inat" | "taieol"; source_id: string; url: string; thumb_url: string | null;
  link: string | null; attribution: string | null; license: string | null; caption: string | null;
}

export type TextField = "common_names" | "description" | "distribution" | "note";

export interface Item extends ItemSummary {
  usage_text: string | null; description: string | null; distribution: string | null; note: string | null;
  edited_fields: TextField[]; synonyms: Synonym[]; specimens: Specimen[]; images: Image[];
  search_names: string[];
}

export interface PublicationSummary {
  id: number; namespace_id: number; title: string; author: string; status: string;
  synced_at: string | null; updated_at: string; n_items: number;
}

export interface Publication extends PublicationSummary { literatures: Literature[]; items: ItemSummary[] }

/** A row from ISLAND /api/occurrences, decorated by the BiotaEditor proxy. */
export interface Occurrence {
  id: string; catalog_number: string | null; scientific_name: string | null; common_name_c: string | null;
  county: string | null; locality: string | null; standard_date: string | null; year: number | null;
  type_status: string | null; dataset_name: string | null; institution_code: string | null;
  recorded_by: string | null; record_number: string | null; thumbnail: string | null;
  standard_latitude: number | null; standard_longitude: number | null;
  picked: boolean; link: string; display_text: string;
  [k: string]: unknown;
}

export interface OccurrencePage { total: number; items: Occurrence[]; limit: number; offset: number; names: string[] }

export interface ImageCandidate {
  source: "inat" | "taieol"; source_id: string; url: string; thumb_url: string; attribution: string;
  license: string; observer: string; link: string; title: string; picked: boolean;
  date?: string; place?: string; kind?: string; license_url?: string;
}

export interface ImagePage { total: number; page: number; has_more: boolean; items: ImageCandidate[]; taxon_id?: string | null }

export interface Facets { [dim: string]: { value: string; count: number }[] }

export interface KeyEntry {
  id?: number; number: number; indent_level: number; description: string;
  result_couplet: number | null; result_item_id: number | null;
}
export interface IdKey { id: number; title: string | null; entries: KeyEntry[] }

/** generate_json() context */
export interface PreviewItem {
  number: number; scientificName: string; nameSuffix: string; fullScientificName: string; rankId: number | string;
  commonName: string; synonyms: string[]; description: string; distribution: string; note: string;
  specimens: { county: string; region: string; records: string[] }[];
  images: { url: string; captionText: string; license: string }[];
}
export interface PreviewPub {
  title: string; author: string; literatures: string[];
  category: { heading: string; description: string } | null;
  keys: { title: string; entries: { number: number; indentLevel: number; description: string; result: string | number; resultType: string }[] }[];
  items: PreviewItem[];
}
export interface Preview { generator: string; generatedAt: string; publications: PreviewPub[] }
