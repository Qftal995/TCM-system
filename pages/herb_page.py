"""Page 5: 中药药材管理"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QComboBox, QDoubleSpinBox,
    QSpinBox, QDateEdit, QDialogButtonBox,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont

from database import get_conn
from widgets.searchbox import SearchBox
from widgets.paginator import Paginator

PAGE_SIZE = 30


class HerbPage(QWidget):
    def __init__(self):
        super().__init__()
        self.page = 1
        self.search_keyword = ""
        self._building = False
        self._row_ids = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Top bar
        top = QHBoxLayout()
        top.setContentsMargins(18, 14, 18, 10)
        title = QLabel("中药药材管理")
        title.setStyleSheet("font-family: KaiTi, SimSun; font-size: 16px; color: #3E2723; letter-spacing: 2px;")
        top.addWidget(title)

        self.search = SearchBox("搜药名、别名、药商…")
        self.search.search_triggered.connect(self._on_search)
        self.search.set_search_fn(self._search_fn)
        top.addWidget(self.search)

        self.count_lbl = QLabel()
        self.count_lbl.setStyleSheet("font-size: 11px; color: #8D6E63;")
        top.addStretch()
        top.addWidget(self.count_lbl)
        layout.addLayout(top)

        # Toolbar
        tb = QHBoxLayout()
        tb.setContentsMargins(18, 0, 18, 8)
        tb.setSpacing(6)
        btn_style = """
            QPushButton { padding: 6px 14px; border-radius: 3px; font-size: 12px; letter-spacing: 1px; }
        """
        add_btn = QPushButton("＋ 新增药材")
        add_btn.setStyleSheet(btn_style + "QPushButton { background: #7A4C32; color: #FFFEF9; border: none; } QPushButton:hover { background: #5C3322; }")
        add_btn.clicked.connect(self._add_herb)
        tb.addWidget(add_btn)
        edit_btn = QPushButton("✎ 编辑")
        edit_btn.setStyleSheet(btn_style + "QPushButton { background: transparent; color: #5D4037; border: 1px solid #BCAAA4; } QPushButton:hover { background: #F5F0E8; }")
        edit_btn.clicked.connect(self._edit_herb)
        tb.addWidget(edit_btn)
        del_btn = QPushButton("✕ 删除")
        del_btn.setStyleSheet(btn_style + "QPushButton { background: transparent; color: #D4645C; border: 1px solid #D4645C; } QPushButton:hover { background: #FDF0EF; }")
        del_btn.clicked.connect(self._delete_herb)
        tb.addWidget(del_btn)
        tb.addSpacing(12)
        # Excel buttons
        import_btn = QPushButton("↥ 导入Excel")
        import_btn.setStyleSheet(btn_style + "QPushButton { background: transparent; color: #5D4037; border: 1px solid #BCAAA4; } QPushButton:hover { background: #F5F0E8; }")
        import_btn.clicked.connect(self._import_excel)
        tb.addWidget(import_btn)
        tmpl_btn = QPushButton("模板")
        tmpl_btn.setStyleSheet(btn_style + "QPushButton { background: transparent; color: #5D4037; border: 1px solid #BCAAA4; } QPushButton:hover { background: #F5F0E8; }")
        tmpl_btn.clicked.connect(self._download_template)
        tb.addWidget(tmpl_btn)
        export_btn = QPushButton("↧ 导出Excel")
        export_btn.setStyleSheet(btn_style + "QPushButton { background: transparent; color: #5D4037; border: 1px solid #BCAAA4; } QPushButton:hover { background: #F5F0E8; }")
        export_btn.clicked.connect(self._export_excel)
        tb.addWidget(export_btn)
        tb.addSpacing(8)
        layout.addLayout(tb)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels(
            ["品名","编号","厂家","数量(kg)","采购","效期","价格","合计","售价(/g)","品名Ⅱ","预警天数"]
        )
        self.table.horizontalHeader().setStyleSheet("QHeaderView::section { background: #5C3322; color: #E8DFD2; padding: 8px; font-size: 11px; border: none; }")
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget { background: #FFFEF9; border: 1px solid #D7CCC8; font-size: 12px; gridline-color: rgba(188,170,164,0.2); }
            QTableWidget::item { padding: 6px 8px; color: #3E2723; }
            QTableWidget::item:alternate { background: rgba(232,223,210,0.25); }
            QTableWidget::item:selected { background: rgba(200,164,92,0.15); color: #3E2723; }
        """)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 95)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 65)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(2, 85)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 65)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 60)
        hh.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 85)
        hh.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 60)
        hh.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(7, 65)
        hh.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(8, 70)
        hh.setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(9, 95)
        hh.setSectionResizeMode(10, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(10, 65)
        layout.addWidget(self.table, 1)

        # Paginator
        self.paginator = Paginator(PAGE_SIZE)
        self.paginator.page_changed.connect(self._on_page)
        layout.addWidget(self.paginator)

        self.load_data()

    def load_data(self):
        conn = get_conn()
        cur = conn.cursor()
        base_sql = "FROM herbs"
        params = []
        if self.search_keyword:
            base_sql += " WHERE name LIKE ? OR alias LIKE ? OR supplier LIKE ? OR name2 LIKE ?"
            kw = f"%{self.search_keyword}%"
            params = [kw, kw, kw, kw]
        cur.execute(f"SELECT COUNT(*) {base_sql}", params)
        total = cur.fetchone()[0]
        self.paginator.set_data(total)
        offset = (self.paginator.current_page - 1) * PAGE_SIZE
        cur.execute(
            f"SELECT * {base_sql} ORDER BY name COLLATE NOCASE ASC, supplier COLLATE NOCASE ASC LIMIT ? OFFSET ?",
            params + [PAGE_SIZE, offset]
        )
        rows = cur.fetchall()
        conn.close()

        self._building = True
        self._row_ids = [r["id"] for r in rows]
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            qty = row["stock_qty"] or 0
            price = row["purchase_price"] or 0
            total_price = qty * price
            items_data = [
                str(row["name"]),
                str(row["alias"] or ""),
                str(row["supplier"] or ""),
                f"{qty:.2f}",
                str(row["purchase_note"] or ""),
                str(row["expiry_date"] or ""),
                f"¥{price:.2f}",
                f"¥{total_price:.2f}",
                f"¥{row['sell_price'] or 0:.2f}",
                str(row["name2"] or row["name"]),
                str(self._calc_warn_days(row)),
            ]
            for j, val in enumerate(items_data):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, j, item)
            self._apply_row_color(i, row)
        self._building = False
        self.count_lbl.setText(f"共 {total} 条")

    def _calc_warn_days(self, row):
        from datetime import date
        try:
            exp = date.fromisoformat(row["expiry_date"])
            days_left = (exp - date.today()).days
            return f"{days_left}天"
        except Exception:
            return "—"

    def _apply_row_color(self, row_idx, row_data):
        from datetime import date
        try:
            exp = date.fromisoformat(row_data["expiry_date"])
            days_left = (exp - date.today()).days
        except Exception:
            days_left = 9999
        stock = row_data["stock_qty"] or 0
        warn_days = self._calc_warn_days(row_data)
        try:
            wd = int(warn_days.replace("天", ""))
        except Exception:
            wd = 9999

        if days_left < 0:
            color = QColor("#FDF0EF")
        elif stock < 1:
            color = QColor("#FDF3EA")
        elif days_left < 30:
            color = QColor("#FDF8EB")
        else:
            return

        for col in range(self.table.columnCount()):
            item = self.table.item(row_idx, col)
            if item:
                item.setBackground(color)

    def _on_search(self, keyword):
        self.search_keyword = keyword
        self.paginator.current_page = 1
        self.load_data()

    def _on_page(self, page):
        self.load_data()

    def _search_fn(self, text):
        conn = get_conn()
        cur = conn.cursor()
        kw = f"%{text}%"
        cur.execute("SELECT DISTINCT name FROM herbs WHERE name LIKE ? OR alias LIKE ? OR supplier LIKE ? OR name2 LIKE ? LIMIT 8", [kw, kw, kw, kw])
        results = [row["name"] for row in cur.fetchall()]
        conn.close()
        return results

    def _add_herb(self):
        dlg = HerbDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            conn = get_conn()
            d = dlg.data
            conn.execute("""INSERT INTO herbs(name,alias,name2,supplier,purchase_note,purchase_price,sell_price,purchase_date,shelf_life_days,expiry_date,stock_qty)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                [d["name"],d["alias"],d["name2"],d["supplier"],d["purchase_note"],
                 d["purchase_price"],d["sell_price"],d["purchase_date"],
                 d["shelf_life_days"],d["expiry_date"],d["stock_qty"]])
            conn.commit(); conn.close()
            self.load_data()

    def _edit_herb(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._row_ids):
            QMessageBox.warning(self, "提示", "请先选中一行")
            return
        hid = self._row_ids[row]
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM herbs WHERE id=?", [hid])
        data = cur.fetchone()
        conn.close()
        if not data:
            return
        dlg = HerbDialog(self, dict(data))
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.data
            conn = get_conn()
            conn.execute("""UPDATE herbs SET name=?,alias=?,name2=?,supplier=?,purchase_note=?,purchase_price=?,sell_price=?,purchase_date=?,shelf_life_days=?,expiry_date=?,stock_qty=?,updated_at=date('now')
                WHERE id=?""",
                [d["name"],d["alias"],d["name2"],d["supplier"],d["purchase_note"],
                 d["purchase_price"],d["sell_price"],d["purchase_date"],
                 d["shelf_life_days"],d["expiry_date"],d["stock_qty"],hid])
            conn.commit(); conn.close()
            self.load_data()

    def _delete_herb(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._row_ids):
            QMessageBox.warning(self, "提示", "请先选中一行")
            return
        hid = self._row_ids[row]
        name = self.table.item(row, 1).text()
        supplier = self.table.item(row, 3).text()
        ret = QMessageBox.question(self, "确认删除", f"确定删除 {name}（{supplier}）？此操作不可恢复。", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if ret != QMessageBox.StandardButton.Yes:
            return
        conn = get_conn()
        try:
            conn.execute("DELETE FROM herbs WHERE id=?", [hid])
            conn.commit()
        except Exception as e:
            QMessageBox.warning(self, "删除失败", f"该药材可能被处方或方剂引用，无法删除。\n{str(e)}")
        finally:
            conn.close()
        self.load_data()

    def _import_excel(self):
        from PyQt6.QtWidgets import QFileDialog
        from utils.excel_io import import_herbs
        path, _ = QFileDialog.getOpenFileName(self, "导入药材Excel", "", "Excel (*.xlsx)")
        if not path:
            return
        try:
            success, errs = import_herbs(path)
            msg = f"成功导入 {success} 条"
            if errs:
                msg += f"\n{len(errs)} 条错误:\n" + "\n".join(errs[:5])
            QMessageBox.information(self, "导入完成", msg)
            self.load_data()
        except Exception as e:
            QMessageBox.warning(self, "导入失败", str(e))

    def _download_template(self):
        from PyQt6.QtWidgets import QFileDialog
        from utils.excel_io import generate_herb_template
        path, _ = QFileDialog.getSaveFileName(self, "下载药材导入模板", "药材导入模板.xlsx", "Excel (*.xlsx)")
        if not path:
            return
        try:
            generate_herb_template(path)
            QMessageBox.information(self, "成功", f"模板已保存到：\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "失败", str(e))

    def _export_excel(self):
        from PyQt6.QtWidgets import QFileDialog
        from utils.excel_io import export_herbs
        from datetime import date
        path, _ = QFileDialog.getSaveFileName(self, "导出药材Excel", f"药材数据_{date.today().isoformat()}.xlsx", "Excel (*.xlsx)")
        if not path:
            return
        try:
            where = ""
            params = []
            if self.search_keyword:
                kw = f"%{self.search_keyword}%"
                where = "WHERE name LIKE ? OR alias LIKE ? OR supplier LIKE ? OR name2 LIKE ?"
                params = [kw, kw, kw, kw]
            export_herbs(path, where, params)
            QMessageBox.information(self, "导出成功", f"数据已导出到：\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "导出失败", str(e))


class HerbDialog(QDialog):
    def __init__(self, parent, data=None):
        super().__init__(parent)
        self.setWindowTitle("编辑药材" if data else "新增药材")
        self.setMinimumWidth(450)
        self.setStyleSheet("QDialog { background: #FFFEF9; }")
        self.data = {}

        layout = QFormLayout(self)
        fields = [
            ("name","品名"), ("alias","编号"), ("name2","品名Ⅱ"),
            ("supplier","厂家"), ("purchase_note","采购"),
            ("purchase_price","价格"), ("sell_price","售价(/g)"),
            ("purchase_date_text","进货日期"), ("shelf_life_days","保存时长(天)"),
            ("expiry_date_text","效期"), ("stock_qty","数量(kg)"),
        ]
        self.widgets = {}
        for key, label in fields:
            if key in ("purchase_price","sell_price","stock_qty"):
                w = QDoubleSpinBox()
                w.setMaximum(999999)
                w.setDecimals(2)
                if data:
                    w.setValue(data.get(key, 0))
            elif key in ("shelf_life_days",):
                w = QSpinBox()
                w.setMaximum(9999)
                if data:
                    w.setValue(data.get(key, 0))
                else:
                    w.setValue(365)
            else:
                w = QLineEdit(data.get(key.replace("_text",""),"") if data else "")
            w.setStyleSheet("padding: 6px 10px; border: 1px solid #C9B99A; border-radius: 3px; background: #FFFEF9;")
            self.widgets[key] = w
            layout.addRow(QLabel(label), w)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def _save(self):
        self.data = {
            "name": self.widgets["name"].text().strip(),
            "alias": self.widgets["alias"].text().strip(),
            "name2": self.widgets["name2"].text().strip() or self.widgets["name"].text().strip(),
            "supplier": self.widgets["supplier"].text().strip(),
            "purchase_note": self.widgets["purchase_note"].text().strip(),
            "purchase_price": self.widgets["purchase_price"].value(),
            "sell_price": self.widgets["sell_price"].value(),
            "purchase_date": self.widgets["purchase_date_text"].text().strip(),
            "shelf_life_days": self.widgets["shelf_life_days"].value(),
            "expiry_date": self.widgets["expiry_date_text"].text().strip(),
            "stock_qty": self.widgets["stock_qty"].value(),
        }
        if not self.data["name"]:
            QMessageBox.warning(self, "提示", "请输入品名")
            return
        self.accept()
