"""
=== Phase 4: 自动裁决与启发式推断 ===
M1: 哈希消歧 - COLLISION 自动裁决
M2: ZIP/RAR 内视 - 压缩包内部文件名推断
M3: TXT/CSV 首行提取 - 纯文本文件标题推断
M4: 时序聚类归档 - 媒体/未知文件按日期打包

继承: P1-Salary, P2-Torrent, P3-PDF/Docx, P4-Media/Video, P5-Fixed

输出: rename_phase4_preview.csv (仅预览，不执行)
"""
import os, re, hashlib, datetime, shutil, zipfile, tarfile, pandas as pd

DOWNLOADS = os.path.expanduser(r"~\Downloads")
OUTPUT = os.path.expanduser(r"~\Desktop\rename_phase4_preview.csv")
TRASH = os.path.join(DOWNLOADS, "_Trash_Duplicates")

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

def safe_name(name):
    return re.sub(r'[\\/:*?"<>|]', '', name).strip()

def get_hash(fpath, quick=False):
    if quick:
        try: return os.path.getsize(fpath)
        except: return None
    h = hashlib.md5()
    try:
        with open(fpath, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                h.update(chunk)
        return h.hexdigest()
    except:
        return None

# ============ M1: 哈希消歧 ============
def resolve_collision(old_path, new_name, base_dir):
    """Auto-resolve COLLISION by comparing content with existing file"""
    target_path = os.path.join(base_dir, new_name)
    if not os.path.exists(target_path):
        return new_name, "OK"
    
    sz1 = get_hash(old_path, quick=True)
    sz2 = get_hash(target_path, quick=True)
    
    if sz1 and sz2 and sz1 == sz2:
        # Same size - do full hash
        h1 = get_hash(old_path)
        h2 = get_hash(target_path)
        if h1 and h2 and h1 == h2:
            return f"[DELETE duplicate of {new_name}]", "DELETE"
    
    # Different content - add timestamp
    try:
        mtime = os.path.getmtime(old_path)
        ts = datetime.datetime.fromtimestamp(mtime).strftime("%m%d_%H%M")
        base, ext = os.path.splitext(new_name)
        return f"{base}_v{ts}{ext}", "COLLISION_FIXED"
    except:
        base, ext = os.path.splitext(new_name)
        return f"{base}_DUP{ext}", "COLLISION_FIXED"

# ============ M2: ZIP/RAR 内视 ============
def rebuild_archive(fpath):
    """Infer filename from archive contents"""
    try:
        if zipfile.is_zipfile(fpath):
            with zipfile.ZipFile(fpath, 'r') as z:
                names = z.namelist()
                if not names: return None
                # Find top-level directory or largest file
                toplevel = set()
                for n in names:
                    parts = n.strip('/').split('/')
                    if parts[0]:
                        toplevel.add(parts[0])
                if toplevel:
                    best = max(toplevel, key=len)
                    if len(best) > 3:
                        return best + os.path.splitext(fpath)[1]
                # Fallback: largest file name
                best = max(names, key=lambda n: len(n))
                base = best.strip('/').split('/')[-1] or best.strip('/').split('/')[0]
                if len(base) > 3:
                    return base
    except:
        pass
    
    # Try tarfile
    try:
        if tarfile.is_tarfile(fpath):
            with tarfile.open(fpath, 'r') as tar:
                names = tar.getnames()
                if names:
                    toplevel = set()
                    for n in names:
                        parts = n.strip('/').split('/')
                        if parts[0]:
                            toplevel.add(parts[0])
                    if toplevel:
                        best = max(toplevel, key=len)
                        if len(best) > 3:
                            return best + os.path.splitext(fpath)[1]
    except:
        pass
    
    return None

# ============ M3: TXT/CSV 首行提取 ============
def rebuild_textfile(fpath):
    """Infer filename from first line of text file"""
    encodings = ['utf-8', 'gbk', 'utf-16', 'latin-1']
    
    for enc in encodings:
        try:
            with open(fpath, 'r', encoding=enc, errors='replace') as f:
                first = f.readline().strip()
                if first and len(first) > 3:
                    # Skip binary-looking lines (>30% non-printable)
                    printable = sum(1 for c in first if c.isprintable() or c in ' \t\n\r')
                    if len(first) > 0 and printable / len(first) < 0.7:
                        continue
                    # Clean up
                    clean = safe_name(first[:60])
                    clean = re.sub(r'^[#=/*\s-]+', '', clean)
                    clean = re.sub(r'[#=/*\s-]+$', '', clean)
                    if len(clean) >= 3:
                        return clean + os.path.splitext(fpath)[1]
        except:
            continue
    return None

# ============ M4: 时序聚类归档 ============
def cluster_by_time(fpath):
    """Group media files by creation date into folders"""
    try:
        ctime = os.path.getctime(fpath)
        date_str = datetime.datetime.fromtimestamp(ctime).strftime("%Y-%m-%d")
        
        ext = os.path.splitext(fpath)[1].lower()
        if ext in ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.heic'):
            folder = f"Recovered_Images_{date_str}"
            prefix = "IMG"
        elif ext in ('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv'):
            folder = f"Recovered_Videos_{date_str}"
            prefix = "VID"
        elif ext in ('.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma'):
            folder = f"Recovered_Audio_{date_str}"
            prefix = "AUD"
        elif ext in ('.doc', '.docx', '.pdf', '.xls', '.xlsx', '.ppt', '.pptx'):
            folder = f"Recovered_Docs_{date_str}"
            prefix = "DOC"
        else:
            folder = f"Recovered_Files_{date_str}"
            prefix = "FILE"
        
        # Find next sequence number
        folder_path = os.path.join(DOWNLOADS, folder)
        existing = set()
        if os.path.exists(folder_path):
            existing = set(os.listdir(folder_path))
        seq = 1
        while f"{prefix}_{date_str.replace('-','')}_{seq:03d}{ext}" in existing:
            seq += 1
        
        new_name = os.path.join(folder, f"{prefix}_{date_str.replace('-','')}_{seq:03d}{ext}")
        return new_name, "M4-Cluster"
    except:
        return None

# ============ 遗留策略 ============
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

def rebuild_torrent(fpath):
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

def rebuild_pdf(fpath):
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(fpath)
        title = reader.metadata.get('/Title', None) if reader.metadata else None
        if title and len(str(title)) > 2:
            t = str(title)
            skip = ['幻灯片', 'Slide', '无标题', 'Untitled', '演示文稿']
            if any(s in t for s in skip) and len(t) < 10: return None
            return t + '.pdf'
    except: pass
    return None

def rebuild_docx(fpath):
    try:
        from docx import Document
        doc = Document(fpath)
        title = doc.core_properties.title
        if title and len(str(title)) > 2:
            return str(title) + '.docx'
    except: pass
    return None

def rebuild_media_meta(fpath):
    try:
        from mutagen import File
        mf = File(fpath)
        if mf is None: return None
        for tag in ('title', 'Title', 'TIT2', '\xa9nam', '©nam'):
            title = mf.get(tag, None)
            if title:
                if isinstance(title, list) and title: title = title[0]
                if isinstance(title, str) and len(title) > 2:
                    return str(title) + os.path.splitext(fpath)[1]
    except: pass
    return None

FIXED_PATTERNS = [
    (r'閿熸枻鎷峰綍閿熸枻鎷烽敓绲痑v', '录像.wav'),
    (r'閿熸枻鎷峰綍閿熸枻鎷烽敓缁茬', '录像.wa'),
    (r'锟斤拷录锟斤拷锟絯av', '录像.wav'),
    (r'图片转锟斤拷频', '图片转视频'),
    (r'微锟斤拷图片', '微信图片'),
    (r'微锟斤拷频', '微信视频'),
    (r'微锟斤拷', '微信'),
    (r'閿熸枻鎷烽敓鏂ゆ嫹鍐欓敓鏁欑櫢鎷烽敓鏂ゆ嫹', '镜像写盘工具'),
]

def rebuild_fixed(name):
    for pat, repl in FIXED_PATTERNS:
        new = re.sub(pat, repl, name)
        if new != name: return new
    return None

# ============ 主扫描 ============
records = []
skip_prefixes = [r'^\d{5}(闸北|杨浦|康桥|泗泾|南翔|飞牛淮阴|薪资组|工资项)']
# Skip files already fixed in earlier phases
already_fixed = ['录像', '镜像写盘工具', '微信图片', '图片转视频']
skip_folders = ['_Trash_Duplicates']

# Create trash folder
if not os.path.exists(TRASH):
    os.makedirs(TRASH)

for fname in sorted(os.listdir(DOWNLOADS)):
    fpath = os.path.join(DOWNLOADS, fname)
    if os.path.isdir(fpath):
        if fname not in ('_Trash_Duplicates',) and not fname.startswith('Recovered_'):
            # Check if directory name is garbled
            if any(ord(c) > 127 for c in fname):
                # Try fixed patterns on directory names too
                new_name = rebuild_fixed(fname)
                if new_name and new_name != fname:
                    records.append((fname, new_name, "P5-Fixed-Dir", "OK"))
                else:
                    records.append((fname, "", "SKIP-DIR", "MANUAL"))
        continue
    
    # Skip already-fixed salary files and previously recovered files
    skip = False
    for pat in skip_prefixes:
        if re.match(pat, fname): skip = True; break
    for kw in already_fixed:
        if kw in fname: skip = True; break
    if skip: continue
    
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
    
    # P3: PDF/DOCX metadata
    elif ext == '.pdf':
        new_name = rebuild_pdf(fpath)
        if new_name: strategy = "P3-PDF"
    elif ext in ('.docx', '.doc'):
        new_name = rebuild_docx(fpath)
        if new_name: strategy = "P3-Docx"
    
    # P4: Video metadata
    elif ext in ('.mp4', '.mkv', '.avi', '.mov'):
        new_name = rebuild_media_meta(fpath)
        if new_name: strategy = "P4-MediaMeta"
    
    # M2: Archive interior
    elif ext in ('.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'):
        new_name = rebuild_archive(fpath)
        if new_name: strategy = "M2-Archive"
    
    # M3: Text file first line
    elif ext in ('.txt', '.csv', '.log', '.md', '.html', '.json', '.xml', '.yaml', '.yml', '.cfg', '.conf', '.ini', '.sh', '.bat', '.ps1', '.py', '.js', '.ts', '.vue'):
        new_name = rebuild_textfile(fpath)
        if new_name: strategy = "M3-TextFirstLine"
    
    # P5: Fixed patterns (fallback for known patterns)
    if not new_name:
        new_name = rebuild_fixed(fname)
        if new_name: strategy = "P5-Fixed"
    
    # M4: Cluster (ultimate fallback for media/unknown)
    if not new_name and ext in ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.mp3', '.flac', '.aac', '.wma', '.wav'):
        result = cluster_by_time(fpath)
        if result:
            new_name, strategy = result
    
    if new_name and new_name != fname:
        # Check if target exists (COLLISION)
        target_path = os.path.join(DOWNLOADS, new_name)
        if os.path.exists(target_path) and 'DELETE' not in new_name:
            # M1: Resolve collision
            resolved, status = resolve_collision(fpath, new_name, DOWNLOADS)
            records.append((fname, resolved, f"{strategy}->M1", status))
        else:
            records.append((fname, new_name, strategy, "OK"))
    elif not new_name and any(ord(c) > 127 for c in fname):
        # M4: cluster fallback for any remaining garbled non-ASCII files
        result = cluster_by_time(fpath)
        if result:
            new_name, strategy = result
            records.append((fname, new_name, "M4-Cluster-Fallback", "OK"))
        else:
            records.append((fname, "", "SKIP", "MANUAL"))

# Output
df = pd.DataFrame(records, columns=["OldName","NewName","Strategy","Status"])
df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")

print("=== Phase 4 Preview ===")
for s in sorted(df['Strategy'].unique()):
    sub = df[df['Strategy'] == s]
    dels = len(sub[sub['Status'] == 'DELETE'])
    cols = len(sub[sub['Status'] == 'COLLISION_FIXED'])
    extra = ""
    if dels: extra += f" ({dels} DEL)"
    if cols: extra += f" ({cols} COL)"
    print(f"  {s}: {len(sub)}{extra}")
print(f"  TOTAL: {len(df)}")
print(f"  DELETE: {len(df[df['Status']=='DELETE'])}")
print(f"  COLLISION_FIXED: {len(df[df['Status']=='COLLISION_FIXED'])}")
print(f"  MANUAL: {len(df[df['Status']=='MANUAL'])}")
print(f"\nSaved: {OUTPUT}")
