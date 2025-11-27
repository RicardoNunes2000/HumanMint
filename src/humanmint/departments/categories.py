"""
Department category classification for HumanMint.

Classifies canonical departments into logical categories like Public Safety,
Finance, Administration, Education, etc.
"""

from typing import Optional

# Department-to-category mapping
DEPARTMENT_CATEGORIES = {
    # Public Safety & Law Enforcement
    "Police": "Public Safety",
    "Fire": "Public Safety",
    "Emergency Management": "Public Safety",
    "Emergency Communications": "Public Safety",
    "Coroner": "Public Safety",
    "Public Safety": "Public Safety",
    # Courts & Legal
    "City Attorney": "Courts & Legal",
    "District Attorney": "Courts & Legal",
    "Public Defender": "Courts & Legal",
    "Municipal Court": "Courts & Legal",
    "District Court": "Courts & Legal",
    "Juvenile Court": "Courts & Legal",
    "Clerk of Courts": "Courts & Legal",
    "Probation": "Courts & Legal",
    # Administration & Management
    "Administration": "Administration",
    "City Manager": "Administration",
    "Mayor's Office": "Administration",
    "City Clerk": "Administration",
    "Human Resources": "Administration",
    "Superintendent": "Administration",
    "City Council": "Administration",
    # Finance & Budget
    "Finance": "Finance",
    "Budget": "Finance",
    "Treasurer": "Finance",
    "Auditor": "Finance",
    "Risk Management": "Finance",
    "Purchasing": "Finance",
    # Public Works & Infrastructure
    "Public Works": "Infrastructure",
    "Streets & Roads": "Infrastructure",
    "Water": "Infrastructure",
    "Wastewater": "Infrastructure",
    "Utilities": "Infrastructure",
    "Stormwater": "Infrastructure",
    "Solid Waste": "Infrastructure",
    "Engineering": "Infrastructure",
    "Facilities Management": "Infrastructure",
    "Fleet Management": "Infrastructure",
    # Planning & Development
    "Planning": "Planning & Development",
    "Community Development": "Planning & Development",
    "Building & Inspections": "Planning & Development",
    "Zoning": "Planning & Development",
    # Education
    "Board of Education": "Education",
    "Elementary School": "Education",
    "Middle School": "Education",
    "High School": "Education",
    "Curriculum & Instruction": "Education",
    "Special Education": "Education",
    "Student Services": "Education",
    "Food Service": "Education",
    # Parks & Recreation
    "Parks & Recreation": "Parks & Recreation",
    "Athletics": "Parks & Recreation",
    "Library": "Parks & Recreation",
    # Health & Human Services
    "Health": "Health & Human Services",
    "Human Services": "Health & Human Services",
    "Senior Services": "Health & Human Services",
    "Veterans Services": "Health & Human Services",
    # Other Services
    "Assessor": "Other",
    "Elections": "Other",
    "Communications": "Other",
    "Information Technology": "Other",
    "Airport": "Other",
    "Animal Control": "Other",
    "Cemetery": "Other",
    "Transportation Services": "Other",
}


def get_department_category(dept: str) -> Optional[str]:
    """
    Get the category for a canonical department name.

    Example:
        >>> get_department_category("Police")
        "Public Safety"
        >>> get_department_category("Water")
        "Infrastructure"
        >>> get_department_category("Unknown Department")
        None

    Args:
        dept: Canonical department name.

    Returns:
        Optional[str]: Category name, or None if the department is not
                      recognized.
    """
    return DEPARTMENT_CATEGORIES.get(dept)


def get_all_categories() -> set[str]:
    """
    Get all unique department categories.

    Returns:
        set[str]: Set of all category names.
    """
    return set(DEPARTMENT_CATEGORIES.values())


def get_departments_by_category(category: str) -> list[str]:
    """
    Get all departments belonging to a specific category.

    Example:
        >>> get_departments_by_category("Public Safety")
        ["Police", "Fire", "Emergency Management", ...]

    Args:
        category: Category name.

    Returns:
        list[str]: List of canonical departments in that category, sorted
                  alphabetically.
    """
    departments = [
        dept for dept, cat in DEPARTMENT_CATEGORIES.items() if cat == category
    ]
    return sorted(departments)


def categorize_departments(dept_names: list[str]) -> dict[str, Optional[str]]:
    """
    Categorize multiple department names.

    Useful for batch processing to assign categories to a list of
    departments.

    Example:
        >>> categorize_departments(["Police", "Water", "Unknown"])
        {
            "Police": "Public Safety",
            "Water": "Infrastructure",
            "Unknown": None
        }

    Args:
        dept_names: List of canonical department names.

    Returns:
        dict[str, Optional[str]]: Mapping of department names to their
                                  categories (None if not recognized).
    """
    return {dept: get_department_category(dept) for dept in dept_names}
