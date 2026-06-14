"""
Phase 2-3: Universal Metadata Extraction
Reads embedded metadata from all supported file types.
No business-specific logic - purely file format extraction.
"""
import os, re, zipfile, tarfile

# === Document readers ===
def _read_xlsx_cell(fpath, cell="A1"):
    try:
        import openpyxl
        wb = openpyxl.load_workbook(fpath, data_only=True)
        ws = wb.active
        c = ws.cell(1, 1).value
        wb.close()
        return str(c).strip() if c else None
    except: return None

def _read_pdf_title(fpath):
    try:
        from PyPDF2 import PdfReader
        r = PdfReader(fpath)
        t = r.metadata.get('/Title', None) if r.metadata else None
        return str(t).strip() if t and len(str(t))>2 else None
    except: return None

def _read_docx_title(fpath):
    try:
        from docx import Document
        d = Document(fpath)
        t = d.core_properties.title
        return str(t).strip() if t and len(t)>2 else None
    except: return None

# === Media readers ===
def _read_torrent_name(fpath):
    try:
        import bencode
        with open(fpath, 'rb') as f:
            data = bencode.decode(f.read())
        info = data.get('info', {})
        name = info.get('name.utf-8') or info.get('name')
        if name:
            if isinstance(name, bytes):
                try: name = name.decode('utf-8')
                except:
                    try: name = name.decode('gbk')
                    except: name = str(name)
            return str(name)
    except: return None

def _read_media_tags(fpath):
    try:
        from mutagen import File
        mf = File(fpath)
        if not mf: return None
        for tag in ('title', 'Title', 'TIT2', '\xa9nam'):
            v = mf.get(tag, None)
            if v:
                if isinstance(v, list) and v: v = v[0]
                if isinstance(v, str) and len(v) > 2:
                    return str(v)
    except: return None

# === Archive readers ===
def _read_archive_top(fpath):
    ext = os.path.splitext(fpath)[1].lower()
    try:
        if zipfile.is_zipfile(fpath):
            with zipfile.ZipFile(fpath) as z:
                names = z.namelist()
                if names:
                    tops = {n.strip('/').split('/')[0] for n in names if n.strip('/').split('/')[0]}
                    if tops:
                        return max(tops, key=len)
                    best = max(names, key=lambda n: len(n.strip('/').split('/')[-1]))
                    return best.strip('/').split('/')[-1]
    except: pass
    try:
        if tarfile.is_tarfile(fpath):
            with tarfile.open(fpath) as tar:
                names = tar.getnames()
                if names:
                    tops = {n.strip('/').split('/')[0] for n in names if n.strip('/').split('/')[0]}
                    if tops: return max(tops, key=len)
    except: pass
    return None

# === Text header reader ===
def _read_first_line(fpath):
    for enc in ('utf-8', 'gbk', 'latin-1'):
        try:
            with open(fpath, 'r', encoding=enc, errors='replace') as f:
                line = f.readline().strip()
                if line and len(line) > 3:
                    printable = sum(1 for c in line if c.isprintable() or c in ' \t')
                    if printable / len(line) >= 0.7:
                        clean = re.sub(r'[\\/:*?"<>|]', '', line[:80])
                        clean = re.sub(r'^[#=/*\s-]+', '', clean).strip()
                        if len(clean) >= 2: return clean
        except: continue
    return None

# === Main extractor ===
EXT_HANDLERS = {
    '.xlsx': ('document', _read_xlsx_cell),
    '.xls':  ('document', _read_xlsx_cell),
    '.pdf':  ('document', _read_pdf_title),
    '.docx': ('document', _read_docx_title),
    '.doc':  ('document', _read_docx_title),
    '.torrent': ('media', _read_torrent_name),
    '.mp4':  ('media', _read_media_tags),
    '.mkv':  ('media', _read_media_tags),
    '.avi':  ('media', _read_media_tags),
    '.mov':  ('media', _read_media_tags),
    '.mp3':  ('media', _read_media_tags),
    '.flac': ('media', _read_media_tags),
    '.wav':  ('media', _read_media_tags),
    '.zip':  ('archive', _read_archive_top),
    '.rar':  ('archive', _read_archive_top),
    '.7z':   ('archive', _read_archive_top),
    '.tar':  ('archive', _read_archive_top),
    '.gz':   ('archive', _read_archive_top),
}

TEXT_EXTS = {'.txt','.csv','.log','.md','.html','.json','.xml','.yaml','.yml',
             '.cfg','.conf','.ini','.sh','.bat','.ps1','.py','.js','.ts','.vue'}

def extract_metadata(fpath):
    """Extract a meaningful name from file metadata. Returns (name, category) or None."""
    ext = os.path.splitext(fpath)[1].lower()
    
    # Check registered handlers
    if ext in EXT_HANDLERS:
        category, handler = EXT_HANDLERS[ext]
        result = handler(fpath)
        if result and len(result) >= 2:
            return result + ext, category
    
    # Text file: first line
    if ext in TEXT_EXTS:
        result = _read_first_line(fpath)
        if result and len(result) >= 2:
            return result + ext, 'text'
    
    return None

def scan_metadata(directory, config=None):
    """Scan directory and return [(old_name, new_name, strategy), ...]"""
    records = []
    skip = set()
    if config:
        skip.update(config.get('skip_patterns', []))
        skip.add(r'^Recovered_')
        skip.add(r'^_Trash')
        skip.add(r'^_Sisyphus')
    
    for fname in sorted(os.listdir(directory)):
        fpath = os.path.join(directory, fname)
        if os.path.isdir(fpath): continue
        if any(re.match(p, fname) for p in skip): continue
        if not any(ord(c) > 127 for c in fname): continue
        
        result = extract_metadata(fpath)
        if result:
            new_name, category = result
            if new_name != fname:
                records.append((fname, new_name, category.capitalize()))
    
    return records
