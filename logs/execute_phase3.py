"""
=== Phase 3: 执行重命名 ===
读取 rename_phase3_preview.csv，按 Status 执行：
  OK -> 重命名
  DELETE -> 删除重复文件
  COLLISION -> 重命名为 _COLLISION 后缀
  MANUAL -> 跳过
"""
import os, shutil, pandas as pd

DOWNLOADS = os.path.expanduser(r"~\Downloads")
CSV = os.path.expanduser(r"~\Desktop\rename_phase3_preview.csv")
LOG = os.path.expanduser(r"~\Desktop\phase3_execution_log.csv")

df = pd.read_csv(CSV)

executed = []
renamed = 0; deleted = 0; collision = 0; failed = 0

for _, row in df.iterrows():
    old_name = row['OldName']
    new_name = row['NewName']
    status = row['Status']
    strategy = row['Strategy']
    
    old_path = os.path.join(DOWNLOADS, old_name)
    
    if not os.path.exists(old_path):
        executed.append({'OldName': old_name, 'NewName': new_name, 'Action': 'SKIP_NOT_FOUND', 'Status': status})
        failed += 1
        continue
    
    if status == 'OK':
        new_path = os.path.join(DOWNLOADS, new_name)
        try:
            os.rename(old_path, new_path)
            executed.append({'OldName': old_name, 'NewName': new_name, 'Action': 'RENAMED', 'Status': status})
            renamed += 1
        except Exception as e:
            executed.append({'OldName': old_name, 'NewName': new_name, 'Action': f'FAIL: {e}', 'Status': status})
            failed += 1
    
    elif status == 'DELETE':
        try:
            # Confirm it really says DELETE in NewName
            if 'DELETE' in new_name:
                os.remove(old_path)
                executed.append({'OldName': old_name, 'NewName': new_name, 'Action': 'DELETED', 'Status': status})
                deleted += 1
            else:
                executed.append({'OldName': old_name, 'NewName': new_name, 'Action': 'SKIP_BAD_DELETE', 'Status': status})
                failed += 1
        except Exception as e:
            executed.append({'OldName': old_name, 'NewName': new_name, 'Action': f'FAIL_DELETE: {e}', 'Status': status})
            failed += 1
    
    elif status == 'COLLISION':
        new_path = os.path.join(DOWNLOADS, new_name)
        if os.path.exists(new_path):
            executed.append({'OldName': old_name, 'NewName': new_name, 'Action': 'SKIP_EXISTS', 'Status': status})
            failed += 1
        else:
            try:
                os.rename(old_path, new_path)
                executed.append({'OldName': old_name, 'NewName': new_name, 'Action': 'RENAMED_COLLISION', 'Status': status})
                collision += 1
            except Exception as e:
                executed.append({'OldName': old_name, 'NewName': new_name, 'Action': f'FAIL: {e}', 'Status': status})
                failed += 1
    
    else:  # MANUAL or unknown
        pass  # skip

# Save execution log
log_df = pd.DataFrame(executed, columns=['OldName', 'NewName', 'Action', 'Status'])
log_df.to_csv(LOG, index=False, encoding='utf-8-sig')

print(f"=== Execution Complete ===")
print(f"  Renamed:    {renamed}")
print(f"  Deleted:    {deleted}")
print(f"  Collision:  {collision}")
print(f"  Failed:     {failed}")
print(f"  Skipped:    {len(df) - renamed - deleted - collision - failed}")
print(f"\nLog: {LOG}")
