"""
=== Phase 5: 100% Ultimate Cleanup ===
M1: False Positive Filter - skip already-correct Chinese
M2: Hardcode Dictionary - exact 1:1 mapping
M3: Directory Cleanup - strip garbled chars, keep English
M4: Regex Preserve - extract surviving identifiers

Output: phase5_final_log.csv
"""
import os, re, shutil, datetime, pandas as pd

DOWNLOADS = os.path.expanduser(r"~\Downloads")
LOG = os.path.expanduser(r"~\Desktop\phase5_final_log.csv")

# ============ M1: False Positive Detection ============
# Files containing these garbled markers are truly garbled
GARBLED_MARKERS = ['閿', '熸', '枻', '鎷', '鏂', 'ゆ', '嫹', '┼', '╠', '╝', 'ç', '»', 'Ÿ', '╟', 'δ',
                   '﻿', '����', '锟斤拷', '痑v']

def is_garbled(name):
    """True if filename contains known garbled markers"""
    for m in GARBLED_MARKERS:
        if m in name:
            return True
    return False

def is_false_positive(name):
    """True if name has CJK but no garbled markers - likely correct"""
    has_cjk = any(0x4E00 <= ord(c) <= 0x9FFF for c in name)
    has_garbled = is_garbled(name)
    return has_cjk and not has_garbled

# ============ M2: Hardcode Dictionary ============
HARDCODE = {
    "ç³»ç»Ÿ.csv": "系统.csv",
    "360U┼╠╝°╢¿╞≈╢└┴ó░µ.exe.zip": "360U盘鉴定器独立版.exe.zip",
    "╟δ╧╚╜Γ╤╣ú¼╚╗║≤╘┘╘╦╨╨úíúíúí.txt.zip": "请先解压，然后再运行！！！.txt.zip",
    "男,,28岁,178cm,,,,,,,,,,,.csv": "体检数据_男_28岁.csv",
}

# ============ M3: Directory Cleanup ============
GARBLED_CHARS_RE = re.compile(r'[閿熸枻鎷鏂ゆ嫹烽敓绲痑铻厧搴楃骇缁存唻碉拷婵锟斤拷锟絯锟斤拷塕捇屽姵塻墿瀵屽▍瀵曟禍椋庢嫹塳鏂ゆ壈濠婄€犲摜瀵斿▍椋庢嫹渚濞€濞€濞€濞€]+', re.UNICODE)

def clean_dir_name(name):
    """Strip garbled characters, keep English + common symbols"""
    cleaned = GARBLED_CHARS_RE.sub('', name)
    # Clean up artifacts
    cleaned = re.sub(r'_+', '_', cleaned)
    cleaned = re.sub(r'\.{2,}', '.', cleaned)
    cleaned = re.sub(r' {2,}', ' ', cleaned)
    cleaned = re.sub(r'\(\s*\)', '', cleaned)
    cleaned = cleaned.strip(' _-')
    return cleaned if cleaned else None

# ============ M4: Regex Preserve ============
def rebuild_keyfile(name):
    """Extract prefix_key + email/token from garbled filenames"""
    # Pattern: Something_key GARBLED email@domain.zip
    m = re.match(r'^([A-Za-z0-9_]+)_[\u4e00-\u9fff\u3000-\u303f\u0080-\uffef]+([A-Za-z0-9@.]+)(\s*\(\d+\))?\.(.+)$', name)
    if m:
        prefix = m.group(1)
        suffix = m.group(2)
        seq = m.group(3) or ''
        ext = m.group(4)
        return f"{prefix}_{suffix}{seq}.{ext}"
    
    # Fallback: just join ASCII parts
    ext = os.path.splitext(name)[1]
    parts = re.findall(r'[A-Za-z0-9_@.]+', name)
    if parts:
        # Join parts with _, skip short ones
        meaningful = [p for p in parts if len(p) > 2 or '@' in p]
        if meaningful:
            result = '_'.join(meaningful) + ext
            result = re.sub(r'_+', '_', result)
            return result
    return None

def rebuild_generic(name):
    """Generic cleanup: strip all CJK garbled, keep numbers + ASCII"""
    ext = os.path.splitext(name)[1]
    
    # Extract numbers (IDs, dates, sequences)
    nums = re.findall(r'\d+', name)
    seq_match = re.search(r'\((\d+)\)', name)
    seq = f" ({seq_match.group(1)})" if seq_match else ""
    
    # Extract English words
    eng_words = re.findall(r'[A-Za-z][A-Za-z0-9._]*', name)
    
    # Special cases
    if name.startswith('02') and 'RPA' in name:
        return f"02_1.2_RPA{ext}"
    
    # For the weird Excel file
    m = re.search(r'(\d{4,5})', name)
    if m and ext in ('.xlsx', '.xls'):
        return f"{m.group(1)}{seq}{ext}"
    
    # Generic: join English parts
    if eng_words:
        base = '_'.join([w for w in eng_words if len(w) > 1])
        if len(base) > 3:
            return base + ext
    
    # Last resort: just use the first number found + extension
    if nums:
        return f"file_{nums[0]}{ext}"
    
    return None

