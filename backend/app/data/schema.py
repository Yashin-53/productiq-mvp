"""
Canonical Product Attribute Schema
-----------------------------------
This is the FIXED schema the AI pipeline fills in (analogous to Unilog's
252-column output template, scoped down to a demo-able MVP subset for the
"DIN-rail power supply" product category).

Every attribute below is filled with: value, unit (optional), source,
evidence snippet, and a confidence score - never a bare value. This mirrors
the hackathon's core requirement: no evidence -> no fact.
"""

BASE_FIELDS = [
    "part_number",
    "brand",
    "product_name",
    "category",
    "short_description",
]

# (key, label, unit_expected)
ATTRIBUTE_SCHEMA = [
    ("input_voltage", "Input Voltage", "V AC"),
    ("input_frequency", "Input Frequency", "Hz"),
    ("output_voltage", "Output Voltage", "V DC"),
    ("output_current", "Output Current", "A"),
    ("output_power", "Output Power", "W"),
    ("efficiency", "Efficiency", "%"),
    ("mounting_type", "Mounting Type", None),
    ("operating_temp", "Operating Temperature", None),
    ("dimensions", "Dimensions (L x W x H)", "mm"),
    ("weight", "Weight", "g"),
    ("protection_features", "Protection Features", None),
    ("certifications", "Certifications / Approvals", None),
    ("isolation_class", "Isolation Class", None),
    ("no_load_consumption", "No-Load Power Consumption", "W"),
    ("warranty", "Warranty", None),
]

FEATURE_FIELDS = ["key_features", "applications"]

DOCUMENT_FIELDS = [
    "datasheet_url",
    "manufacturer_product_page",
]

CONFIDENCE_BANDS = [
    (90, 100, "verified"),
    (75, 89, "high"),
    (55, 74, "needs_review"),
    (0, 54, "unverified"),
]


def confidence_band(score: float) -> str:
    for lo, hi, label in CONFIDENCE_BANDS:
        if lo <= score <= hi:
            return label
    return "unverified"
