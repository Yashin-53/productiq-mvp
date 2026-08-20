"""
Enrichment pipeline orchestrator.

    Minimal input
        -> Normalize input (Phase 5)
        -> Source discovery                (seed documents stand in here)
        -> Document processing             (already-captured text)
        -> AI extraction (Phase 4)         extraction.py
        -> Multi-source validation         validation.py
        -> Confidence scoring              validation.py
        -> Human review queue (Phase 8)    status field surfaced to API
        -> Enriched product profile
"""

import re

from app.data.schema import ATTRIBUTE_SCHEMA, confidence_band
from app.services.extraction import extract_from_document, llm_extract_stub
from app.services.validation import resolve_attribute, resolve_multi_value_attribute, MULTI_VALUE_ATTRIBUTES

# The real challenge dataset uses placeholder tokens like "-- Unbranded --",
# "-- No Unilog Brand --", "-- No DIB Brand --" to mean the field is EMPTY,
# not that the brand is literally named "-- Unbranded --". The solution
# guide explicitly warns: "Placeholders are not data... filter them out
# before matching or prompting." Any token of the shape "-- ... --" is
# treated as empty here, regardless of the exact wording inside.
_PLACEHOLDER_PATTERN = re.compile(r"^--.*--$")


def _is_placeholder(value: str) -> bool:
    return bool(_PLACEHOLDER_PATTERN.match(value.strip())) if value else True


def normalize_brand(raw_e1, raw_unilog, raw_dib, raw_part_manuf=None):
    """
    Collapse brand-alias variants (e.g. 'Meanwell' vs 'MEAN WELL') into one
    canonical brand, filtering out placeholder tokens rather than treating
    them as real brand names. Falls back to the distributor/manufacturer
    field (Part_Manuf) if every brand field is empty/placeholder - still
    real data, unlike "-- Unbranded --".
    """
    candidates = [raw_unilog, raw_e1, raw_dib]
    for c in candidates:
        if c and not _is_placeholder(c):
            return c.strip()
    if raw_part_manuf and not _is_placeholder(raw_part_manuf):
        return raw_part_manuf.strip()
    return "Unknown"


def run_enrichment(product: dict) -> dict:
    part_number = product["mfg_part_num"]
    brand = normalize_brand(product.get("unilog_brand"), product.get("e1_brand"), product.get("dib_brand"), product.get("part_manuf"))
    documents = product["documents"]

    # --- AI extraction step (per document) ---
    llm_result = llm_extract_stub(product, documents)
    per_doc_candidates = {}  # attribute -> [candidate, ...]

    if llm_result is not None:
        per_doc_candidates = llm_result
    else:
        for doc in documents:
            extracted = extract_from_document(doc["text"])
            for attr_key, payload in extracted.items():
                per_doc_candidates.setdefault(attr_key, []).append({
                    "value": payload["value"],
                    "unit": payload["unit"],
                    "evidence": payload["evidence"],
                    "source_name": doc["source_name"],
                    "source_type": doc["source_type"],
                    "reliability": doc["reliability"],
                    "source_url": doc.get("source_url"),
                })

    # --- Validation + confidence scoring ---
    resolved_attributes = {}
    review_needed = []
    for key, label, expected_unit in ATTRIBUTE_SCHEMA:
        candidates = per_doc_candidates.get(key)
        if candidates and key in MULTI_VALUE_ATTRIBUTES:
            resolved = resolve_multi_value_attribute(candidates)
        elif candidates:
            resolved = resolve_attribute(candidates)
        else:
            resolved = None
        if resolved:
            resolved["label"] = label
            resolved["status"] = confidence_band(resolved["confidence"])
            resolved["key"] = key
            if resolved["conflict"] or resolved["confidence"] < 75:
                review_needed.append(key)
        else:
            resolved = {
                "key": key,
                "label": label,
                "value": None,
                "unit": expected_unit,
                "confidence": 0,
                "status": "not_found",
                "conflict": False,
                "primary_source": None,
                "primary_evidence": None,
                "all_sources": [],
            }
        resolved_attributes[key] = resolved

    found_values = [a for a in resolved_attributes.values() if a["value"] is not None]
    overall_confidence = round(
        sum(a["confidence"] for a in found_values) / max(1, len(found_values)),
        1,
    )
    completeness = round(
        100 * len(found_values) / len(ATTRIBUTE_SCHEMA), 1
    )
    if not found_values:
        review_needed = list(resolved_attributes.keys())

    return {
        "id": product["id"],
        "part_number": part_number,
        "brand": brand,
        "product_name": f"{part_number} {product['part_desc'].replace(part_number, '').strip()}".strip(),
        "short_description": product["part_desc"],
        "category": product.get("category", "DIN-Rail Power Supply"),
        "attributes": resolved_attributes,
        "overall_confidence": overall_confidence,
        "completeness_pct": completeness,
        "review_needed": review_needed,
        "status": "needs_review" if review_needed else "verified",
        "source_documents": [
            {"source_name": d["source_name"], "source_type": d["source_type"], "reliability": d["reliability"], "source_url": d.get("source_url")}
            for d in documents
        ],
    }
