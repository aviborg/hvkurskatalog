import os
import json
import re
import time
import random
from dotenv import load_dotenv
from tqdm import tqdm
import pdfplumber
from jsonschema import validate
from openai import OpenAI, RateLimitError

# =========================
# CONFIG
# =========================

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY missing")

PDF_DIR = "public/kurskataloger"
TEXT_DIR = "extracted_text"
TEMPLATE_FILE = "data/hemvarn_course_templates_all.json"
SCHEMA_FILE = "data/course_template_schema.json"
OUTPUT_FILE = "data/hemvarn_course_templates_enriched.json"

MODEL = "gpt-4.1"
TEMPERATURE = 0.2
THROTTLE_SECONDS = 0.5

os.makedirs(TEXT_DIR, exist_ok=True)

client = OpenAI(api_key=OPENAI_API_KEY)

# =========================
# PDF → TEXT EXTRACTION
# =========================

def extract_pdf_to_text(pdf_name):
    txt_path = os.path.join(TEXT_DIR, pdf_name.replace(".pdf", ".txt"))
    pdf_path = os.path.join(PDF_DIR, pdf_name)

    if os.path.exists(txt_path):
        return

    print(f"[INFO] Extracting {pdf_name}")
    with pdfplumber.open(pdf_path) as pdf, open(txt_path, "w", encoding="utf-8") as out:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                out.write(f"\n=== PAGE {i+1} ===\n")
                out.write(text)
                out.write("\n")

# =========================
# ALIAS GENERATION
# =========================

def build_course_aliases(template):
    name = template["name"]
    short = template.get("shortName")

    aliases = {name.lower()}

    base = re.sub(r"\s+\d+.*$", "", name)
    aliases.update({
        f"{base}kurs".lower(),
        f"{base} kurs".lower(),
    })

    if short:
        aliases.add(short.lower())
        aliases.add(short.replace("-", "").lower())

    return aliases

# =========================
# LOAD SOURCE TEXT (BEST EFFORT)
# =========================

