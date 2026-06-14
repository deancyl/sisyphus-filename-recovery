# Phase 4-M2: Archive interior inspection recovery
import os, re, zipfile, tarfile

def recover_from_archive(fpath):
    """Infer filename from archive contents (top-level folder or largest file)"""
    ext = os.path.splitext(fpath)[1].lower()
    
    # ZIP
    try:
        if zipfile.is_zipfile(fpath):
            with zipfile.ZipFile(fpath, 'r') as z:
                names = z.namelist()
                if names:
                    toplevel = set(n.strip('/').split('/')[0] for n in names if n.strip('/').split('/')[0])
                    if toplevel:
                        best = max(toplevel, key=len)
                        if len(best) > 2:
                            return best + ext
                    best = max(names, key=lambda n: len(
                        n.strip('/').split('/')[-1]))
                    base = best.strip('/').split('/')[-1]
                    if len(base) > 2: return base + ext
    except: pass
    
    # TAR
    try:
        if tarfile.is_tarfile(fpath):
            with tarfile.open(fpath, 'r') as tar:
                names = tar.getnames()
                if names:
                    toplevel = set(n.strip('/').split('/')[0] for n in names if n.strip('/').split('/')[0])
                    if toplevel:
                        best = max(toplevel, key=len)
                        if len(best) > 2:
                            return best + ext
    except: pass
    
    return None

def scan_archives(directory):
    """Scan archives in directory for recoverable names"""
    records = []
    for fname in sorted(os.listdir(directory)):
        fpath = os.path.join(directory, fname)
        if os.path.isdir(fpath): continue
        ext = os.path.splitext(fname)[1].lower()
        if ext not in ('.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'): continue
        if not any(ord(c) > 127 for c in fname): continue
        
        new_name = recover_from_archive(fpath)
        if new_name and new_name != fname:
            records.append((fname, new_name))
    
    return records
