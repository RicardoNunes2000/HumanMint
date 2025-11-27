"""Comprehensive test suite for department matching edge cases."""

import sys
sys.path.insert(0, "src")

from humanmint.departments.matching import find_best_match, find_all_matches

# Test cases: (input, expected_canonical, description)
test_cases = [
    # Basic cases (should work before and after)
    ("Public Works", "Public Works", "Exact match"),
    ("Police", "Police", "Exact canonical"),
    ("005 - Public Wrks Dept", "Public Works", "Codes and abbreviations"),

    # Typo cases (the main issue we're fixing)
    ("Polce", "Police", "Single letter typo"),
    ("Polce Dept", "Police", "Typo with extra word"),
    ("Polce Department", "Police", "Typo with full word"),
    ("Polce - North Precinct", "Police", "Typo with additional context"),

    # Extra words (token_set_ratio should help)
    ("Public Works Department", "Public Works", "Extra word"),
    ("Police Force", "Police", "Alternative phrasing"),
    ("Fire Department Service", "Fire", "Multiple extra words"),

    # Case variations
    ("POLICE", "Police", "All caps"),
    ("public works", "Public Works", "All lowercase"),
    ("PoLiCe", "Police", "Mixed case"),

    # Abbreviations
    ("PW", "Public Works", "Two-letter abbreviation"),
    ("PD", "Police", "Two-letter abbreviation"),

    # Codes and prefixes (handled by normalize_department)
    ("001 - Finance", "Finance", "Code prefix"),
    ("Finance Dept", "Finance", "Dept suffix"),

    # Similar departments (should not confuse)
    ("Public Safety", "Public Safety", "Public Safety (not Works)"),
    ("Parks & Recreation", "Parks & Recreation", "Ampersand"),
]

print("=" * 100)
print("DEPARTMENT MATCHING EDGE CASES TEST SUITE")
print("=" * 100)

passed = 0
failed = 0
failures = []

for input_val, expected, description in test_cases:
    result = find_best_match(input_val, threshold=0.6)
    status = "[PASS]" if result == expected else "[FAIL]"

    if result == expected:
        passed += 1
    else:
        failed += 1
        failures.append((input_val, expected, result, description))

    print(f"\n{status} | {description}")
    print(f"       Input: '{input_val}'")
    print(f"       Expected: '{expected}'")
    print(f"       Got: '{result}'")

print("\n" + "=" * 100)
print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} total")
print("=" * 100)

if failures:
    print("\nFAILED CASES:")
    for input_val, expected, got, desc in failures:
        print(f"\n  • {desc}")
        print(f"    Input: '{input_val}' → Expected: '{expected}', Got: '{got}'")

        # Show alternatives
        alternatives = find_all_matches(input_val, threshold=0.5, top_n=3)
        if alternatives and alternatives[0] != got:
            print(f"    Top alternatives: {alternatives}")
else:
    print("\n[SUCCESS] ALL TESTS PASSED!")
