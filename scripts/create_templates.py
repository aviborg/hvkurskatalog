import json

templates = []

def add(id, name, category, shortName=None, resp="HvSS", sources=None, base=None, courseCode=None):
    templates.append({
        "id": id,
        "name": name,
        "shortName": shortName,
        "category": category,
        "courseCode": courseCode,
        "description": "",
        "targetAudience": "",
        "syllabus": "",
        "purpose": "",
        "primaryLearningObjective": "",
        "secondaryLearningObjectives": [],
        "examination": "",
        "prerequisites": [],
        "literature": [],
        "additionalInfo": None,
        "typicalDuration": "",
        "courseResponsible": resp,
        "baseTemplateIds": base or [],
        "sourceFiles": sources or []
    })

# ---------- HvSS 2023 / 2025 ----------

# Grundläggande militärutbildning
add("kombu","Kombattantutbildning för krigsplacerad, obeväpnad personal (KombU)","Grundläggande militärutbildning","KombU","HvSS",["hvss-kurskatalog-2023.pdf", "mr-m-utbildningskatalog-2026-a1.pdf"])

# Chefsutbildningar
for n in ["1","2","3"]:
    add(f"gruppchef-{n}",f"Gruppchefskurs {n}","Chefsutbildningar",f"GC{n}","HvSS",["hvss-kurskatalog-2023.pdf","hvss-kurskatalog-2025.pdf"])
add("gruppchef-12","Gruppchefskurs 1 + 2","Chefsutbildningar","GC12","HvSS",["hvss-kurskatalog-2025.pdf", "mr-m-utbildningskatalog-2026-a1.pdf"],["gruppchef-1","gruppchef-2"])
add("gruppchef-x","Gruppchefskurs X","Chefsutbildningar","GCX","HvSS",["hvss-kurskatalog-2023.pdf","hvss-kurskatalog-2025.pdf"])
add("troppchef-stab-tross","Troppchef Stab och Tross","Chefsutbildningar","CSOT","HvSS",["hvss-kurskatalog-2023.pdf","hvss-kurskatalog-2025.pdf"])
for n in ["1","2","3"]:
    add(f"plutonchef-{n}",f"Plutonchefskurs {n}","Chefsutbildningar",f"PC{n}","HvSS",["hvss-kurskatalog-2023.pdf","hvss-kurskatalog-2025.pdf"])
add("plutonchef-12","Plutonchefskurs 1 + 2","Chefsutbildningar","PC12","HvSS",["hvss-kurskatalog-2025.pdf", "mr-m-utbildningskatalog-2026-a1.pdf"],["plutonchef-1","plutonchef-2"], "MAHGK8100030")
add("ledningsplutonchef","Ledningsplutonchefskurs","Chefsutbildningar","LPC","HvSS",["hvss-kurskatalog-2023.pdf","hvss-kurskatalog-2025.pdf"])
for n in ["1","2","3"]:
    add(f"kompanichef-{n}",f"Kompanichefskurs {n}","Chefsutbildningar",f"KC{n}","HvSS",["hvss-kurskatalog-2023.pdf","hvss-kurskatalog-2025.pdf"])
add("kompanistridskurs","Kompanistridskurs","Chefsutbildningar","KSTR","HvSS",["hvss-kurskatalog-2023.pdf","hvss-kurskatalog-2025.pdf"])
for n in ["1","2","3"]:
    add(f"bataljonchef-{n}",f"Bataljonchefskurs {n}","Chefsutbildningar",f"BC{n}","HvSS",["hvss-kurskatalog-2023.pdf","hvss-kurskatalog-2025.pdf"])
add("bataljonstridskurs","Bataljonstridskurs","Chefsutbildningar","BSTR","HvSS",["hvss-kurskatalog-2023.pdf","hvss-kurskatalog-2025.pdf"])

# Instruktörsutbildningar (full list from TOC)
instruktors = [
    "Instruktörskurs 1","Instruktörskurs 2","Instruktörskurs FUSA grupp",
    "Instruktörskurs Gevär 22 Ungdomsvapen","Instruktörskurs Granattillsats Ak4B",
    "Instruktörskurs Grg m/48","Instruktörskurs IS Hv","Instruktörskurs Ksp 58B",
    "Instruktörskurs ODEN","Instruktörskurs Pansarskott m86","Instruktörskurs Pistol 88",
    "Instruktörskurs Psg90 alt. AK4B med kikarsikte","Instruktörskurs Rekrytering",
    "Instruktörskurs SkjutR AK 4B/C del 1","Instruktörskurs SkjutR AK 4B/C del 2",
    "Instruktörskurs stabstjänst","Instruktörskurs SäkR avlyst terräng",
    "Instruktörskurs SäkR skjutbana","Instruktörskurs Tårgas",
    "Instruktörskurs grundkurs övningsledare Strisim PC",
    "Instruktörskurs fortsättningskurs övningsledare Strisim PC",
    "HALVAR Huvudinstruktörskurs","HALVAR Instruktörskurs"
]

