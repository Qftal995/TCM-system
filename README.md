# 中药诊疗管理系统

PyQt6 + SQLite3 桌面应用，面向中医诊所的日常诊疗管理工具。

## 功能

- **患者登记与开方** — 患者信息自动补全，选择复诊患者自动加载上次处方，选药计价，自动扣库
- **患者信息管理** — 增删改查，月序号自动分配，Excel 导入导出
- **药材入库** — 搜索选药商，填写入库单，提交验收，自动更新库存
- **中药药材管理** — 药材增删改查，效期预警，库存总值统计，Excel 导入导出
- **方子管理** — 常用方剂维护，后台值（诊金）设置
- **库存预警** — 低库存、近效期自动高亮提醒

## 运行

```powershell
pip install PyQt6 openpyxl
python main.py
```

## 构建单文件

```powershell
python -m PyInstaller --onefile --windowed --icon=logo.ico --add-data "data/tcm.db;data" --name "中药管理系统" main.py
```

产物在 `dist/`，发给他人直接双击运行。

## 项目结构

```
├── main.py              # 主窗口、侧边栏导航
├── database.py          # 数据库初始化、迁移、连接
├── pages/
│   ├── presc_page.py    # 患者登记与开方
│   ├── patient_page.py  # 患者信息管理
│   ├── stockin_page.py  # 药材入库
│   ├── herb_page.py     # 中药药材管理
│   ├── formula_page.py  # 方子管理
│   ├── alert_page.py    # 库存预警
│   └── backup_page.py   # 数据备份
├── widgets/
│   ├── searchbox.py     # 搜索联想输入框
│   ├── paginator.py     # 分页控件
│   ├── presc_preview.py # 处方预览
│   └── sidebar.py       # 侧边栏
├── utils/
│   ├── excel_io.py      # Excel 导入导出
│   └── backup.py        # 备份工具
└── data/
    └── tcm.db           # SQLite 数据库（不入 git）
```

## 技术栈

- Python 3.14
- PyQt6
- SQLite3
- openpyxl
