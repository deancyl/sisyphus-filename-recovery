"""Internationalization support for Sisyphus GUI"""
import locale, os, json

# Language strings
STRINGS = {
    "en": {
        "title": "Sisyphus - File Name Recovery",
        "target_label": "Target:",
        "browse": "Browse",
        "strategies_label": " Recovery Strategies ",
        "strategy_salary": "Excel Salary Recovery",
        "strategy_metadata": "Metadata (Torrent/PDF/Docx)",
        "strategy_archives": "ZIP Interior Inspection",
        "strategy_textfiles": "Text First-Line Extraction",
        "strategy_cluster": "Time-Based Clustering",
        "strategy_hardcode": "Hardcode Mapping + Regex",
        "btn_scan": "1. Scan & Preview",
        "btn_execute": "2. Execute All",
        "btn_export": "Export Preview CSV",
        "btn_clear": "Clear Preview",
        "col_num": "#",
        "col_old": "Old Name (current)",
        "col_new": "New Name (recovered)",
        "col_strategy": "Strategy",
        "status_ready": "Ready. Click 'Scan & Preview' to begin.",
        "status_loading": "Loading recovery engine...",
        "status_scan_salary": "Scanning: Excel salary files...",
        "status_scan_metadata": "Scanning: metadata (Torrent/PDF/Docx/Media)...",
        "status_scan_archives": "Scanning: ZIP/RAR interiors...",
        "status_scan_text": "Scanning: text file first lines...",
        "status_scan_cluster": "Scanning: time-based clustering...",
        "status_scan_hardcode": "Scanning: hardcode + regex...",
        "status_scan_done": "Scan complete. {} candidates found. {}",
        "status_backup_saved": "Backup saved: {}",
        "status_exported": "Exported to: {}",
        "status_cleared": "Preview cleared.",
        "status_exec_done": "Done. Renamed:{} Deleted:{} Clustered:{}",
        "err_invalid_dir": "Not a valid directory:",
        "err_no_data": "Run scan first.",
        "err_deps": "Missing required module: {}\nRun: pip install -r requirements.txt",
        "confirm_exec": "This will rename {} files.\nA backup has already been created.\n\nContinue?",
        "complete_title": "Complete",
        "complete_msg": "Execution complete!\n\n  Renamed:    {}\n  Deleted:    {}\n  Clustered:  {}\n  Failed:     {}\n\nLog: {}",
        "acp_ok": "correct for Chinese software",
        "acp_warn": "will cause garbled text",
        "lang_label": "Language",
    },
    "zh": {
        "title": "西西弗斯 - 文件名乱码修复",
        "target_label": "目标目录:",
        "browse": "浏览",
        "strategies_label": " 恢复策略 ",
        "strategy_salary": "Excel 薪资文件恢复",
        "strategy_metadata": "元数据恢复 (种子/PDF/文档)",
        "strategy_archives": "压缩包内视推断",
        "strategy_textfiles": "文本首行提取",
        "strategy_cluster": "时序聚类归档",
        "strategy_hardcode": "硬编码映射 + 正则清洗",
        "btn_scan": "1. 扫描预览",
        "btn_execute": "2. 执行全部",
        "btn_export": "导出预览 CSV",
        "btn_clear": "清除预览",
        "col_num": "#",
        "col_old": "旧文件名 (当前)",
        "col_new": "新文件名 (恢复)",
        "col_strategy": "策略",
        "status_ready": "就绪。点击「扫描预览」开始。",
        "status_loading": "正在加载恢复引擎...",
        "status_scan_salary": "扫描中: Excel 薪资文件...",
        "status_scan_metadata": "扫描中: 元数据 (种子/PDF/文档/媒体)...",
        "status_scan_archives": "扫描中: 压缩包内部...",
        "status_scan_text": "扫描中: 文本文件首行...",
        "status_scan_cluster": "扫描中: 时序聚类...",
        "status_scan_hardcode": "扫描中: 硬编码 + 正则...",
        "status_scan_done": "扫描完成。{} 个候选文件。{}",
        "status_backup_saved": "备份已保存: {}",
        "status_exported": "已导出到: {}",
        "status_cleared": "预览已清除。",
        "status_exec_done": "完成。重命名:{} 删除:{} 归档:{}",
        "err_invalid_dir": "无效的目录:",
        "err_no_data": "请先运行扫描。",
        "err_deps": "缺少模块: {}\n运行: pip install -r requirements.txt",
        "confirm_exec": "将重命名 {} 个文件。\n已创建备份。\n\n确认执行？",
        "complete_title": "完成",
        "complete_msg": "执行完成！\n\n  重命名:    {}\n  删除重复:  {}\n  时序归档:  {}\n  失败:      {}\n\n日志: {}",
        "acp_ok": "适合中文软件",
        "acp_warn": "可能导致乱码",
        "lang_label": "语言",
    }
}

class I18n:
    """Language manager with auto-detection"""
    
    def __init__(self):
        self.lang = self._detect_lang()
    
    def _detect_lang(self):
        """Auto-detect system language"""
        try:
            loc = locale.getdefaultlocale()
            if loc and loc[0]:
                if loc[0].startswith('zh'):
                    return 'zh'
        except:
            pass
        return 'en'
    
    def set_lang(self, lang):
        if lang in STRINGS:
            self.lang = lang
    
    def get(self, key, *args):
        s = STRINGS.get(self.lang, STRINGS['en']).get(key, key)
        if args:
            return s.format(*args)
        return s
    
    def get_all_langs(self):
        return list(STRINGS.keys())

# Global instance
i18n = I18n()
