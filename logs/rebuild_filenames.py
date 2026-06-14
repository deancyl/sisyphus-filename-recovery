"""
=== 分层模式重建脚本 ===
策略1: Excel薪资表 - 字典+正则重建
策略2: 影视/BT种子 - 提取英文原名去乱码
策略3: 软件/安装包 - 白名单保留英文名
输出: rename_preview.csv (仅预览，不执行重命名)
"""
import os, re, pandas as pd

DOWNLOADS = os.path.expanduser(r"~\Downloads")

# ========== 字典 ==========
shop_dict = {
    "10001": "闸北店", "10002": "杨浦店", "10027": "康桥店",
    "10066": "泗泾店", "10150": "南翔店",
    "10910": "", "40909": "", "90907": "飞牛淮阴"
}

def infer_date(name):
    if "0263" in name or "202603" in name: return "2026年03月"
    if "0264" in name or "202604" in name: return "2026年04月"
    if "0265" in name or "202605" in name: return "2026年05月"
    return ""

def infer_type(name):
    if "妯￠敓" in name or "模板" in name or "ģ" in name:
        return "税前工资模板"
    if "鏀圭尨" in name or "修改前" in name or "改猴" in name or "޸ǰ" in name:
        return "税前工资表-手工修改前数据"
    if "闈╂嫹" in name or "修改后" in name or "革拷" in name or "޸ĺ" in name:
        return "税前工资表-手工修改后数据"
    if "税后" in name:
        return "税后工资表"
    if "询薪" in name or "配置" in name:
        return "工资项配置模板"
    return "税前工资表"

# ========== 策略1: Excel薪资表 ==========
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
    
    suffix = ".xlsx"
    if name.endswith(".xls"): suffix = ".xls"
    
    if sid in ("10910",):
        new = f"{sid}{ftype}{seq}{suffix}"
    elif shop:
        if "202604" in name and "模板" in ftype:
            new = f"{sid}{shop}薪资组_202604_{ftype}{seq}{suffix}"
        elif date:
            new = f"{sid}{shop}薪资组_{date}_{ftype}{seq}{suffix}"
        else:
            new = f"{sid}{shop}薪资组_{ftype}{seq}{suffix}"
    else:
        if date:
            new = f"{sid}薪资组_{date}_{ftype}{seq}{suffix}"
        else:
            new = f"{sid}薪资组_{ftype}{seq}{suffix}"
    
    new = new.replace("组__", "组_").replace("配置_", "配置")
    # Remove duplicate underscores
    new = re.sub(r'_+', '_', new)
    return new

# ========== 策略2: 影视/BT种子 ==========
def rebuild_media(name):
    """Extract English title, strip garbled Chinese"""
    # Common English patterns in torrent/movie names
    patterns = [
        r'([A-Z][a-zA-Z0-9]+(?:\.[A-Z][a-zA-Z0-9]+)+)',  # CamelCase.Words
        r'\b([A-Za-z0-9_-]+\.(?:19|20)\d{2}\.)',           # Title.1992.
        r'(\d{4}p\.)',                                      # 1080p.
        r'(x\d{3})',                                        # x264
        r'(HDS-WEB|CMCT|FRDS|HDSky|CarPT|HDArea)',         # Release groups
        r'(WEB-DL|BluRay|BDRIP|UHD)',                       # Source types
        r'(TrueHD|DDP|AAC|AC3|Atmos)',                      # Audio codecs
    ]
    
    # Try to keep the entire name but remove the most garbled parts
    # Strategy: keep ASCII + common separators, remove CJK blocks
    cleaned = []
    i = 0
    while i < len(name):
        c = name[i]
        code = ord(c)
        if code < 128 or c in '[]()., _-':
            cleaned.append(c)
        elif 0x4E00 <= code <= 0x9FFF:
            # Check if this is a known garbled pattern
            if name[i:i+3] in ('閿熸枻', '鎷烽敓', '鏂ゆ嫹'):
                i += 2  # skip the garbled block
            # else keep it (might be real Chinese in some edge cases)
        i += 1
    
    result = ''.join(cleaned).strip()
    # Clean up artifacts
    result = re.sub(r'\.{3,}', '.', result)
    result = re.sub(r'_{2,}', '_', result)
    result = re.sub(r' +', ' ', result)
    result = re.sub(r'\[ +', '[', result)
    result = re.sub(r' +\]', ']', result)
    
    if len(result) < 10:  # too much was stripped
        return None
    return result

