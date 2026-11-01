const en = {
  app: { name: "BiotaEditor", tagline: "Checklist editor for TaiCOL namespaces" },
  auth: {
    login: "Sign in", signup: "Create account", logout: "Sign out", email: "Email", password: "Password",
    name: "Name", emailHint: "Use the email of your TaiCOL nametool account — namespaces are matched by it.",
    toSignup: "No account yet? Create one", toLogin: "Have an account? Sign in",
  },
  pubs: {
    title: "Publications", empty: "No publications yet. Publish a namespace in TaiCOL nametool, or import one.",
    import: "Import namespace", namespaceId: "Namespace ID", available: "Your TaiCOL namespaces",
    imported: "imported", open: "Open", items: "{{n}} names", synced: "synced {{at}}", delete: "Delete",
    confirmDelete: "Delete this publication and all picked specimens/images?",
    loadAvailable: "Could not list namespaces from TaiCOL — enter an ID instead.",
  },
  status: { draft: "Draft", review: "In review", done: "Done" },
  editor: {
    back: "Publications", sync: "Sync from TaiCOL", syncing: "Syncing…",
    synced: "Synced: +{{created}} new, {{updated}} updated, −{{deleted}} removed",
    export: "Export", preview: "Preview", hidePreview: "Hide preview", literatures: "Literature",
    keys: "Identification keys", pick: "Pick a name on the left", filter: "Filter names…",
    title: "Title", author: "Author", save: "Save", saved: "Saved", cancel: "Cancel", addLit: "Add citation",
  },
  tabs: { text: "Text", specimens: "Specimens", images: "Images" },
  text: {
    common_names: "Common names (| separated)", description: "Description", distribution: "Distribution",
    note: "Note", synonyms: "Synonyms", edited: "edited locally", revert: "Revert to TaiCOL",
    usage: "Name usage", noSynonyms: "No synonyms",
  },
  spec: {
    picked: "Picked specimens ({{n}})", candidates: "From TBIA specimen annotation",
    byNames: "By name", byText: "Free text", search: "Search", names: "Names matched",
    none: "No specimens picked yet.", noResults: "No matching specimens.", total: "{{n}} records",
    add: "Add", added: "Added", remove: "Remove", more: "Load more", county: "County", typeStatus: "Type status",
    dataset: "Dataset", hasMedia: "Has image", open: "Open in ISLAND", reset: "Reset text",
    upstreamDown: "Specimen API unreachable: {{msg}}", clearFilters: "Clear filters",
  },
  img: {
    picked: "Picked images ({{n}})", source: "Source", inat: "iNaturalist", taieol: "TaiEOL",
    none: "No images picked yet.", noResults: "No images found.", more: "Load more", caption: "Caption",
    noLicense: "No CC licence — check before publishing", nameOverride: "Search name",
    taxon: "TaiCOL taxon {{id}}", open: "Source page",
  },
  keys: {
    new: "New key", title: "Key title", number: "No.", indent: "Indent", description: "Lead",
    goto: "→ couplet", result: "→ name", addEntry: "Add lead", delete: "Delete key", empty: "No keys yet.",
  },
  notif: { title: "Notifications", empty: "Nothing new", markRead: "Mark read" },
  common: { loading: "Loading…", error: "Error: {{msg}}", up: "Move up", down: "Move down", drag: "Drag to reorder" },
};
export default en;
export type Dict = typeof en;
