# Phase 1: System encoding check/fix for Chinese Windows
import subprocess, sys

def check_acp():
    """Return current ACP code page"""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Nls\CodePage")
        acp, _ = winreg.QueryValueEx(key, "ACP")
        winreg.CloseKey(key)
        return acp
    except:
        return None

def fix_acp():
    """Set ACP to 936 (GBK) - requires admin"""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Nls\CodePage", 0,
            winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "ACP", 0, winreg.REG_SZ, "936")
        winreg.SetValueEx(key, "OEMCP", 0, winreg.REG_SZ, "936")
        winreg.SetValueEx(key, "MACCP", 0, winreg.REG_SZ, "10008")
        winreg.CloseKey(key)
        return True, "ACP set to 936. Reboot required."
    except PermissionError:
        return False, "Admin privileges required. Run as Administrator."
    except Exception as e:
        return False, str(e)

def get_status():
    """Return diagnostic info"""
    acp = check_acp()
    if acp is None:
        return {"acp": "unknown", "status": "error", "msg": "Cannot read registry"}
    
    if acp == "936":
        return {"acp": acp, "status": "ok", "msg": "GBK (936) - correct for Chinese software"}
    elif acp == "65001":
        return {"acp": acp, "status": "warning", "msg": "UTF-8 (65001) - will cause garbled text in Chinese apps"}
    else:
        return {"acp": acp, "status": "unknown", "msg": f"Unusual ACP: {acp}"}
