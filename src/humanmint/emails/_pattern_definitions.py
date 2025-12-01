"""
Email pattern definitions for HumanMint.

Defines the 13 supported email naming patterns with documentation and examples.
"""

from typing import Any, Dict

# Pattern metadata: name, description, and examples
PATTERNS: Dict[str, Dict[str, Any]] = {
    "f_l": {
        "name": "First initial + Last name (underscore)",
        "description": "First letter of first name + underscore + lowercase last name",
        "examples": [
            ("Alice Johnson", "a_johnson"),
            ("Mark Stone", "m_stone"),
            ("Jane Doe", "j_doe"),
        ],
    },
    "fl": {
        "name": "First initial + Last name (concatenated)",
        "description": "First letter of first name + lowercase last name, no separator",
        "examples": [
            ("Alice Johnson", "ajohnson"),
            ("Mark Stone", "mstone"),
            ("Jane Doe", "jdoe"),
        ],
    },
    "f.l": {
        "name": "First initial + Last name (dot)",
        "description": "First letter of first name + dot + lowercase last name",
        "examples": [
            ("Alice Johnson", "a.johnson"),
            ("Mark Stone", "m.stone"),
            ("Jane Doe", "j.doe"),
        ],
    },
    "f-l": {
        "name": "First initial + Last name (hyphen)",
        "description": "First letter of first name + hyphen + lowercase last name",
        "examples": [
            ("Alice Johnson", "a-johnson"),
            ("Mark Stone", "m-stone"),
            ("Jane Doe", "j-doe"),
        ],
    },
    "first_last": {
        "name": "Full first + Last name (underscore)",
        "description": "Full first name + underscore + lowercase last name",
        "examples": [
            ("Alice Johnson", "alice_johnson"),
            ("Mark Stone", "mark_stone"),
            ("Jane Doe", "jane_doe"),
        ],
    },
    "first.last": {
        "name": "Full first + Last name (dot)",
        "description": "Full first name + dot + lowercase last name",
        "examples": [
            ("Alice Johnson", "alice.johnson"),
            ("Mark Stone", "mark.stone"),
            ("Jane Doe", "jane.doe"),
        ],
    },
    "first-last": {
        "name": "Full first + Last name (hyphen)",
        "description": "Full first name + hyphen + lowercase last name",
        "examples": [
            ("Alice Johnson", "alice-johnson"),
            ("Mark Stone", "mark-stone"),
            ("Jane Doe", "jane-doe"),
        ],
    },
    "firstlast": {
        "name": "First + Last name (concatenated)",
        "description": "Full first name + lowercase last name, no separator",
        "examples": [
            ("Alice Johnson", "alicejohnson"),
            ("Mark Stone", "markstone"),
            ("Jane Doe", "janedoe"),
        ],
    },
    "l_f": {
        "name": "Last name + First initial (underscore)",
        "description": "Lowercase last name + underscore + first letter of first name",
        "examples": [
            ("Alice Johnson", "johnson_a"),
            ("Mark Stone", "stone_m"),
            ("Jane Doe", "doe_j"),
        ],
    },
    "lf": {
        "name": "Last name + First initial (concatenated)",
        "description": "Lowercase last name + first letter of first name, no separator",
        "examples": [
            ("Alice Johnson", "johnsona"),
            ("Mark Stone", "stonem"),
            ("Jane Doe", "doej"),
        ],
    },
    "l.f": {
        "name": "Last name + First initial (dot)",
        "description": "Lowercase last name + dot + first letter of first name",
        "examples": [
            ("Alice Johnson", "johnson.a"),
            ("Mark Stone", "stone.m"),
            ("Jane Doe", "doe.j"),
        ],
    },
    "last_first": {
        "name": "Last + Full first (underscore)",
        "description": "Lowercase last name + underscore + full first name",
        "examples": [
            ("Alice Johnson", "johnson_alice"),
            ("Mark Stone", "stone_mark"),
            ("Jane Doe", "doe_jane"),
        ],
    },
    "last.first": {
        "name": "Last + Full first (dot)",
        "description": "Lowercase last name + dot + full first name",
        "examples": [
            ("Alice Johnson", "johnson.alice"),
            ("Mark Stone", "stone.mark"),
            ("Jane Doe", "doe.jane"),
        ],
    },
}
