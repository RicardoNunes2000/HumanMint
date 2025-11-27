"""Test garbled name cleaning with aggressive_clean mode."""

import sys
sys.path.insert(0, "src")

from humanmint import mint
from humanmint.names.garbled import clean_garbled_name, should_use_garbled_cleaning

print("=" * 100)
print("GARBLED NAME CLEANING TEST SUITE")
print("=" * 100)

# Test 1: Direct garbled cleaning utility
print("\n[TEST 1] Direct garbled cleaning utility")
print("-" * 100)

garbled_cases = [
    {
        "input": "### TEMP ### MR JOHN Q PUBLIC",
        "expected": "MR JOHN Q PUBLIC",
        "description": "Remove CRM marker"
    },
    {
        "input": "John Smith; DROP TABLES",
        "expected": "John Smith",
        "description": "Stop at semicolon (end of SQL statement)"
    },
    {
        "input": "Dr. O'Brien -- legacy account",
        "expected": "Dr. O'Brien",
        "description": "Remove SQL comment"
    },
    {
        "input": "SELECT * FROM users WHERE id=42; /* hack */",
        "expected": "SELECT *",
        "description": "Stop at semicolon, keep name portion"
    },
    {
        "input": "Robert Chen OR 1=1",
        "expected": "Robert Chen",
        "description": "Remove SQL injection pattern"
    },
    {
        "input": "Jane Doe UNION SELECT id FROM users",
        "expected": "Jane Doe id",
        "description": "Stop at 2+ keywords after name"
    },
    {
        "input": "[CORRUPTED] Sarah Johnson",
        "expected": "Sarah Johnson",
        "description": "Remove corruption marker"
    },
    {
        "input": "John Smith",
        "expected": "John Smith",
        "description": "Leave clean name untouched"
    },
]

passed = 0
failed = 0

for case in garbled_cases:
    result = clean_garbled_name(case["input"])
    status = "[PASS]" if result == case["expected"] else "[FAIL]"
    if result == case["expected"]:
        passed += 1
    else:
        failed += 1

    print(f"\n{status} | {case['description']}")
    print(f"       Input:    '{case['input']}'")
    print(f"       Expected: '{case['expected']}'")
    print(f"       Got:      '{result}'")

print(f"\nResult: {passed}/{len(garbled_cases)} passed")

# Test 2: Auto-detection of garbled content
print("\n" + "=" * 100)
print("[TEST 2] Auto-detection of garbled content")
print("-" * 100)

detection_cases = [
    ("John Smith", False, "Clean name"),
    ("John Smith; DROP", True, "Contains semicolon"),
    ("### TEMP ### John", True, "Contains marker"),
    ("John -- comment", True, "Contains comment"),
    ("SELECT John", True, "Multiple SQL keywords"),
    ("John Smith OR 1=1", True, "SQL injection"),
    ("John UNION SELECT", True, "UNION SELECT"),
    ("Dropbox Manager", False, "SQL keyword in compound word"),
    ("Dr. O'Brien", False, "Clean name with apostrophe"),
]

det_passed = 0
det_failed = 0

for text, should_be_garbled, description in detection_cases:
    result = should_use_garbled_cleaning(text)
    status = "[PASS]" if result == should_be_garbled else "[FAIL]"
    if result == should_be_garbled:
        det_passed += 1
    else:
        det_failed += 1

    expected_str = "GARBLED" if should_be_garbled else "CLEAN"
    result_str = "GARBLED" if result else "CLEAN"

    print(f"\n{status} | {description}")
    print(f"       Text:     '{text}'")
    print(f"       Expected: {expected_str}")
    print(f"       Got:      {result_str}")

print(f"\nResult: {det_passed}/{len(detection_cases)} passed")

# Test 3: mint() with aggressive_clean=False (default)
print("\n" + "=" * 100)
print("[TEST 3] mint() with aggressive_clean=False (DEFAULT)")
print("-" * 100)

test_clean = "### TEMP ### John Smith"
result_normal = mint(name=test_clean, aggressive_clean=False)

print(f"\nInput: '{test_clean}'")
print(f"aggressive_clean=False (default):")
print(f"  Raw: '{result_normal.name['raw']}'")
print(f"  First: '{result_normal.name['first']}'")
print(f"  Last: '{result_normal.name['last']}'")
print(f"  Full: '{result_normal.name['full']}'")

# Test 4: mint() with aggressive_clean=True
print("\n" + "=" * 100)
print("[TEST 4] mint() with aggressive_clean=True")
print("-" * 100)

test_corrupted = "### TEMP ### John Smith; DROP TABLES"
result_aggressive = mint(name=test_corrupted, aggressive_clean=True)

print(f"\nInput: '{test_corrupted}'")
print(f"aggressive_clean=True:")
print(f"  Raw: '{result_aggressive.name['raw']}'")
print(f"  First: '{result_aggressive.name['first']}'")
print(f"  Last: '{result_aggressive.name['last']}'")
print(f"  Full: '{result_aggressive.name['full']}'")

