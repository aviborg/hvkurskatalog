import os
import json
import re
import time
import random
from dotenv import load_dotenv
from tqdm import tqdm
import pdfplumber
from jsonschema import validate
from openai import OpenAI
from openai import RateLimitError

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

MODEL = "gpt-4.1-mini"
TEMPERATURE = 0.1
THROTTLE_SECONDS = 0.25

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
# COURSE NAME ALIASES
# =========================

def build_course_aliases(template):
    """
    Swedish-robust alias generation for HvSS / MR catalogs.
    """
    name = template["name"]
    short = template.get("shortName", "")

    aliases = set()

    # Base name
    aliases.add(name)

    # Remove trailing numbers
    base = re.sub(r"\s+\d+.*$", "", name)

    # kurs / skurs variants
    aliases.update({
        f"{base}kurs",
        f"{base}skurs",
        f"{base} kurs",
    })

    # Numbered courses
    m = re.search(r"(\d+\s*\+\s*\d+|\d+)", name)
    if m:
        num = m.group(1)
        aliases.update({
            f"{base}kurs {num}",
            f"{base}skurs {num}",
            f"{base} {num}",
        })

    # Instruktör special case
    if base.lower().startswith("instruktör"):
        aliases.add("instruktörskurs")

    # Abbreviations
    if short:
        aliases.add(short)
        aliases.add(short.replace("-", ""))

    return {a.lower() for a in aliases if a}

# =========================
# LOAD SOURCE TEXT (SECTION-BASED)
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

        capturing = False
        buffer = []

        for line in lines:
            line_l = line.lower()

            # Start capturing on header match
            if any(alias in line_l for alias in aliases):
                capturing = True
                buffer = [line]
                continue

            # Stop on next section header
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
# ENRICH TEMPLATE
# =========================

def enrich_template(template, source_text, schema):
    payload = {
        "template": template,
        "sourceText": source_text,
        "instructions": [
            "Populate only empty fields",
            "Use Swedish",
            "Use verbatim wording where possible",
            "If information is not found, leave the field empty",
            "Do not invent content",
            "Do not modify identifiers, names, short names or category",
            "Return ONLY the course template JSON object"
        ]
    }

    response = call_with_retry([
        {
            "role": "system",
            "content": (
                "You extract Hemvärnet course template data.\n"
                "Return ONLY a valid CourseTemplate JSON object.\n"
                "No wrappers, no explanations."
            )
        },
        {
            "role": "user",
            "content": json.dumps(payload, ensure_ascii=False)
        }
    ])

    raw = response.output_text.strip()
    if not raw:
        raise RuntimeError("Empty model response")

    parsed = json.loads(raw)

    if "template" in parsed and isinstance(parsed["template"], dict):
        parsed = parsed["template"]

    # Strip non-schema keys
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

        if not source_text.strip():
            print(f"[SKIP] No source text for {template['id']}")
            continue

        enriched = enrich_template(template, source_text, schema)
        catalog["templates"][i] = merge_templates(template, enriched)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)

        time.sleep(THROTTLE_SECONDS)

    print("[DONE] Enrichment complete")

if __name__ == "__main__":
    main()
