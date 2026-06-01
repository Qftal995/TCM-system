"""Page 8: 数据备份恢复"""
import os
import json
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFileDialog, QFrame,
)
from PyQt6.QtCore import Qt

from database import get_conn, DB_PATH
from utils.backup import export_json, import_json


class BackupPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        top = QHBoxLayout()
        top.setContentsMargins(18, 14, 18, 10)
        title = QLabel("数据备份恢复")
        title.setStyleSheet("font-family: KaiTi, SimSun; font-size: 16px; color: #3E2723; letter-spacing: 2px;")
        top.addWidget(title)
        top.addStretch()
        layout.addLayout(top)

        content = QVBoxLayout()
        content.setContentsMargins(18, 0, 18, 18)
        content.setSpacing(10)
        card_style = "QFrame { background: #FFFEF9; border: 1px solid #D7CCC8; border-radius: 5px; }"

        # ── Backup / Restore card ──
        bcard = QFrame()
        bcard.setStyleSheet(card_style)
        bl = QVBoxLayout(bcard)
        bl.setContentsMargins(20, 16, 20, 16)
        bl.setSpacing(12)

        bl.addWidget(QLabel("<b>数据备份与恢复</b>"))

        desc = QLabel("将全部数据导出为 JSON 文件保存，或从备份文件恢复数据。恢复操作将覆盖当前数据库全部内容。")
        desc.setStyleSheet("color: #8D6E63; font-size: 11px; line-height: 1.5;")
        desc.setWordWrap(True)
        bl.addWidget(desc)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        backup_btn = QPushButton(" 导出备份  ")
        backup_btn.setStyleSheet(
            "QPushButton { padding: 10px 24px; background: #7A4C32; color: #FFFEF9; "
            "border: none; border-radius: 4px; font-size: 13px; letter-spacing: 1px; }"
            "QPushButton:hover { background: #5C3322; }"
        )
        backup_btn.clicked.connect(self._do_backup)
        btn_row.addWidget(backup_btn)
        restore_btn = QPushButton(" 恢复数据  ")
        restore_btn.setStyleSheet(
            "QPushButton { padding: 10px 24px; border: 1px solid #BCAAA4; border-radius: 4px; "
            "background: transparent; color: #5D4037; font-size: 13px; letter-spacing: 1px; }"
            "QPushButton:hover { background: #F5F0E8; }"
        )
        restore_btn.clicked.connect(self._do_restore)
        btn_row.addWidget(restore_btn)
        btn_row.addStretch()
        bl.addLayout(btn_row)

        content.addWidget(bcard)

        # ── System info card ── (stretch so table fills remaining space)
        icard = QFrame()
        icard.setStyleSheet(card_style)
        il = QVBoxLayout(icard)
        il.setContentsMargins(16, 10, 16, 10)
        il.setSpacing(4)

        hdr = QHBoxLayout()
        hdr.addWidget(QLabel("<b>系统信息</b>"))
        hdr.addStretch()
        refresh_btn = QPushButton("刷新")
        refresh_btn.setStyleSheet(
            "QPushButton { padding: 4px 14px; border: 1px solid #BCAAA4; border-radius: 3px; "
            "background: transparent; color: #5D4037; font-size: 11px; }"
            "QPushButton:hover { background: #F5F0E8; }"
        )
        refresh_btn.clicked.connect(self._refresh_info)
        hdr.addWidget(refresh_btn)
        il.addLayout(hdr)

        self.path_lbl = QLabel()
        self.path_lbl.setStyleSheet("color: #5D4037; font-size: 12px; padding: 4px 0;")
        self.path_lbl.setWordWrap(True)
        il.addWidget(self.path_lbl)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["数据表","记录数"])
        self.table.horizontalHeader().setStyleSheet(
            "QHeaderView::section { background: #5C3322; color: #E8DFD2; padding: 6px; font-size: 11px; border: none; }"
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setStyleSheet(
            "QTableWidget { background: #FFFEF9; border: 1px solid #D7CCC8; font-size: 12px; }"
            "QTableWidget::item { padding: 5px 10px; color: #3E2723; }"
        )
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 80)
        il.addWidget(self.table)

        content.addWidget(icard, 1)
        layout.addLayout(content, 1)
        self._refresh_info()

    def _do_backup(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "导出备份",
            f"tcm_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            "JSON (*.json)"
        )
        if not path:
            return
        try:
            data = export_json()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "备份成功", f"数据已导出到：\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "备份失败", str(e))

    def _do_restore(self):
        ret = QMessageBox.warning(
            self, "确认恢复",
            "恢复将覆盖当前所有数据（以 JSON 内容为准合并写入），确定继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if ret != QMessageBox.StandardButton.Yes:
            return
        path, _ = QFileDialog.getOpenFileName(self, "选择备份文件", "", "JSON (*.json)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            import_json(data)
            QMessageBox.information(self, "恢复成功", "数据已从备份文件恢复")
            self._refresh_info()
        except Exception as e:
            QMessageBox.warning(self, "恢复失败", str(e))

    def _refresh_info(self):
        conn = get_conn()
        cur = conn.cursor()

        if os.path.exists(DB_PATH):
            size_kb = os.path.getsize(DB_PATH) / 1024
            self.path_lbl.setText(f"数据库：{DB_PATH}\n大小：{size_kb:.1f} KB  |  WAL 模式")
        else:
            self.path_lbl.setText(f"数据库：{DB_PATH}\n状态：文件不存在")

        tables = [
            ("herbs", "药材"),
            ("patients", "患者"),
            ("formulas", "方剂"),
            ("formula_items", "方剂明细"),
            ("prescriptions", "处方"),
            ("prescription_items", "处方明细"),
            ("stock_in_records", "入库记录"),
        ]
        self.table.setRowCount(len(tables))
        total = 0
        for i, (t, label) in enumerate(tables):
            cur.execute(f"SELECT COUNT(*) as c FROM {t}")
            c = cur.fetchone()["c"]
            total += c
            self.table.setItem(i, 0, QTableWidgetItem(label))
            self.table.setItem(i, 1, QTableWidgetItem(str(c)))
        conn.close()
