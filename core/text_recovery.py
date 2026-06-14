# Phase 4-M3: Text file first-line extraction recovery
import os, re

def recover_from_first_line(fpath):
    """Infer filename from first line of text file"""
    encodings = ['utf-8', 'gbk', 'utf-16', 'latin-1']
    
    for enc in encodings:
        try:
            with open(fpath, 'r', encoding=enc, errors='replace') as f:
                first = f.readline().strip()
                if first and len(first) > 3:
                    # Skip binary-looking lines
                    printable = sum(1 for c in first if c.isprintable() or c in ' \t\n\r')
                    if len(first) > 0 and printable / len(first) < 0.7:
                        continue
                    clean = re.sub(r'[\\/:*?"<>|]', '', first[:60]).strip()
                    clean = re.sub(r'^[#=/*\s-]+', '', clean)
                    clean = re.sub(r'[#=/*\s-]+$', '', clean)
                    if len(clean) >= 3:
                        return clean + os.path.splitext(fpath)[1]
        except: continue
    return None

def scan_textfiles(directory):
    """Scan text files for recoverable names"""
    records = []
    text_exts = ('.txt', '.csv', '.log', '.md', '.html', '.json', 
                 '.xml', '.yaml', '.yml', '.cfg', '.conf', '.ini',
                 '.sh', '.bat', '.ps1', '.py', '.js', '.ts', '.vue')
    
    for fname in sorted(os.listdir(directory)):
        fpath = os.path.join(directory, fname)
        if os.path.isdir(fpath): continue
        ext = os.path.splitext(fname)[1].lower()
        if ext not in text_exts: continue
        if not any(ord(c) > 127 for c in fname): continue
        
        new_name = recover_from_first_line(fpath)
        if new_name and new_name != fname:
            records.append((fname, new_name))
    
    return records
