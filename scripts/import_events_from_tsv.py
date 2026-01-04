import csv
import json
import os
from datetime import datetime, timezone

# ============================================================
# CONFIG
# ============================================================

TSV_FILE = "public/events.csv"
TEMPLATE_FILE = "data/hemvarn_course_templates_enriched.json"
EVENT_OUTPUT = "data/hemvarn_course_events.json"
TEMPLATE_OUTPUT = "data/hemvarn_course_templates_enriched.json"

DELIMITER = "\t"

HEADER_MAP = {
    "kurskod": "courseCode",
    "kursbenämning": "name",
    "start": "startDate",
    "slut": "endDate",
    "ort": "location",
    "ansvarig": "responsible",
    "platser": "spots",
    "sista ansökan": "applicationDeadline",
    "sista ansökningsdag": "applicationDeadline",
    "kommentar": "notes",
    "övrigt": "notes",
    "kategori": "category"
}


# ============================================================
# HELPERS
# ============================================================

def now_utc():
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

def norm_code(code):
    return code.strip().upper()

def template_id_from_code(code):
    return f"auto-{code.lower()}"

def normalize_date(s):
    return s.replace("-", "").replace(".", "")

def parse_course_dates(start_raw, end_raw):
    """
    Parses comma-separated start/end dates into a list of {start, end}.
    """
    if not start_raw or not end_raw:
        return []

    starts = [s.strip() for s in start_raw.split(",") if s.strip()]
    ends = [e.strip() for e in end_raw.split(",") if e.strip()]

    if len(starts) != len(ends):
        raise ValueError(
            f"Mismatched start/end dates: {start_raw} / {end_raw}"
        )

    return [
        {
            "start": normalize_date(s),
            "end": normalize_date(e),
        }
        for s, e in zip(starts, ends)
    ]



# ============================================================
# LOAD EXISTING TEMPLATES
# ============================================================

with open(TEMPLATE_FILE, encoding="utf-8") as f:
    template_catalog = json.load(f)

templates = template_catalog["templates"]

templates_by_code = {
    t["courseCode"].upper(): t
    for t in templates
    if t.get("courseCode")
}

# ============================================================
# LOAD TSV
# ============================================================

events = []

with open(TSV_FILE, encoding="utf-8") as f:
    reader = csv.reader(f, delimiter=DELIMITER)
    raw_headers = next(reader)

    headers = []
    for h in raw_headers:
        key = h.strip().lower()
        if key not in HEADER_MAP:
            raise ValueError(f"Unknown header column: {h}")
        headers.append(HEADER_MAP[key])

    for row_values in reader:
        row = dict(zip(headers, row_values))

        course_code = norm_code(row["courseCode"])

        # --------------------------------------------
        # TEMPLATE RESOLUTION
        # --------------------------------------------
        if course_code not in templates_by_code:
            template = {
                "id": template_id_from_code(course_code),
                "courseCode": course_code,
                "name": row["name"].strip(),
                "shortName": course_code,
                "category": row.get("category", "").strip(),
                "description": "",
                "targetAudience": "",
                "syllabus": "",
                "purpose": "",
                "learningObjectives": [],
                "finalGoal": "",
                "subGoals": [],
                "examination": "",
                "prerequisites": [],
                "literature": "",
                "additionalInfo": "Automatiskt skapad från kurstillfälle",
                "typicalDuration": "",
                "courseResponsible": "",
                "baseTemplateIds": [],
                "sourceFiles": ["events.csv"],
                "lastModifiedBy": "csv-import",
                "lastModified": now_utc()
            }
            templates.append(template)
            templates_by_code[course_code] = template

        template_id = templates_by_code[course_code]["id"]

        # --------------------------------------------
        # EVENT CREATION
        # --------------------------------------------
        course_dates = parse_course_dates(
            row["startDate"],
            row["endDate"]
        )
        first_start = course_dates[0]["start"] if course_dates else "nodate"
        event = {
            "id": f"evt-{template_id}-{first_start}-{row.get('responsible', '').lower().replace(' ','')}-{row.get('location','').lower().replace(' ','')}",
            "templateId": template_id,
            "courseDates": course_dates,
            "location": row.get("location", ""),
            "eventResponsible": row.get("responsible", ""),
            "applicationDeadline": normalize_date(row.get("applicationDeadline", "")),
            "spots": int(row["spots"]) if row.get("spots") else None,
            "status": "open",
            "notes": row.get("notes", ""),
            "lastModifiedBy": "csv-import",
            "lastModified": now_utc(),
            "sourceFiles": ["events.csv"]
        }

        events.append(event)

# ============================================================
# WRITE OUTPUTS
# ============================================================

with open(EVENT_OUTPUT, "w", encoding="utf-8") as f:
    json.dump({"events": events}, f, ensure_ascii=False, indent=2)

with open(TEMPLATE_OUTPUT, "w", encoding="utf-8") as f:
    json.dump(template_catalog, f, ensure_ascii=False, indent=2)

print(f"[DONE] Imported {len(events)} events")
print(f"[DONE] Templates now total: {len(templates)}")
