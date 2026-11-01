import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import auth, export, hooks, items, keys, publications
from .config import settings

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="BiotaEditor API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_list, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"],
                   expose_headers=["Content-Disposition"])

for r in (auth, hooks, publications, items, export, keys):
    app.include_router(r.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
