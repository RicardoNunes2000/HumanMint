"""Constants for name normalization and parsing."""

# Generational suffixes that should remain part of the standardized name
GENERATIONAL_SUFFIXES = set()
# Professional/credential suffixes that should be stripped from standardized names
CREDENTIAL_SUFFIXES = set()
# Indicators that a string is likely an organization/company rather than a person
CORPORATE_TERMS = set()
# Department/office phrases that should be treated as non-person names
NON_PERSON_PHRASES = set()
# Roman numeral suffixes that should be uppercased in display
ROMAN_NUMERALS = {}
# Title prefixes to strip
TITLE_PREFIXES = set()
# Placeholder values that should be treated as empty/unknown
PLACEHOLDER_NAMES = set()
