# BiotaEditor

Checklist editor for TaiCOL nametool namespaces. A namespace published in nametool lands here by
webhook or manual import. Authors then pick voucher **specimens** from
[tbia-specimen-annotation (ISLAND)](../tbia-specimen-annotation) and **images** from iNaturalist /
TaiEOL, edit the text, and export **docx / pdf / json** (renderers ported from `../biota`).

FastAPI + SQLite (SQLAlchemy/Alembic) · React + Vite + TS · all in Docker.

## Run (dev)
```bash
cp .env.example .env          # fill TAICOL_TOKEN, TAIEOL_TOKEN, TBIA_API …
docker compose up --build     # web http://localhost:5180 · API http://localhost:8100/docs
docker compose exec api python -m app.cli createuser you@example.org 'password'   # or sign up in the UI
```
Sign in with the **same email as your TaiCOL account**: import and the webhook check namespace
ownership through `TAICOL_API/user/namespace?email=` (set `TAICOL_SKIP_OWNERSHIP=true` for local dev only).

Prod: `docker compose -f compose.prod.yml up -d --build` → nginx on :8080 serving the SPA and proxying `/api`. The prod image refuses to start
unless `.env` has a random `SECRET_KEY` of 32+ characters.

## Data flow
| Step | Endpoint | Upstream |
|---|---|---|
| nametool publishes | `POST /api/hooks` `{event, data:{email, namespace_id, name}}` (optional `WEBHOOK_SECRET`) | `TAICOL_API/biota?namespace_id=` |
| manual import / re-sync | `POST /api/publications/import`, `POST /api/publications/{id}/sync` | same |
| specimen candidates | `GET /api/items/{id}/specimen-candidates` | ISLAND `/api/occurrences?scientific_name=` (accepted name + synonyms, or `q=`) |
| image candidates | `GET /api/items/{id}/image-candidates?source=inat\|taieol` | iNat observations · TaiCOL name→taxon_id → TaiEOL |
| export | `GET /api/publications/{id}/export?format=docx\|pdf\|pdf2\|pdf3\|json` | figures are downloaded only from iNat/TaiEOL hosts |

A sync upserts by `name_id`. It **keeps** picked specimens and images, and any text field edited
locally. Use "Revert to TaiCOL" on a field to follow upstream again.

## Tests
```bash
docker build --target dev -t biotaeditor-api-dev backend && docker run --rm biotaeditor-api-dev python -m pytest -q
```

## License
MIT — see [LICENSE](LICENSE). Bundled PDF fonts are under the SIL Open Font License 1.1:
STIX Two Text (`backend/app/export/fonts/OFL-STIXTwoText.txt`) and Noto Serif TC
(`backend/app/export/fonts/OFL-NotoSerifTC.txt`).
