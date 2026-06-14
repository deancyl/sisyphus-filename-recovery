"""
Universal garbled text detector + sanitizer (v1.2).
Built-in fingerprint database - works without any config.
"""
import re, os, datetime, hashlib, shutil

# ============================================================
# Module 1: Built-in garbled fingerprint database
# ============================================================

# Known garbled fingerprints - no config needed
DEFAULT_GARBLED_FINGERPRINTS = [
    # Classic GBK/UTF-8 double-encoding signatures
    '锟斤拷', '閿熸枻', '鎷烽敓', '鏂ゆ嫹', '铻厧',
    # VC++ debug heap fill patterns (rare but real)
    '烫烫烫', '屯屯屯',
    # UTF-8 BOM misread
    '锘',
    # U+FFFD replacement character (byte permanently lost)
    '\ufffd', '\uFFFD',
    # CP437/CP850 misinterpretation signatures
    '┼╠╝', '╟δ╧', 'úí',
    # ISO-8859-1 high-byte noise patterns
    'Ã', 'Â', 'Å',
]

# Continuous control/non-printable character threshold
_CONTROL_THRESHOLD = 3

# Regex: filename is primarily normal Chinese + ASCII = safe
_SAFE_CJK_RE = re.compile(r'^[\u4e00-\u9fa5a-zA-Z0-9\.\-\_\(\)\[\]\,\;\：\（\）\s]+$')

# Garbled character blocks for stripping (expanded)
_GARBLED_BLOCKS = (
    '閿熸枻鎷鏂ゆ嫹烽敓绲痑铻厧搴楃骇缁存唻碉拷婵'
    '锟斤拷锟絯塕捇屽姵塻墿瀵屽▍瀵曟禍椋庢嫹塳鏂ゆ壈'
    '濠婄€犲摜瀵斿▍椋庢嫹渚濞€┼╠╝°╢¿╞≈╢└┴ó░µ'
    '╟δ╧╚╜Γ╤╣ú╚╗║≤╘┘╘╦╨╨úí'
)
_GARBLED_RE = re.compile(f'[{re.escape(_GARBLED_BLOCKS)}]+')
_REPLACEMENT_RE = re.compile(r'[\uFFFD\ufffd]+')
_MULTI_UNDERSCORE = re.compile(r'_+')
_MULTI_SPACE = re.compile(r' {2,}')
_MULTI_DOT = re.compile(r'\.{2,}')

# ============================================================
# is_garbled() - Decision tree
# ============================================================

def _count_control_chars(name):
    """Count non-printable control characters"""
    return sum(1 for c in name if ord(c) < 32 and c not in '\t\n\r')

def is_garbled(filename, extra_patterns=None):
    """
    Decision tree for garbled filename detection.
    
    Fingerprint check FIRST (before safe-CJK gate), because garbled text
    like 閿熸枻 is technically valid CJK but semantically garbled.
    
    Returns True if filename appears garbled and needs recovery.
    """
    # Interceptor: pure ASCII is always safe
    if all(ord(c) < 128 for c in filename):
        return False
    
    # BRANCH 1: User-supplied patterns (highest priority)
    if extra_patterns:
        for pat in extra_patterns:
            try:
                if re.search(pat, filename):
                    return True
            except re.error:
                pass
    
    # BRANCH 2: Built-in fingerprints (check BEFORE safe-CJK gate)
    # Garbled CJK chars like 閿熸枻 are valid Unicode but semantically garbled
    for fp in DEFAULT_GARBLED_FINGERPRINTS:
        if fp in filename:
            return True
    
    # BRANCH 3: Continuous control characters
    if _count_control_chars(filename) >= _CONTROL_THRESHOLD:
        return True
    
    # BRANCH 4: U+FFFD blocks (3+ consecutive replacement chars)
    if re.search(r'\ufffd{3,}', filename) or re.search(r'\uFFFD{3,}', filename):
        return True
    
    # INTERCEPTOR: Normal Chinese + ASCII = safe (false positive prevention)
    if _SAFE_CJK_RE.match(filename):
        return False
    
    return False

# ============================================================
# Sanitizer
# ============================================================

