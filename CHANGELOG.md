# Changelog

All notable changes to HumanMint are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.5] - 2025-01-28

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
