# Sisyphus - 乱码文件名智能修复系统

## 简介

Sisyphus 是一套专门针对 **Windows 中文编码错乱导致文件名乱码** 的智能修复工具。

**核心创新**：放弃传统的字节级编码逆向转换（UTF-8↔GBK），转而采用**文件内容元数据提取 + 特征锚点语义重建**的策略，实现了在原始字节信息已物理丢失的情况下依然能恢复文件名的"降维打击"。

## 适用场景

- Windows 启用"Beta: 使用 Unicode UTF-8"后，国产软件（GBK编码）产生的文件名乱码
- 压缩包解压后中文文件名变成"锟斤拷""閿熸枻鎷"等乱码
- 浏览器下载的中文文件名显示异常
- 多轮错误的编码转换叠加导致文件名不可逆损坏

## 五阶段恢复策略

| 阶段 | 策略 | 方法 |
|------|------|------|
| Phase 1 | 系统编码检查 | 检测并修复 ACP 代码页（936 GBK） |
| Phase 2 | 内容智能识别 | 读取文件内部数据重建文件名（如 Excel 单元格、数据库记录） |
| Phase 3 | 内嵌元数据提取 | 提取 PDF/Torrent/Office 文档/媒体文件的内置标题 |
| Phase 4 | 多层自动裁决 | 压缩包内视 + 文本首行提取 + 按日期归档 + 哈希查重 |
| Phase 5 | 乱码模式清洗 | 剥离乱码 Unicode 块，保留可识别的英文/数字片段 |

## 快速开始

```bash
# Prerequisites: Python 3.8+, tkinter (included with Python on Windows)
pip install -r requirements.txt
python gui.py
```

GUI auto-detects system language (zh-CN / en-US).

## 项目结构

```
├── gui.py                  # 主界面 (纯 tkinter，零额外 GUI 依赖)
├── core/                   # 核心引擎
│   ├── i18n.py             # 中英文语言包 (zh/en)
│   ├── system_check.py     # Phase 1: 系统编码检测
│   ├── salary_recovery.py  # Phase 2: 内容智能识别
│   ├── metadata_recovery.py # Phase 3: 内嵌元数据提取
│   ├── archive_recovery.py # Phase 4: 压缩包内容发现
│   ├── text_recovery.py    # Phase 4: 文本首行命名
│   ├── cluster_recovery.py # Phase 4: 按日期归档 + 哈希消歧
│   └── hardcode_recovery.py # Phase 5: 乱码模式清洗
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
