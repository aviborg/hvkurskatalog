import os
import re
import json
import time
from datetime import datetime, timezone
from dotenv import load_dotenv
from openai import OpenAI
import pdfplumber
from tqdm import tqdm

# =========================
# CONFIG
# =========================

load_dotenv()
client = OpenAI()

PDF_DIR = "public/kurskataloger"
TEXT_DIR = "extracted_text"
TEMPLATE_FILE = "data/hemvarn_course_templates_enriched.json"
OUTPUT_FILE = "data/hemvarn_course_events.json"

MODEL = "gpt-4.1-mini"
TEMPERATURE = 0.1
THROTTLE_SECONDS = 1.5

DATE_REGEX = re.compile(
    r"(20\d{2}[-/.]?\d{2}[-/.]?\d{2})|"
    r"(\d{6,8})|"
    r"(v\.\s?\d{2,3})",
    re.IGNORECASE
)

os.makedirs(TEXT_DIR, exist_ok=True)

# =========================
# HELPERS
# =========================

def now_utc():
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

def extract_candidate_blocks(text):
    lines = text.splitlines()
    candidates = []

    buffer = []

    for line in lines:
        if DATE_REGEX.search(line):
            buffer.append(line)
        elif buffer:
            buffer.append(line)

            # stop buffer when it gets too large
            if len(buffer) >= 6:
                candidates.append("\n".join(buffer))
                buffer = []

    if buffer:
        candidates.append("\n".join(buffer))

    return candidates

def extract_pdf_text(pdf_name):
    txt_path = os.path.join(TEXT_DIR, pdf_name.replace(".pdf", ".txt"))
    pdf_path = os.path.join(PDF_DIR, pdf_name)

    if os.path.exists(txt_path):
        return txt_path

    with pdfplumber.open(pdf_path) as pdf, open(txt_path, "w", encoding="utf-8") as out:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                out.write(text + "\n")

    return txt_path

# =========================
# STEP 1: LOAD TEMPLATES
# =========================

with open(TEMPLATE_FILE, encoding="utf-8") as f:
    templates = json.load(f)["templates"]

# Build lookup by name + shortName
TEMPLATE_LOOKUP = {}
for t in templates:
    TEMPLATE_LOOKUP[t["id"]] = t
    TEMPLATE_LOOKUP[t["name"].lower()] = t
    if t.get("shortName"):
        TEMPLATE_LOOKUP[t["shortName"].lower()] = t

# =========================
# STEP 2: FIND EVENT BLOCKS
# =========================

EVENT_BLOCK_HINTS = [
    "plats", "datum", "sista ansökningsdag",
    "antal platser", "anmälan", "genomförs"
]

def is_event_block(text):
    text_l = text.lower()
    return sum(h in text_l for h in EVENT_BLOCK_HINTS) >= 2

# =========================
# STEP 3: AI NORMALIZATION
# =========================

SYSTEM_PROMPT = """
You are extracting Swedish Hemvärnet course event information.

Input:
- Raw text describing a course event
- A list of known course templates

Your task:
- Identify the course
- Extract event details
- Normalize dates to YYYYMMDD
- Output ONE JSON object matching the CourseEvent schema

Rules:
- Use Swedish
- Be conservative
- If a field is missing, use null
- Do not invent data
- Output JSON only
"""

def normalize_event(block_text, source_file):
    payload = {
        "text": block_text,
        "knownTemplates": [
            {"id": t["id"], "name": t["name"], "shortName": t.get("shortName")}
            for t in templates
        ]
    }

    response = client.responses.create(
        model=MODEL,
        temperature=TEMPERATURE,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}
        ]
    )

    raw = response.output_text.strip()
    event = json.loads(raw)

    # Metadata
    event["lastModifiedBy"] = MODEL
    event["lastModified"] = now_utc()
    event["sourceFiles"] = [source_file]

    return event

# =========================
# STEP 4: MAIN
# =========================

events = []
seen_fingerprints = {}

for pdf in tqdm(os.listdir(PDF_DIR), desc="Scanning PDFs"):
    if not pdf.lower().endswith(".pdf"):
        continue

    txt_path = extract_pdf_text(pdf)

    with open(txt_path, encoding="utf-8") as f:
        blocks = f.read().split("\n\n")

    for block in blocks:
        if not is_event_block(block):
            continue

        try:
            event = normalize_event(block, pdf)
        except Exception:
            continue

        # Deduplication fingerprint
        fp = (
            event.get("templateId"),
            json.dumps(event.get("courseDates"), sort_keys=True),
            event.get("location"),
            event.get("eventResponsible")
        )

        if fp in seen_fingerprints:
            seen_fingerprints[fp]["sourceFiles"].append(pdf)
        else:
            seen_fingerprints[fp] = event
            events.append(event)

        time.sleep(THROTTLE_SECONDS)

# =========================
# OUTPUT
# =========================

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump({"events": events}, f, ensure_ascii=False, indent=2)

print(f"[DONE] Created {len(events)} unique course events")