for name in instruktors:
    cid = name.lower().replace(" ", "-").replace("/", "").replace(".", "")
    add(cid,name,"Instruktörsutbildningar",None,"HvSS",["hvss-kurskatalog-2023.pdf","hvss-kurskatalog-2025.pdf"])

# Funktionsutbildningar
funktion = [
    "Anställda vid utbildningsgrupp","Anställda vid MR-grupp","Fredsadministrativkurs",
    "Fordon Förare PB8","HALVAR Figurantkurs","Hemvärns Personnel Recovery Officerskurs (Hv PR-O)",
    "Informatör/webredaktör bataljon","IS Hv Super User","IS Hv Teknikerkurs",
    "Krigsförbandsplaneringskurs","Kvartermästarkurs 1","Kvartermästarkurs 2",
    "Marin hemvärnstaktik","Nordisk chefskurs","Scanbal","Stabschefskurs",
    "Grundkurs Stabstjänst","Grundkurs Störa","Grundkurs Underrättelsetjänst Hv",
    "VaktB kurs","Stridsledning Sensor Hund Hv","Säkerhetstjänstkurs Hv"
]

for name in funktion:
    cid = name.lower().replace(" ", "-").replace("/", "").replace(".", "")
    add(cid,name,"Funktionsutbildningar",None,"HvSS",["hvss-kurskatalog-2023.pdf","hvss-kurskatalog-2025.pdf"])

# Vapenkurser
vapenkurser = [
    "Hv-Intro Automatkarbin 4","Basförmåga 8,4 cm Granatgevär","Basförmåga Automatkarbin 4",
    "Basförmåga Granattillsats 40mm","Basförmåga Kulspruta 58","Basförmåga Pansarskott m/86",
    "Pistolkurs fortsättning","Spetsförmåga 8,4 cm Granatgevär","Spetsförmåga Pansarskott m/86",
    "Tilläggsförmåga 8,4 cm Granatgevär","Tilläggsförmåga Automatkarbin 4",
    "Tilläggsförmåga Granattillsats 40mm","Tilläggsförmåga Kulspruta m/58",
    "Tilläggsförmåga Pansarskott m/86","Skarpskytt PSG90 Hv"
]

for name in vapenkurser:
    cid = name.lower().replace(" ", "-").replace("/", "").replace(".", "")
    add(cid,name,"Vapenkurser",None,"HvSS",["hvss-kurskatalog-2023.pdf"])

# Ledarskap
ledarskap = [
    ["Indirekt ledarskap", "IL"],["Ledarskap och självkännedom", "LoS"],
    ["Utveckling grupp ledare", "UGL"],["Utvecklande ledarskap", "UL"]
]

for name in ledarskap:
    cid = name[0].lower().replace(" ", "-").replace("(", "").replace(")", "")
    add(cid,name[0],"Ledarskapsutbildningar",name[1],"HvSS",["hvss-kurskatalog-2023.pdf"])

# Musik
add("chef-musikkar","Chef musikkår","Musikutbildningar","CMK","HvSS",["hvss-kurskatalog-2023.pdf"])

# MR M 2026
add("gu-f","Grundläggande soldatutbildning för frivillig personal, GU-F","Grundläggande militärutbildning","GU-F","MRM",["mr-m-utbildningskatalog-2026-a1.pdf"])
add("tccc-cls","TCCC-CLS (Combat Life Saver)","Funktionsutbildningar","TCCC-CLS","MRM",["mr-m-utbildningskatalog-2026-a1.pdf"])
add("pb8","PB8 (Personbil 8)","Funktionsutbildningar","PB8","MRM",["mr-m-utbildningskatalog-2026-a1.pdf"])
add("gk-tung-slapkarra","Gk Tung släpkärra","Funktionsutbildningar","GKTSK","MRM",["mr-m-utbildningskatalog-2026-a1.pdf"])
add("instruktörskurs-12","Instruktörskurs 1 + 2","Instruktörsutbildningar","IK12","MRM",["mr-m-utbildningskatalog-2026-a1.pdf"],["instruktörskurs-1","instruktörskurs-2"])

out = {"templates": templates}

path = "data/hemvarn_course_templates_all.json"
with open(path,"w",encoding="utf-8") as f:
    json.dump(out,f,ensure_ascii=False,indent=2)

path
