"""
=== Phase 3: 分层元数据恢复脚本 ===
- Phase 0: 哈希查重 - 删除重复的乱码副本
- Phase 1: Excel薪资表 - 字典+正则重建
- Phase 2: .torrent - bencode 读取内部真实文件名
- Phase 3: .pdf/.docx - 提取文档标题元数据
- Phase 4: .mkv/.mp4 - mutagen 读取视频标题
- Phase 5: 固定特征 - 硬映射正则替换
输出: rename_phase3_preview.csv
"""
import os, re, hashlib, pandas as pd

DOWNLOADS = os.path.expanduser(r"~\Downloads")
OUTPUT = os.path.expanduser(r"~\Desktop\rename_phase3_preview.csv")

# ============ 字典 ============
shop_dict = {"10001":"闸北店","10002":"杨浦店","10027":"康桥店","10066":"泗泾店","10150":"南翔店","10910":"","40909":"","90907":"飞牛淮阴"}

def infer_date(name):
    if "0263" in name or "202603" in name: return "2026年03月"
    if "0264" in name or "202604" in name: return "2026年04月"
    if "0265" in name or "202605" in name: return "2026年05月"
    return ""

def infer_type(name):
    if "妯" in name or "模" in name or "ģ" in name: return "税前工资模板"
    if "鏀圭尨" in name or "修改前" in name or "改猴" in name or "ǰ" in name: return "税前工资表-手工修改前数据"
    if "闈" in name or "修改后" in name or "革拷" in name or "ĺ" in name: return "税前工资表-手工修改后数据"
    if "税后" in name: return "税后工资表"
    if "询薪" in name or "配置" in name: return "工资项配置模板"
    return "税前工资表"

# ============ Phase 0: 哈希查重 ============
def get_file_hash(filepath):
    h = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        return h.hexdigest()
    except:
        return None

def find_duplicates(directory):
    """Find garbled files that are duplicates of already-correct files"""
    # Build hash map of "clean" files first
    clean_files = {}
    skip_patterns = [r'^\d{5}(闸北|杨浦|康桥|泗泾|南翔|飞牛淮阴|薪资组)']
    
    for fname in os.listdir(directory):
        is_clean = False
        for pat in skip_patterns:
            if re.match(pat, fname):
                is_clean = True
                break
        if is_clean:
            fpath = os.path.join(directory, fname)
            h = get_file_hash(fpath)
            if h:
                clean_files[h] = fname
    
    # Check garbled files against clean ones
    duplicates = []
    for fname in os.listdir(directory):
        is_clean = False
        for pat in skip_patterns:
            if re.match(pat, fname):
                is_clean = True
                break
        if is_clean: continue
        
        fpath = os.path.join(directory, fname)
        if os.path.isdir(fpath): continue
        h = get_file_hash(fpath)
        if h and h in clean_files and clean_files[h] != fname:
            duplicates.append((fname, clean_files[h], h))
    
    return duplicates

# ============ Phase 1: Excel 薪资表 ============
def rebuild_salary(name):
    m = re.search(r'^(\d{5})', name)
    if not m: return None
    sid = m.group(1)
    shop = shop_dict.get(sid, "")
    date = infer_date(name)
    ftype = infer_type(name)
    seq = ""
    sm = re.search(r'\((\d+)\)', name)
    if sm: seq = f" ({sm.group(1)})"
    ext = os.path.splitext(name)[1].lower() or ".xlsx"
    
    if sid in ("10910",):
        new = f"{sid}{ftype}{seq}{ext}"
    elif shop:
        if "202604" in name and "模板" in ftype:
            new = f"{sid}{shop}薪资组_202604_{ftype}{seq}{ext}"
        elif date:
            new = f"{sid}{shop}薪资组_{date}_{ftype}{seq}{ext}"
        else:
            new = f"{sid}{shop}薪资组_{ftype}{seq}{ext}"
    else:
        if date:
            new = f"{sid}薪资组_{date}_{ftype}{seq}{ext}"
        else:
            new = f"{sid}薪资组_{ftype}{seq}{ext}"
    return re.sub(r'_+', '_', new).replace("组__","组_").replace("配置_","配置")

# ============ Phase 2: .torrent 种子 ============
def rebuild_torrent(fpath):
    try:
        import bencode
        with open(fpath, 'rb') as f:
            data = bencode.decode(f.read())
        info = data.get('info', {})
        # Try utf-8 name first, then fallback
        name = info.get('name.utf-8') or info.get('name')
        if name:
            if isinstance(name, bytes):
                try:
                    name = name.decode('utf-8')
                except:
                    try:
                        name = name.decode('gbk')
                    except:
                        name = str(name)
            return str(name) + '.torrent'
    except:
        pass
    return None

# ============ Phase 3: .pdf / .docx 文档 ============
def rebuild_pdf(fpath):
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(fpath)
        title = reader.metadata.get('/Title', None) if reader.metadata else None
        if title and len(str(title)) > 2:
            t = str(title)
            # Skip generic titles
            skip_titles = ['幻灯片', 'Slide', '无标题', 'Untitled', '演示文稿']
            if any(s in t for s in skip_titles) and len(t) < 10:
                return None
            return t + '.pdf'
    except:
        pass
    return None

