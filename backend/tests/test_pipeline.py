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


def test_dynamic_custom_product_extracts_from_pasted_evidence():
    """Regression test for the dynamic enrichment feature: a product the
    pipeline has NEVER seen before (not in SEED_PRODUCTS) must still be
    correctly enriched from pasted source text, proving the pipeline
    executes live rather than looking up a fixed catalog."""
    from app.services.ingestion import build_custom_product
    from app.services.pipeline import run_enrichment

    product = build_custom_product({
        "mfg_part_num": "REGTEST-0001",
        "part_desc": "Regression test fictional power supply",
        "part_manuf": "RegTestCorp",
        "documents": [{
            "source_name": "RegTestCorp datasheet",
            "source_type": "manufacturer_website",
            "text": "Input 90-260V AC. Output 12V DC, 4A, 48W. DIN rail mounting.",
        }],
    })
    result = run_enrichment(product)
    assert result["attributes"]["output_voltage"]["value"] == "12"
    assert result["attributes"]["mounting_type"]["value"] == "DIN rail"


def test_dynamic_product_with_zero_evidence_is_never_labeled_verified():
    """Regression test for a real bug: a product with NO source documents
    at all (nothing to extract from) was incorrectly showing status
    'verified' with 0% confidence - the single most misleading outcome
    possible for an evidence-backed system. A product with zero
    completeness must never be labeled verified."""
    from app.services.ingestion import build_custom_product
    from app.services.pipeline import run_enrichment

    product = build_custom_product({
        "mfg_part_num": "NO-EVIDENCE-REGTEST",
        "part_desc": "Product with no source documents provided",
    })
    result = run_enrichment(product)
    assert result["completeness_pct"] == 0.0
    assert result["status"] != "verified", "a product with zero evidence must never show as verified"
    assert result["status"] == "needs_review"


def test_bulk_csv_upload_parses_real_challenge_schema():
    """Regression test for bulk dynamic upload: must correctly parse the
    exact column names from the real challenge input schema
    (Mfg_Part_Num, Part_Desc, E1_Brand, Unilog_Brand, DIB_Brand,
    Part_Manuf) and produce one pipeline-ready product per row."""
    from app.services.ingestion import parse_bulk_csv

    csv_bytes = (
        "Mfg_Part_Num,Part_Desc,E1_Brand,Unilog_Brand,DIB_Brand,Part_Manuf\n"
        "ABC-123,Test widget one,-- Unbranded --,-- No Unilog Brand --,-- No DIB Brand --,Acme Corp\n"
        "XYZ-456,Test widget two,-- Unbranded --,-- No Unilog Brand --,-- No DIB Brand --,Acme Corp\n"
    ).encode("utf-8")

    products = parse_bulk_csv(csv_bytes)
    assert len(products) == 2
    assert products[0]["mfg_part_num"] == "ABC-123"
    assert products[0]["part_manuf"] == "Acme Corp"
    assert products[0]["documents"] == []


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


def test_placeholder_brand_tokens_are_not_treated_as_real_data():
    """Regression test: the real challenge dataset uses placeholder tokens
    like '-- Unbranded --', '-- No Unilog Brand --', '-- No DIB Brand --'
    to mean the field is EMPTY, not that the brand is literally named
    that. The solution guide explicitly warns these must be filtered out
    before matching - this test locks that behavior in."""
    from app.services.pipeline import normalize_brand

    result = normalize_brand("-- Unbranded --", "-- No Unilog Brand --", "-- No DIB Brand --", "Freud Inc (2435)")
    assert result == "Freud Inc (2435)"
    assert "--" not in result

    result2 = normalize_brand("-- Unbranded --", "", "", "")
    assert result2 == "Unknown"
    assert "--" not in result2

    result3 = normalize_brand("Meanwell", "", "", "")
    assert result3 == "Meanwell"


def test_bulk_upload_on_real_dataset_rows_is_honest_not_fabricated():
    """End-to-end regression test using ACTUAL rows from the challenge's
    real 1,000-item sample dataset (sanding belts / abrasive discs - not
    DIN-rail power supplies, and with no source documents attached).
    The pipeline must not fabricate DIN-rail specs for unrelated products,
    must not surface placeholder brand tokens as real data, and must
    honestly report 0% confidence rather than a hallucinated result."""
    from app.services.ingestion import parse_bulk_csv
    from app.services.pipeline import run_enrichment

    csv_bytes = (
        "Mfg_Part_Num,Part_Desc,E1_Brand,Unilog_Brand,DIB_Brand,Part_Manuf\n"
        'DCB518ASTS06G,"DCB518ASTS06G Diablo 1/2\\"x18\\" - Sanding Belt 6pc",'
        "-- Unbranded --,-- No Unilog Brand --,-- No DIB Brand --,Freud Inc (2435)\n"
    ).encode("utf-8")

    products = parse_bulk_csv(csv_bytes)
    result = run_enrichment(products[0])

    assert result["overall_confidence"] == 0.0
    assert result["status"] == "needs_review"
    assert result["brand"] == "Freud Inc (2435)"
    assert result["category"] == "Uncategorized (taxonomy classification not implemented in this MVP)"
    for attr in result["attributes"].values():
        assert attr["value"] is None
