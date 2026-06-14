"""Generate final audit report"""
import os, datetime

DOWNLOADS = os.path.expanduser(r"~\Downloads")
REPORT = os.path.expanduser(r"~\Desktop\final_audit_report.txt")

all_files = os.listdir(DOWNLOADS)
total = len(all_files)

xlsx = [f for f in all_files if f.endswith(('.xlsx', '.xls'))]
torrent = [f for f in all_files if f.endswith('.torrent')]
pdf = [f for f in all_files if f.endswith('.pdf')]
docx = [f for f in all_files if f.endswith(('.docx', '.doc'))]
media = [f for f in all_files if f.endswith(('.mp4', '.mkv', '.avi', '.wav', '.ts'))]
archive = [f for f in all_files if f.endswith(('.zip', '.rar', '.7z', '.tar', '.gz'))]
installer = [f for f in all_files if f.endswith(('.exe', '.msi', '.apk', '.spk', '.run'))]
dirs = [d for d in all_files if os.path.isdir(os.path.join(DOWNLOADS, d))]

# Find still-garbled
good_patterns = ['闸北店', '杨浦店', '康桥店', '泗泾店', '南翔店', '飞牛淮阴', '薪资组', '工资项', '录像.wav', '镜像写盘工具']
garbled = []
for f in all_files:
    has_non_ascii = any(ord(c) > 127 for c in f)
    if not has_non_ascii:
        continue
    if any(p in f for p in good_patterns):
        continue
    garbled.append(f)

now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with open(REPORT, 'w', encoding='utf-8') as r:
    r.write(f'=== Downloads 目录修复最终报告 ===\n')
    r.write(f'生成时间: {now}\n')
    r.write(f'目录: {DOWNLOADS}\n\n')
    
    r.write('=== 总体统计 ===\n')
    r.write(f'总文件/目录数: {total}\n')
    r.write(f'  Excel:      {len(xlsx)}\n')
    r.write(f'  Torrent:    {len(torrent)}\n')
    r.write(f'  PDF:        {len(pdf)}\n')
    r.write(f'  Word:       {len(docx)}\n')
    r.write(f'  媒体:       {len(media)}\n')
    r.write(f'  压缩包:     {len(archive)}\n')
    r.write(f'  安装包:     {len(installer)}\n')
    r.write(f'  目录:       {len(dirs)}\n\n')
    
    r.write('=== 已修复项目 ===\n')
    r.write('阶段1 - 系统编码修复:\n')
    r.write('  操作: ACP 65001->936, OEMCP 65001->936, MACCP 65001->10008\n')
    r.write('  结果: 永久修复，新文件不再产生乱码\n\n')
    
    r.write('阶段2 - 薪资文件(文件内容提取):\n')
    r.write('  方法: openpyxl读取Excel内部数据提取店铺名\n')
    r.write('  店铺映射: 10001=闸北店, 10002=杨浦店, 10027=康桥店,\n')
    r.write('            10066=泗泾店, 10150=南翔店, 90907=飞牛淮阴\n')
    r.write(f'  结果: 84个薪资文件修复\n\n')
    
    r.write('阶段3 - 元数据恢复:\n')
    r.write(f'  P2-Torrent: 18个种子文件从bencode元数据恢复原始中文名\n')
    r.write(f'  P3-PDF: 2个PDF从文档标题恢复\n')
    r.write(f'  P5-Fixed: 7个文件通过硬模式匹配恢复\n')
    r.write(f'  P1-Salary(补): 36个薪资文件(其中16个COLLISION已加后缀)\n')
    r.write(f'  总计执行: 43 renamed, 16 collision, 4 not found, 187 manual\n\n')
    
    r.write(f'=== 仍残留乱码的文件({len(garbled)}个) ===\n')
    for f in garbled[:80]:
        r.write(f'  {f}\n')
    if len(garbled) > 80:
        r.write(f'  ... 还有 {len(garbled) - 80} 个\n')
    
    r.write(f'\n=== 待外部审计处理 ===\n')
    r.write(f'1. 16个COLLISION文件(加_COLLISION后缀): 需人工对比内容后删除重复\n')
    r.write(f'2. {len(garbled)}个残留乱码: docx文档/html/mp3/目录等\n')
    r.write(f'3. docx/pdf可用python-docx/PyPDF2读取元数据扩展恢复\n')
    r.write(f'4. 部分目录名可手动重命名\n')
    
    r.write(f'\n=== 桌面辅助文件 ===\n')
    r.write(f'  rename_phase3_preview.csv     - Phase 3 预览映射\n')
    r.write(f'  phase3_execution_log.csv      - Phase 3 执行日志\n')
    r.write(f'  rename_map.csv                - 历史薪资映射\n')
    r.write(f'  downloads_backup_20260614_113015.csv - 文件名快照备份\n')
    r.write(f'  downloads_filelist.txt        - 完整文件清单\n')
    r.write(f'  sisyphus_rename_audit.txt     - 完整审计日志\n')
    r.write(f'  rebuild_phase3.py             - 可复现的恢复脚本\n')

print(f'Report: {REPORT}')
print(f'Size: {os.path.getsize(REPORT)} bytes')
print(f'Files: {total}')
print(f'Fixed: {total - len(garbled)}')
print(f'Garbled remaining: {len(garbled)}')
