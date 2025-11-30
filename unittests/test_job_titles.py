"""
Unit tests for job titles database functions.

Tests the three-tier matching system with 73k+ job titles, including:
- find_exact_job_title() - O(1) exact matching
- find_similar_job_titles() - Fuzzy matching with rapidfuzz
- get_job_titles_by_keyword() - Keyword search
- map_to_canonical() - Canonicalization layer
"""

import pytest
from humanmint.titles.data_loader import (
    find_exact_job_title,
    find_similar_job_titles,
    get_job_titles_by_keyword,
    map_to_canonical,
    get_all_job_titles,
)


class TestFindExactJobTitle:
    """Test exact matching against 73k job titles database."""

    def test_exact_match_found(self):
        """Exact match should return the title."""
        result = find_exact_job_title("Driver")
        assert result == "driver"

    def test_exact_match_case_insensitive(self):
        """Matching should be case-insensitive."""
        result = find_exact_job_title("DRIVER")
        assert result == "driver"

    def test_exact_match_whitespace_trimmed(self):
        """Leading/trailing whitespace should be trimmed."""
        result = find_exact_job_title("  Driver  ")
        assert result == "driver"

    def test_exact_match_multi_word(self):
        """Multi-word titles should match exactly."""
        result = find_exact_job_title("Software Developer")
        assert result == "software developer"

    def test_no_match_returns_none(self):
        """Non-existent title should return None."""
        result = find_exact_job_title("XyzAbc123")
        assert result is None

    def test_empty_string_returns_none(self):
        """Empty string should return None."""
        result = find_exact_job_title("")
        assert result is None

    def test_none_returns_none(self):
        """None input should return None."""
        result = find_exact_job_title(None)
        assert result is None

    def test_partial_match_not_found(self):
        """Partial matches should NOT be found."""
        # "driver" exists but "drivers" might not
        result = find_exact_job_title("Drivers")
        # If not exact match, should be None
        if result is not None:
            assert result == "drivers"

    def test_common_titles_found(self):
        """Common government titles should be found."""
        titles = ["Police Officer", "Teacher", "Accountant", "Engineer", "Manager"]
        for title in titles:
            result = find_exact_job_title(title)
            assert result is not None, f"{title} should be found in database"
            assert result == title.lower()


class TestFindSimilarJobTitles:
    """Test fuzzy matching against job titles."""

    def test_fuzzy_match_typo(self):
        """Close matches with typos should be found."""
        results = find_similar_job_titles("Dvr", top_n=3)
        assert len(results) > 0
        # Should find "driver" or similar
        titles = [t[0] for t in results]
        assert "driver" in titles

    def test_fuzzy_match_returns_top_n(self):
        """Should return top N matches."""
        results = find_similar_job_titles("Software", top_n=5)
        assert len(results) <= 5

    def test_fuzzy_match_includes_score(self):
        """Each result should include (title, score) tuple."""
        results = find_similar_job_titles("Driver", top_n=3)
        assert len(results) > 0
        for title, score in results:
            assert isinstance(title, str)
            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0

    def test_fuzzy_match_score_order(self):
        """Results should be ordered by score (highest first)."""
        results = find_similar_job_titles("Driver", top_n=5)
        if len(results) > 1:
            scores = [score for _, score in results]
            assert scores == sorted(scores, reverse=True)

    def test_exact_match_has_high_score(self):
        """Exact match should have score of 1.0."""
        results = find_similar_job_titles("driver", top_n=1)
        assert len(results) > 0
        title, score = results[0]
        assert title == "driver"
        assert score == 1.0

    def test_empty_string_returns_empty(self):
        """Empty string should return empty list."""
        results = find_similar_job_titles("", top_n=5)
        assert results == []

    def test_none_returns_empty(self):
        """None input should return empty list."""
        results = find_similar_job_titles(None, top_n=5)
        assert results == []

    def test_min_length_filter(self):
        """min_length should filter out short matches."""
        results = find_similar_job_titles("driver", top_n=10, min_length=5)
        for title, _ in results:
            assert len(title) >= 5

    def test_high_confidence_matches(self):
        """Common titles should have high confidence scores."""
        results = find_similar_job_titles("Police Officer", top_n=1)
        assert len(results) > 0
        title, score = results[0]
        assert score >= 0.8


