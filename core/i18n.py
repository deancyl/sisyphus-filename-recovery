"""Internationalization support for Sisyphus GUI (v1.1)"""
import locale

STRINGS = {
    "en": {
        "title": "Sisyphus - Filename Recovery v1.1",
        "target_label": "Target:",
        "browse": "Browse",
        "strategies_label": " Pipeline ",
        "btn_scan": "1. Scan & Preview",
        "btn_execute": "2. Execute All",
        "btn_export": "Export Preview CSV",
        "btn_clear": "Clear Preview",
        "btn_about": "About",
        "col_num": "#",
        "col_old": "Old Name",
        "col_new": "New Name",
        "col_strategy": "Strategy",
        "status_ready": "Ready. Click Scan & Preview to begin.",
        "status_loading": "Loading recovery pipeline...",
        "status_scan_done": "Scan complete. {} candidates found.",
        "status_backup_saved": "Backup saved: {}",
        "status_exported": "Exported to: {}",
        "status_cleared": "Preview cleared.",
        "status_exec_done": "Done. Renamed:{} Deleted:{} Clustered:{}",
        "err_invalid_dir": "Not a valid directory:",
        "err_no_data": "Run scan first.",
        "confirm_exec": "Rename {} files?\nBackup already created.\n\nContinue?",
        "complete_title": "Complete",
        "complete_msg": "Execution complete!\n\n  Renamed:    {}\n  Deleted:    {}\n  Clustered:  {}\n  Failed:     {}\n\nLog: {}",
        "acp_ok": "correct for Chinese software",
        "acp_warn": "may cause garbled text",
        "lang_label": "Lang",
        "config_label": "Config:",
        "pipeline_info": "Pipeline: Hardcode Mappings → Metadata Extraction → Regex Rules → Sanitizer → Fallback Cluster",
        "lang_restart": "Restart to apply language change.",
        "about_title": "Sisyphus v1.1.0",
        "about_text": "Universal Garbled Filename Recovery\n\nPipeline:\n  Hardcode → Metadata → Regex → Sanitizer → Fallback\n\ngithub.com/deancyl/sisyphus-filename-recovery",
        "error_title": "Error",
        "scan_error_title": "Scan Error",
        "lang_title": "Language",
        "no_data_title": "No Data",
    },
    "zh": {
        "title": "西西弗斯 - 文件名修复 v1.1",
        "target_label": "目标:",
        "browse": "浏览",
        "strategies_label": " 恢复流水线 ",
        "btn_scan": "1. 扫描预览",
        "btn_execute": "2. 执行全部",
        "btn_export": "导出预览 CSV",
        "btn_clear": "清除预览",
        "btn_about": "关于",
        "col_num": "#",
        "col_old": "旧文件名",
        "col_new": "新文件名",
        "col_strategy": "策略",
        "status_ready": "就绪。点击扫描预览开始。",
        "status_loading": "正在加载恢复流水线...",
        "status_scan_done": "扫描完成。{} 个候选。",
        "status_backup_saved": "备份已保存: {}",
        "status_exported": "已导出: {}",
        "status_cleared": "预览已清除。",
        "status_exec_done": "完成。重命名:{} 删除:{} 归档:{}",
        "err_invalid_dir": "无效目录:",
        "err_no_data": "请先运行扫描。",
        "confirm_exec": "将重命名 {} 个文件？\n备份已创建。\n\n确认执行？",
        "complete_title": "完成",
        "complete_msg": "执行完成！\n\n  重命名:    {}\n  删除重复:  {}\n  归档:      {}\n  失败:      {}\n\n日志: {}",
        "acp_ok": "适合中文软件",
        "acp_warn": "可能导致乱码",
        "lang_label": "语言",
        "config_label": "配置:",
        "pipeline_info": "流水线: 硬编码映射 → 元数据提取 → 正则规则 → 通用清洗 → 兜底归档",
        "lang_restart": "重启程序以应用语言变更。",
        "about_title": "西西弗斯 v1.1.0",
        "about_text": "通用乱码文件名恢复工具\n\n恢复流水线:\n  硬编码 → 元数据 → 正则 → 清洗 → 归档\n\ngithub.com/deancyl/sisyphus-filename-recovery",
        "error_title": "错误",
        "scan_error_title": "扫描错误",
        "lang_title": "语言",
        "no_data_title": "无数据",
    }
}

class I18n:
    def __init__(self):
        self.lang = self._detect()
    
    def _detect(self):
        try:
            loc = locale.getdefaultlocale()
            if loc and loc[0] and loc[0].startswith('zh'): return 'zh'
        except: pass
        return 'en'
    
    def set_lang(self, lang):
        if lang in STRINGS: self.lang = lang
    
    def get(self, key, *args):
        s = STRINGS.get(self.lang, STRINGS['en']).get(key, key)
        if args: return s.format(*args)
        return s
    
    def get_all_langs(self):
        return list(STRINGS.keys())

i18n = I18n()
