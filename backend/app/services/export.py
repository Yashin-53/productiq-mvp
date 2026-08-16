"""
CSV export service.

Maps ProductIQ's enriched product records onto column names taken
directly from Unilog's real expected-output template (the 252-column
delivery format). We don't populate all 252 columns in this MVP -
that's explicitly out of scope per the challenge's own guidance to
"go narrower" for the prototype - but every column we DO emit uses
Unilog's exact header naming, so the export is a genuine subset of
their real target format rather than an ad-hoc shape.

Columns emitted:
  - Identity: PART_NUMBER, MANUFACTURER_PART_NUMBER, MANUFACTURER_NAME,
    BRAND_NAME, SHORT_DESC
  - Up to 15 ATTRIBUTE_LABEL / ATTRIBUTE_VALUE / ATTRIBUTE_UOM triplets,
    matching the real template's repeating attribute-slot pattern
    (the real template goes up to 50 slots; we use 15 to match our
    MVP schema 1:1)
  - ProductIQ-specific provenance columns (prefixed PRODUCTIQ_) that
    the real template doesn't have, but that make the evidence-backed
    claim auditable in the exported file itself: confidence, status,
    and source document names per row.
"""

import csv
import io

from app.data.schema import ATTRIBUTE_SCHEMA


def _product_row(product: dict) -> dict:
    row = {
        "PART_NUMBER": product["part_number"],
        "MANUFACTURER_PART_NUMBER": product["part_number"],
        "MANUFACTURER_NAME": product["brand"],
        "BRAND_NAME": product["brand"],
        "SHORT_DESC": product["short_description"],
        "PRODUCTIQ_CATEGORY": product["category"],
        "PRODUCTIQ_STATUS": product["status"],
        "PRODUCTIQ_OVERALL_CONFIDENCE": product["overall_confidence"],
        "PRODUCTIQ_COMPLETENESS_PCT": product["completeness_pct"],
        "PRODUCTIQ_SOURCE_DOCUMENTS": "; ".join(d["source_name"] for d in product["source_documents"]),
    }

    for i, (key, label, _unit) in enumerate(ATTRIBUTE_SCHEMA, start=1):
        attr = product["attributes"][key]
        row[f"ATTRIBUTE_LABEL {i}"] = label
        row[f"ATTRIBUTE_VALUE {i}"] = attr["value"] or ""
        row[f"ATTRIBUTE_UOM {i}"] = attr["unit"] or ""

    return row


def export_products_csv(products: list) -> str:
    if not products:
        return ""

    fieldnames = list(_product_row(products[0]).keys())
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for p in products:
        writer.writerow(_product_row(p))

    return buffer.getvalue()
