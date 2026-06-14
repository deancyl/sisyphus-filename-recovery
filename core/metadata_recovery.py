# Phase 3: Metadata recovery (torrent, PDF, docx, media, fixed patterns)
import os, re

def recover_from_torrent(fpath):
    """Recover filename from torrent bencode metadata"""
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
            return str(name) + '.torrent'
    except: pass
    return None

def recover_from_pdf(fpath):
    """Recover filename from PDF title metadata"""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(fpath)
        title = reader.metadata.get('/Title', None) if reader.metadata else None
        if title and len(str(title)) > 2:
            t = str(title)
            skip = ['幻灯片', 'Slide', '无标题', 'Untitled']
            if any(s in t for s in skip) and len(t) < 10: return None
            return t + '.pdf'
    except: pass
    return None

def recover_from_docx(fpath):
    """Recover filename from docx core properties"""
    try:
        from docx import Document
        doc = Document(fpath)
        title = doc.core_properties.title
        if title and len(str(title)) > 2:
            return str(title) + '.docx'
    except: pass
    return None

def recover_from_media(fpath):
    """Recover filename from media file metadata"""
    try:
        from mutagen import File
        mf = File(fpath)
        if mf is None: return None
        for tag in ('title', 'Title', 'TIT2', '\xa9nam', '\u00a9nam'):
            title = mf.get(tag, None)
            if title:
                if isinstance(title, list) and title: title = title[0]
                if isinstance(title, str) and len(title) > 2:
                    return str(title) + os.path.splitext(fpath)[1]
    except: pass
    return None

# Fixed pattern replacements (garbled -> correct)
FIXED_PATTERNS = [
    (r'閿熸枻鎷峰綍閿熸枻鎷烽敓绲痑v', '录像.wav'),
    (r'锟斤拷录锟斤拷锟絯av', '录像.wav'),
    (r'图片转锟斤拷频', '图片转视频'),
    (r'微锟斤拷图片', '微信图片'),
    (r'微锟斤拷频', '微信视频'),
    (r'微锟斤拷', '微信'),
    (r'閿熸枻鎷烽敓鏂ゆ嫹鍐欓敓鏁欑櫢鎷烽敓鏂ゆ嫹', '镜像写盘工具'),
]

def recover_fixed_pattern(fname):
    """Apply known garbled->correct pattern replacements"""
    for pat, repl in FIXED_PATTERNS:
        new = re.sub(pat, repl, fname)
        if new != fname: return new
    return None

def scan_metadata(directory):
    """Scan directory for files recoverable via metadata"""
    records = []
    skip_prefixes = [r'^\d{5}(闸北|杨浦|康桥|泗泾|南翔|飞牛淮阴|薪资组|工资项)']
    
    for fname in sorted(os.listdir(directory)):
        fpath = os.path.join(directory, fname)
        if os.path.isdir(fpath): continue
        if any(re.match(p, fname) for p in skip_prefixes): continue
        
        ext = os.path.splitext(fname)[1].lower()
        new_name = None; strategy = ""
        
        if ext == '.torrent':
            new_name = recover_from_torrent(fpath)
            strategy = "Torrent"
        elif ext == '.pdf':
            new_name = recover_from_pdf(fpath)
            strategy = "PDF"
        elif ext in ('.docx', '.doc'):
            new_name = recover_from_docx(fpath)
            strategy = "Docx"
        elif ext in ('.mp4', '.mkv', '.avi', '.mov'):
            new_name = recover_from_media(fpath)
            strategy = "Media"
        
        if not new_name:
            new_name = recover_fixed_pattern(fname)
            strategy = "FixedPattern"
        
        if new_name and new_name != fname:
            records.append((fname, new_name, strategy))
    
    return records
