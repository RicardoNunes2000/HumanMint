# Changelog

All notable changes to HumanMint are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.11] - 2025-11-28

### Added
- **`title_str` property**: Added convenient `title_str` property to `MintResult` that returns canonical title
  - Matches the pattern of other `_str` properties (`name_str`, `email_str`, `phone_str`, `department_str`)
  - Returns `title["canonical"]` for consistent API access across all field types
  - Example: `result.title_str` → `"police chief"` (shorthand for `result.title["canonical"]`)

### Changed
- **Improved documentation accuracy**: All code examples in README and use case docs now verified to run correctly
  - Updated field access examples to reflect actual API behavior
  - Corrected gender output format (`"female"` instead of `"Female"`)
  - Fixed title normalization stage descriptions
  - Added comprehensive test suite (`tests/test_docs_examples.py`) with 8 tests covering all major examples

### Fixed
- **Documentation consistency**: Aligned all property examples across README and use case documentation
  - Fixed discrepancies between documented and actual API behavior
  - All examples are now copy-pasteable and guaranteed to work

## [0.1.10] - 2025-11-28

### Added
- **Complete batch export suite**: Production-ready export functionality for cleaned data
  - `export_json()` — Export to JSON with full nested structure preserved
  - `export_csv()` — Export to CSV with optional field flattening (name.first → name_first)
  - `export_parquet()` — Export to Apache Parquet for analytics and data science workflows (requires pyarrow)
  - `export_sql()` — Export directly to SQL databases (requires sqlalchemy)
  - Full support for both nested and flattened output formats
  - Comprehensive test coverage with 8 dedicated test cases

### Changed
- Consolidated and stabilized batch processing pipeline with `bulk()` → `export_*()` workflow
- Enhanced flexibility for downstream data integration and analytics

## [0.1.9] - 2025-11-28

### Added
- **Batch export functionality**: Export cleaned results to multiple formats for downstream processing
  - `export_json()` — Export results to JSON with full structure preserved
  - `export_csv()` — Export to CSV with optional flattening (name_first, email_domain, etc.)
  - `export_parquet()` — Export to Apache Parquet for analytics workflows (requires pyarrow)
  - `export_sql()` — Export directly to SQL databases (requires sqlalchemy)
  - All exporters support flattened and nested data structures
  - Comprehensive test coverage with 8 test cases for all export formats

### Changed
- Enhanced data pipeline flexibility: `bulk()` → `export_*()` workflow enables seamless data integration

## [0.1.8] - 2025-11-28

### Added
- **`MintResult.get()` accessor method**: Safely access nested fields using dot notation with optional defaults
  - Supports dot notation: `result.get("name.first")`, `result.get("email.domain")`, `result.get("phone.e164")`
  - Returns `None` or a custom default if field doesn't exist: `result.get("phone.e164", "+1 000-000-0000")`
  - Comprehensive test coverage with 24 test cases in new `test_get_accessor.py`

### Changed
- **Enhanced cache documentation**: All `@lru_cache` decorated functions now include detailed docstrings explaining cache behavior
  - Documented cache size (maxsize=4096) and performance benefits
  - Added examples for cache inspection (`cache_info()`) and clearing (`cache_clear()`)
  - Affected functions: `_normalize_name_cached`, `_find_best_match_normalized` (departments), `normalize_department`, `is_free_provider`, `_normalize_email_cached`, `_normalize_phone_cached`, `_find_best_match_normalized` (titles), `normalize_title`

### Fixed
- **Variable shadowing in `compare()` function**: Renamed local `weights` variable to `weight_pairs` to avoid shadowing the `weights` parameter
  - Improves code clarity while maintaining backward compatibility
  - No functional change; linting and static analysis improvements

## [0.1.7] - 2025-11-28

### Added
- **Improved email fuzzy matching** in `compare()` function for better handling of similar email addresses within same domain
- **Weighted scoring refinements**: Better ratio scaling ensuring floors and penalties respect field weights

### Changed
- Enhanced `compare()` function with improved fuzzy email matching logic
- Refactored scoring to use weighted contributions more consistently

### Fixed
- Email matching now correctly handles abbreviated and similar local parts within same domain
- Fixed edge cases in weighted score calculations for partial field matches

## [0.1.6] - 2025-11-28

### Added
- Enhanced department matching with segment-aware scoring for multi-part names

### Changed
- Improved department canonicalization for complex department name structures

### Fixed
- Better handling of "and" separators in department names
- Improved edge case handling for department normalization with special characters

## [0.1.5] - 2025-11-28

### Added
- **Weighted comparison scoring**: The `compare()` function now accepts optional `weights` parameter for field-level control over similarity calculation
  - Customize how much each field (name, email, phone, department, title, etc.) contributes to overall similarity score
  - Perfect for building custom deduplication strategies
  - Example: `compare(r1, r2, weights={"name": 0.4, "email": 0.3, "phone": 0.2, "department": 0.1})`

### Changed
- Enhanced `compare()` API for more flexible record matching
- Improved department matching algorithm with segment-aware scoring for multi-part department names
- Better handling of "and" separators in department names (e.g., "Planning and Development")

### Fixed
- Department matching now correctly handles comma-separated and slash-separated department names
- Improved edge case handling for single-character inputs in department normalization

## [0.1.4] - 2025-01-27

### Changed
- Updated project links to point to correct GitHub repository (https://github.com/RicardoNunes2000/HumanMint)
- Documentation and bug tracker URLs now reflect official repository

## [0.1.3] - 2025-01-27

### Added
- 60+ comprehensive tests covering all 7 modules (Names, Emails, Phones, Departments, Titles, Addresses, Organizations)
- Test suite includes integration tests and module-specific tests

### Changed
- Updated phone number examples throughout documentation to use real area codes (202, 415) instead of reserved 555
- Added documentation explaining why 555 area code fails validation

### Fixed
- Phone number validation examples now use valid area codes that will successfully normalize

## [0.1.2] - 2025-01-26

### Added
- Complete API reference documentation with all 45+ public functions
- Comprehensive examples for each module
- Addresses module integration in all documentation
- Organizations module integration in all documentation

### Changed
- Expanded README with full module-by-module API documentation
- Updated feature list to include all 7 data normalization modules
- Better organization of code examples and use cases

## [0.1.1] - 2025-01-25

### Added
- Initial release to TestPyPI for testing
- Core normalization functionality for names, emails, phones, departments, and titles
- Batch processing with `bulk()` function
- Record comparison with `compare()` function

### Features
- **Names**: Parse, normalize, infer gender, detect nicknames
- **Emails**: Validate, detect free providers, extract domains
- **Phones**: E164 normalization, extension extraction, type detection
- **Departments**: 23,452 mappings to 64 canonical forms
- **Titles**: Canonicalize job titles with confidence scores
- **Addresses**: Parse US postal addresses
- **Organizations**: Normalize agency/organization names

## [0.1.0] - 2025-01-24

### Added
- Initial project structure and core files
- Base API and module organization
- Data files and mapping resources
- CLI interface

---

## Versioning Notes

### What Gets Bumped?
- **Major (X.0.0)**: Breaking API changes
- **Minor (0.X.0)**: New features, backward compatible
- **Patch (0.0.X)**: Bug fixes, internal improvements

### Planned for Future Releases
- v0.2.0: Deduplication API (`deduplicate()` function)
- v0.3.0: Enhanced Pandas integration
- v1.0.0: Stable API release
