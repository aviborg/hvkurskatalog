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
from datetime import datetime, timezone

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
THROTTLE_SECONDS = 2.5

os.makedirs(TEXT_DIR, exist_ok=True)

client = OpenAI(api_key=OPENAI_API_KEY)

# =========================
# Date helpers
# =========================

def now_utc_timestamp():
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

# =========================
# PDF → TEXT
# =========================

def extract_pdf_to_text(pdf_name):
    txt_path = os.path.join(TEXT_DIR, pdf_name.replace(".pdf", ".txt"))
    pdf_path = os.path.join(PDF_DIR, pdf_name)

    if os.path.exists(txt_path):
        return

    with pdfplumber.open(pdf_path) as pdf, open(txt_path, "w", encoding="utf-8") as out:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                out.write(f"\n=== PAGE {i+1} ===\n{text}\n")

# =========================
# ALIASES
# =========================

def build_course_aliases(template):
    aliases = {template["name"].lower()}
    if template.get("shortName"):
        aliases.add(template["shortName"].lower())
    base = re.sub(r"\s+\d+.*$", "", template["name"])
    aliases.update({
        f"{base}kurs".lower(),
        f"{base} kurs".lower()
    })
    return aliases

# =========================
# LOAD SOURCE TEXT
# =========================

def load_source_text(template):
    aliases = build_course_aliases(template)
    collected = []

    for pdf in template["sourceFiles"]:
        extract_pdf_to_text(pdf)
        txt_path = os.path.join(TEXT_DIR, pdf.replace(".pdf", ".txt"))
        if not os.path.exists(txt_path):
            continue

        with open(txt_path, encoding="utf-8") as f:
            content = f.read().lower()

        for alias in aliases:
            if alias in content:
                collected.append(content)
                break

    return "\n".join(collected)

# =========================
# MERGE
# =========================

IMMUTABLE_FIELDS = {
    "id", "name", "shortName", "category",
    "courseResponsible", "baseTemplateIds", "sourceFiles"
}

def merge_templates(original, enriched):
    merged = original.copy()
    for k, v in enriched.items():
        if k in IMMUTABLE_FIELDS:
            continue
        if original.get(k) in ("", [], None) and v not in ("", [], None):
            merged[k] = v
    return merged

# =========================
# OPENAI CALL
# =========================

def call_with_retry(messages, retries=6):
    for attempt in range(retries):
        try:
            return client.responses.create(
                model=MODEL,
                temperature=TEMPERATURE,
                input=messages
            )
        except RateLimitError as e:
            wait = 10 + attempt * 5
            print(f"[RATE LIMIT] waiting {wait}s before retry")
            time.sleep(wait)

    raise RuntimeError("Rate limit exceeded after retries")

# =========================
# PROMPT
# =========================

SYSTEM_PROMPT = """
You are enriching Swedish Hemvärnet course templates.

Use the following guidance:

PRIMARY EXAMPLE:
- A fully populated Gruppchefskurs template demonstrates the expected structure, tone, and level of detail.

CONTRAST EXAMPLE:
- Functional/specialist courses (e.g. TCCC-CLS) are typically described more concisely,
  with focus on skills, application, and target audience rather than leadership progression.

Rules:
- Write in Swedish.
- Be neutral, professional, and concise.
- Prefer provided source text when available.
- If source text is missing, you MAY synthesize high-level, well-established knowledge.
- Do NOT invent exact hours, regulations, or examination rules unless obvious.
- Do NOT modify id, name, shortName, category, courseResponsible, baseTemplateIds, or sourceFiles.
- Output ONLY a valid CourseTemplate JSON object.
"""


