# Sisyphus - 乱码文件名智能修复系统

## 简介

Sisyphus 是一套专门针对 **Windows 中文编码错乱导致文件名乱码** 的智能修复工具。

**核心创新**：放弃传统的字节级编码逆向转换（UTF-8↔GBK），转而采用**文件内容元数据提取 + 特征锚点语义重建**的策略，实现了在原始字节信息已物理丢失的情况下依然能恢复文件名的"降维打击"。

## 适用场景

- Windows 启用"Beta: 使用 Unicode UTF-8"后，国产软件（GBK编码）产生的文件名乱码
- 压缩包解压后中文文件名变成"锟斤拷""閿熸枻鎷"等乱码
- 浏览器下载的中文文件名显示异常
- 多轮错误的编码转换叠加导致文件名不可逆损坏

## 恢复流水线

```
Hardcode Mappings → Metadata Extraction → Regex Rules → Sanitizer → Fallback Cluster
```

| 优先级 | 策略 | 方法 |
|--------|------|------|
| P0 | 硬编码映射 | 用户自定义 YAML 精确匹配规则 |
| P1 | 元数据提取 | 读取文件内部标题/标签 (Excel/PDF/Docx/Torrent/媒体) |
| P2 | 正则规则 | 用户自定义正则替换模式 |
| P3 | 通用清洗 | 剥离已知乱码字符块，保留可识别片段 |
| P4 | 兜底归档 | 按创建日期 + MD5 指纹归档到 Recovered_* 目录 |

## 自定义配置

复制 `config/config_template.yaml` 为 `config.yaml`，按需编辑：
- `hardcode_mappings`: 精确文件名 → 新文件名
- `regex_rules`: 正则模式 → 替换文本
- `skip_patterns`: 跳过保护的文件名模式

## 快速开始

```bash
pip install -r requirements.txt
python gui.py
```

GUI 自动检测系统语言（中文/English）。无需配置即可使用——内置乱码指纹库覆盖绝大多数场景。

选择一个预设或直接扫描：

| 预设 | 适用场景 |
|------|---------|
| 标准 GBK/UTF-8 修复 | 系统编码错乱导致的经典乱码 |
| 媒体与种子恢复 | PT/BT 下载，读取元数据优先 |
| 办公批量文件恢复 | Excel/PDF/Word 深度内容提取 |

## 项目结构

```
├── gui.py                  # 主界面 (纯 tkinter，零额外 GUI 依赖)
├── core/                   # 核心引擎
│   ├── i18n.py             # 中英文语言包 (zh/en)
│   ├── system_check.py     # Phase 1: 系统编码检测
│   ├── metadata.py         # 通用元数据提取 (Excel/PDF/Docx/Torrent/媒体)
│   ├── sanitizer.py        # 通用乱码清洗 + 按日期兜底归档
│   └── pipeline.py         # 策略编排器 (硬编码→元数据→正则→清洗→归档)
├── config/                 # 用户自定义规则
│   └── config_template.yaml # 配置模板 (复制为 config.yaml 使用)
├── logs/                   # 历史执行记录
├── requirements.txt
├── README.md
└── CHANGELOG.md
```

## 安全机制

- **强制预览**：所有操作默认仅生成 CSV 预览，需手动确认后执行
- **自动备份**：执行前自动生成文件名快照
- **哈希查重**：COLLISION 冲突自动 MD5 判重，避免误删
- **假阳性保护**：正确中文文件自动识别并跳过

## 许可证

MIT License
