"""Execute Phase 4 renames based on preview CSV"""
import os, shutil, pandas as pd

DOWNLOADS = os.path.expanduser(r"~\Downloads")
CSV = os.path.expanduser(r"~\Desktop\rename_phase4_preview.csv")
LOG = os.path.expanduser(r"~\Desktop\phase4_execution_log.csv")
TRASH = os.path.join(DOWNLOADS, "_Trash_Duplicates")

if not os.path.exists(TRASH):
    os.makedirs(TRASH)

df = pd.read_csv(CSV)

renamed = 0; deleted = 0; collision = 0; clustered = 0; failed = 0
log = []

for _, row in df.iterrows():
    old_name = row['OldName']
    new_name = row['NewName']
    status = row['Status']
    strategy = row['Strategy']
    
    old_path = os.path.join(DOWNLOADS, old_name)
    if not os.path.exists(old_path):
        log.append((old_name, new_name, "SKIP_NOT_FOUND", status))
        continue
    
    if status == 'DELETE' or 'DELETE' in str(new_name):
        try:
            trash_path = os.path.join(TRASH, old_name)
            if os.path.exists(trash_path):
                base, ext = os.path.splitext(old_name)
                trash_path = os.path.join(TRASH, f"{base}_dup{ext}")
            shutil.move(old_path, trash_path)
            log.append((old_name, new_name, "DELETED_TO_TRASH", status))
            deleted += 1
        except Exception as e:
            log.append((old_name, new_name, f"FAIL: {e}", status))
            failed += 1
    
    elif 'M4-Cluster' in strategy:
        # Create cluster folder and move file
        parts = new_name.replace('\\', '/').split('/')
        folder = parts[0]
        file_name = parts[1] if len(parts) > 1 else old_name
        folder_path = os.path.join(DOWNLOADS, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        target_path = os.path.join(folder_path, file_name)
        try:
            shutil.move(old_path, target_path)
            log.append((old_name, new_name, "MOVED_TO_CLUSTER", status))
            clustered += 1
        except Exception as e:
            log.append((old_name, new_name, f"FAIL: {e}", status))
            failed += 1
    
    elif status in ('OK', 'COLLISION_FIXED'):
        target_path = os.path.join(DOWNLOADS, new_name)
        if os.path.exists(target_path):
            log.append((old_name, new_name, "SKIP_EXISTS", status))
            failed += 1
        else:
            try:
                if '\\' in new_name or '/' in new_name:
                    # Has subfolder - need to ensure parent exists
                    parent = os.path.dirname(target_path)
                    if not os.path.exists(parent):
                        os.makedirs(parent)
                os.rename(old_path, target_path)
                log.append((old_name, new_name, "RENAMED", status))
                if status == 'COLLISION_FIXED': collision += 1
                else: renamed += 1
            except Exception as e:
                log.append((old_name, new_name, f"FAIL: {e}", status))
                failed += 1

log_df = pd.DataFrame(log, columns=["OldName","NewName","Action","Status"])
log_df.to_csv(LOG, index=False, encoding="utf-8-sig")

print("=== Phase 4 Execution ===")
print(f"  Renamed:       {renamed}")
print(f"  Collision fix: {collision}")
print(f"  Deleted/Dup:   {deleted}")
print(f"  Clustered:     {clustered}")
print(f"  Failed:        {failed}")
print(f"  Total:         {renamed + collision + deleted + clustered}")
print(f"\nLog: {LOG}")
