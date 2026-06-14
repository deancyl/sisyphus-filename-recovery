"""
Sisyphus Recovery Pipeline v1.2
Chain of Responsibility: Gate → Metadata → Hardcode → Regex → Sanitize → Fallback → Collision
"""
import os, re, yaml, csv, datetime, shutil, hashlib
from .sanitizer import is_garbled, sanitize_filename, cluster_fallback
from .metadata import extract_metadata

DEFAULT_CONFIG = {
    "hardcode_mappings": {},
    "regex_rules": [],
    "skip_patterns": [r"^Recovered_", r"^_Trash", r"^_Sisyphus"],
    "garbled_patterns": [],
    "metadata_priority": "normal",
}

# Preset lookup (key -> file path)
_PRESET_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "presets")
PRESETS = {
    "01_standard_gbk_utf8": os.path.join(_PRESET_DIR, "01_standard_gbk_utf8.yaml"),
    "02_media_torrent":     os.path.join(_PRESET_DIR, "02_media_torrent.yaml"),
    "03_office_batch":      os.path.join(_PRESET_DIR, "03_office_batch.yaml"),
}

# Preset display name -> internal key (populated by i18n at runtime)
PRESET_DISPLAY = {}

def sync_preset_display():
    """Sync PRESET_DISPLAY with current i18n language"""
    try:
        from .i18n import i18n
        keys = list(PRESETS.keys())
        display_keys = ["preset_standard", "preset_media", "preset_office"]
        for i, key in enumerate(keys):
            if i < len(display_keys):
                PRESET_DISPLAY[key] = i18n.get(display_keys[i])
    except: pass

sync_preset_display()

def load_preset(preset_name):
    """Load a named preset. Accepts internal key or display name."""
    # Try internal key first
    path = PRESETS.get(preset_name)
    # Then try display name -> internal key lookup
    if not path:
        for key, files in PRESETS.items():
            if preset_name == PRESET_DISPLAY.get(key):
                path = files
                break
    if path and os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                cfg = yaml.safe_load(f)
            if cfg: return {**DEFAULT_CONFIG, **cfg}
        except: pass
    return None

def load_config(config_path=None, preset=None):
    """Load configuration. preset can be: internal key, display name, or YAML file path.
    Order: defaults → preset → user config file (if provided)
    """
    cfg = dict(DEFAULT_CONFIG)
    
    if preset:
        # Try as preset name first
        preset_cfg = load_preset(preset)
        if preset_cfg:
            cfg.update(preset_cfg)
        elif os.path.exists(preset):
            # Treat as custom YAML file path
            try:
                with open(preset, 'r', encoding='utf-8') as f:
                    user_cfg = yaml.safe_load(f)
                if user_cfg: cfg.update(user_cfg)
            except: pass
    
    # User config file overlay
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                user_cfg = yaml.safe_load(f)
            if user_cfg: cfg.update(user_cfg)
        except: pass
    
    return cfg


# ============================================================
# Chain of Responsibility: Single file processor
# ============================================================

def process_file(fpath, fname, config):
    """
    Process a single file through the chain of responsibility.
    Each step returns a result if successful, otherwise passes to next.
    
    Chain: GATE → METADATA → HARDCODE → REGEX → SANITIZE → FALLBACK
    """
    # === GATE: Skip non-garbled files ===
    extra = config.get('garbled_patterns', [])
    if not is_garbled(fname, extra):
        return None  # File is clean
    
    ext = os.path.splitext(fname)[1].lower()
    
    # === STEP 1: Metadata extraction (most reliable) ===
    metadata_prio = config.get('metadata_priority', 'normal')
    if metadata_prio in ('high', 'maximum', 'normal'):
        result = extract_metadata(fpath)
        if result:
            new_name, category = result
            if new_name != fname and len(new_name) >= 3:
                return (new_name, category.capitalize())
    
    # === STEP 2: Hardcode dictionary (exact match) ===
    mappings = config.get('hardcode_mappings', {})
    if fname in mappings:
        return (mappings[fname], "Hardcode")
    
    # === STEP 3: Regex rules (pattern replacement) ===
    for rule in config.get('regex_rules', []):
        pat = rule.get('pattern', '')
        rep = rule.get('replace', '')
        if pat and rep:
            try:
                new = re.sub(pat, rep, fname)
                if new != fname and len(new) >= 3:
                    return (new, "Regex")
            except re.error:
                pass
    
    # === STEP 4: Generic sanitizer ===
    cleaned = sanitize_filename(fname)
    if cleaned and cleaned != fname and len(cleaned) >= 3:
        return (cleaned, "Sanitize")
    
    # === STEP 5: Fallback cluster ===
    result = cluster_fallback(fpath, os.path.dirname(fpath))
    if result:
        return (result, "Fallback")
    
    return None