def load_source_text(template):
    collected = []
    aliases = build_course_aliases(template)

    for pdf in template["sourceFiles"]:
        extract_pdf_to_text(pdf)
        txt_path = os.path.join(TEXT_DIR, pdf.replace(".pdf", ".txt"))
        if not os.path.exists(txt_path):
            continue

        with open(txt_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        buffer = []
        capturing = False

        for line in lines:
            line_l = line.lower()

            if any(a in line_l for a in aliases):
                capturing = True
                buffer = [line]
                continue

            if capturing and re.match(r"^[A-ZÅÄÖ].{6,}$", line.strip()):
                break

            if capturing:
                buffer.append(line)

        if buffer:
            collected.append("".join(buffer))

    return "\n".join(collected)

# =========================
# MERGE LOGIC
# =========================

IMMUTABLE_FIELDS = {
    "id", "name", "shortName", "category",
    "courseResponsible", "baseTemplateIds", "sourceFiles"
}

def merge_templates(original, enriched):
    merged = original.copy()
    for key, value in enriched.items():
        if key in IMMUTABLE_FIELDS:
            continue
        if original.get(key) in ("", [], None) and value not in ("", [], None):
            merged[key] = value
    return merged

# =========================
# OPENAI CALL WITH RETRY
# =========================

def call_with_retry(messages, retries=5):
    for attempt in range(retries):
        try:
            return client.responses.create(
                model=MODEL,
                temperature=TEMPERATURE,
                input=messages
            )
        except RateLimitError:
            wait = 2 ** attempt + random.uniform(0, 1)
            print(f"[RATE LIMIT] sleeping {wait:.2f}s")
            time.sleep(wait)
    raise RuntimeError("Exceeded retry limit")

# =========================
# ENRICH TEMPLATE (NEW STRATEGY)
# =========================

SYSTEM_PROMPT = """
You are enriching Swedish Hemvärnet course templates.

You may use:
- Provided source text (if any)
- Well-established, widely accepted knowledge about Hemvärnet and Försvarsmakten courses

Rules:
- Write in Swedish.
- Be professional and concise.
- Prefer source text when available.
- If source text is missing or minimal, you MAY synthesize a reasonable high-level description.
- Do NOT invent highly specific details (exact hours, regulations, page numbers).
- Do NOT modify id, name, shortName, category, courseResponsible, baseTemplateIds, or sourceFiles.
- Output ONLY a single JSON object that conforms exactly to the CourseTemplate schema.
"""

EXAMPLE_TEMPLATE = {
    "id": "gruppchef-1",
    "name": "Gruppchefskurs 1",
    "shortName": "GC1",
    "category": "Chefsutbildningar",
    "courseCode": "MAHGK2011230",
    "description": "Kursen omfattar grundläggande gruppchefsutbildning där fokus ligger på orderträning, stridsteknik, beslutsfattning där teori varvas med praktiska övningar utomhus.",
    "targetAudience": "Avsedd för dig som är eller skall placeras i befattning som gruppchef/stf inom Hemvärnet.",
    "syllabus": "Grundläggande ledarskap, ordergivning, gruppens stridsteknik, soldatregler och tillämpade övningar.",
    "purpose": "Att deltagaren skall kunna verka som gruppchef/stf inom Hemvärnet eller frivilligorganisation.",
    "finalGoal": "Efter genomförd kurs ska deltagaren kunna verka som gruppchef inom Hemvärnet eller frivilligorganisation.",
    "subGoals": [
        "Förklara och utveckla gruppchefens roll, ansvar och utförande av befälsföring av grupp vid uppgifts lösande samt tillämpandet av soldatreglerna, FM Värdegrund och fysiskt stridsvärde.",
        "Förklara och använda högre chefs order i form av att ge order till egen grupp.",
        "Exemplifiera och använda stridsteknik enligt handbok hemvärnspluton-grupp vid framryckande och tagande av skyddsobjekt inom hemvärnsplutons ram.",
        "Beskriva upprättandet av förläggning, observationsplats och postställe.",
        "Definiera och beskriva hemvärnsplutonernas organisation och uppgifter."
        ],
    "examination": "Praktiskt lärande examinationer där elevens ordergivning vid nedbrytande av plutonchefs order, användande av OBO alternativt 5 punkts order enligt handbok och agerande i rollen som gruppchef utvärderas fortlöpande under kursen med tyngdpunkt på fältdygnen. Max 2 examinationstillfälle under kursen.",
    "prerequisites": [
        "VPL, GMU, eller GU.",
        "Genomfört kompetensprov Ak 4B/C.",
        "Fysisk status för att klara minst två fältdygn."
        ],
    "literature": "Handbok Hvplut/Hvgrp del 1-2, (Grunder och Objektet), MSR, FM Handböcker och reglementen",
    "additionalInfo": "Utbildning till gruppchef/stf omfattar två kurser; Gruppchefskurs1 och Gruppchefskurs 2. Gruppchefskurs 3 är endast avsedd för de som är eller skall bli chef/stf för en understödsgrupp.",
    "typicalDuration": "10 dagar om totalt 106 timmar.",
    "courseResponsible": "HvSS",
    "baseTemplateIds": [],
    "sourceFiles": [
        "hvss-kurskatalog-2023.pdf",
        "hvss-kurskatalog-2025.pdf"
      ]
}

def enrich_template(template, source_text, schema):
    user_payload = {
        "example": EXAMPLE_TEMPLATE,
        "template": template,
        "sourceText": source_text
    }

    response = call_with_retry([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)}
    ])

    raw = response.output_text.strip()
    if not raw:
        raise RuntimeError("Empty model response")

    parsed = json.loads(raw)

    parsed = {k: v for k, v in parsed.items() if k in schema["properties"]}
    validate(instance=parsed, schema=schema)
    return parsed

# =========================
# MAIN
# =========================

def main():
    with open(TEMPLATE_FILE, encoding="utf-8") as f:
        catalog = json.load(f)

    with open(SCHEMA_FILE, encoding="utf-8") as f:
        schema = json.load(f)

    for i, template in enumerate(tqdm(catalog["templates"], desc="Enriching")):
        if template.get("description"):
            continue

        source_text = load_source_text(template)

        enriched = enrich_template(template, source_text, schema)
        catalog["templates"][i] = merge_templates(template, enriched)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)

        time.sleep(THROTTLE_SECONDS)

    print("[DONE] Enrichment complete")

if __name__ == "__main__":
    main()
