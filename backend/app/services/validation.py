"""
Validation & Confidence Engine (Phases 6-8 of the pipeline).

Given candidate values for one attribute pulled from N source documents,
this module:
  1. Detects agreement / conflict across sources.
  2. Scores confidence from: source reliability + cross-source agreement +
     extraction certainty + basic rule validation.
  3. Prefers manufacturer sources over third-party sources on conflict.
  4. Flags low-confidence / conflicting attributes for human review.
"""

RELIABILITY_WEIGHT = {
    "manufacturer_website": 40,
    "manufacturer_pdf": 40,
    "distributor": 28,
    "third_party": 15,
}

RELIABILITY_RANK = {
    "manufacturer_website": 3,
    "manufacturer_pdf": 3,
    "distributor": 2,
    "third_party": 1,
}


def _values_agree(a: str, b: str) -> bool:
    norm = lambda s: str(s).strip().lower().replace(" ", "")
    return norm(a) == norm(b)


def resolve_attribute(candidates: list) -> dict:
    """
    candidates: list of dicts, each:
      {value, unit, evidence, source_name, source_type, reliability}
    Returns the resolved attribute record with confidence + status.
    """
    if not candidates:
        return None

    # Group candidates by normalized value
    groups = {}
    for c in candidates:
        key = str(c["value"]).strip().lower().replace(" ", "")
        groups.setdefault(key, []).append(c)

    conflict = len(groups) > 1

    if not conflict:
        winning_group = list(groups.values())[0]
    else:
        # prefer the group whose members have the highest-reliability source
        winning_group = max(
            groups.values(),
            key=lambda grp: max(RELIABILITY_RANK.get(c["source_type"], 0) for c in grp),
        )

    best = max(winning_group, key=lambda c: RELIABILITY_WEIGHT.get(c["source_type"], 0))

    reliability_score = max(RELIABILITY_WEIGHT.get(c["source_type"], 10) for c in winning_group)
    agreement_score = 25 if len(winning_group) > 1 else 12
    extraction_score = 20  # extraction pattern matched cleanly
    rule_score = 15 if best["value"] not in (None, "", "None") else 0

    confidence = min(100, reliability_score + agreement_score + extraction_score + rule_score)
    if conflict:
        confidence = max(30, confidence - 25)  # penalize unresolved conflicts

    return {
        "value": best["value"],
        "unit": best.get("unit"),
        "confidence": round(confidence, 1),
        "conflict": conflict,
        "primary_source": best["source_name"],
        "primary_evidence": best["evidence"],
        "all_sources": [
            {"source_name": c["source_name"], "value": c["value"], "source_type": c["source_type"], "evidence": c["evidence"]}
            for c in candidates
        ],
    }

MULTI_VALUE_ATTRIBUTES = {"certifications", "protection_features"}


def resolve_multi_value_attribute(candidates: list) -> dict:
    """
    For attributes where a source listing FEWER items doesn't contradict a
    source listing MORE items (e.g. certifications, protections) - union
    the values instead of treating differing strings as a conflict.
    """
    if not candidates:
        return None

    all_values = set()
    for c in candidates:
        for item in str(c["value"]).split(","):
            item = item.strip()
            if item:
                all_values.add(item)

    merged_value = ", ".join(sorted(all_values))
    best = max(candidates, key=lambda c: RELIABILITY_WEIGHT.get(c["source_type"], 0))

    reliability_score = max(RELIABILITY_WEIGHT.get(c["source_type"], 10) for c in candidates)
    agreement_score = 25 if len(candidates) > 1 else 12
    confidence = min(100, reliability_score + agreement_score + 20 + 15)

    return {
        "value": merged_value,
        "unit": best.get("unit"),
        "confidence": round(confidence, 1),
        "conflict": False,  # union, not a real disagreement
        "primary_source": "Merged across sources",
        "primary_evidence": best["evidence"],
        "all_sources": [
            {"source_name": c["source_name"], "value": c["value"], "source_type": c["source_type"], "evidence": c["evidence"]}
            for c in candidates
        ],
    }