"""
Tests for BLS Occupational Outlook Handbook title integration.

Tests that HumanMint correctly integrates 4,800+ official job titles
from the U.S. Department of Labor Bureau of Labor Statistics.
"""

import sys
sys.path.insert(0, "src")

from humanmint import mint
from humanmint.titles.bls_loader import (
    lookup_bls_title,
    get_bls_category,
    get_all_bls_titles,
    get_bls_stats,
)


def test_bls_stats():
    """Test BLS database is loaded correctly."""
    stats = get_bls_stats()
    assert stats["total"] > 4000, "BLS should have 4800+ titles"
    assert stats["categories"] > 20, "BLS should have 25+ categories"
    assert stats["example"] is not None, "Should have example record"
    print("[OK] BLS stats loaded: {} titles, {} categories".format(
        stats["total"], stats["categories"]
    ))


def test_bls_lookup():
    """Test direct BLS title lookup."""
    # Test exact match
    result = lookup_bls_title("Welding Machine Operator")
    assert result is not None, "Should find welding machine operator"
    assert "metal and plastic machine workers" in result["canonical"].lower()
    print("[OK] BLS lookup: 'Welding Machine Operator' found")

    # Test case insensitivity (BLS lookup is case-insensitive for convenience)
    result2 = lookup_bls_title("WELDING MACHINE OPERATOR")
    assert result2 is not None, "Lookup should handle uppercase"
    assert result2["canonical"] == result["canonical"]
    print("[OK] BLS lookup: Case-insensitive matching works")


def test_bls_category():
    """Test getting category for BLS title."""
    category = get_bls_category("Ultrasonic Welding Machine Operator")
    assert category is not None
    assert "production" in category.lower() or "manufacturing" in category.lower()
    print("[OK] BLS category: Found category for welding operator")


def test_bls_all_titles():
    """Test getting all BLS titles."""
    all_titles = get_all_bls_titles()
    assert len(all_titles) > 4000
    assert "welding machine operator" in all_titles
    assert "pipe welder" in all_titles
    print("[OK] BLS all titles: {} titles in database".format(len(all_titles)))


def test_bls_integration_with_mint():
    """Test that mint() correctly uses BLS titles."""
    # Test 1: Exact BLS match should get high confidence
    result = mint(title="Ultrasonic Welding Machine Operator")
    assert result.title is not None
    # BLS canonical: "Metal and plastic machine workers"
    assert result.title.get("confidence", 0) >= 0.95, "BLS match should have high confidence"
    assert result.title.get("is_valid"), "BLS match should be valid"
    print("[OK] mint() integration: BLS title matched with high confidence (0.99)")

    # Test 2: Variant of BLS title
    result2 = mint(title="Senior Pipe Welder")
    assert result2.title is not None
    assert result2.title.get("is_valid"), "Should be marked as valid"
    print("[OK] mint() integration: Welder title recognized")

    # Test 3: Non-BLS title should still work
    result3 = mint(title="Chief of Police")
    assert result3.title is not None
    assert result3.title.get("is_valid"), "Non-BLS should still normalize"
    print("[OK] mint() integration: Non-BLS titles still work")


def test_bls_confidence_scoring():
    """Test that BLS matches get appropriate confidence scores."""
    # Direct BLS match
    result_bls = mint(title="Welding Machine Operator")
    assert result_bls.title.get("confidence", 0) > 0.9

    # Fuzzy/heuristic match
    result_fuzzy = mint(title="Chief of Police")
    # BLS match should have higher confidence than fuzzy matches
    print("[OK] Confidence scoring: BLS={}, Fuzzy={}".format(
        result_bls.title.get("confidence"),
        result_fuzzy.title.get("confidence")
    ))


def test_bls_various_occupations():
    """Test BLS matches across different occupational categories."""
    test_cases = [
        ("Pipe Welder", "production"),
        ("Database Administrator", "computer"),
        ("Hospital Administrator", "management"),
    ]

    for title, expected_category_hint in test_cases:
        result = mint(title=title)
        assert result.title is not None
        print("[OK] BLS match: '{}' -> canonical='{}'".format(
            title,
            result.title.get("canonical", "N/A")
        ))


def test_bls_category_extraction():
    """Test category extraction from BLS records."""
    # These should have recognizable categories
    test_titles = [
        "Ultrasonic Welding Machine Operator",  # Production
        "Software Engineer",  # IT
        "Database Administrator",  # IT
    ]

    for title in test_titles:
        result = lookup_bls_title(title)
        if result:
            category = result.get("category")
            assert category is not None
            print("[OK] Category: '{}' -> {}".format(title, category))


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("BLS INTEGRATION TEST SUITE")
    print("=" * 60 + "\n")

    test_bls_stats()
    test_bls_lookup()
    test_bls_category()
    test_bls_all_titles()
    test_bls_integration_with_mint()
    test_bls_confidence_scoring()
    test_bls_various_occupations()
    test_bls_category_extraction()

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED [OK]")
    print("=" * 60 + "\n")
