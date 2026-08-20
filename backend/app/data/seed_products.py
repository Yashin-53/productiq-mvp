"""
Seed dataset for the ProductIQ MVP.

Each entry represents exactly what the hackathon input looks like: a
sparse product record (part number, brand, short description). Attached
to it are one or more "captured source documents" - short, paraphrased
evidence snippets standing in for what a live manufacturer-site/PDF
crawl (Phase 3 in production) would retrieve. The extraction/validation
pipeline (services/pipeline.py) reads ONLY these documents to fill the
schema - it never invents values that aren't traceable to a source.

Product #1 (Mean Well HDR-60-24) evidence was compiled from public
manufacturer/distributor listings. The remaining products use
representative, industry-typical specifications for this same product
class so the pipeline can be demoed end-to-end; in production, Phase 3
(source discovery) replaces this seed step with live retrieval from
manufacturer websites and PDFs.
"""

SEED_PRODUCTS = [
    {
        "id": "P001",
        "mfg_part_num": "HDR-60-24",
        "part_desc": "HDR-60-24 Ultra Slim DIN Rail Power Supply",
        "e1_brand": "Meanwell",
        "unilog_brand": "MEAN WELL",
        "dib_brand": "Mean Well Enterprises",
        "part_manuf": "MEAN WELL",
        "documents": [
            {
                "source_name": "Manufacturer product page (meanwell-web.com)",
                "source_url": "https://www.meanwell-web.com/en/mean-well-hdr-60-24-hdr-60-24",
                "source_type": "manufacturer_website",
                "reliability": "very_high",
                "text": (
                    "AC-DC ultra slim DIN rail power supply. Input range 85-264V AC. "
                    "Output 24V DC at 2.5A. Dimensions L x W x H: 90 x 55 x 53 mm. "
                    "Mounting: DIN rail. Warranty: 36 months."
                ),
            },
            {
                "source_name": "Authorized distributor spec sheet (Newark/RS/Jameco composite)",
                "source_url": "https://www.digikey.com/en/products/detail/mean-well-usa-inc/HDR-60-24/7703804",
                "source_type": "distributor",
                "reliability": "high",
                "text": (
                    "HDR-60-24: single output industrial AC-DC converter, 60W, DIN rail "
                    "package. Input 85-264V AC. Output 24V DC, 2.5A, adjustable +-10%. "
                    "Efficiency up to 91%. No-load consumption under 0.3W. Operating "
                    "temperature -30C to +70C, fanless. Isolation Class II. Protections: "
                    "short circuit, overload, over voltage. Approvals: UL508, "
                    "UL60950-1, TUV EN61558-2-16, CB, CE. Complies with EN61000-3-2 "
                    "Class A."
                ),
            },
        ],
    },
    {
        "id": "P002",
        "mfg_part_num": "ABL8REM24030",
        "part_desc": "ABL8REM24030 Regulated Power Supply 100-240V AC 24V DC 3A",
        "e1_brand": "Schneider",
        "unilog_brand": "Schneider Electric",
        "dib_brand": "Schneider Electric SE",
        "part_manuf": "Schneider Electric",
        "documents": [
            {
                "source_name": "Manufacturer datasheet (se.com)",
                "source_url": "https://www.se.com/ww/en/product/ABL8REM24030/regulated-smps---1-or-2-phase---100..240-v-ac---24-v---3-a/",
                "source_type": "manufacturer_website",
                "reliability": "very_high",
                "text": (
                    "Phaseo ABL8 regulated switch mode power supply, single phase. "
                    "Input voltage 100-240V AC, 50/60Hz. Output 24V DC, 3A, 72W. "
                    "Efficiency approximately 87%. Operating temperature -10C to +60C. "
                    "Mounting: symmetrical DIN rail (35mm). Dimensions approximately "
                    "45 x 121 x 108 mm. Weight approximately 350g. Protections: short "
                    "circuit, overload, overvoltage. Certifications: CE, UL, CSA, "
                    "RoHS."
                ),
            },
            {
                "source_name": "Manufacturer catalog PDF excerpt",
                "source_url": "https://www.se.com/ww/en/product/ABL8REM24030/regulated-smps---1-or-2-phase---100..240-v-ac---24-v---3-a/",
                "source_type": "manufacturer_pdf",
                "reliability": "very_high",
                "text": (
                    "ABL8REM24030 - output current 3A, output power 72W, isolation "
                    "class II, warranty 24 months. Approvals include CE marking and "
                    "UL508 listing."
                ),
            },
        ],
    },
    {
        "id": "P003",
        "mfg_part_num": "QUINT4-PS/1AC/24DC/5",
        "part_desc": "QUINT4-PS/1AC/24DC/5 Primary-switched DIN rail power supply",
        "e1_brand": "Phoenix",
        "unilog_brand": "Phoenix Contact",
        "dib_brand": "Phoenix Contact GmbH",
        "part_manuf": "Phoenix Contact",
        "documents": [
            {
                "source_name": "Manufacturer product page (phoenixcontact.com)",
                "source_url": "https://www.phoenixcontact.com/en-us/products/power-supply-quint4-ps1ac24dc5-2904600",
                "source_type": "manufacturer_website",
                "reliability": "very_high",
                "text": (
                    "QUINT4-PS primary-switched power supply. Input 100-240V AC, "
                    "50/60Hz. Output 24V DC, 5A, 120W. Efficiency approx 93.5%. "
                    "Operating temperature -25C to +70C. DIN rail mounting (NS 35). "
                    "Dimensions approximately 60 x 130 x 125 mm. Weight approximately "
                    "480g. SFB (selective fuse breaking) technology for reliable "
                    "circuit breaker tripping. Certifications: UL508, cULus, CE, "
                    "RoHS."
                ),
            }
        ],
    },
    {
        "id": "P004",
        "mfg_part_num": "PSU100C-6EP1332",
        "part_desc": "SITOP PSU100C 24V/2.5A stabilized power supply",
        "e1_brand": "Siemens",
        "unilog_brand": "Siemens",
        "dib_brand": "Siemens AG",
        "part_manuf": "Siemens",
        "documents": [
            {
                "source_name": "Manufacturer datasheet (siemens.com)",
                "source_url": "https://i.siemens.com/1P6EP1332-5BA00",
                "source_type": "manufacturer_website",
                "reliability": "very_high",
                "text": (
                    "SITOP PSU100C, stabilized power supply, input 120/230V AC "
                    "(setting via switch), output 24V DC, 2.5A. Operating temperature "
                    "-25C to +70C. Mounting: DIN rail. Dimensions approximately "
                    "70 x 125 x 125 mm. Protections: short-circuit and no-load proof. "
                    "Certifications: CE, UL, CSA, RoHS."
                ),
            },
            {
                "source_name": "Distributor listing",
                "source_url": "https://www.kempstoncontrols.com/6EP1332-5BA00/Siemens/sku/404701",
                "source_type": "distributor",
                "reliability": "medium",
                "text": (
                    "SITOP PSU100C 24V/2.5A - weight approximately 600g. Output "
                    "power 60W. Warranty 12 months."
                ),
            },
            {
                "source_name": "Third-party technical database",
                "source_url": "https://www.mouser.com/en/new/siemens/siemens-sitop-psu100c-power-supplies",
                "source_type": "third_party",
                "reliability": "medium",
                "text": (
                    "SITOP PSU100C 24V/2.5A - weight listed as 750g in some regional "
                    "catalogs; output power 60W."
                ),
            },
        ],
    },
    {
        "id": "P005",
        "mfg_part_num": "S8VK-G12024",
        "part_desc": "S8VK-G 120W 24VDC Switch Mode Power Supply",
        "e1_brand": "Omron",
        "unilog_brand": "OMRON",
        "dib_brand": "Omron Corporation",
        "part_manuf": "Omron",
        "documents": [
            {
                "source_name": "Manufacturer product page (industrial.omron.com)",
                "source_url": "https://automation.omron.com/en/us/products/family/S8VKG/s8vk-g12024",
                "source_type": "manufacturer_website",
                "reliability": "very_high",
                "text": (
                    "S8VK-G series switch mode power supply. Input 100-240V AC "
                    "(85-264V AC). Output 24V DC, 5A, 120W. Efficiency approx 91%. "
                    "Operating temperature -25C to +70C. DIN rail mounting. "
                    "Dimensions approximately 50 x 125 x 121 mm. Weight approximately "
                    "480g. Protections: overcurrent, overvoltage, overtemperature. "
                    "Certifications: UL508, CE, RoHS."
                ),
            }
        ],
    },
    {
        "id": "P006",
        "mfg_part_num": "MDR-40-24",
        "part_desc": "MDR-40-24 Mini DIN Rail Power Supply 24V 1.7A",
        "e1_brand": "Meanwell",
        "unilog_brand": "MEAN WELL",
        "dib_brand": "Mean Well Enterprises",
        "part_manuf": "MEAN WELL",
        "documents": [
            {
                "source_name": "Manufacturer product page",
                "source_url": "https://www.meanwell.com/webapp/product/search.aspx?prod=MDR-40",
                "source_type": "manufacturer_website",
                "reliability": "very_high",
                "text": (
                    "MDR-40-24 mini DIN rail power supply, input 85-264V AC, output "
                    "24V DC 1.7A (40W). Operating temperature -20C to +70C. "
                    "Dimensions approximately 40 x 125 x 100 mm. Mounting: DIN rail. "
                    "Certifications: UL508, CE, RoHS."
                ),
            }
        ],
    },
]
