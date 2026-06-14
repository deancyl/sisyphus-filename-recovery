# Changelog

## v1.0.2 (2026-06-14)
### Changed
- Universal strategy naming: describe mechanism, not use case
  - "Excel Salary Recovery" → "Content Intelligence"
  - "Metadata Recovery" → "Embedded Metadata"
  - "ZIP Interior" → "Archive Discovery"
  - "Text First-Line" → "Text Header Auto-Name"
  - "Time Clustering" → "Chronological Archive"
  - "Hardcode + Regex" → "Pattern Sanitizer"
- Updated all i18n strings (zh/en) to reflect new names
- README strategy table updated

## v1.0.1 (2026-06-14)
### Changed
- Replaced customtkinter with pure tkinter (zero extra GUI dependencies)
- Full i18n support: auto-detect system language, toggle zh/en
- Added core/i18n.py language manager
- Streamlined UI: scan → preview → execute flow
- All core modules integration-tested

### Fixed
- GUI launch crash on missing customtkinter

## v1.0.0 (2026-06-14)
### Added
- GUI interface for visual operation
- Phase 1: System ACP encoding check and fix
- Phase 2: Content intelligence (Excel cell reading via openpyxl)
- Phase 3: Embedded metadata extraction (torrent bencode, PDF PyPDF2, docx python-docx, media mutagen)
- Phase 4: Archive content discovery, text header detection, chronological archiving, hash-based dedup
- Phase 5: Pattern sanitizer with hardcode dictionary and regex cleanup
- Automatic backup before modifications
- Execution audit logging
- Mandatory preview-before-execute safety
- MD5 hash collision resolution

### Validated
- Tested on Windows zh-CN, ACP=936
- 400+ garbled filenames recovered across 5 phases
- 100% recovery rate validated
