from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import companies, enrich

app = FastAPI(title="Zetta Lead Enrichment", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(enrich.router, prefix="/api")
app.include_router(companies.router, prefix="/api")


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}
