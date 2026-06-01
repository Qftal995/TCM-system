"""Page 7: 预警面板 — 库存不足 / 临期 / 已过期"""
from datetime import date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QTabWidget, QFrame, QDialog, QFormLayout, QDoubleSpinBox, QLineEdit,
    QSpinBox, QDialogButtonBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from database import get_conn


class AlertPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        top = QHBoxLayout()
        top.setContentsMargins(18, 14, 18, 10)
        title = QLabel("预警面板")
        title.setStyleSheet("font-family: KaiTi, SimSun; font-size: 16px; color: #3E2723; letter-spacing: 2px;")
        top.addWidget(title)
        sub = QLabel("库存不足 / 临期 / 已过期 药材一览")
        sub.setStyleSheet("font-size: 11px; color: #8D6E63;")
        top.addWidget(sub)
        top.addStretch()
        refresh_btn = QPushButton("刷新")
        refresh_btn.setStyleSheet("QPushButton { padding: 4px 12px; border: 1px solid #BCAAA4; border-radius: 3px; background: transparent; color: #5D4037; font-size: 11px; } QPushButton:hover { background: #F5F0E8; }")
        refresh_btn.clicked.connect(self.load_data)
        top.addWidget(refresh_btn)
        layout.addLayout(top)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #D7CCC8; background: #FFFEF9; }
            QTabBar::tab { padding: 8px 20px; font-size: 12px; color: #5D4037; border: 1px solid #D7CCC8; border-bottom: none; background: #F5F0E8; }
            QTabBar::tab:selected { background: #FFFEF9; color: #3E2723; font-weight: bold; border-bottom: 2px solid #7A4C32; }
        """)

        self.out_of_stock_tab = self._make_tab()
        self.low_stock_tab = self._make_tab()
        self.near_expiry_tab = self._make_tab()
        self.expired_tab = self._make_tab()

        self.tabs.addTab(self.out_of_stock_tab["frame"], "缺货")
        self.tabs.addTab(self.low_stock_tab["frame"], "库存不足")
        self.tabs.addTab(self.near_expiry_tab["frame"], "临期预警")
        self.tabs.addTab(self.expired_tab["frame"], "已过期")

        layout.addWidget(self.tabs, 1)
        self.load_data()

    def _make_tab(self):
        frame = QFrame()
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(0, 0, 0, 0)
        table = QTableWidget()
        table.setColumnCount(10)
        table.setHorizontalHeaderLabels([
            "序号","品名","编号","厂家","数量(kg)","效期","价格","售价(/g)","预警天数","操作"
        ])
        table.horizontalHeader().setStyleSheet("QHeaderView::section { background: #5C3322; color: #E8DFD2; padding: 6px; font-size: 11px; border: none; }")
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setStyleSheet("QTableWidget { background: #FFFEF9; border: none; font-size: 11px; } QTableWidget::item { padding: 4px 6px; }")
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        fl.addWidget(table)
        return {"frame": frame, "table": table}

    def load_data(self):
        today = date.today().isoformat()
        conn = get_conn()
        cur = conn.cursor()

        # Out of stock: stock_qty <= 0
        cur.execute("SELECT * FROM herbs WHERE stock_qty <= 0 ORDER BY name COLLATE NOCASE ASC")
        out = cur.fetchall()

        # Low stock: 0 < stock_qty < 1 (1kg hardcoded threshold)
        cur.execute("SELECT * FROM herbs WHERE stock_qty > 0 AND stock_qty < 1 ORDER BY name COLLATE NOCASE ASC")
        low = cur.fetchall()

        # Near expiry: expiry_date >= today AND days left < 30
        cur.execute("SELECT * FROM herbs WHERE expiry_date >= ? AND expiry_date != '' AND (julianday(expiry_date) - julianday(?)) < 30 ORDER BY expiry_date ASC", [today, today])
        near = cur.fetchall()

        # Expired: expiry_date < today AND not empty
        cur.execute("SELECT * FROM herbs WHERE expiry_date < ? AND expiry_date != '' ORDER BY expiry_date ASC", [today])
        expired = cur.fetchall()

        conn.close()

        self._fill_table(self.out_of_stock_tab["table"], out, "out")
        self._fill_table(self.low_stock_tab["table"], low, "low")
        self._fill_table(self.near_expiry_tab["table"], near, "near")
        self._fill_table(self.expired_tab["table"], expired, "expired")

        self.tabs.setTabText(0, f"缺货 ({len(out)})")
        self.tabs.setTabText(1, f"库存不足 ({len(low)})")
        self.tabs.setTabText(2, f"临期预警 ({len(near)})")
        self.tabs.setTabText(3, f"已过期 ({len(expired)})")

    def _fill_table(self, table, rows, tab_type):
        from datetime import date
        table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            try:
                exp = date.fromisoformat(r["expiry_date"])
                warn_days = (exp - date.today()).days
            except Exception:
                warn_days = "—"
            items_data = [
                str(i + 1),
                str(r["name"]),
                str(r["alias"] or ""),
                str(r["supplier"]),
                f"{r['stock_qty']:.2f}",
                str(r["expiry_date"] or ""),
                f"¥{r['purchase_price']:.2f}",
                f"¥{r['sell_price']:.2f}",
                f"{warn_days}天",
            ]
            for j, val in enumerate(items_data):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(i, j, item)

            # Row color
            if tab_type == "out":
                color = QColor("#FDE8E8")
            elif tab_type == "expired":
                color = QColor("#FDF0EF")
            elif tab_type == "low":
                color = QColor("#FDF3EA")
            else:
                color = QColor("#FDF8EB")
            for col in range(9):
                it = table.item(i, col)
                if it:
                    it.setBackground(color)

            # Action button
            act_w = QWidget()
            act = QHBoxLayout(act_w)
            act.setContentsMargins(0, 0, 0, 0)
            edit_btn = QPushButton("调整")
            edit_btn.setStyleSheet("QPushButton { padding: 2px 8px; border: 1px solid #7A4C32; border-radius: 3px; color: #7A4C32; font-size: 10px; } QPushButton:hover { background: #F5F0E8; }")
            hid = r["id"]
            edit_btn.clicked.connect(lambda checked, x=hid: self._edit_herb(x))
            act.addWidget(edit_btn)
            table.setCellWidget(i, 9, act_w)

    def _edit_herb(self, hid):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM herbs WHERE id=?", [hid])
        data = cur.fetchone()
        conn.close()
        if not data:
            return
        dlg = AlertEditDialog(self, dict(data))
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.data
            conn = get_conn()
            conn.execute(
                "UPDATE herbs SET stock_qty=?, expiry_date=?, updated_at=date('now') WHERE id=?",
                [d["stock_qty"], d["expiry_date"], hid]
            )
            conn.commit()
            conn.close()
            self.load_data()


class AlertEditDialog(QDialog):
    def __init__(self, parent, data=None):
        super().__init__(parent)
        self.setWindowTitle(f"调整药材 — {data.get('name','')}")
        self.setMinimumWidth(320)
        self.setStyleSheet("QDialog { background: #FFFEF9; }")
        self.data = {}

        layout = QFormLayout(self)
        self.w_qty = QDoubleSpinBox()
        self.w_qty.setMaximum(999999)
        self.w_qty.setDecimals(2)
        self.w_qty.setValue(data.get("stock_qty", 0) if data else 0)
        layout.addRow("数量(kg)", self.w_qty)

        self.w_expiry = QLineEdit(data.get("expiry_date", "") if data else "")
        self.w_expiry.setStyleSheet("padding: 6px 10px; border: 1px solid #C9B99A; border-radius: 3px; background: #FFFEF9;")
        layout.addRow("效期", self.w_expiry)

        self.w_qty.setStyleSheet("padding: 6px 10px; border: 1px solid #C9B99A; border-radius: 3px; background: #FFFEF9;")

        self.w_qty.setStyleSheet("padding: 6px 10px; border: 1px solid #C9B99A; border-radius: 3px; background: #FFFEF9;")

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def _save(self):
        self.data = {
            "stock_qty": self.w_qty.value(),
            "expiry_date": self.w_expiry.text().strip(),
        }
        self.accept()
