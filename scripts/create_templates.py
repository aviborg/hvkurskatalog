import json
from datetime import datetime, timezone

templates = []

def now_utc_timestamp():
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

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
        "sourceFiles": sources or [],
        "lastModifiedBy": "create_templates_script",
        "lastModified": now_utc_timestamp()
    })

# ---------- HvSS 2023 / 2025 ----------

# Grundläggande militärutbildning
add("kombu","Kombattantutbildning för krigsplacerad, obeväpnad personal (KombU)","Grundläggande militärutbildning","KombU","HvSS",["hvss-kurskatalog-2023.pdf", "mr-m-utbildningskatalog-2026-a1.pdf"], None, "UTPGK450KU02")

# Chefsutbildningar
for course in [["1", "MAHGK2011230"], ["2", "MAHFK2011181"],["3","MAHFK2011231"]]:
    add(f"gruppchef-{course[0]}",f"Gruppchefskurs {course[0]}","Chefsutbildningar",f"GC{course[0]}","HvSS",["hvss-kurskatalog-2023.pdf","hvss-kurskatalog-2025.pdf",], None, course[1])
add("gruppchef-12","Gruppchefskurs 1 + 2","Chefsutbildningar","GC12","HvSS",["hvss-kurskatalog-2025.pdf", "mr-m-utbildningskatalog-2026-a1.pdf"],["gruppchef-1","gruppchef-2"], None, "GC12")
add("gruppchef-x","Gruppchefskurs X","Chefsutbildningar","GCX","HvSS",["hvss-kurskatalog-2023.pdf","hvss-kurskatalog-2025.pdf"], None, "MAHGK119GP00")
add("troppchef-stab-tross","Troppchef Stab och Tross","Chefsutbildningar","CSOT","HvSS",["hvss-kurskatalog-2023.pdf","hvss-kurskatalog-2025.pdf"], None, "HVT422CGP01")
for course in [["1", "MAHGK2011222"], ["2", "MAHFK2011223"],["3","MAHFK2011520"]]:
    add(f"plutonchef-{course[0]}",f"Plutonchefskurs {course[0]}","Chefsutbildningar",f"PC{course[0]}","HvSS",["hvss-kurskatalog-2023.pdf","hvss-kurskatalog-2025.pdf"], None, course[1])
add("plutonchef-12","Plutonchefskurs 1 + 2","Chefsutbildningar","PC12","HvSS",["hvss-kurskatalog-2025.pdf", "mr-m-utbildningskatalog-2026-a1.pdf"],["plutonchef-1","plutonchef-2"], "MAHGK8100030")
add("ledningsplutonchef","Ledningsplutonchefskurs","Chefsutbildningar","LPC","HvSS",["hvss-kurskatalog-2023.pdf","hvss-kurskatalog-2025.pdf"], None, "MAHGK2011502")
for course in [["1", "MAHGK119KB11"], ["2", "MAHFK2011220"],["3","HVT422FKB03"]]:
    add(f"kompanichef-{course[0]}",f"Kompanichefskurs {course[0]}","Chefsutbildningar",f"KC{course[0]}","HvSS",["hvss-kurskatalog-2023.pdf","hvss-kurskatalog-2025.pdf"], None, course[1])
add("kompanistridskurs","Kompanistridskurs","Chefsutbildningar","KSTR","HvSS",["hvss-kurskatalog-2023.pdf","hvss-kurskatalog-2025.pdf"], None, "MAHGK119KB10")
for course in [["1", "MAHGK119KB01"], ["2", "MAHFK2011218"],["3","HVT422FKB04"]]:
    add(f"bataljonchef-{course[0]}",f"Bataljonchefskurs {course[0]}","Chefsutbildningar",f"BC{course[0]}","HvSS",["hvss-kurskatalog-2023.pdf","hvss-kurskatalog-2025.pdf"], None, course[1])
add("bataljonstridskurs","Bataljonstridskurs","Chefsutbildningar","BSTR","HvSS",["hvss-kurskatalog-2023.pdf","hvss-kurskatalog-2025.pdf"], None, "MAHGK119KB00")

