# Phase 5: Hardcode mapping + regex preserve + directory cleanup
import os, re

# Hardcoded 1:1 mappings for non-standard encoding corruptions
HARDCODE_DICT = {
    "ç³»ç»Ÿ.csv": "系统.csv",
    "360U┼╠╝°╢¿╞≈╢└┴ó░µ.exe.zip": "360U盘鉴定器独立版.exe.zip",
    "╟δ╧╚╜Γ╤╣ú¼╚╗║≤╘┘╘╦╨╨úíúíúí.txt.zip": "请先解压，然后再运行！！！.txt.zip",
}

# Garbled character regex for stripping
GARBLED_RE = re.compile(
    r'[閿熸枻鎷鏂ゆ嫹烽敓绲痑铻厧搴楃骇缁存唻碉拷婵锟斤拷锟絯锟斤拷'
    r'塕捇屽姵塻墿瀵屽▍瀵曟禍椋庢嫹塳鏂ゆ壈濠婄€犲摜瀵斿▍椋庢嫹渚濞€濞€濞€濞€'
    r'┼╠╝°╢¿╞≈╢└┴ó░µ╟δ╧╚╜Γ╤╣ú¼╚╗║≤╘┘╘╦╨╨úí'
    r'?????????]+',
    re.UNICODE
)

GARBLED_MARKERS = ['閿', '熸', '枻', '鎷', '鏂', 'ゆ', '嫹', '┼', '╠', '╝',
                   'ç', '»', 'Ÿ', '╟', 'δ', '锟斤拷', '痑v', '\ufffd']

def is_garbled(name):
    """Check if filename contains known garbled markers"""
    return any(m in name for m in GARBLED_MARKERS)

def clean_name(raw_name):
    """Strip garbled characters from filename, keep English + symbols"""
    cleaned = GARBLED_RE.sub('', raw_name)
    cleaned = re.sub(r'_+', '_', cleaned)
    cleaned = re.sub(r'\.{2,}', '.', cleaned)
    cleaned = re.sub(r' {2,}', ' ', cleaned)
    cleaned = re.sub(r'\(\s*\)', '', cleaned)
    cleaned = cleaned.strip(' _-')
    return cleaned if cleaned else None

def rebuild_keyfile(fname):
    """Extract prefix_key + email/token from garbled filenames"""
    m = re.match(
        r'^([A-Za-z0-9_]+)_[\u4e00-\u9fff\u0080-\uffef]+([A-Za-z0-9@.]+)(\s*\(\d+\))?\.(.+)$',
        fname)
    if m:
        prefix = m.group(1)
        suffix = m.group(2)
        seq = m.group(3) or ''
        ext = m.group(4)
        return f"{prefix}_{suffix}{seq}.{ext}"
    return None

def rebuild_generic(fname):
    """Generic rebuild: extract surviving identifiers"""
    ext = os.path.splitext(fname)[1]
    
    # RPA tutorial pattern
    if 'RPA' in fname:
        nums = re.findall(r'\d+', fname[:10])
        return f"{'_'.join(nums[:2])}_RPA{ext}" if nums else None
    
    # Numbered files
    m = re.search(r'(\d{4,5})', fname)
    seq_m = re.search(r'\((\d+)\)', fname)
    if m and ext in ('.xlsx', '.xls'):
        seq = f" ({seq_m.group(1)})" if seq_m else ""
        return f"{m.group(1)}{seq}{ext}"
    
    # Extract English words
    eng = re.findall(r'[A-Za-z][A-Za-z0-9._]*', fname)
    if eng:
        base = '_'.join(w for w in eng if len(w) > 1)
        if len(base) > 3: return base + ext
    
    return None

def scan_hardcode(directory):
    """Apply hardcode and regex strategies to remaining files"""
    records = []
    goods = ['闸北店','杨浦店','康桥店','泗泾店','南翔店','飞牛淮阴',
             '薪资组','工资项','录像.wav','镜像写盘工具','微信图片',
             '图片转视频','Recovered_','_Trash','Auto Release','DS918',
             'win32diskimager','系统.csv','未命名_double']
    
    for item in sorted(os.listdir(directory)):
        if any(g in item for g in goods): continue
        if not any(ord(c) > 127 for c in item): continue
        
        itempath = os.path.join(directory, item)
        is_dir = os.path.isdir(itempath)
        new_name = None
        
        # Hardcode dict
        if item in HARDCODE_DICT:
            new_name = HARDCODE_DICT[item]
        
        # Directory cleanup
        elif is_dir and is_garbled(item):
            new_name = clean_name(item)
        
        # Keyfile rebuild
        elif not is_dir and ('key' in item.lower() or '@' in item):
            new_name = rebuild_keyfile(item)
            if not new_name:
                new_name = clean_name(item)
        
        # Generic rebuild
        elif not is_dir and is_garbled(item):
            new_name = clean_name(item)
            if not new_name or len(new_name) < 3:
                new_name = rebuild_generic(item)
        
        if new_name and new_name != item:
            records.append((item, new_name, is_dir))
    
    return records