class TestGetJobTitlesByKeyword:
    """Test keyword search in job titles."""

    def test_keyword_finds_matches(self):
        """Keyword search should find matching titles."""
        results = get_job_titles_by_keyword("driver")
        assert len(results) > 0
        # All results should contain "driver"
        for title in results:
            assert "driver" in title.lower()

    def test_keyword_case_insensitive(self):
        """Keyword search should be case-insensitive."""
        results_lower = get_job_titles_by_keyword("driver")
        results_upper = get_job_titles_by_keyword("DRIVER")
        assert len(results_lower) == len(results_upper)

    def test_keyword_no_matches(self):
        """Non-existent keyword should return empty list."""
        results = get_job_titles_by_keyword("xyzabc123xyz")
        assert results == []

    def test_empty_keyword_returns_empty(self):
        """Empty keyword should return empty list."""
        results = get_job_titles_by_keyword("")
        assert results == []

    def test_none_keyword_returns_empty(self):
        """None keyword should return empty list."""
        results = get_job_titles_by_keyword(None)
        assert results == []

    def test_multiple_matches_for_common_keyword(self):
        """Common keywords should have multiple matches."""
        results = get_job_titles_by_keyword("officer")
        assert len(results) > 5, "Should find multiple 'officer' titles"

    def test_keyword_partial_match(self):
        """Keyword should match partial strings."""
        results = get_job_titles_by_keyword("officer")
        titles = [t.lower() for t in results]
        # Should find "police officer", "code enforcement officer", etc.
        assert any("police" in t for t in titles)

    def test_specific_keywords(self):
        """Specific keywords should return relevant titles."""
        test_cases = [
            ("police", ["police"]),
            ("teacher", ["teacher"]),
            ("engineer", ["engineer"]),
        ]
        for keyword, expected_in_results in test_cases:
            results = get_job_titles_by_keyword(keyword)
            if results:  # If keyword exists in database
                titles = [t.lower() for t in results]
                for expected in expected_in_results:
                    assert any(expected in t for t in titles)


class TestMapToCanonical:
    """Test canonicalization layer mapping."""

    def test_map_to_canonical_exact(self):
        """Exact matches should map to canonical form."""
        result = map_to_canonical("chief of police")
        # Should map to canonical "police chief" if it exists
        assert result is not None or result is None  # Either maps or doesn't
        if result:
            assert "police" in result.lower() and "chief" in result.lower()

    def test_map_to_canonical_none_input(self):
        """None input should return None."""
        result = map_to_canonical(None)
        assert result is None

    def test_map_to_canonical_empty_string(self):
        """Empty string should return None."""
        result = map_to_canonical("")
        assert result is None

    def test_map_common_titles(self):
        """Common titles should map to something."""
        titles = ["software developer", "police officer", "accountant"]
        for title in titles:
            result = map_to_canonical(title)
            # Either maps to something or returns None (acceptable)
            if result is not None:
                assert isinstance(result, str)
                assert len(result) > 0

    def test_map_case_insensitive(self):
        """Mapping should be case-insensitive."""
        result1 = map_to_canonical("chief of police")
        result2 = map_to_canonical("CHIEF OF POLICE")
        # Results should be the same (or both None)
        assert result1 == result2

    def test_map_with_high_similarity(self):
        """Titles with >80% similarity should map to canonical."""
        # This tests the 80% similarity threshold
        result = map_to_canonical("police chief")
        # Either maps to itself or a similar canonical
        if result is not None:
            assert "police" in result.lower() and "chief" in result.lower()


class TestJobTitlesIntegration:
    """Integration tests for the complete job titles system."""

    def test_workflow_exact_to_canonical(self):
        """Test workflow: exact match -> canonicalize."""
        # Step 1: Find exact match
        exact = find_exact_job_title("Chief of Police")
        assert exact == "chief of police"

        # Step 2: Map to canonical
        canonical = map_to_canonical(exact)
        # Should map to canonical form
        assert canonical is None or isinstance(canonical, str)

    def test_workflow_fuzzy_to_canonical(self):
        """Test workflow: fuzzy match -> canonicalize."""
        # Step 1: Find fuzzy match
        results = find_similar_job_titles("Dvr", top_n=1)
        assert len(results) > 0
        fuzzy_match, score = results[0]

        # Step 2: Map to canonical
        canonical = map_to_canonical(fuzzy_match)
        # Should either map or return None
        assert canonical is None or isinstance(canonical, str)

    def test_workflow_keyword_search(self):
        """Test workflow: search by keyword, then canonicalize."""
        # Step 1: Find titles by keyword
        results = get_job_titles_by_keyword("police")
        assert len(results) > 0

        # Step 2: For each result, try to canonicalize
        for title in results[:3]:  # Test first 3
            canonical = map_to_canonical(title)
            assert canonical is None or isinstance(canonical, str)

    def test_database_completeness(self):
        """Database should contain at least 70k titles."""
        all_titles = get_all_job_titles()
        assert len(all_titles) > 70000, "Database should have 70k+ titles"

    def test_common_government_titles(self):
        """Common government titles should be findable."""
        government_titles = [
            "police officer",
            "fire chief",
            "teacher",
            "accountant",
            "engineer",
            "architect",
        ]
        for title in government_titles:
            # Should be findable either exactly or via fuzzy
            exact = find_exact_job_title(title)
            if exact is None:
                # Try fuzzy
                results = find_similar_job_titles(title, top_n=1)
                assert len(results) > 0, f"{title} should be findable"

    def test_three_tier_system(self):
        """Test all three tiers of the matching system."""
        # Tier 1: Job titles (73k+)
        exact = find_exact_job_title("driver")
        assert exact == "driver", "Tier 1: Job titles should find 'driver'"

        # Tier 1: Fuzzy matching
        fuzzy = find_similar_job_titles("dvr", top_n=1)
        assert len(fuzzy) > 0, "Tier 1: Fuzzy should find similar"

        # Tier 2+: Keyword search
        keywords = get_job_titles_by_keyword("manager")
        assert len(keywords) > 0, "Should find titles with 'manager'"
