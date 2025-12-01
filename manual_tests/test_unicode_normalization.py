"""Test Unicode normalization in default pipeline."""

import sys

sys.path.insert(0, "src")

from humanmint import mint

print("=" * 100)
print("UNICODE NORMALIZATION TEST SUITE")
print("=" * 100)

# Test cases: Unicode accents and special punctuation should be normalized by default
test_cases = [
    {
        "input": "Dr. Andréa López",
        "expected_first": "Andrea",
        "expected_last": "Lopez",
        "description": "Spanish accents (é, ó)"
    },
    {
        "input": "José García",
        "expected_first": "Jose",
        "expected_last": "Garcia",
        "description": "Spanish accents (é, í, á)"
    },
    {
        "input": "Café François",
        "expected_first": "Cafe",
        "expected_last": "Francois",
        "description": "French accents (é, ç)"
    },
    {
        "input": "Müller Schmidt",
        "expected_first": "Muller",
        "expected_last": "Schmidt",
        "description": "German umlaut (ü)"
    },
    {
        "input": "López–Martínez",
        "expected_first": "Lopez",
        "expected_last": "Martinez",
        "description": "Unicode dashes (– becomes -) + hyphenated name"
    },
    {
        "input": "O'Brien",
        "expected_first": "O",
        "expected_last": "Brien",
        "description": "Apostrophe/smart quote in name"
    },
    {
        "input": "John Manager",
        "expected_first": "John",
        "expected_last": "Manager",
        "description": "Two-word name with spaces"
    },
    {
        "input": "Péter Kovács",
        "expected_first": "Peter",
        "expected_last": "Kovacs",
        "description": "Hungarian accents"
    },
    {
        "input": "Åse Svendsen",
        "expected_first": "Ase",
        "expected_last": "Svendsen",
        "description": "Scandinavian rings (å)"
    },
    {
        "input": "Björn Svensén",
        "expected_first": "Bjorn",
        "expected_last": "Svensen",
        "description": "Nordic characters (ö, é)"
    },
]

print("\n[TEST] Unicode normalization happens by default (no flag needed)")
print("-" * 100)

passed = 0
failed = 0

for case in test_cases:
    result = mint(name=case["input"])

    first_match = result.name['first'] == case["expected_first"]
    last_match = result.name['last'] == case["expected_last"]
    status = "[PASS]" if (first_match and last_match) else "[FAIL]"

    if first_match and last_match:
        passed += 1
    else:
        failed += 1

    print(f"\n{status} | {case['description']}")
    print(f"       Input:    '{case['input']}'")
    print(f"       Expected: {case['expected_first']} {case['expected_last']}")
    print(f"       Got:      {result.name['first']} {result.name['last']}")

print(f"\n" + "=" * 100)
print(f"RESULTS: {passed}/{len(test_cases)} passed")
print("=" * 100)

if failed == 0:
    print("\n[SUCCESS] All Unicode normalization tests passed!")
else:
    print(f"\n[WARNING] {failed} test(s) failed")

# Additional test: Verify aggressive_clean still works with normalized Unicode
print("\n" + "=" * 100)
print("[TEST] Unicode normalization + aggressive_clean work together")
print("-" * 100)

corrupted_unicode = "### TEMP ### Dr. Andréa López; DROP TABLES"
result_aggressive = mint(name=corrupted_unicode, aggressive_clean=True)

print(f"\nInput: '{corrupted_unicode}'")
print(f"Result (aggressive_clean=True):")
print(f"  First: {result_aggressive.name['first']}")
print(f"  Last: {result_aggressive.name['last']}")
print(f"  Full: {result_aggressive.name['full']}")

if (result_aggressive.name['first'] == "Andrea" and
    result_aggressive.name['last'] == "Lopez"):
    print("\n[SUCCESS] Unicode normalization + aggressive_clean work together!")
else:
    print(f"\n[FAIL] Expected 'Andrea Lopez' but got '{result_aggressive.name['first']} {result_aggressive.name['last']}'")

# Test: Verify it works with the extreme edge case from the requirements
print("\n" + "=" * 100)
print("[TEST] Extreme edge case from requirements")
print("-" * 100)

edge_case = "Dr. Andréa   López–Martínez (TEMP USER)"
result_edge = mint(name=edge_case)

print(f"\nInput: '{edge_case}'")
print(f"Result:")
print(f"  First: {result_edge.name['first']}")
print(f"  Last: {result_edge.name['last']}")
print(f"  Full: {result_edge.name['full']}")

if (result_edge.name['first'] == "Andrea" and
    result_edge.name['last'] == "Lopez-martinez"):
    print("\n[SUCCESS] Edge case handled correctly!")
else:
    print(f"\n[INFO] Got: {result_edge.name['first']} {result_edge.name['last']}")