# Instruktörsutbildningar (full list from TOC)
instruktors = [
    ["Grundkurs Övningsledare Automatkarbin BAS", "GKÖLAK", "HVT423F10001"],
    ["Instruktörskurs 1", "IK1", "MAHGK9090001"], ["Instruktörskurs 2", "IK2", "MAHFK2011553"], ["Instruktörskurs FUSA grupp", "IKFUSA", "MAHAK2111559"],
    ["Instruktörskurs Gevär 22 Ungdomsvapen", "IKG22U", "MAHFÖ6121005"], ["Instruktörskurs Granattillsats Ak4B", "IKGTAK", "MAHFÖ2111660"],
    ["Instruktörskurs Grg m/48", "IKGRG", "MAHFÖ2111556"], ["Instruktörskurs IS Hv", "IKISHV", "MAHGK7110001"], ["Instruktörskurs Ksp 58B", "IKKSP", "MAHFÖ2111555"],
    ["Instruktörskurs ODEN", "IKODEN", "HVT422FIK00"],["Instruktörskurs Pansarskott m86", "IKPSM86", "MAHFÖ2111557"],["Instruktörskurs Pistol 88", "IKP88", "MAHFÖ2111558"],
    ["Instruktörskurs Psg90 alt. AK4B med kikarsikte", "IKPSG", "MAHFÖ2111560"],["Instruktörskurs Rekrytering", "IKREK", "MAHGK2019526"],
    ["Instruktörskurs SkjutR AK 4B/C del 1", "IKSR1", "MAHGK2111565"],["Instruktörskurs SkjutR AK 4B/C del 2", "IKSR2", "MAHFÖ2111566"],
    ["Instruktörskurs stabstjänst", "IKST", "MAHGK119IN00"],["Instruktörskurs SäkR avlyst terräng", "IKSRAT", "MAHFÖ2111564"],
    ["Instruktörskurs SäkR skjutbana", "IKSRSB", "MAHFÖ2111563"],["Instruktörskurs Tårgas", "IKTG", "MAHFÖ2119502"],
    ["Instruktörskurs grundkurs övningsledare Strisim PC", "GKÖLSPC", "MARGK510ÖSSP"], 
    ["Instruktörskurs fortsättningskurs övningsledare Strisim PC", "FKÖLSPC", "MARFK510ÖSSP"],
    ["HALVAR Huvudinstruktörskurs", "HALVARHIK", "MAHFÖ2011558"],["HALVAR Instruktörskurs", "HALVARIK", "MAHGK2011557"]
]

for name in instruktors:
    cid = name[0].lower().replace(" ", "-").replace("/", "").replace(".", "")
    add(cid,name[0],"Instruktörsutbildningar",name[1],"HvSS",["hvss-kurskatalog-2023.pdf","hvss-kurskatalog-2025.pdf"], None, name[2])

# Funktionsutbildningar
funktion = [
    ["Anställda vid MR-grupp", "MAHGK2011301"], ["Fredsadministrativkurs", "MAHGK119FU01"],
    ["Fordon Förare PB8", "MAHGK5111102"],["HALVAR Figurantkurs", "MAHFÖ2011560"], ["Hemvärns Personnel Recovery Officerskurs (Hv PR-O)", "MAÖGK043P007"],
    ["Informatör/webredaktör bataljon", "MAHGK2019501"], ["IS Hv Super User", "MAHFÖ7110002"], ["IS Hv Teknikerkurs", "MAHGK7090001"],
    ["Krigsförbandsplaneringskurs", "MAHFÖ2011515"], ["Kvartermästarkurs 1", "MAHGK2019222"], ["Kvartermästarkurs 2", "MAHFK4109223"],
    ["Marin hemvärnstaktik", "MAHGK2061519"], ["Nordisk chefskurs", "MAHFÖ2019812"], ["Scanbal", "MAHFÖ7120001"], ["Stabschefskurs", "MAHGK119FU03"],
    ["Grundkurs Stabstjänst", "MAHGK119FU02"], ["Grundkurs Störa", "MAHGK119FU04"], ["Grundkurs Underrättelsetjänst Hv", "HVT422FFU00"],
    ["VaktB kurs", "MAHGK0440001"], ["Stridsledning Sensor Hund Hv", "HVT424L0000"], ["Säkerhetstjänstkurs Hv", "MAHGK8100020"], ["Ungdomsledarkurs", "MAHGK2011535"]
]

