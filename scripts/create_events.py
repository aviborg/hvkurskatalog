import os
import re
import json
import time
from datetime import datetime, timezone
from dotenv import load_dotenv
from openai import OpenAI
import pdfplumber
from tqdm import tqdm

# ============================================================
# CONFIG
# ============================================================

load_dotenv()
client = OpenAI()

PDF_DIR = "public/kurskataloger"
TEXT_DIR = "extracted_text"
TEMPLATE_FILE = "data/hemvarn_course_templates_enriched.json"
OUTPUT_FILE = "data/hemvarn_course_events.json"

MODEL = "gpt-4.1-mini"
TEMPERATURE = 0.1
THROTTLE_SECONDS = 2.0

os.makedirs(TEXT_DIR, exist_ok=True)

# ============================================================
# UTILITIES
# ============================================================

def now_utc():
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

def norm(s):
    if not s:
        return "unknown"
    return (
        s.lower()
        .replace("å", "a")
        .replace("ä", "a")
        .replace("ö", "o")
        .replace(" ", "")
        .replace("/", "")
        .replace(".", "")
    )

def build_date_hash(course_dates):
    parts = []
    for d in course_dates or []:
        if d.get("start") and d.get("end"):
            parts.append(f"{d['start']}_{d['end']}")
    return "+".join(parts) if parts else "nodates"

def generate_event_id(event, existing_ids):
    base = f"evt-{norm(event['templateId'])}-{norm(event.get('eventResponsible'))}-{build_date_hash(event.get('courseDates'))}"
    if base not in existing_ids:
        return base
    suffix = "a"
    while f"{base}-{suffix}" in existing_ids:
        suffix = chr(ord(suffix) + 1)
    return f"{base}-{suffix}"

# ============================================================
# PDF → TEXT
# ============================================================

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

# ============================================================
# HIGH-RECALL CANDIDATE EXTRACTION
# ============================================================

DATE_REGEX = re.compile(
    r"(20\d{2}[-/.]?\d{2}[-/.]?\d{2})|"   # 2026-09-01
    r"(\d{8})|"                           # 20260901
    r"(v\.\s?\d{2,3})",                   # v.39
    re.IGNORECASE
)

def extract_candidate_blocks(text):
    lines = text.splitlines()
    blocks = []
    buffer = []

    for line in lines:
        if DATE_REGEX.search(line):
            buffer = [line]
        elif buffer:
            buffer.append(line)
            if len(buffer) >= 6:
                blocks.append("\n".join(buffer))
                buffer = []

    if buffer:
        blocks.append("\n".join(buffer))

    return blocks

# ============================================================
# LOAD TEMPLATES
# ============================================================

with open(TEMPLATE_FILE, encoding="utf-8") as f:
    templates = json.load(f)["templates"]

TEMPLATE_HINTS = [
    {"id": t["id"], "name": t["name"], "shortName": t.get("shortName")}
    for t in templates
]

# ============================================================
# AI NORMALIZATION
# ============================================================

SYSTEM_PROMPT = """
You extract COURSE EVENTS from Swedish Hemvärnet catalogs.

Input:
- Raw text that MAY describe one scheduled course event
- Known course templates

If the text does NOT describe a concrete event:
→ return null

If it DOES:
→ return ONE JSON object with:
templateId
courseDates [{start, end}]
location
eventResponsible
applicationDeadline
spots
status
notes

Rules:
- Use Swedish
- Normalize dates to YYYYMMDD
- Do not invent data
- Output JSON or null ONLY
"""

def normalize_event(block_text):
    response = client.responses.create(
        model=MODEL,
        temperature=TEMPERATURE,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    {"text": block_text, "knownTemplates": TEMPLATE_HINTS},
                    ensure_ascii=False,
                ),
            },
        ],
    )

    raw = response.output_text.strip()

    if raw.lower() == "null":
        return None

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None

# ============================================================
# MAIN
# ============================================================

events = []
existing_ids = set()
fingerprints = {}

stats = {"candidates": 0, "accepted": 0}

for pdf in tqdm(os.listdir(PDF_DIR), desc="Scanning PDFs"):
    if not pdf.lower().endswith(".pdf"):
        continue

    txt_path = extract_pdf_text(pdf)
    with open(txt_path, encoding="utf-8") as f:
        text = f.read()

    candidates = extract_candidate_blocks(text)
    stats["candidates"] += len(candidates)

    for block in candidates:
        event = normalize_event(block)

        if not event or not event.get("templateId"):
            continue

        stats["accepted"] += 1

        event["lastModifiedBy"] = MODEL
        event["lastModified"] = now_utc()
        event["sourceFiles"] = [pdf]

        fp = (
            event["templateId"],
            json.dumps(event.get("courseDates"), sort_keys=True),
            event.get("location"),
            event.get("eventResponsible"),
        )

        if fp in fingerprints:
            fingerprints[fp]["sourceFiles"].append(pdf)
            continue

        event["id"] = generate_event_id(event, existing_ids)
        existing_ids.add(event["id"])

        fingerprints[fp] = event
        events.append(event)

        time.sleep(THROTTLE_SECONDS)

# ============================================================
# OUTPUT
# ============================================================

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump({"events": events}, f, ensure_ascii=False, indent=2)

print(
    f"[DONE] Candidates: {stats['candidates']} | "
    f"Accepted events: {stats['accepted']} | "
    f"Unique events: {len(events)}"
)
