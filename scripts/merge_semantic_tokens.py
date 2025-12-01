"""
Merge expanded semantic tokens from agents into semantic_tokens.json.gz.
"""

import json
import gzip
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DATA_DIR = REPO_ROOT / "src" / "humanmint" / "data"

# Load existing semantic tokens
with gzip.open(DATA_DIR / "semantic_tokens.json.gz", "rt", encoding="utf-8") as f:
    semantic_data = json.load(f)

print(f"Existing tokens: {len(semantic_data)}")

# Agent-generated expansions mapped to semantic tags
expansions = {
    "ADMIN": [
        "admin", "administration", "administrative", "administrator", "office", "clerk", "secretary",
        "assistant", "coordinator", "manager", "management", "staff", "support", "services", "operations",
        "general", "executive", "clerical", "records", "filing", "scheduling", "reception", "receptionist",
        "front", "desk", "business", "corporate", "municipal", "city", "county", "township", "village",
        "borough", "district", "government", "hall", "headquarters", "central", "main", "department",
        "division", "bureau", "unit", "section", "branch", "director", "supervisor", "chief", "officer",
        "official", "personnel", "human", "resources", "payroll", "accounting", "finance", "budget",
        "purchasing", "procurement", "contracts", "compliance", "policy", "planning", "development",
        "communications", "public", "relations", "information", "technology", "systems", "data", "analysis",
        "reporting", "documentation", "correspondence", "mail", "distribution", "logistics", "facilities",
        "building", "maintenance", "custodial", "janitorial", "supplies", "inventory", "asset", "property",
        "risk", "insurance", "legal", "counsel", "advisory", "board", "commission", "committee", "council",
        "clerk-treasurer", "treasurer", "auditor", "controller", "assessor", "registrar", "notary",
        "licensing", "permits", "registration", "certification", "archive", "document", "file", "processing",
        "workflow", "project", "program", "initiative", "strategy", "oversight", "governance", "regulatory"
    ],
    "LEGAL": [
        "court", "judge", "attorney", "lawyer", "legal", "counsel", "law", "litigation", "prosecutor",
        "defense", "defender", "probation", "trial", "justice", "judicial", "magistrate", "bailiff", "clerk",
        "solicitor", "barrister", "advocate", "paralegal", "jurisprudence", "jurisdiction", "verdict",
        "judgment", "ruling", "decree", "injunction", "lawsuit", "plaintiff", "defendant", "testimony",
        "deposition", "subpoena", "summons", "warrant", "affidavit", "brief", "pleading", "motion", "appeal",
        "appellate", "arbitration", "mediation", "settlement", "contract", "tort", "criminal", "civil",
        "statute", "ordinance", "regulation", "code", "compliance", "enforcement", "prosecution", "arraignment",
        "indictment", "conviction", "sentencing", "parole", "bail", "bond", "custody", "incarceration",
        "imprisonment", "felony", "misdemeanor", "infraction", "violation", "offense", "crime", "case",
        "docket", "filing", "petition", "writ", "certiorari", "habeas", "corpus", "discovery", "evidence",
        "witness", "jury", "tribunal", "hearing", "proceeding", "dispute", "resolution", "adjudication",
        "adjudicator", "notary", "patent", "trademark", "copyright", "intellectual", "property", "estate",
        "probate", "guardianship", "conservatorship", "family", "divorce", "custody", "adoption", "juvenile",
        "delinquency", "municipal", "superior", "supreme", "district", "circuit", "chancery", "equity"
    ],
    "SAFETY": [
        "police", "fire", "emergency", "rescue", "enforcement", "officer", "patrol", "dispatch", "911",
        "paramedic", "firefighter", "crime", "incident", "response", "sheriff", "deputy", "chief", "captain",
        "lieutenant", "sergeant", "detective", "investigator", "investigation", "security", "safety", "protection",
        "prevention", "hazmat", "hazardous", "materials", "bomb", "squad", "swat", "tactical", "operations",
        "communications", "dispatcher", "call", "center", "medical", "services", "ems", "ambulance", "first",
        "responder", "firefighting", "suppression", "arson", "inspection", "citation", "arrest", "custody",
        "jail", "corrections", "detention", "parole", "court", "bailiff", "marshal", "constable", "warden",
        "correctional", "inmate", "prisoner", "lockup", "holding", "booking", "processing", "fingerprint",
        "evidence", "forensic", "lab", "analysis", "crime", "scene", "homicide", "narcotics", "drug", "vice",
        "gang", "canine", "k9", "mounted", "marine", "aviation", "helicopter", "air", "backup", "pursuit",
        "traffic", "accident", "crash", "collision", "dui", "ticket", "violation", "parking"
    ],
    "ANIMAL": [
        "animal", "pet", "dog", "cat", "canine", "feline", "puppy", "kitten", "livestock", "cattle", "horse",
        "pig", "chicken", "goat", "sheep", "wildlife", "wild", "stray", "shelter", "rescue", "adoption",
        "foster", "fostering", "veterinary", "veterinarian", "vet", "clinic", "care", "welfare", "control",
        "enforcement", "officer", "warden", "bite", "attack", "dangerous", "vicious", "aggressive", "rabies",
        "vaccination", "vaccine", "spay", "neuter", "sterilization", "microchip", "license", "licensing",
        "registration", "tag", "permit", "kennel", "boarding", "grooming", "pound", "impound", "impoundment",
        "quarantine", "cruelty", "abuse", "neglect", "abandoned", "lost", "found", "trap", "trapping",
        "capture", "seized", "euthanasia", "humane", "leash", "collar", "cage", "crate", "enclosure", "pen",
        "corral", "barn", "farm", "farming", "ranching", "ranch", "breed", "breeding", "breeder", "exotic",
        "service", "therapy", "companion", "owner", "ownership", "guardian", "keeper", "handler", "complaint",
        "violation", "ordinance", "regulation", "nuisance", "noise", "barking", "roaming", "loose", "containment"
    ],
    "ENVIRONMENT": [
        "environmental", "sustainability", "ecology", "conservation", "green", "climate", "pollution", "emissions",
        "recycling", "waste", "renewable", "energy", "solar", "wind", "carbon", "footprint", "reduction",
        "mitigation", "adaptation", "resilience", "biodiversity", "habitat", "ecosystem", "wildlife", "species",
        "endangered", "preservation", "restoration", "remediation", "cleanup", "contamination", "hazardous",
        "toxic", "landfill", "compost", "composting", "organic", "zero", "circular", "economy", "sustainable",
        "stewardship", "natural", "resources", "water", "quality", "air", "soil", "earth", "planet", "nature",
        "flora", "fauna", "forest", "forestry", "marine", "ocean", "wetland", "watershed", "aquatic",
        "terrestrial", "land", "use", "planning", "management", "protection", "compliance", "regulation", "permit",
        "permitting", "monitoring", "assessment", "impact", "epa", "federal", "state", "local", "agency",
        "department", "division", "office", "services", "program", "initiative", "project", "outreach",
        "education", "awareness", "community", "public", "health", "hazmat", "spill", "response", "emergency"
    ],
    "SOCIAL": [
        "welfare", "assistance", "benefits", "casework", "counseling", "outreach", "advocacy", "eligibility",
        "intake", "referral", "support", "services", "community", "family", "child", "children", "youth",
        "senior", "elderly", "aging", "adult", "foster", "adoption", "protective", "abuse", "neglect",
        "intervention", "prevention", "crisis", "emergency", "housing", "homeless", "shelter", "food",
        "nutrition", "meals", "medicaid", "medicare", "insurance", "healthcare", "mental", "behavioral",
        "substance", "addiction", "recovery", "rehabilitation", "disability", "special", "needs", "developmental",
        "intellectual", "physical", "caregiver", "respite", "daycare", "childcare", "preschool", "headstart",
        "program", "aid", "relief", "grant", "subsidy", "voucher", "snap", "tanf", "wic", "employment",
        "job", "training", "workforce", "education", "literacy", "tutoring", "mentoring", "volunteer",
        "charitable", "nonprofit", "outpatient", "clinic", "therapy", "treatment", "case", "management",
        "coordination", "navigator", "liaison", "worker", "public", "client", "beneficiary", "recipient"
    ],
    "PROPERTY": [
        "assessor", "property", "tax", "taxation", "appraisal", "valuation", "assessment", "appraiser", "land",
        "real", "estate", "realty", "deed", "parcel", "lot", "plat", "survey", "surveyor", "registry", "records",
        "recording", "recorder", "title", "ownership", "owner", "taxable", "exempt", "exemption", "homestead",
        "residential", "commercial", "industrial", "agricultural", "vacant", "improved", "unimproved", "acreage",
        "square", "footage", "building", "structure", "improvement", "market", "value", "assessed", "appraised",
        "fair", "millage", "levy", "rate", "bill", "billing", "payment", "delinquent", "lien", "foreclosure",
        "sale", "auction", "tract", "subdivision", "zoning", "zone", "classification", "class", "cadastral",
        "gis", "mapping", "maps", "geographic", "spatial", "boundary", "frontage", "depth", "dimensions",
        "legal", "description", "metes", "bounds", "section", "township", "range", "quarter", "taxmap", "folio",
        "account", "number", "identification", "pin", "parcelid", "address", "location", "situs"
    ],
    "PLANNING": [
        "zoning", "permits", "land", "development", "code", "enforcement", "building", "inspection", "design",
        "subdivision", "variance", "review", "planning", "application", "rezoning", "ordinance", "compliance",
        "site", "plan", "approval", "construction", "residential", "commercial", "industrial", "setback",
        "overlay", "district", "comprehensive", "master", "urban", "rural", "growth", "boundary", "annexation",
        "density", "housing", "mixed-use", "environmental", "impact", "assessment", "traffic", "infrastructure",
        "utilities", "sewer", "water", "stormwater", "drainage", "erosion", "grading", "surveying", "platting",
        "easement", "right-of-way", "footprint", "coverage", "height", "restriction", "covenant", "property",
        "boundary", "survey", "topography", "elevation", "flood", "floodplain", "wetland", "buffer",
        "conservation", "preservation", "historic", "heritage", "landmark", "architectural", "aesthetic"
    ],
    "ELECTIONS": [
        "voting", "ballot", "poll", "polling", "election", "voter", "vote", "registration", "register",
        "candidate", "primary", "general", "absentee", "early", "commission", "commissioner", "registrar",
        "precinct", "district", "campaign", "referendum", "initiative", "recall", "canvass", "canvassing",
        "recount", "provisional", "municipal", "county", "state", "federal", "local", "partisan", "nonpartisan",
        "bipartisan", "democrat", "republican", "independent", "write-in", "incumbent", "challenger", "turnout",
        "tabulation", "tabulate", "tally", "count", "counting", "certify", "certification", "results",
        "outcome", "winner", "runoff", "special", "electoral", "elector", "suffrage", "franchise", "polling-place",
        "voting-booth", "machine", "electronic", "paper", "mail-in", "postmark", "deadline", "registration-deadline",
        "eligibility", "eligible", "qualified", "citizenship", "residency", "identification", "verify",
        "signature", "affidavit", "superintendent", "board", "authority", "official", "worker", "judge"
    ],
    "BURIAL": [
        "cemetery", "grave", "burial", "interment", "cremation", "headstone", "plot", "mausoleum", "mortuary",
        "funeral", "deceased", "casket", "coffin", "urn", "memorial", "monument", "tombstone", "gravestone",
        "marker", "crypt", "columbarium", "niche", "sepulcher", "vault", "graveyard", "necropolis", "churchyard",
        "potter", "indigent", "pauper", "remains", "corpse", "cadaver", "body", "internment", "entombment",
        "inurnment", "exhumation", "disinterment", "reinterment", "cremains", "ashes", "scattering", "epitaph",
        "inscription", "engraving", "perpetual", "endowment", "maintenance", "landscaping", "grounds", "sexton",
        "caretaker", "groundskeeper", "superintendent", "undertaker", "embalmer", "mortician", "pallbearer",
        "hearse", "procession", "visitation", "wake", "viewing", "service", "ceremony", "rites", "ritual",
        "obsequies", "commemoration", "remembrance", "tribute", "eulogy", "obituary", "death", "dying",
        "passing", "demise", "bereavement", "mourning", "grief", "condolence", "sympathy", "family"
    ],
    "RECREATION": [
        "park", "parks", "recreation", "rec", "playground", "sports", "athletic", "athletics", "field",
        "stadium", "arena", "gym", "gymnasium", "fitness", "wellness", "pool", "swimming", "aquatic", "aquatics",
        "trail", "hiking", "biking", "bike", "walking", "greenway", "greenways", "pathway", "paths", "baseball",
        "softball", "soccer", "football", "basketball", "tennis", "volleyball", "golf", "course", "league",
        "leagues", "tournament", "tournaments", "camp", "camps", "summer", "youth", "senior", "community",
        "center", "centers", "facility", "facilities", "complex", "pavilion", "pavilions", "shelter", "picnic",
        "bbq", "grill", "nature", "natural", "wildlife", "conservation", "preserve", "open", "space", "green",
        "lawn", "grass", "turf", "court", "courts", "diamond", "diamonds", "track", "running", "jogging",
        "exercise", "workout", "program", "programs", "activity", "activities", "event", "events", "rental",
        "rentals", "booking", "reservation", "permit", "permits", "maintenance", "grounds"
    ],
    "MAINTENANCE": [
        "maintenance", "repair", "repairs", "facilities", "facility", "custodial", "custodian", "janitorial",
        "janitor", "grounds", "groundskeeper", "landscaping", "mechanical", "hvac", "heating", "ventilation",
        "cooling", "plumbing", "plumber", "electrical", "electrician", "building", "buildings", "upkeep",
        "infrastructure", "operations", "equipment", "tools", "carpentry", "carpenter", "painting", "painter",
        "welding", "welder", "locksmith", "roofing", "flooring", "walls", "doors", "windows", "boiler",
        "furnace", "chiller", "refrigeration", "air", "conditioning", "ductwork", "piping", "pipes", "valves",
        "pumps", "motors", "generators", "elevator", "escalator", "lighting", "fixtures", "circuit", "breaker",
        "wiring", "outlets", "switches", "cleaning", "sanitation", "trash", "waste", "recycling", "disposal",
        "sweeping", "mopping", "dusting", "vacuuming", "polishing", "disinfecting", "sanitizing", "supplies"
    ]
}

# Add new tokens
added_count = 0
for tag, words in expansions.items():
    for word in words:
        word_lower = word.lower()
        if word_lower not in semantic_data:
            semantic_data[word_lower] = tag
            added_count += 1

print(f"Added {added_count} new tokens")
print(f"Total tokens now: {len(semantic_data)}")

# Save updated semantic tokens
with gzip.open(DATA_DIR / "semantic_tokens.json.gz", "wt", encoding="utf-8") as f:
    json.dump(semantic_data, f, ensure_ascii=False)

print("Saved updated semantic_tokens.json.gz")

# Show summary by tag
tag_counts = {}
for v in semantic_data.values():
    tag_counts[v] = tag_counts.get(v, 0) + 1

print("\nToken summary by tag:")
for tag in sorted(tag_counts.keys()):
    print(f"  {tag:15} {tag_counts[tag]:4} tokens")