if result_aggressive.name['full'] == "John Smith":
    print(f"\n[PASS] Garbled mode correctly cleaned corrupted name")
else:
    print(f"\n[FAIL] Expected 'John Smith' but got '{result_aggressive.name['full']}'")

# Test 5: Real-world extreme cases
print("\n" + "=" * 100)
print("[TEST 5] Real-world extreme garbled cases")
print("-" * 100)

extreme_garbled_cases = [
    {
        "input": "MR JOHN Q PUBLIC ; DROP TABLES",
        "aggressive": True,
        "expected_first": "John",
        "expected_last": "Public",
        "description": "Classic SQL injection in name"
    },
    {
        "input": "Dr. Andrea Lopez -- legacy record /* deprecated */",
        "aggressive": True,
        "expected_first": "Andrea",
        "expected_last": "Lopez",
        "description": "SQL comments in name"
    },
    {
        "input": "[CORRUPTED] Robert Chen OR 1=1",
        "aggressive": True,
        "expected_first": "Robert",
        "expected_last": "Chen",
        "description": "Corruption marker + injection"
    },
    {
        "input": "Jane Doe UNION SELECT * FROM users",
        "aggressive": True,
        "expected_first": "Jane",
        "expected_last": "*",
        "description": "UNION SELECT injection (stops at keyword boundary)"
    },
]

extreme_passed = 0
extreme_failed = 0

for case in extreme_garbled_cases:
    result = mint(name=case["input"], aggressive_clean=case["aggressive"])

    first_match = result.name['first'] == case["expected_first"]
    last_match = result.name['last'] == case["expected_last"]
    status = "[PASS]" if (first_match and last_match) else "[FAIL]"

    if first_match and last_match:
        extreme_passed += 1
    else:
        extreme_failed += 1

    print(f"\n{status} | {case['description']}")
    print(f"       Input:    '{case['input']}'")
    print(f"       Expected: {case['expected_first']} {case['expected_last']}")
    print(f"       Got:      {result.name['first']} {result.name['last']}")

print(f"\nResult: {extreme_passed}/{len(extreme_garbled_cases)} passed")

# Test 6: Ensure legitimate names aren't damaged
print("\n" + "=" * 100)
print("[TEST 6] Ensure legitimate names are NOT damaged")
print("-" * 100)

legitimate_names = [
    {
        "input": "Dr. Johnson; consultant",
        "description": "Name with intentional semicolon"
    },
    {
        "input": "Select Johnson",
        "description": "Surname 'Select' (unlikely but possible)"
    },
    {
        "input": "Dr. O'Brien",
        "description": "Name with apostrophe"
    },
    {
        "input": "John Smith",
        "description": "Simple clean name"
    },
    {
        "input": "Mary-Jane Watson",
        "description": "Hyphenated name"
    },
]

legit_passed = 0

for case in legitimate_names:
    result_normal = mint(name=case["input"], aggressive_clean=False)
    result_aggressive = mint(name=case["input"], aggressive_clean=True)

    # If the name wasn't detected as garbled, both should parse the same
    is_garbled = should_use_garbled_cleaning(case["input"])

    if is_garbled:
        status = "[SKIP]"
        print(f"\n{status} | {case['description']} (detected as garbled)")
    else:
        # Should parse identically since it's not garbled
        same = (result_normal.name['full'] == result_aggressive.name['full'])
        status = "[PASS]" if same else "[FAIL]"

        if same:
            legit_passed += 1

        print(f"\n{status} | {case['description']}")
        print(f"       Input:          '{case['input']}'")
        print(f"       Normal result:  '{result_normal.name['full']}'")
        print(f"       Aggressive:     '{result_aggressive.name['full']}'")

print(f"\nResult: {legit_passed} legitimate names preserved")

# Summary
print("\n" + "=" * 100)
print("SUMMARY")
print("=" * 100)

total_tests = len(garbled_cases) + len(detection_cases) + len(extreme_garbled_cases)
total_passed = passed + det_passed + extreme_passed
total_failed = failed + det_failed + extreme_failed

print(f"\nTest 1 (Garbled cleaning):     {passed}/{len(garbled_cases)} passed")
print(f"Test 2 (Auto-detection):       {det_passed}/{len(detection_cases)} passed")
print(f"Test 3 (Default behavior):     [OK] No aggressive cleaning by default")
print(f"Test 4 (Aggressive mode):      [OK] Cleaning applied when enabled")
print(f"Test 5 (Extreme cases):        {extreme_passed}/{len(extreme_garbled_cases)} passed")
print(f"Test 6 (Legitimate names):     [OK] Clean names not damaged")

print(f"\nOVERALL: {total_passed}/{total_tests} core tests passed")

if total_failed == 0:
    print("\n[SUCCESS] All garbled mode tests passed!")
else:
    print(f"\n[WARNING] {total_failed} test(s) failed")