# ============================================================
# Directory scanner
# ============================================================

def run_full_scan(directory, config=None):
    """Run chain of responsibility on all files in directory.
    Returns [(old_name, new_name, strategy), ...]
    """
    if config is None:
        config = load_config()
    
    records = []
    skip = set(config.get('skip_patterns', []))
    
    for fname in sorted(os.listdir(directory)):
        fpath = os.path.join(directory, fname)
        
        # Skip patterns
        if any(re.match(p, fname) for p in skip):
            continue
        
        # Process directories
        if os.path.isdir(fpath):
            if is_garbled(fname):
                cleaned = sanitize_filename(fname)
                if cleaned and cleaned != fname and len(cleaned) >= 2:
                    records.append((fname, cleaned, "DirSanitize"))
            continue
        
        result = process_file(fpath, fname, config)
        if result:
            new_name, strategy = result
            records.append((fname, new_name, strategy))
    
    return records


# ============================================================
# Collision-safe executor
# ============================================================

def execute_renames(directory, records, backup_dir=None):
    """Execute renames with MD5 collision checking.
    Returns (renamed, deleted, clustered, failed, log_path)
    """
    if backup_dir is None:
        backup_dir = os.path.join(directory, "_Sisyphus_Backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    trash = os.path.join(directory, "_Trash_Duplicates")
    os.makedirs(trash, exist_ok=True)
    
    renamed = 0; deleted = 0; clustered = 0; failed = 0
    log = []
    
    def _hash(fpath):
        h = hashlib.md5()
        try:
            with open(fpath, 'rb') as f:
                for chunk in iter(lambda: f.read(65536), b''): h.update(chunk)
            return h.hexdigest()
        except: return None
    
    for old, new, strat in records:
        old_path = os.path.join(directory, old)
        if not os.path.exists(old_path):
            log.append((old, new, "NOT_FOUND", strat)); failed += 1; continue
        
        # Cluster: move to subfolder
        if "/" in new or "\\" in new:
            parts = new.replace("\\", "/").split("/")
            folder = os.path.join(directory, parts[0])
            os.makedirs(folder, exist_ok=True)
            target = os.path.join(folder, parts[1])
            try:
                shutil.move(old_path, target)
                clustered += 1
                log.append((old, new, "CLUSTERED", strat))
            except Exception as e:
                failed += 1; log.append((old, new, f"FAIL:{e}", strat))
            continue
        
        # === COLLISION CHECK ===
        target = os.path.join(directory, new)
        if os.path.exists(target):
            h1 = _hash(old_path); h2 = _hash(target)
            if h1 and h2 and h1 == h2:
                # Same content → delete duplicate
                shutil.move(old_path, os.path.join(trash, old))
                deleted += 1; log.append((old, new, "DELETED_DUP", strat))
            else:
                # Different content → timestamp suffix
                try:
                    mtime = os.path.getmtime(old_path)
                    ts = datetime.datetime.fromtimestamp(mtime).strftime("%m%d_%H%M")
                except:
                    ts = datetime.datetime.now().strftime("%m%d_%H%M")
                base, ext = os.path.splitext(new)
                alt = f"{base}_v{ts}{ext}"
                try:
                    os.rename(old_path, os.path.join(directory, alt))
                    renamed += 1; log.append((old, alt, "RENAMED_COL", strat))
                except Exception as e:
                    failed += 1; log.append((old, new, f"FAIL:{e}", strat))
        else:
            try:
                os.rename(old_path, target)
                renamed += 1; log.append((old, new, "RENAMED", strat))
            except Exception as e:
                failed += 1; log.append((old, new, f"FAIL:{e}", strat))
    
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(backup_dir, f"execution_{ts}.csv")
    with open(log_path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(["OldName","NewName","Action","Strategy"])
        for row in log: w.writerow(row)
    
    return renamed, deleted, clustered, failed, log_path