PRIMARY_EXAMPLE = {
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

CONTRAST_EXAMPLE = {
  "courseType": "Grundläggande militärutbildning / funktionsutbildning",
  "exampleName": "Kombattantutbildning för krigsplacerad, obeväpnad personal (KombU)",
  "descriptionStyle": "Saklig och kortfattad, fokus på grundläggande förståelse och tillämpning",
  "typicalDescription": "Grundläggande utbildning som ger personal förståelse för sin roll, status och uppgifter i Försvarsmaktens krigsorganisation.",
  "typicalTargetAudience": "Krigsplacerad personal utan ordinarie beväpning.",
  "typicalPurpose": "Att ge deltagaren grundläggande kunskap om totalförsvaret, värdegrund, folkrätt och det egna förbandets uppgift.",
  "typicalLearningObjectives": [
    "Förstå egen roll i krigsorganisationen",
    "Tillämpa grundläggande soldatkunskaper",
    "Följa Försvarsmaktens värdegrund och regelverk"
  ]
}

'''
CONTRAST_EXAMPLE = {
      "id": "kombu",
      "name": "Kombattantutbildning för krigsplacerad, obeväpnad personal (KombU)",
      "shortName": "KombU",
      "category": "Grundläggande militärutbildning",
      "courseCode": "UTPGK450KU02",
      "description": "Nedbrytning av lärandemål till specifika utbildningsmål sker i centralt utgiven kursbeskrivning. Undervisningsformerna utgörs av teoretiska och praktiska utbildningsmoment.",
      "targetAudience": "Krigsplacerad, obeväpnad personal, såväl kombattanter som icke kombattanter (dessa icke kombattanter kan efter särskild utbildning tilldelas lättare beväpning).",
      "syllabus": "Fysisk träning, Exercis, CBRN, Hälso- och sjukvårdsutbildning, Försvarsupplysning, FM Värdegrund, Folkrätt, förmanskap, Uniformssystem 90, Förevisningsskjutning, Brandutbildning",
      "purpose": "Ge viss personal i Försvarsmaktens krigsorganisation förståelse för sin roll och sin status som ”kombattant” alternativt ”icke kombattant”.",
      "finalGoal": "Ge deltagarna kunskap om Totalförsvaret, Försvarsmaktens Värdegrund, Folkrätt och det egna krigsförbandets uppgift och funktion i krigsorganisationen.",
      "subGoals": [
        "Kursen ska, tillsammans med eventuell specifik befattningsutbildning, ge sådan förmåga att eleven ska kunna krigsplaceras på avsedd befattning i krigsorganisationen."
      ],
      "examination": "För godkänt krävs att respektive kursdeltagaren deltagit i samtliga utbildningsmoment. Eventuell komplettering ska ske inom 6 månader från kurstillfället.",
      "prerequisites": [],
      "literature": "Underlag för utbildningen utgörs främst av delar av underlag för GMU. Dessa framgår av kursbeskrivningen för KombU.",
      "additionalInfo": "Samverkan och synkronisering mot GMU och FSU har skett med kursansvarig för GMU och FSU (se vidare i kursbeskrivningen). Kursen kan även genomföras med ”icke kombattanter”. Kursen reviderad enligt MHS H 2014-12-18, 19 100:20260 avseende utbildningslängd, målgrupp samt syfte.",
      "typicalDuration": "3 dagar",
      "courseResponsible": "MHSH",
      "baseTemplateIds": [],
      "sourceFiles": [
        "hvss-kurskatalog-2023.pdf",
        "mr-m-utbildningskatalog-2026-a1.pdf"
      ]
    }
'''
# =========================
# ENRICH
# =========================

def enrich_template(template, source_text, schema):
    payload = {
        "primaryExample": PRIMARY_EXAMPLE,      # full GC1 JSON
        "contrastExample": CONTRAST_EXAMPLE,    # reduced KombU
        "template": template,
        "sourceText": source_text
    }

    response = call_with_retry([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}
    ])

    enriched = json.loads(response.output_text.strip())

    # Strip extras
    enriched = {k: v for k, v in enriched.items() if k in schema["properties"]}
    validate(instance=enriched, schema=schema)

    return enriched

# =========================
# MAIN
# =========================

def main():
    with open(TEMPLATE_FILE, encoding="utf-8") as f:
        catalog = json.load(f)

    with open(SCHEMA_FILE, encoding="utf-8") as f:
        schema = json.load(f)

    for i, template in enumerate(tqdm(catalog["templates"], desc="Enriching")):

        # Skip merged templates
        if template.get("baseTemplateIds"):
            continue

        if template.get("description"):
            continue

        source_text = load_source_text(template)
        enriched = enrich_template(template, source_text, schema)

        # Confidence + provenance
        filled_fields = sum(bool(enriched.get(k)) for k in schema["properties"])
        confidence = (
            "high" if filled_fields > 10 else
            "medium" if filled_fields > 5 else
            "low"
        )

        enriched["enrichmentConfidence"] = confidence
        enriched["enrichmentProvenance"] = {
            k: ("pdf" if source_text else "synthesized")
            for k, v in enriched.items()
            if v not in ("", [], None)
        }

        merged = merge_templates(template, enriched)

        # Only update metadata if something actually changed
        if merged != template:
            merged["lastModifiedBy"] = MODEL
            merged["lastModified"] = now_utc_timestamp()

        catalog["templates"][i] = merged


        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)

        time.sleep(THROTTLE_SECONDS)

    print("[DONE] Enrichment complete")

if __name__ == "__main__":
    main()
