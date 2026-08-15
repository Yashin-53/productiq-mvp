"""
Extraction service (Phase 4 of the pipeline: "AI extraction").

This module performs structured attribute extraction from each source
document's text. It is written as deterministic pattern extraction so the
whole pipeline runs with zero external dependencies / API keys out of the
box - but it is built to the exact contract an LLM-based extractor would
fulfil (see `llm_extract_stub` below), so swapping in a real LLM call
(OpenAI/Anthropic/etc.) for production is a one-function change, not an
architecture change.

Every extracted attribute keeps: value, unit, the source document it came
from, and the literal evidence snippet that supports it. Nothing is
returned without a supporting snippet.
"""

import os
import re
from typing import Optional

from app.data.schema import ATTRIBUTE_SCHEMA

CERT_KEYWORDS = ["CE", "RoHS", "UL508", "UL60950-1", "cULus", "UL", "CSA", "TUV", "CB"]
PROTECTION_KEYWORDS = [
    "short circuit",
    "overload",
    "over voltage",
    "overvoltage",
    "overcurrent",
    "overtemperature",
    "no-load proof",
]


def _find(pattern: str, text: str, flags=re.IGNORECASE) -> Optional[re.Match]:
    return re.search(pattern, text, flags)


def _snippet(text: str, match: re.Match, pad: int = 40) -> str:
    start = max(0, match.start() - pad)
    end = min(len(text), match.end() + pad)
    snippet = text[start:end].strip()
    return ("..." if start > 0 else "") + snippet + ("..." if end < len(text) else "")


def extract_from_document(text: str) -> dict:
    """
    Extract every attribute we can find evidence for in a single source
    document's text. Returns {attribute_key: {value, unit, evidence}}.
    """
    found = {}

    m = _find(r"(input(?: voltage)?[^.]{0,20}?)(\d{2,3}\s?[/\-to]{1,4}\s?\d{2,3}\s?V\s?AC)", text)
    if m:
        found["input_voltage"] = {"value": m.group(2).replace(" ", ""), "unit": "V AC", "evidence": _snippet(text, m)}

    m = _find(r"(\d{1,2})\s?A\s?/\s?60\s?Hz|50\s?/\s?60\s?Hz", text)
    if _find(r"50\s?/\s?60\s?Hz", text):
        m2 = _find(r"50\s?/\s?60\s?Hz", text)
        found["input_frequency"] = {"value": "50/60", "unit": "Hz", "evidence": _snippet(text, m2)}

    m = _find(r"(\d{1,3})\s?V\s?DC", text)
    if m:
        found["output_voltage"] = {"value": m.group(1), "unit": "V DC", "evidence": _snippet(text, m)}

    # output_current / output_power: scope the search to the sentence that
    # mentions "output" so a stray A/W elsewhere in the document (e.g. in a
    # product-type description) can't be misattributed to these fields.
    output_sentence = None
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        if re.search(r"\boutput\b", sentence, re.IGNORECASE):
            output_sentence = sentence
            break

    if output_sentence:
        m = _find(r"(\d+(?:\.\d+)?)\s?A\b(?!\w)", output_sentence)
        if m:
            found["output_current"] = {"value": m.group(1), "unit": "A", "evidence": _snippet(output_sentence, m)}

        m = _find(r"(\d{2,3})\s?W\b", output_sentence)
        if m:
            found["output_power"] = {"value": m.group(1), "unit": "W", "evidence": _snippet(output_sentence, m)}

    m = _find(r"efficiency[^.\d]{0,15}(\d{2}(?:\.\d+)?)\s?%", text)
    if m:
        found["efficiency"] = {"value": m.group(1), "unit": "%", "evidence": _snippet(text, m)}

    if re.search(r"din rail", text, re.IGNORECASE):
        m = _find(r"din rail", text)
        found["mounting_type"] = {"value": "DIN rail", "unit": None, "evidence": _snippet(text, m)}

    m = _find(r"-?\d+\s?C to \+?-?\d+\s?C", text)
    if m:
        found["operating_temp"] = {"value": m.group(0).replace(" ", ""), "unit": None, "evidence": _snippet(text, m)}

    m = _find(r"(\d{2,3})\s?x\s?(\d{2,3})\s?x\s?(\d{2,3})\s?mm", text)
    if m:
        found["dimensions"] = {"value": f"{m.group(1)} x {m.group(2)} x {m.group(3)}", "unit": "mm", "evidence": _snippet(text, m)}

    m = _find(r"weight[^.\d]{0,20}(\d{2,4})\s?g\b", text)
    if m:
        found["weight"] = {"value": m.group(1), "unit": "g", "evidence": _snippet(text, m)}

    protections = [kw for kw in PROTECTION_KEYWORDS if kw.lower() in text.lower()]
    if protections:
        m = _find(re.escape(protections[0]), text)
        found["protection_features"] = {"value": ", ".join(sorted(set(p.title() for p in protections))), "unit": None, "evidence": _snippet(text, m) if m else text[:80]}

    certs = [kw for kw in CERT_KEYWORDS if re.search(rf"\b{re.escape(kw)}\b", text, re.IGNORECASE)]
    if certs:
        m = _find(rf"\b{re.escape(certs[0])}\b", text)
        found["certifications"] = {"value": ", ".join(sorted(set(certs))), "unit": None, "evidence": _snippet(text, m) if m else text[:80]}

    m = _find(r"isolation class\s?(i{1,3}|ii)", text)
    if m:
        found["isolation_class"] = {"value": f"Class {m.group(1).upper()}", "unit": None, "evidence": _snippet(text, m)}

    m = _find(r"no-?load[^.\d]{0,20}(<?\s?\d+(?:\.\d+)?)\s?W", text)
    if m:
        found["no_load_consumption"] = {"value": m.group(1).replace(" ", ""), "unit": "W", "evidence": _snippet(text, m)}

    m = _find(r"warranty[^.\d]{0,10}(\d{1,2})\s?months?", text)
    if m:
        found["warranty"] = {"value": f"{m.group(1)} months", "unit": None, "evidence": _snippet(text, m)}

    return found


def llm_extract_stub(product: dict, documents: list) -> dict:
    """
    Placeholder for a production LLM-based extraction call.

    In production this function would call an LLM (Anthropic/OpenAI) with
    the retrieved document chunks and a structured-output prompt asking it
    to return {attribute: {value, unit, evidence, confidence}} JSON,
    constrained to only report values it can point to in the provided
    text (no external knowledge). Wire ANTHROPIC_API_KEY / OPENAI_API_KEY
    via environment variables and swap the body of this function -
    `pipeline.py` does not need to change.
    """
    if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("OPENAI_API_KEY"):
        return None  # signal: fall back to rule-based extraction
    raise NotImplementedError("Wire your LLM provider call here for production use.")