for name in funktion:
    cid = name[0].lower().replace(" ", "-").replace("/", "").replace(".", "")
    add(cid,name[0],"Funktionsutbildningar",None,"HvSS",["hvss-kurskatalog-2023.pdf","hvss-kurskatalog-2025.pdf"], None, name[1])

# Vapenkurser
vapenkurser = [
    ["Hv-Intro Automatkarbin 4", "MAHGK119VA00"], ["Basförmåga 8,4 cm Granatgevär", "MAHGK119VA01"], ["Basförmåga Automatkarbin 4", "MAHGK119VA02"],
    ["Basförmåga Granattillsats 40mm", "MAHGK119VA03"], ["Basförmåga Kulspruta 58","MAHGK119VA04"], ["Basförmåga Pansarskott m/86", "MAHGK119VA05"],
    ["Pistolkurs fortsättning","MAHFK119VA10"], ["Spetsförmåga 8,4 cm Granatgevär","MAHFK119VA21"], ["Spetsförmåga Pansarskott m/86","MAHFK119VA20"],
    ["Tilläggsförmåga 8,4 cm Granatgevär","MAHFK119VA11"], ["Tilläggsförmåga Automatkarbin 4","MAHFK119VA12"],
    ["Tilläggsförmåga Granattillsats 40mm","MAHGK119VA13"], ["Tilläggsförmåga Kulspruta m/58","MAHFK119VA14"],
    ["Tilläggsförmåga Pansarskott m/86","MAHFK119VA15"], ["Skarpskytt PSG90 Hv","MAHGK4101701"]
]

for name in vapenkurser:
    cid = name[0].lower().replace(" ", "-").replace("/", "").replace(".", "")
    add(cid,name[0],"Vapenkurser",None,"HvSS",["hvss-kurskatalog-2023.pdf"], None, name[1])

# Ledarskap
ledarskap = [
    ["Indirekt ledarskap", "IL", "ÄMLGK705LE11"],["Ledarskap och självkännedom", "LoS", "ÄMLGK705LE12"],
    ["Utveckling grupp ledare", "UGL", "ÄMLGK705LE13"],["Utvecklande ledarskap", "UL", "ÄMLGK816LE10"]
]

for name in ledarskap:
    cid = name[0].lower().replace(" ", "-").replace("(", "").replace(")", "")
    add(cid,name[0],"Ledarskapsutbildningar",name[1],"HvSS",["hvss-kurskatalog-2023.pdf"], None, name[2])

# Musik
add("chef-musikkar","Chef musikkår","Musikutbildningar","CMK","HvSS",["hvss-kurskatalog-2023.pdf"], None, "MAHGK3031741")

# MR M 2026
add("gu-f","Grundläggande soldatutbildning för frivillig personal, GU-F","Grundläggande militärutbildning","GU-F","MRM",["mr-m-utbildningskatalog-2026-a1.pdf"])
add("tccc-cls","TCCC-CLS (Combat Life Saver)","Funktionsutbildningar","TCCC-CLS","MRM",["mr-m-utbildningskatalog-2026-a1.pdf"])
add("gk-tung-slapkarra","Gk Tung släpkärra","Funktionsutbildningar","GKTSK","MRM",["mr-m-utbildningskatalog-2026-a1.pdf"])
add("instruktörskurs-12","Instruktörskurs 1 + 2","Instruktörsutbildningar","IK12","MRM",["mr-m-utbildningskatalog-2026-a1.pdf"],["instruktörskurs-1","instruktörskurs-2"], None, "IK12")

out = {"templates": templates}

path = "data/hemvarn_course_templates_all.json"
with open(path,"w",encoding="utf-8") as f:
    json.dump(out,f,ensure_ascii=False,indent=2)

path
