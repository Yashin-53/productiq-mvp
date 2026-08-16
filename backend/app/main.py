import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from app.data.seed_products import SEED_PRODUCTS
from app.services.pipeline import run_enrichment
from app.services.export import export_products_csv

app = FastAPI(title="ProductIQ API", version="0.1.0")

# In production, set ALLOWED_ORIGINS to your deployed frontend URL(s),
# comma-separated (e.g. "https://productiq.vercel.app"). Defaults to "*"
# for local development so nothing breaks if it's unset.
_allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "*")
allow_origins = ["*"] if _allowed_origins_env == "*" else [o.strip() for o in _allowed_origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store: enriched on first access, cached after that.
_ENRICHED_CACHE = {}


def _get_seed(product_id: str):
    for p in SEED_PRODUCTS:
        if p["id"] == product_id:
            return p
    return None


def _enrich_and_cache(product_id: str):
    if product_id in _ENRICHED_CACHE:
        return _ENRICHED_CACHE[product_id]
    seed = _get_seed(product_id)
    if not seed:
        return None
    result = run_enrichment(seed)
    _ENRICHED_CACHE[product_id] = result
    return result


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/export/csv")
def export_csv():
    """
    Export all enriched products as CSV, using column names drawn from
    Unilog's real expected-output template (see app/services/export.py
    for the exact mapping and what's in/out of MVP scope).
    """
    results = [_enrich_and_cache(p["id"]) for p in SEED_PRODUCTS]
    csv_text = export_products_csv(results)
    return PlainTextResponse(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=productiq_export.csv"},
    )


@app.get("/api/products")
def list_products():
    """Dashboard list view - enriches every seed product (cached)."""
    results = [_enrich_and_cache(p["id"]) for p in SEED_PRODUCTS]
    return {
        "total": len(results),
        "verified": len([r for r in results if r["status"] == "verified"]),
        "needs_review": len([r for r in results if r["status"] == "needs_review"]),
        "avg_confidence": round(sum(r["overall_confidence"] for r in results) / len(results), 1) if results else 0,
        "products": results,
    }


@app.get("/api/products/candidates")
def list_candidates():
    """Un-enriched input rows, for the 'Enrich Product' picker screen."""
    return [
        {
            "id": p["id"],
            "mfg_part_num": p["mfg_part_num"],
            "part_desc": p["part_desc"],
            "brand": p["unilog_brand"] or p["e1_brand"],
        }
        for p in SEED_PRODUCTS
    ]


@app.post("/api/products/{product_id}/enrich")
def enrich_product(product_id: str):
    seed = _get_seed(product_id)
    if not seed:
        raise HTTPException(status_code=404, detail="Product not found")
    _ENRICHED_CACHE.pop(product_id, None)  # force re-run
    result = _enrich_and_cache(product_id)
    return result


@app.get("/api/products/{product_id}")
def get_product(product_id: str):
    result = _enrich_and_cache(product_id)
    if not result:
        raise HTTPException(status_code=404, detail="Product not found")
    return result


@app.get("/api/review-queue")
def review_queue():
    results = [_enrich_and_cache(p["id"]) for p in SEED_PRODUCTS]
    queue = []
    for r in results:
        for key in r["review_needed"]:
            attr = r["attributes"][key]
            queue.append({
                "product_id": r["id"],
                "part_number": r["part_number"],
                "attribute_key": key,
                "attribute_label": attr["label"],
                "value": attr["value"],
                "confidence": attr["confidence"],
                "conflict": attr["conflict"],
                "all_sources": attr["all_sources"],
            })
    return {"count": len(queue), "items": queue}


@app.post("/api/review/{product_id}/{attribute_key}")
def resolve_review(product_id: str, attribute_key: str, decision: dict):
    """decision: {'action': 'accept' | 'reject', 'value': optional override}"""
    result = _enrich_and_cache(product_id)
    if not result or attribute_key not in result["attributes"]:
        raise HTTPException(status_code=404, detail="Attribute not found")
    attr = result["attributes"][attribute_key]
    action = decision.get("action", "accept")
    if action == "accept":
        attr["confidence"] = 100.0
        attr["status"] = "verified"
        attr["conflict"] = False
    elif action == "reject":
        attr["value"] = None
        attr["status"] = "not_found"
    elif action == "edit" and "value" in decision:
        attr["value"] = decision["value"]
        attr["confidence"] = 100.0
        attr["status"] = "verified"
        attr["conflict"] = False
    if attribute_key in result["review_needed"]:
        result["review_needed"].remove(attribute_key)
    result["status"] = "needs_review" if result["review_needed"] else "verified"
    return result
