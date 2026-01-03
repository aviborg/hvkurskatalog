import os
from dotenv import load_dotenv
import json
import re
from tqdm import tqdm
import pdfplumber
from jsonschema import validate
from openai import OpenAI

# =========================
# CONFIG
# =========================
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PDF_DIR = "public/kurskataloger"
TEXT_DIR = "extracted_text"
TEMPLATE_FILE = "data/hemvarn_course_templates_all.json"
SCHEMA_FILE = "data/course_template_schema.json"
OUTPUT_FILE = "data/hemvarn_course_templates_enriched.json"

MODEL = "gpt-4.1-mini"
TEMPERATURE = 0.1

os.makedirs(TEXT_DIR, exist_ok=True)

client = OpenAI()

# =========================
# PDF → TEXT EXTRACTION
# =========================

def build_course_aliases(template):
    """
    Generate plausible name variants as they appear in PDFs.
    """
    name = template["name"]

    aliases = {name}

    # Add "kurs" variants
    aliases.add(f"{name}kurs")
    aliases.add(f"{name} kurs")

    # Handle numbered courses: Gruppchef 1 → Gruppchefskurs 1
    parts = name.split()
    if parts[-1].isdigit():
        aliases.add(f"{parts[0]}kurs {parts[-1]}")
        aliases.add(f"{parts[0]} kurs {parts[-1]}")

    # Handle "1 + 2" merged courses
    if "+" in name:
        base = name.split("+")[0].strip()
        aliases.add(f"{base}kurs")

    return {a.lower() for a in aliases}

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
                out.write(f"\n\n=== PAGE {i+1} ===\n")
                out.write(text)

# =========================
# LOAD SOURCE TEXT
# =========================

def load_source_text(template):
    collected = []

    for pdf in template["sourceFiles"]:
        extract_pdf_to_text(pdf)
        txt_path = os.path.join(TEXT_DIR, pdf.replace(".pdf", ".txt"))

        if not os.path.exists(txt_path):
            continue

        with open(txt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Keep only paragraphs mentioning the course
        blocks = content.split("\n\n")

        aliases = build_course_aliases(template)

        for block in blocks:
            block_lower = block.lower()
            if any(alias in block_lower for alias in aliases):
                collected.append(block)

    return "\n\n".join(collected)

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
# CHATGPT ENRICHMENT
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
            "Output ONLY valid JSON that conforms to the course template schema"
        ]
    }

    response = client.responses.create(
        model=MODEL,
        temperature=TEMPERATURE,
        input=[
            {
              "role": "system",
              "content": (
                "You are extracting Hemvärnet course template data.\n"
                "You MUST return ONLY a single JSON object that conforms to the CourseTemplate schema.\n"
                "Do NOT include keys like 'template', 'sourceText', 'instructions', or explanations.\n"
                "Return ONLY the populated course template object."
              )
            },
            {
                "role": "user",
                "content": json.dumps(payload, ensure_ascii=False)
            }
        ]
    )

    # ---- Parse output safely ----
    raw_text = response.output_text.strip()

    if not raw_text:
        raise RuntimeError("Empty response from model")

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON returned:\n{raw_text}") from e

    # ---- IMPORTANT PART ----
    # If the model wrapped the template, unwrap it safely
    if "template" in parsed and isinstance(parsed["template"], dict):
        enriched = parsed["template"]
    else:
        enriched = parsed

    # Remove any accidental non-schema keys
    enriched = {
        k: v for k, v in enriched.items()
        if k in schema["properties"]
    }

    # Validate strictly
    validate(instance=enriched, schema=schema)

    return enriched


# =========================
# MAIN PIPELINE
# =========================

def main():
    with open(TEMPLATE_FILE, encoding="utf-8") as f:
        catalog = json.load(f)

    with open(SCHEMA_FILE, encoding="utf-8") as f:
        schema = json.load(f)

    for i, template in enumerate(tqdm(catalog["templates"], desc="Enriching")):
        # Skip already enriched templates
        if template.get("description"):
            continue

        source_text = load_source_text(template)

        if not source_text.strip():
            print(f"[SKIP] No source text for {template['id']}")
            continue

        enriched = enrich_template(template, source_text, schema)
        merged = merge_templates(template, enriched)
        catalog["templates"][i] = merged

        # Incremental save (important)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)

    print("[DONE] Enrichment complete")

if __name__ == "__main__":
    main()
