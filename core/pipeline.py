"""
Sisyphus Recovery Pipeline Orchestrator.
Runs strategies in priority order: metadata → sanitize → fallback.
"""
import os, re, yaml, csv, datetime, shutil, hashlib
from .metadata import scan_metadata
from .sanitizer import scan_sanitize

DEFAULT_CONFIG = {
    "hardcode_mappings": {},
    "regex_rules": [],
    "skip_patterns": [
        r"^Recovered_", r"^_Trash", r"^_Sisyphus"
    ],
    "garbled_chars": "",
}


def load_config(config_path=None):
    """Load YAML config or return defaults"""
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = yaml.safe_load(f)
            if cfg:
                return {**DEFAULT_CONFIG, **cfg}
        except: pass
    
    # Auto-discover config.yaml in project root
    for candidate in ('config.yaml', 'config/config.yaml', 'config_template.yaml'):
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), candidate)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    cfg = yaml.safe_load(f)
                if cfg: return {**DEFAULT_CONFIG, **cfg}
            except: pass
    
    return DEFAULT_CONFIG


def apply_hardcode_mappings(directory, config):
    """Apply exact filename mappings from config"""
    records = []
    mappings = config.get('hardcode_mappings', {})
    for fname in sorted(os.listdir(directory)):
        if fname in mappings:
            records.append((fname, mappings[fname], "Hardcode"))
    return records


def apply_regex_rules(directory, config):
    """Apply regex replace rules from config"""
    records = []
    rules = config.get('regex_rules', [])
    for fname in sorted(os.listdir(directory)):
        fpath = os.path.join(directory, fname)
        if os.path.isdir(fpath): continue
        for rule in rules:
            pattern = rule.get('pattern', '')
            replace = rule.get('replace', '')
            if pattern and replace:
                new = re.sub(pattern, replace, fname)
                if new != fname:
                    records.append((fname, new, "Regex"))
                    break
    return records


def run_full_scan(directory, config=None):
    """Run all recovery strategies in priority order.
    Returns [(old_name, new_name, strategy), ...]
    """
    if config is None:
        config = load_config()
    
    all_records = []
    seen_old = set()
    
    # Priority 0: Hardcode mappings (user-specified exact matches)
    hardcode = apply_hardcode_mappings(directory, config)
    for old, new, strat in hardcode:
        if old not in seen_old:
            all_records.append((old, new, strat))
            seen_old.add(old)
    
    # Priority 1: Metadata extraction (most reliable)
    metadata = scan_metadata(directory, config)
    for old, new, strat in metadata:
        if old not in seen_old:
            all_records.append((old, new, strat))
            seen_old.add(old)
    
    # Priority 2: Regex rules (user-specified patterns)
    regex = apply_regex_rules(directory, config)
    for old, new, strat in regex:
        if old not in seen_old:
            all_records.append((old, new, strat))
            seen_old.add(old)
    
    # Priority 3: Generic sanitizer + fallback cluster
    sanitized = scan_sanitize(directory, config)
    for old, new, strat in sanitized:
        if old not in seen_old:
            all_records.append((old, new, strat))
            seen_old.add(old)
    
    return all_records


def execute_renames(directory, records, backup_dir=None):
    """Execute a list of (old_name, new_name, strategy) renames.
    Returns (renamed, deleted, clustered, failed, log_path).
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
                for chunk in iter(lambda: f.read(65536), b''):
                    h.update(chunk)
            return h.hexdigest()
        except: return None
    
    for old, new, strat in records:
        old_path = os.path.join(directory, old)
        if not os.path.exists(old_path):
            log.append((old, new, "NOT_FOUND", strat))
            failed += 1
            continue
        
        if "/" in new or "\\" in new:
            # Cluster: move to subfolder
            parts = new.replace("\\", "/").split("/")
            folder = os.path.join(directory, parts[0])
            os.makedirs(folder, exist_ok=True)
            target = os.path.join(folder, parts[1])
            try:
                shutil.move(old_path, target)
                clustered += 1
                log.append((old, new, "CLUSTERED", strat))
            except Exception as e:
                failed += 1
                log.append((old, new, f"FAIL:{e}", strat))
        else:
            target = os.path.join(directory, new)
            if os.path.exists(target):
                h1 = _hash(old_path)
                h2 = _hash(target)
                if h1 and h2 and h1 == h2:
                    shutil.move(old_path, os.path.join(trash, old))
                    deleted += 1
                    log.append((old, new, "DELETED_DUP", strat))
                else:
                    base, ext = os.path.splitext(new)
                    alt = f"{base}_DUP{ext}"
                    os.rename(old_path, os.path.join(directory, alt))
                    renamed += 1
                    log.append((old, alt, "RENAMED_COL", strat))
            else:
                try:
                    os.rename(old_path, target)
                    renamed += 1
                    log.append((old, new, "RENAMED", strat))
                except Exception as e:
                    failed += 1
                    log.append((old, new, f"FAIL:{e}", strat))
    
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(backup_dir, f"execution_{ts}.csv")
    with open(log_path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(["OldName","NewName","Action","Strategy"])
        for row in log: w.writerow(row)
    
    return renamed, deleted, clustered, failed, log_path
