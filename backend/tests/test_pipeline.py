import re

from app.data.seed_products import SEED_PRODUCTS
from app.services.extraction import extract_from_document
from app.services.pipeline import run_enrichment


def _all_results():
    return {product["id"]: run_enrichment(product) for product in SEED_PRODUCTS}


def test_catalog_size():
    assert len(SEED_PRODUCTS) == 6


def test_overall_counts():
    results = _all_results()
    verified = sum(1 for result in results.values() if result["status"] == "verified")
    needs_review = sum(1 for result in results.values() if result["status"] == "needs_review")
    assert verified == 5
    assert needs_review == 1


def test_avg_confidence_in_expected_range():
    results = _all_results().values()
    avg = sum(result["overall_confidence"] for result in results) / len(SEED_PRODUCTS)
    assert 80 <= avg <= 90


def test_siemens_weight_conflict_detected():
    result = run_enrichment(next(product for product in SEED_PRODUCTS if product["id"] == "P004"))
    assert result["attributes"]["weight"]["conflict"] is True
    assert "weight" in result["review_needed"]


def test_certifications_are_unioned_not_conflicted():
    p001 = run_enrichment(next(product for product in SEED_PRODUCTS if product["id"] == "P001"))
    p002 = run_enrichment(next(product for product in SEED_PRODUCTS if product["id"] == "P002"))

    p001_cert = p001["attributes"]["certifications"]
    p002_cert = p002["attributes"]["certifications"]

    assert p001_cert["conflict"] is False
    assert "UL" in p001_cert["value"]
    assert "UL60950-1" in p001_cert["value"]

    assert p002_cert["conflict"] is False
    assert "CSA" in p002_cert["value"]
    assert "UL508" in p002_cert["value"]


def test_output_current_and_power_scoped_to_output_context():
    text = (
        "The device is a 24V DIN-rail supply. Model family 40W, 3A variant. "
        "Output 24V DC at 2.5A, 60W. The power module is 40W in the product label."
    )
    extracted = extract_from_document(text)

    assert extracted["output_current"]["value"] == "2.5"
    assert extracted["output_power"]["value"] == "60"


def test_no_attribute_returned_without_evidence():
    extracted = extract_from_document("No field matches this sentence. Some generic text without values.")
    assert extracted == {}


def test_csv_export_produces_valid_rows():
    """Regression test for the CSV export feature: output should parse
    cleanly and preserve the resolved (post-validation) values, including
    the genuine Siemens weight conflict resolving to the manufacturer-
    priority value rather than an empty or garbled cell."""
    import csv
    import io
    from app.services.export import export_products_csv

    results = list(_all_results().values())
    csv_text = export_products_csv(results)

    reader = csv.DictReader(io.StringIO(csv_text))
    rows = list(reader)
    assert len(rows) == 6

    siemens_row = next(r for r in rows if r["PART_NUMBER"] == "PSU100C-6EP1332")
    assert siemens_row["PRODUCTIQ_STATUS"] == "needs_review"
    weight_idx = next(
        i for i, (key, _label, _unit) in enumerate(
            __import__("app.data.schema", fromlist=["ATTRIBUTE_SCHEMA"]).ATTRIBUTE_SCHEMA, start=1
        ) if key == "weight"
    )
    assert siemens_row[f"ATTRIBUTE_VALUE {weight_idx}"] == "600"