def sanitize_filename(name):
    """Strip garbled characters, keep surviving ASCII/CJK fragments.
    Returns sanitized name or None if nothing useful remains."""
    
    cleaned = _GARBLED_RE.sub('', name)
    cleaned = _REPLACEMENT_RE.sub('', cleaned)
    cleaned = _MULTI_UNDERSCORE.sub('_', cleaned)
    cleaned = _MULTI_SPACE.sub(' ', cleaned)
    cleaned = _MULTI_DOT.sub('.', cleaned)
    cleaned = cleaned.strip(' _-')
    cleaned = re.sub(r'\(\s*\)', '', cleaned)
    
    meaningful = sum(1 for c in cleaned if c.isalnum() or c in '._-()[]')
    if meaningful < 2:
        return None
    
    return cleaned

# ============================================================
# Fallback cluster
# ============================================================

def cluster_fallback(fpath, directory):
    """Move unrecoverable files into Recovered_YYYY-MM-DD/ with hash names"""
    try:
        mtime = os.path.getmtime(fpath)
        date_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
        
        ext = os.path.splitext(fpath)[1].lower()
        category_map = {
            '.jpg': 'Images', '.jpeg': 'Images', '.png': 'Images', '.gif': 'Images', '.bmp': 'Images', '.webp': 'Images',
            '.mp4': 'Videos', '.mkv': 'Videos', '.avi': 'Videos', '.mov': 'Videos', '.wmv': 'Videos',
            '.mp3': 'Audio', '.wav': 'Audio', '.flac': 'Audio', '.aac': 'Audio',
            '.doc': 'Docs', '.docx': 'Docs', '.pdf': 'Docs', '.xls': 'Docs', '.xlsx': 'Docs', '.ppt': 'Docs', '.pptx': 'Docs',
        }
        prefix_map = {
            '.jpg': 'IMG', '.jpeg': 'IMG', '.png': 'IMG', '.gif': 'IMG', '.bmp': 'IMG', '.webp': 'IMG',
            '.mp4': 'VID', '.mkv': 'VID', '.avi': 'VID', '.mov': 'VID', '.wmv': 'VID',
            '.mp3': 'AUD', '.wav': 'AUD', '.flac': 'AUD', '.aac': 'AUD',
            '.doc': 'DOC', '.docx': 'DOC', '.pdf': 'DOC', '.xls': 'DOC', '.xlsx': 'DOC', '.ppt': 'DOC', '.pptx': 'DOC',
        }
        
        cat = category_map.get(ext, 'Files')
        prefix = prefix_map.get(ext, 'FILE')
        folder = f"Recovered_{cat}_{date_str}"
        
        h = hashlib.md5()
        try:
            with open(fpath, 'rb') as f:
                for chunk in iter(lambda: f.read(65536), b''): h.update(chunk)
            short_hash = h.hexdigest()[:8]
        except:
            short_hash = datetime.datetime.now().strftime("%H%M%S")
        
        folder_path = os.path.join(directory, folder)
        return f"{folder}/{prefix}_{date_str.replace('-','')}_{short_hash}{ext}"
    except:
        return None

# ============================================================
# Scanner
# ============================================================

def scan_sanitize(directory, config=None):
    """Apply sanitizer + fallback to garbled files. Returns [(old, new, strategy), ...]"""
    records = []
    skip = set(config.get('skip_patterns', [])) if config else set()
    
    for fname in sorted(os.listdir(directory)):
        fpath = os.path.join(directory, fname)
        
        # Gate: skip directories (handled separately)
        if os.path.isdir(fpath):
            if is_garbled(fname):
                cleaned = sanitize_filename(fname)
                if cleaned and cleaned != fname and len(cleaned) >= 2:
                    records.append((fname, cleaned, "DirSanitize"))
            continue
        
        # Gate: skip patterns
        if any(re.match(p, fname) for p in skip):
            continue
        
        # Gate: only process garbled files
        extra = config.get('garbled_patterns', []) if config else []
        if not is_garbled(fname, extra):
            continue
        
        # Try sanitize first
        cleaned = sanitize_filename(fname)
        if cleaned and cleaned != fname and len(cleaned) >= 3:
            records.append((fname, cleaned, "Sanitize"))
        else:
            # Fallback cluster
            result = cluster_fallback(fpath, directory)
            if result:
                records.append((fname, result, "Fallback"))
    
    return records
