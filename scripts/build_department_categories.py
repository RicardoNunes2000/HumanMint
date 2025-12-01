"""
Build department_categories.json.gz from semantic tokens and canonical departments.

This script generates category mappings for all canonical departments by:
1. Extracting semantic tags from department names
2. Mapping tags to high-level categories
3. Using keyword-based fallbacks for untagged departments
4. Saving as department_categories.json.gz
"""

import json
import gzip
from pathlib import Path

# Assume we're running from repo root
REPO_ROOT = Path(__file__).parent.parent
DATA_DIR = REPO_ROOT / "src" / "humanmint" / "data"

# Semantic tag to category mapping
SEMANTIC_TO_CATEGORY = {
    "EDU": "Education",
    "IT": "Technology",
    "HEALTH": "Health & Human Services",
    "FINANCE": "Finance",
    "LEGAL": "Courts & Legal",
    "SAFETY": "Public Safety",
    "INFRA": "Infrastructure",
}

# Keyword-based fallback categories (for untagged departments)
# Order matters: longer/more specific keywords should come first
KEYWORD_CATEGORY_MAP = {
    # Infrastructure & Public Works
    "water": "Infrastructure",
    "wastewater": "Infrastructure",
    "sewer": "Infrastructure",
    "stormwater": "Infrastructure",
    "street": "Infrastructure",
    "road": "Infrastructure",
    "public works": "Infrastructure",
    "utilities": "Infrastructure",
    "maintenance": "Infrastructure",
    "fleet": "Infrastructure",
    "transportation": "Infrastructure",
    "facilities": "Infrastructure",
    "environmental": "Infrastructure",

    # Administration
    "administration": "Administration",
    "mayor": "Administration",
    "manager": "Administration",
    "clerk": "Administration",
    "council": "Administration",
    "board": "Administration",
    "election": "Administration",
    "superintendent": "Administration",
    "human resources": "Administration",
    "treasurer": "Finance",

    # Education & Schools
    "school": "Education",
    "education": "Education",
    "library": "Education",
    "curriculum": "Education",
    "student": "Education",
    "food service": "Education",

    # Planning & Development
    "planning": "Planning & Development",
    "zoning": "Planning & Development",
    "code": "Planning & Development",
    "community development": "Planning & Development",
    "development": "Planning & Development",
    "building": "Planning & Development",
    "inspection": "Planning & Development",
    "engineering": "Planning & Development",

    # Courts & Legal
    "attorney": "Courts & Legal",
    "court": "Courts & Legal",
    "defender": "Courts & Legal",
    "probation": "Courts & Legal",

    # Finance
    "finance": "Finance",
    "budget": "Finance",
    "auditor": "Finance",
    "purchasing": "Finance",
    "risk management": "Finance",

    # Health & Services
    "health": "Health & Human Services",
    "human services": "Health & Human Services",
    "senior": "Health & Human Services",
    "veterans": "Health & Human Services",

    # Parks & Recreation
    "parks": "Parks & Recreation",
    "recreation": "Parks & Recreation",
    "athletics": "Parks & Recreation",

    # Utilities & Services (complementary)
    "utility": "Infrastructure",
    "solid waste": "Infrastructure",
    "waste": "Infrastructure",

    # Other Services
    "airport": "Other",
    "animal": "Other",
    "assessor": "Other",
    "cemetery": "Other",
    "coroner": "Other",
    "communication": "Technology",
}


def load_json_gz(path):
    """Load a .json.gz file."""
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def save_json_gz(data, path):
    """Save data as .json.gz file."""
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def extract_tokens(text):
    """Simple token extraction (lowercase, split on non-alphanumeric)."""
    import re
    tokens = re.findall(r"\b\w+\b", text.lower())
    return tokens


def get_semantic_tags_for_dept(dept_name, semantic_data):
    """Extract semantic tags from a department name."""
    tokens = extract_tokens(dept_name)
    tags = set()
    for token in tokens:
        if token in semantic_data:
            tag = semantic_data[token]
            if tag not in ("NULL", "GENERIC", "CATEGORY"):
                tags.add(tag)
    return tags


def get_fallback_category(dept_name):
    """Use keyword matching for untagged departments."""
    dept_lower = dept_name.lower()
    # Sort keywords by length (longest first) to match more specific phrases
    sorted_keywords = sorted(KEYWORD_CATEGORY_MAP.keys(), key=len, reverse=True)
    for keyword in sorted_keywords:
        if keyword in dept_lower:
            return KEYWORD_CATEGORY_MAP[keyword]

    # If no exact keyword match, look for word boundaries
    # This helps match "Public Safety Communications" to "SAFETY" via "safety"
    words = dept_lower.split()
    for word in words:
        if word in KEYWORD_CATEGORY_MAP:
            return KEYWORD_CATEGORY_MAP[word]

    return "Other"


def main():
    """Generate department categories from semantic tokens."""
    print("Loading semantic tokens...")
    semantic_data = load_json_gz(DATA_DIR / "semantic_tokens.json.gz")

    print("Loading canonical departments...")
    from humanmint.departments.data_loader import get_canonical_departments

    canonicals = get_canonical_departments()

    print(f"Building categories for {len(canonicals)} departments...")
    categories = {}

    for dept in canonicals:
        # Try to get tags from semantic data
        tags = get_semantic_tags_for_dept(dept, semantic_data)

        if tags:
            # If we have semantic tags, map the first one to a category
            tag = list(tags)[0]  # Take first tag
            category = SEMANTIC_TO_CATEGORY.get(tag, "Other")
        else:
            # Fallback to keyword matching
            category = get_fallback_category(dept)

        categories[dept] = category
        print(f"  {dept:35} -> {category}")

    # Save to file
    output_path = DATA_DIR / "department_categories.json.gz"
    save_json_gz(categories, output_path)
    print(f"\nSaved {len(categories)} categories to {output_path}")

    # Print summary
    category_counts = {}
    for cat in categories.values():
        category_counts[cat] = category_counts.get(cat, 0) + 1

    print("\nCategory summary:")
    for cat in sorted(category_counts.keys()):
        print(f"  {cat:35} ({category_counts[cat]:2} departments)")


if __name__ == "__main__":
    main()