# ========== 策略3: 白名单（安装包/软件/文档）==========
def rebuild_whitelist(name):
    """Strip garbled Chinese from known software/document names"""
    # Extract extension
    ext = os.path.splitext(name)[1]
    
    # Known patterns to preserve
    known = [
        r'(AIDA64|putty|rclone|immich|syncthing|tailscale|ZeroTier|Docker|VSCode)',
        r'(Gemini\s*CLI)',
        r'(Synology|ubuntu|istoreos|openwrt)',
        r'(Bandizip|DingTalk|WeChat|BaiduNetdisk)',
        r'(Bulk\s*Rename|Advanced\s*Renamer)',
        r'(Strategy|Wealth|Audit)',
    ]
    
    # Try to extract an English base name
    cleaned = []
    for ch in name:
        if ord(ch) < 128 or ch in '._- ()[]':
            cleaned.append(ch)
    
    result = ''.join(cleaned).strip()
    result = re.sub(r' +', ' ', result)
    result = re.sub(r'\.{2,}', '.', result)
    
    if len(result) > 5:
        return result + ext if not result.endswith(ext) else result
    return None

# ========== 主扫描 ==========
records = []
already_ok = set()

# Skip patterns - files that are already correctly named
skip_patterns = [
    r'^\d{5}(闸北|杨浦|康桥|泗泾|南翔|飞牛淮阴|薪资组|工资项)',
]

for fname in os.listdir(DOWNLOADS):
    fpath = os.path.join(DOWNLOADS, fname)
    ext = os.path.splitext(fname)[1].lower()
    
    # Skip already-fixed salary files
    should_skip = False
    for pat in skip_patterns:
        if re.match(pat, fname):
            should_skip = True
            break
    if should_skip:
        continue
    
    new_name = None
    strategy = ""
    
    # Strategy 1: Excel files with store ID prefix
    if re.match(r'^\d{5}', fname) and ext in ('.xlsx', '.xls'):
        new_name = rebuild_salary(fname)
        strategy = "S1-Salary"
    
    # Strategy 2: Torrent/media files
    elif ext in ('.torrent', '.mp4', '.mkv', '.avi'):
        new_name = rebuild_media(fname)
        strategy = "S2-Media"
    
    # Strategy 3: Known installers/docs
    elif ext in ('.exe', '.msi', '.zip', '.rar', '.7z', '.pdf', '.docx', '.doc', '.md', '.html', '.apk', '.spk', '.run', '.iso'):
        new_name = rebuild_whitelist(fname)
        strategy = "S3-Clean"
    
    if new_name and new_name != fname:
        # Check for collisions
        if os.path.exists(os.path.join(DOWNLOADS, new_name)):
            records.append((fname, new_name, strategy, "COLLISION"))
        else:
            records.append((fname, new_name, strategy, "OK"))
    elif not new_name and any(ord(c) > 127 for c in fname):
        records.append((fname, "", "SKIP", "MANUAL_NEEDED"))

# Build DataFrame
df = pd.DataFrame(records, columns=["OldName", "NewName", "Strategy", "Status"])

# Save preview CSV
output = os.path.expanduser(r"~\Desktop\rename_preview.csv")
df.to_csv(output, index=False, encoding="utf-8-sig")

print(f"Preview saved: {output}")
print(f"Total candidates: {len(df)}")
print(f"  S1-Salary:  {len(df[df['Strategy']=='S1-Salary'])}")
print(f"  S2-Media:   {len(df[df['Strategy']=='S2-Media'])}")
print(f"  S3-Clean:   {len(df[df['Strategy']=='S3-Clean'])}")
print(f"  MANUAL:     {len(df[df['Status']=='MANUAL_NEEDED'])}")
print(f"  COLLISION:  {len(df[df['Status']=='COLLISION'])}")
