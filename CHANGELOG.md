# Changelog

## [0.3.0] - 2025-04-05

### Added
- Created mbox generator script for producing test data files
  - Supports generation of 16 or 32 email mbox files
  - Includes various email types (plain text, HTML, mixed content)
  - Generates reproducible test data with attachments
  - Added comprehensive test suite in test_mbox_generator.py
- Added pytest-mock to development dependencies

### Changed
- Updated documentation (README.md, CONTRIBUTING.md, mbox_analyzer.md) with test data generation details
- Modified test_cli.py to use sample32.mbox for consistency

### Fixed
- Corrected mbox file generation location to tests/data/ directory

## [0.2.0] - 2025-04-04
### Changed
- Refactored major functionalities in mbox_analyzer for modularity and maintainability.
- Cleaned up unnecessary duplicate directories and files
- Improved project organization and maintainability

### Added
- Set up pytest configuration for testing
- Added unit tests for core functionality

## [0.1.0] - Initial Release
- Initial implementation of mbox file analyzer
- Basic reporting functionality
- Support for visualization generation
- JSON output support