# ============ Main ============
records = []

for item in sorted(os.listdir(DOWNLOADS)):
    itempath = os.path.join(DOWNLOADS, item)
    is_dir = os.path.isdir(itempath)
    
    # Skip already-fixed
    goods = ['闸北店','杨浦店','康桥店','泗泾店','南翔店','飞牛淮阴','薪资组','工资项','录像.wav','镜像写盘工具','微信图片','图片转视频','Recovered_','_Trash']
    if any(g in item for g in goods): continue
    
    # Skip ASCII-only
    if not any(ord(c) > 127 for c in item): continue
    
    tag = "[DIR]" if is_dir else "[FILE]"
    strategy = ""; new_name = None; status = ""
    
    # M1: Check if false positive (correct Chinese, no garbled markers)
    if is_false_positive(item):
        records.append((item, item, "M1-FalsePositive", "SKIP_OK"))
        continue
    
    # M2: Hardcode dictionary
    if item in HARDCODE:
        new_name = HARDCODE[item]
        strategy = "M2-Hardcode"
        status = "OK"
    
    # M3: Directory cleanup
    elif is_dir:
        new_name = clean_dir_name(item)
        strategy = "M3-DirClean"
        status = "OK" if new_name else "MANUAL"
    
    # M4: Regex preserve (files)
    else:
        # Try keyfile pattern first
        if 'key' in item.lower() or '@' in item:
            new_name = rebuild_keyfile(item)
            if new_name: strategy = "M4-Keyfile"
        
        # Generic rebuild
        if not new_name:
            # Check if has garbled markers
            if is_garbled(item):
                # Strip garbled chars first
                cleaned = clean_dir_name(item)  # works on filenames too
                if cleaned and len(cleaned) > 3:
                    new_name = cleaned
                    strategy = "M4-CleanStrip"
                else:
                    new_name = rebuild_generic(item)
                    strategy = "M4-Generic"
            else:
                # No garbled markers but still has non-ASCII - probably OK
                records.append((item, item, "M1-Pass", "SKIP_OK"))
                continue
        
        status = "OK" if new_name else "MANUAL"
    
    if new_name and new_name != item:
        records.append((item, new_name, strategy, status))
    elif not new_name:
        records.append((item, "", strategy, "MANUAL"))

# ============ Execute ============
renamed = 0; skipped = 0; manual = 0
log_rows = []

for old, new, strat, st in records:
    if st == "SKIP_OK":
        log_rows.append((old, new, "SKIPPED_OK", strat))
        skipped += 1
        continue
    
    if st == "MANUAL":
        log_rows.append((old, new, "SKIPPED_MANUAL", strat))
        manual += 1
        continue
    
    old_path = os.path.join(DOWNLOADS, old)
    new_path = os.path.join(DOWNLOADS, new)
    
    if not os.path.exists(old_path):
        log_rows.append((old, new, "NOT_FOUND", strat))
        continue
    
    if os.path.exists(new_path) and old != new:
        log_rows.append((old, new, "COLLISION", strat))
        continue
    
    try:
        os.rename(old_path, new_path)
        log_rows.append((old, new, "RENAMED", strat))
        renamed += 1
    except Exception as e:
        log_rows.append((old, new, f"FAIL: {e}", strat))

# Save log
df = pd.DataFrame(log_rows, columns=["OldName","NewName","Action","Strategy"])
df.to_csv(LOG, index=False, encoding="utf-8-sig")

# ============ Summary ============
print("=== Phase 5: Final Cleanup ===")
for s in sorted(df['Strategy'].unique()):
    sub = df[df['Strategy'] == s]
    print(f"  {s}: {len(sub)}")
print(f"\n  Renamed:  {renamed}")
print(f"  Skipped:  {skipped} (already correct)")
print(f"  Manual:   {manual}")
print(f"  TOTAL:    {len(df)}")

# Verify: any remaining garbled?
remaining = 0
for f in sorted(os.listdir(DOWNLOADS)):
    if any(ord(c) > 127 for c in f):
        # Check if it's a known good pattern
        kgoods = ['闸北店','杨浦店','康桥店','泗泾店','南翔店','飞牛淮阴','薪资组','工资项','录像.wav','镜像写盘工具','微信图片','图片转视频','Recovered_','_Trash']
        if any(g in f for g in kgoods): continue
        # Check if it's real Chinese (no garbled markers)
        if is_false_positive(f): continue
        remaining += 1
        if remaining <= 10:
            t = '[DIR]' if os.path.isdir(os.path.join(DOWNLOADS, f)) else '[FILE]'
            print(f"  REMAINING: {t} {f}")

print(f"\n  Final garbled remaining: {remaining}")
print(f"Log: {LOG}")
