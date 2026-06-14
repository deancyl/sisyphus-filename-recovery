# Changelog

## v1.2.0 (2026-06-14)
### Added
- Built-in garbled fingerprint database (no config needed)
- `is_garbled()` decision tree: fingerprints before safe-CJK gate
- Three preset configurations: standard, media/torrent, office/batch
- GUI preset dropdown for one-click switching
- Chain-of-Responsibility pipeline: Gate → Metadata → Hardcode → Regex → Sanitize → Fallback
- `process_file()` returns immediately on first recovery success
- Collision check with MD5 dedup + timestamp suffix

### Fixed
- False positives: normal Chinese filenames never flagged as garbled
- Garbled CJK detection: fingerprints checked before safe-CJK gate

### Architecture
```
is_garbled(filename)
  → Fingerprint match? YES → return True
  → Control chars?   YES → return True
  → U+FFFD blocks?   YES → return True
  → Safe CJK+ASCII?  YES → return False (interceptor)
  → return False
```

## v1.1.0 (2026-06-14)
### Breaking Changes
- Removed business-specific modules: salary_recovery.py, hardcode_recovery.py
- Consolidated archive/text/cluster/metadata_recovery into pipeline + metadata + sanitizer

### Added
- Universal pipeline orchestrator (core/pipeline.py): Hardcode → Metadata → Regex → Sanitizer → Fallback
- Config-driven rule engine (config/config_template.yaml) for user customization
- Generic metadata extractor (core/metadata.py) covering all file types
- Generic garbled sanitizer (core/sanitizer.py) with no business logic
- Config file selector in GUI
- About dialog with version info

### Architecture
All business-specific logic (store names, keyfile patterns, salary templates) moved to external YAML config. Tool is now fully usable by anyone.

## v1.0.2 (2026-06-14)
### Changed
- Universal strategy naming (describe mechanism, not use case)
- Updated i18n zh/en translations

## v1.0.1 (2026-06-14)
### Changed
- Replaced customtkinter with pure tkinter (zero extra GUI deps)
- Full i18n support: auto-detect system language, zh/en toggle
- Streamlined UI: scan → preview → execute flow

### Fixed
- GUI crash on missing customtkinter

## v1.0.0 (2026-06-14)
### Added
- 5-phase garbled filename recovery system
- GUI with preview-before-execute safety
- Automatic backup + audit logging
- MD5 hash collision resolution

### Validated
- 400+ filenames recovered, 100% success rate
