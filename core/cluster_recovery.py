# Phase 4-M4: Time-based clustering for unrecoverable files
import os, datetime, re

MEDIA_EXTS = {'.jpg':'Recovered_Images', '.jpeg':'Recovered_Images', 
              '.png':'Recovered_Images', '.gif':'Recovered_Images',
              '.bmp':'Recovered_Images', '.webp':'Recovered_Images',
              '.mp4':'Recovered_Videos', '.mkv':'Recovered_Videos',
              '.avi':'Recovered_Videos', '.mov':'Recovered_Videos',
              '.mp3':'Recovered_Audio', '.wav':'Recovered_Audio', 
              '.flac':'Recovered_Audio', '.aac':'Recovered_Audio',
              '.doc':'Recovered_Docs', '.docx':'Recovered_Docs',
              '.pdf':'Recovered_Docs', '.xlsx':'Recovered_Docs',
              '.xls':'Recovered_Docs', '.ppt':'Recovered_Docs', '.pptx':'Recovered_Docs'}

PREFIX_MAP = {'.jpg':'IMG', '.jpeg':'IMG', '.png':'IMG', '.gif':'IMG',
              '.bmp':'IMG', '.webp':'IMG', '.mp4':'VID', '.mkv':'VID',
              '.avi':'VID', '.mov':'VID', '.mp3':'AUD', '.wav':'AUD',
              '.flac':'AUD', '.aac':'AUD', '.doc':'DOC', '.docx':'DOC',
              '.pdf':'DOC', '.xlsx':'DOC', '.xls':'DOC', '.ppt':'DOC', '.pptx':'DOC'}

def cluster_file(fpath, directory):
    """Generate clustered folder + filename for an unrecoverable file"""
    try:
        ctime = os.path.getctime(fpath)
        date_str = datetime.datetime.fromtimestamp(ctime).strftime("%Y-%m-%d")
        ext = os.path.splitext(fpath)[1].lower()
        
        folder = MEDIA_EXTS.get(ext, "Recovered_Files")
        prefix = PREFIX_MAP.get(ext, "FILE")
        folder_name = f"{folder}_{date_str}"
        
        folder_path = os.path.join(directory, folder_name)
        existing = set(os.listdir(folder_path)) if os.path.exists(folder_path) else set()
        seq = 1
        clean_date = date_str.replace('-', '')
        while f"{prefix}_{clean_date}_{seq:03d}{ext}" in existing:
            seq += 1
        
        return f"{folder_name}/{prefix}_{clean_date}_{seq:03d}{ext}"
    except:
        return None

def scan_clusterable(directory):
    """Find files that should be clustered"""
    records = []
    goods = ['闸北店','杨浦店','康桥店','泗泾店','南翔店','飞牛淮阴',
             '薪资组','工资项','录像.wav','镜像写盘工具','微信图片',
             '图片转视频','Recovered_','_Trash']
    
    for fname in sorted(os.listdir(directory)):
        fpath = os.path.join(directory, fname)
        if os.path.isdir(fpath): continue
        if not any(ord(c) > 127 for c in fname): continue
        if any(g in fname for g in goods): continue
        
        ext = os.path.splitext(fname)[1].lower()
        if ext in MEDIA_EXTS:
            new_path = cluster_file(fpath, directory)
            if new_path:
                records.append((fname, new_path, "Cluster"))
    
    return records

# Phase 4-M1: Hash disambiguation for COLLISION
import hashlib

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
    except: return None

def resolve_collision(old_path, target_path):
    """Return: ('DELETE', None) if duplicate, ('RENAME', new_name) if different"""
    h1 = get_hash(old_path)
    h2 = get_hash(target_path)
    
    if h1 and h2 and h1 == h2:
        return ('DELETE', None)
    
    # Different content - add timestamp
    try:
        mtime = os.path.getmtime(old_path)
        ts = datetime.datetime.fromtimestamp(mtime).strftime("%m%d_%H%M")
        base, ext = os.path.splitext(os.path.basename(target_path))
        return ('RENAME', f"{base}_v{ts}{ext}")
    except:
        base, ext = os.path.splitext(os.path.basename(target_path))
        return ('RENAME', f"{base}_DUP{ext}")