def rebuild_docx(fpath):
    try:
        from docx import Document
        doc = Document(fpath)
        title = doc.core_properties.title
        if title and len(str(title)) > 2:
            return str(title) + '.docx'
    except:
        pass
    return None

# ============ Phase 4: 视频媒体 ============
def rebuild_media(fpath):
    try:
        from mutagen import File
        mf = File(fpath)
        if mf is None: return None
        # Try common title tags
        for tag in ('title', 'Title', 'TIT2', '\xa9nam', '©nam'):
            title = mf.get(tag, None)
            if title:
                if isinstance(title, list) and title:
                    title = title[0]
                if isinstance(title, str) and len(title) > 2:
                    return str(title) + os.path.splitext(fpath)[1]
    except:
        pass
    return None

# ============ Phase 5: 固定特征硬映射 ============
FIXED_PATTERNS = [
    # WAV recordings: full pattern match first
    (r'閿熸枻鎷峰綍閿熸枻鎷烽敓绲痑v', '录像.wav'),
    (r'閿熸枻鎷峰綍閿熸枻鎷烽敓缁茬', '录像.wa'),
    # Generic
    (r'锟斤拷录锟斤拷锟絯av', '录像.wav'),
    (r'图片转锟斤拷频', '图片转视频'),
    (r'微锟斤拷图片', '微信图片'),
    (r'微锟斤拷频', '微信视频'),
    (r'微锟斤拷', '微信'),
    # Image patterns
    (r'閿熸枻鎷烽敓鏂ゆ嫹鍐欓敓鏁欑櫢鎷烽敓鏂ゆ嫹', '镜像写盘工具'),
]

def rebuild_fixed(name):
    for pat, repl in FIXED_PATTERNS:
        new = re.sub(pat, repl, name)
        if new != name:
            return new
    return None

# ============ 主流程 ============
records = []
skip_prefixes = [r'^\d{5}(闸北|杨浦|康桥|泗泾|南翔|飞牛淮阴|薪资组|工资项)']

# Phase 0: Find and mark duplicates
dupes = find_duplicates(DOWNLOADS)
for old, clean, h in dupes:
    records.append((old, f"[DELETE - duplicate of {clean}]", "P0-Duplicate", "DELETE"))

# Scan remaining
for fname in os.listdir(DOWNLOADS):
    fpath = os.path.join(DOWNLOADS, fname)
    if os.path.isdir(fpath): continue
    
    # Skip already-fixed
    skip = False
    for pat in skip_prefixes:
        if re.match(pat, fname): skip = True; break
    if skip: continue
    
    # Skip already-marked duplicates
    if any(d[0] == fname for d in dupes): continue
    
    ext = os.path.splitext(fname)[1].lower()
    new_name = None; strategy = ""
    
    # P1: Salary Excel
    if re.match(r'^\d{5}', fname) and ext in ('.xlsx', '.xls'):
        new_name = rebuild_salary(fname)
        strategy = "P1-Salary"
    
    # P2: Torrent
    elif ext == '.torrent':
        new_name = rebuild_torrent(fpath)
        if new_name: strategy = "P2-Torrent"
    
    # P3: PDF/DOCX
    elif ext == '.pdf':
        new_name = rebuild_pdf(fpath)
        if new_name: strategy = "P3-PDF"
    elif ext in ('.docx', '.doc'):
        new_name = rebuild_docx(fpath)
        if new_name: strategy = "P3-Docx"
    
    # P4: Media
    elif ext in ('.mp4', '.mkv', '.avi'):
        new_name = rebuild_media(fpath)
        if new_name: strategy = "P4-Media"
    
    # P5: Fixed patterns (fallback)
    if not new_name:
        new_name = rebuild_fixed(fname)
        if new_name: strategy = "P5-Fixed"
    
    if new_name and new_name != fname:
        target = os.path.join(DOWNLOADS, new_name)
        if os.path.exists(target):
            # Hash comparison: same content = duplicate, delete garbage
            h1 = get_file_hash(fpath)
            h2 = get_file_hash(target)
            if h1 and h2 and h1 == h2:
                records.append((fname, f"[DELETE - duplicate of {new_name}]", strategy, "DELETE"))
            else:
                # Different content - add collision marker
                base, ext = os.path.splitext(new_name)
                alt = f"{base}_COLLISION{ext}"
                records.append((fname, alt, strategy, "COLLISION"))
        else:
            records.append((fname, new_name, strategy, "OK"))
    elif not new_name and any(ord(c) > 127 for c in fname):
        records.append((fname, "", "SKIP", "MANUAL"))

# Output
df = pd.DataFrame(records, columns=["OldName","NewName","Strategy","Status"])
df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")

print("=== Phase 3 Preview ===")
for s in ["P0-Duplicate","P1-Salary","P2-Torrent","P3-PDF","P3-Docx","P4-Media","P5-Fixed","SKIP"]:
    count = len(df[df['Strategy']==s])
    del_count = len(df[(df['Strategy']==s)&(df['Status']=='DELETE')])
    col_count = len(df[(df['Strategy']==s)&(df['Status']=='COLLISION')])
    extra = ""
    if del_count: extra += f" ({del_count} DEL)"
    if col_count: extra += f" ({col_count} COL)"
    if count > 0: print(f"  {s}: {count}{extra}")
print(f"  MANUAL: {len(df[df['Status']=='MANUAL'])}")
print(f"\nSaved: {OUTPUT}")
