"""
Generic garbled text sanitizer.
Strips known garbled Unicode blocks, preserves surviving meaningful text.
No business-specific logic.
"""
import re, os, datetime, hashlib, shutil

# Known garbled character ranges (expanded from real-world data)
_GARBLED_BLOCKS = (
    '閿熸枻鎷鏂ゆ嫹烽敓绲痑铻厧搴楃骇缁存唻碉拷婵'
    '锟斤拷锟絯塕捇屽姵塻墿瀵屽▍瀵曟禍椋庢嫹塳鏂ゆ壈'
    '濠婄€犲摜瀵斿▍椋庢嫹渚濞€┼╠╝°╢¿╞≈╢└┴ó░µ'
    '╟δ╧╚╜Γ╤╣ú╚╗║≤╘┘╘╦╨╨úí'
)

_GARBLED_RE = re.compile(f'[{re.escape(_GARBLED_BLOCKS)}]+')
_REPLACEMENT_RE = re.compile(r'[\uFFFD\ufffd]+')  # U+FFFD replacement characters
_MULTI_UNDERSCORE = re.compile(r'_+')
_MULTI_SPACE = re.compile(r' {2,}')
_MULTI_DOT = re.compile(r'\.{2,}')

def sanitize_filename(name):
    """Strip garbled characters, keep surviving ASCII/CJK fragments.
    Returns sanitized name or None if nothing useful remains."""
    
    # 1. Strip known garbled blocks
    cleaned = _GARBLED_RE.sub('', name)
    
    # 2. Strip replacement characters
    cleaned = _REPLACEMENT_RE.sub('', cleaned)
    
    # 3. Clean up artifacts
    cleaned = _MULTI_UNDERSCORE.sub('_', cleaned)
    cleaned = _MULTI_SPACE.sub(' ', cleaned)
    cleaned = _MULTI_DOT.sub('.', cleaned)
    cleaned = cleaned.strip(' _-')
    
    # 4. Remove empty parens
    cleaned = re.sub(r'\(\s*\)', '', cleaned)
    
    # 5. Check if anything useful remains
    meaningful = sum(1 for c in cleaned if c.isalnum() or c in '._-()[]')
    if meaningful < 2:
        return None
    
    return cleaned

# === Fallback: cluster into date-based folders ===
def cluster_fallback(fpath, directory):
    """Move un-recoverable files into Recovered_YYYY-MM-DD/ with hash-based names"""
    try:
        mtime = os.path.getmtime(fpath)
        date_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
        
        # Determine category from extension
        ext = os.path.splitext(fpath)[1].lower()
        if ext in ('.jpg','.jpeg','.png','.gif','.bmp','.webp'):
            folder = f"Recovered_Images_{date_str}"
            prefix = "IMG"
        elif ext in ('.mp4','.mkv','.avi','.mov','.wmv'):
            folder = f"Recovered_Videos_{date_str}"
            prefix = "VID"
        elif ext in ('.mp3','.wav','.flac','.aac','.wma'):
            folder = f"Recovered_Audio_{date_str}"
            prefix = "AUD"
        elif ext in ('.doc','.docx','.pdf','.xls','.xlsx','.ppt','.pptx'):
            folder = f"Recovered_Docs_{date_str}"
            prefix = "DOC"
        else:
            folder = f"Recovered_Files_{date_str}"
            prefix = "FILE"
        
        # Generate unique name with content hash
        h = hashlib.md5()
        try:
            with open(fpath, 'rb') as f:
                for chunk in iter(lambda: f.read(65536), b''):
                    h.update(chunk)
            short_hash = h.hexdigest()[:8]
        except:
            short_hash = datetime.datetime.now().strftime("%H%M%S")
        
        folder_path = os.path.join(directory, folder)
        return f"{folder}/{prefix}_{date_str.replace('-','')}_{short_hash}{ext}"
    except:
        return None

def scan_sanitize(directory, config=None):
    """Apply sanitizer to all files, cluster fallbacks. Returns [(old, new, strategy), ...]"""
    records = []
    skip = set()
    if config:
        skip.update(config.get('skip_patterns', []))
    
    for fname in sorted(os.listdir(directory)):
        fpath = os.path.join(directory, fname)
        if os.path.isdir(fpath):
            # Also clean directory names
            cleaned = sanitize_filename(fname)
            if cleaned and cleaned != fname:
                records.append((fname, cleaned, "DirSanitize"))
            continue
        
        if any(re.match(p, fname) for p in skip): continue
        if not any(ord(c) > 127 for c in fname): continue
        
        # Try sanitize first
        cleaned = sanitize_filename(fname)
        if cleaned and cleaned != fname and len(cleaned) >= 3:
            records.append((fname, cleaned, "Sanitize"))
        else:
            # Fallback: cluster
            result = cluster_fallback(fpath, directory)
            if result:
                records.append((fname, result, "Fallback"))
    
    return records
