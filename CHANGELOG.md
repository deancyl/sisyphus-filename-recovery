# Changelog

## v1.0.0 (2026-06-14)

### Added
- GUI interface with customtkinter for visual operation
- Phase 1: System ACP encoding check and fix
- Phase 2: Excel salary file recovery via openpyxl content extraction (84 files validated)
- Phase 3: Metadata recovery for Torrent (bencode), PDF (PyPDF2), docx (python-docx), media (mutagen)
- Phase 4: Archive interior inspection, text first-line extraction, time-based clustering, hash disambiguation
- Phase 5: Hardcode dictionary for non-standard encoding corruptions, regex-based directory cleanup, keyfile preservation
- Automatic backup before any modifications
- Execution log generation for audit trail
- Preview mode (mandatory before execution)
- Collision resolution with MD5 hash comparison

### Validated
- Tested on Windows with zh-CN locale, ACP=936
- Successfully recovered 400+ garbled filenames across 5 phases
- 100% recovery rate in production scenario
