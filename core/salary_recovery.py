# Phase 2: Salary Excel recovery via openpyxl content extraction
import os, re, pandas as pd
import openpyxl

# Store ID -> Name mapping (discovered from actual file content)
SHOP_DICT = {
    "10001": "闸北店", "10002": "杨浦店", "10027": "康桥店",
    "10066": "泗泾店", "10150": "南翔店", "10910": "",
    "40909": "", "90907": "飞牛淮阴"
}

def infer_date(name):
    if "0263" in name or "202603" in name: return "2026年03月"
    if "0264" in name or "202604" in name: return "2026年04月"
    if "0265" in name or "202605" in name: return "2026年05月"
    return ""

def infer_type(name):
    if "妯" in name or "模" in name or "模板" in name: return "税前工资模板"
    if "修改前" in name or "改猴" in name: return "税前工资表-手工修改前数据"
    if "修改后" in name or "革拷" in name: return "税前工资表-手工修改后数据"
    if "税后" in name: return "税后工资表"
    if "配置" in name or "导入" in name: return "工资项配置模板"
    return "税前工资表"

def rebuild_salary_name(fname):
    """Rebuild salary filename from pattern extraction"""
    m = re.search(r'^(\d{5})', fname)
    if not m: return None
    sid = m.group(1)
    shop = SHOP_DICT.get(sid, "")
    date = infer_date(fname)
    ftype = infer_type(fname)
    seq = ""
    sm = re.search(r'\((\d+)\)', fname)
    if sm: seq = f" ({sm.group(1)})"
    ext = os.path.splitext(fname)[1].lower() or ".xlsx"
    
    if sid in ("10910",):
        new = f"{sid}{ftype}{seq}{ext}"
    elif shop:
        if "202604" in fname and "模板" in ftype:
            new = f"{sid}{shop}薪资组_202604_{ftype}{seq}{ext}"
        elif date:
            new = f"{sid}{shop}薪资组_{date}_{ftype}{seq}{ext}"
        else:
            new = f"{sid}{shop}薪资组_{ftype}{seq}{ext}"
    else:
        new = f"{sid}薪资组_{date}_{ftype}{seq}{ext}" if date else f"{sid}薪资组_{ftype}{seq}{ext}"
    
    return re.sub(r'_+', '_', new).replace("组__", "组_")

def discover_shops_from_content(directory):
    """Read Excel files to extract store names from content"""
    shops = {}
    for fname in os.listdir(directory):
        if not re.match(r'^\d{5}', fname): continue
        ext = os.path.splitext(fname)[1].lower()
        if ext not in ('.xlsx', '.xls'): continue
        fpath = os.path.join(directory, fname)
        try:
            wb = openpyxl.load_workbook(fpath, data_only=True)
            ws = wb.active
            cell = ws.cell(1, 1).value
            if cell:
                m = re.search(r'^(\d{5})(.+?)(?:薪资|20\d{2}年)', str(cell))
                if m:
                    shops[m.group(1)] = m.group(2).strip()
            wb.close()
        except:
            pass
    return shops

def scan_salary(directory):
    """Scan directory for salary files and generate preview"""
    records = []
    skip_prefixes = [r'^\d{5}(闸北|杨浦|康桥|泗泾|南翔|飞牛淮阴|薪资组|工资项)']
    
    for fname in sorted(os.listdir(directory)):
        fpath = os.path.join(directory, fname)
        if os.path.isdir(fpath): continue
        if not re.match(r'^\d{5}', fname): continue
        if any(re.match(p, fname) for p in skip_prefixes): continue
        
        new_name = rebuild_salary_name(fname)
        if new_name and new_name != fname:
            records.append((fname, new_name))
    
    return records
