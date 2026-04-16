# Changelog

All notable changes to this project will be documented in this file.

---

## [Unreleased]

### Added
- Granular solution output modes, providing clearer labeling for optimal and sub-optimal repairs.

### Changed
- Unified solution selection logic under a single `--sol` argument (replacing internal `--single-sol` and `--sub-opt` flags).
- Updated README and documentation to reflect the new command-line interface.

## v0.3.0 - 2026-04-11

### Changed
- Variable names are now quoted in generated logic programs for ASP compliance.
- Replaced the `-v`/`--verbose` flag with the more specific `-f`/`--format` implementation.
- Refined internal configuration names and progress output terminology for consistency.

### Fixed
- Fixed a bug where providing multiple observation-updater pairs would only process the last one.

## v0.2 - Mar 2026

### Added
- Added `.csv`, `.xls`, and `.xlsx` formats support for observation files.

---

## v0.1 - Mar 2026

### Added
- Added `.csv` format support as a proposal for observation files.
- Option to write and export repaired model files under a new unified parser module.
- Full `model.zginml` support with unified parsing of Boolean expressions.
- Added `vertex` node support.
- Fully functioning `asp_reader` with example files and `pytest` integration.
- Replaced custom shell test scripts (`run_tests.sh`) with native `pytest` testing (`test_model_files.py`).
- Extensively populated the `examples/` directory for test automation.
- Introduced a standard logging system, including a specific debug mode for updaters.
- Support for multiple observation files of the same topology in a single run.

### Changed
- Readers have been redesigned as polymorphic Parsers (`parser_ginml.py`, `parser_bnet.py`, `parser_asp.py`), capable of both `read()` and `write()` operations.
- The BNET parser now evaluates functions comprehensively using Quine-McCluskey logic reduction, dropping degenerate regulators, and assuming monotonicity (defaulting to positive).
- Repaired `GINsim` networks now retain their original `.ginml` XML layout styling and preserve the inner files of `.zginml` zip archives.
- Edge signs are explicitly displayed in function repair proposals.
- Significant refactoring of the repair engine, and simplified dynamic loading of updater classes.
- Changed configuration class structures, now utilizing elegant pythonic `@property` getters and setters.
- Migrated all command-line interface arguments to `argparse`.
- Cleaned up unneeded dependencies such as `asp_helper` and consolidated the code.

### Fixed
- Fixed node order sorting in multiple `.lp` model test files.
- Resolved severe syntax errors causing invalid `JSON` outputs.

---

## v0.x - Feb 2025
- First base stable release with consistency check and repair operations
