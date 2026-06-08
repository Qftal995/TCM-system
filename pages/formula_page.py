"""Page 6: 方子管理 — 方剂模板 + 处方记录"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFrame, QDialog, QFormLayout, QLineEdit, QComboBox,
    QDoubleSpinBox, QDialogButtonBox, QCompleter, QSpinBox,
)
from PyQt6.QtCore import Qt

from database import get_conn
from widgets.paginator import Paginator
from widgets.presc_preview import PrescPreview
from widgets.searchbox import SearchBox

PAGE_SIZE = 25


class FormulaPage(QWidget):
    def __init__(self):
        super().__init__()
        self.presc_page = 1

        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        top = QHBoxLayout()
        top.setContentsMargins(18, 14, 18, 10)
        title = QLabel("方子管理")
        title.setStyleSheet("font-family: KaiTi, SimSun; font-size: 16px; color: #3E2723; letter-spacing: 2px;")
        top.addWidget(title)
        top.addStretch()
        self.count_lbl = QLabel()
        self.count_lbl.setStyleSheet("font-size: 11px; color: #8D6E63;")
        top.addWidget(self.count_lbl)
        main.addLayout(top)

        content = QVBoxLayout()
        content.setContentsMargins(18, 0, 18, 18)
        content.setSpacing(8)

        card_style = "QFrame { background: #FFFEF9; border: 1px solid #D7CCC8; border-radius: 5px; }"
        btn_style = (
            "QPushButton { padding: 5px 12px; border-radius: 3px; font-size: 11px; "
            "border: 1px solid #BCAAA4; background: transparent; color: #5D4037; }"
            "QPushButton:hover { background: #F5F0E8; }"
        )

        # ── Formula templates card ──
        fcard = QFrame()
        fcard.setStyleSheet(card_style)
        flayout = QVBoxLayout(fcard)
        flayout.setContentsMargins(12, 8, 12, 10)
        flayout.setSpacing(6)

        fhead = QHBoxLayout()
        fhead.addWidget(QLabel("<b>经典方剂模板</b>"))
        fhead.addStretch()
        # Service fee editor
        fhead.addWidget(QLabel("后台值(¥)："))
        self.service_fee_spin = QSpinBox()
        self.service_fee_spin.setMinimum(0)
        self.service_fee_spin.setMaximum(99999)
        self.service_fee_spin.setStyleSheet("QSpinBox { padding: 4px 8px; border: 1px solid #C9B99A; border-radius: 3px; background: #FFFEF9; font-size: 11px; max-width: 70px; }")
        self.service_fee_spin.valueChanged.connect(self._save_service_fee)
        fhead.addWidget(self.service_fee_spin)
        fhead.addSpacing(12)
        go_btn = QPushButton("去开方")
        go_btn.setStyleSheet(
            "QPushButton { padding: 5px 12px; border-radius: 3px; font-size: 11px; "
            "background: #7A4C32; color: #FFFEF9; border: none; }"
            "QPushButton:hover { background: #5C3322; }"
        )
        go_btn.clicked.connect(self._go_presc)
        fhead.addWidget(go_btn)
        fhead.addSpacing(6)
        add_btn = QPushButton("＋ 新增")
        add_btn.setStyleSheet(btn_style)
        add_btn.clicked.connect(self._add_formula)
        fhead.addWidget(add_btn)
        edit_btn = QPushButton("✎ 编辑")
        edit_btn.setStyleSheet(btn_style)
        edit_btn.clicked.connect(self._edit_formula)
        fhead.addWidget(edit_btn)
        del_btn = QPushButton("✕ 删除")
        del_btn.setStyleSheet(
            "QPushButton { padding: 5px 12px; border-radius: 3px; font-size: 11px; "
            "border: 1px solid #D4645C; background: transparent; color: #D4645C; }"
            "QPushButton:hover { background: #FDF0EF; }"
        )
        del_btn.clicked.connect(self._delete_formula)
        fhead.addWidget(del_btn)
        flayout.addLayout(fhead)

        self.formula_table = QTableWidget()
        self.formula_table.setMouseTracking(True)
        self.formula_table.setColumnCount(5)
        self.formula_table.setHorizontalHeaderLabels(["序号","方剂名称","说明","分类","包含药材"])
        self.formula_table.horizontalHeader().setStyleSheet("QHeaderView::section { background: #5C3322; color: #E8DFD2; padding: 5px; font-size: 11px; border: none; }")
        self.formula_table.verticalHeader().setVisible(False)
        self.formula_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.formula_table.setMaximumHeight(340)
        self.formula_table.setStyleSheet("QTableWidget { background: #FFFEF9; border: 1px solid #D7CCC8; font-size: 11px; } QTableWidget::item { padding: 3px 6px; }")
        self.formula_table.cellDoubleClicked.connect(self._show_formula_detail)
        self.formula_table.cellEntered.connect(self._on_formula_cell_entered)
        hh = self.formula_table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.formula_table.setColumnWidth(0, 40)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.formula_table.setColumnWidth(1, 260)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        flayout.addWidget(self.formula_table)
        content.addWidget(fcard)

        # ── Prescriptions card ──
        pcard = QFrame()
        pcard.setStyleSheet(card_style)
        playout = QVBoxLayout(pcard)
        playout.setContentsMargins(12, 8, 12, 10)
        playout.setSpacing(6)
        phead = QHBoxLayout()
        phead.addWidget(QLabel("<b>处方记录</b>"))
        phead.addStretch()
        del_presc_btn = QPushButton("✕ 删除")
        del_presc_btn.setStyleSheet(
            "QPushButton { padding: 5px 12px; border-radius: 3px; font-size: 11px; "
            "border: 1px solid #D4645C; background: transparent; color: #D4645C; }"
            "QPushButton:hover { background: #FDF0EF; }"
        )
        del_presc_btn.clicked.connect(self._delete_prescription)
        phead.addWidget(del_presc_btn)
        playout.addLayout(phead)
        self.presc_table = QTableWidget()
        self.presc_table.setColumnCount(8)
        self.presc_table.setHorizontalHeaderLabels(["序号","处方编号","患者","方剂","诊断","门诊处理","总价","开方时间"])
        self.presc_table.horizontalHeader().setStyleSheet("QHeaderView::section { background: #5C3322; color: #E8DFD2; padding: 5px; font-size: 11px; border: none; }")
        self.presc_table.verticalHeader().setVisible(False)
        self.presc_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.presc_table.setStyleSheet("QTableWidget { background: #FFFEF9; border: 1px solid #D7CCC8; font-size: 11px; } QTableWidget::item { padding: 3px 6px; }")
        self.presc_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.presc_table.doubleClicked.connect(self._show_presc_detail)
        playout.addWidget(self.presc_table)

        self.paginator = Paginator(PAGE_SIZE)
        self.paginator.page_changed.connect(lambda p: self.load_data())
        playout.addWidget(self.paginator)

        content.addWidget(pcard)
        main.addLayout(content, 1)
        self.load_data()

    def load_data(self):
        conn = get_conn()
        cur = conn.cursor()

        # Load service_fee
        try:
            cur.execute("SELECT value FROM settings WHERE key='service_fee'")
            row = cur.fetchone()
            if row:
                self.service_fee_spin.blockSignals(True)
                self.service_fee_spin.setValue(int(float(row["value"])))
                self.service_fee_spin.blockSignals(False)
        except Exception:
            pass

        # Formulas
        cur.execute("SELECT * FROM formulas ORDER BY id")
        formulas = cur.fetchall()
        self.formula_table.setRowCount(len(formulas))
        for i, f in enumerate(formulas):
            self.formula_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.formula_table.setItem(i, 1, QTableWidgetItem(f["name"]))
            self.formula_table.setItem(i, 2, QTableWidgetItem(f["description"] or ""))
            self.formula_table.setItem(i, 3, QTableWidgetItem(f["category"] or ""))
            cur.execute("SELECT h.name, fi.default_grams FROM formula_items fi JOIN herbs h ON fi.herb_id=h.id WHERE fi.formula_id=?", [f["id"]])
            items = cur.fetchall()
            if items:
                tooltip = ";\n".join(f"{r['name']} {r['default_grams']}g" for r in items)
                summary_item = QTableWidgetItem(f"{len(items)} 味")
                summary_item.setToolTip(tooltip)
            else:
                summary_item = QTableWidgetItem("—")
            self.formula_table.setItem(i, 4, summary_item)
        # Center all formula table cells
        for row in range(self.formula_table.rowCount()):
            for col in range(self.formula_table.columnCount()):
                item = self.formula_table.item(row, col)
                if item:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        # Prescriptions
        cur.execute("SELECT COUNT(*) as c FROM prescriptions")
        total = cur.fetchone()["c"]
        self.paginator.set_data(total)
        offset = (self.paginator.current_page - 1) * PAGE_SIZE
        cur.execute("SELECT p.*, pt.name as patient_name FROM prescriptions p LEFT JOIN patients pt ON p.patient_id=pt.id ORDER BY p.created_at DESC LIMIT ? OFFSET ?", [PAGE_SIZE, offset])
        prescs = cur.fetchall()
        conn.close()

        self.presc_table.setRowCount(len(prescs))
        for i, p in enumerate(prescs):
            self.presc_table.setItem(i, 0, QTableWidgetItem(str(offset + i + 1)))
            self.presc_table.setItem(i, 1, QTableWidgetItem(p["prescription_no"]))
            self.presc_table.setItem(i, 2, QTableWidgetItem(p["patient_name"] or ""))
            self.presc_table.setItem(i, 3, QTableWidgetItem(p["formula_name"] or ""))
            self.presc_table.setItem(i, 4, QTableWidgetItem(p["diagnosis"] or ""))
            self.presc_table.setItem(i, 5, QTableWidgetItem(p["treatment"] or ""))
            self.presc_table.setItem(i, 6, QTableWidgetItem(f"¥{p['total_price']:.2f}"))
            self.presc_table.setItem(i, 7, QTableWidgetItem(p["created_at"] or ""))
        # Center all presc table cells except 诊断 (col 4)
        for row in range(self.presc_table.rowCount()):
            for col in range(self.presc_table.columnCount()):
                if col == 4:
                    continue
                item = self.presc_table.item(row, col)
                if item:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        self.count_lbl.setText(f"方剂 {len(formulas)} · 处方 {total}")

    def _on_formula_cell_entered(self, row, col):
        from PyQt6.QtGui import QCursor
        from PyQt6.QtWidgets import QToolTip
        item = self.formula_table.item(row, col)
        if item and col == 4:
            tt = item.toolTip()
            if tt:
                QToolTip.showText(QCursor.pos(), tt, self.formula_table)
                return
        QToolTip.hideText()

    def _show_formula_detail(self, row, col):
        from widgets.presc_preview import PrescPreview
        if col != 1:
            return
        name = self.formula_table.item(row, 1)
        if not name:
            return
        name = name.text()
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM formulas WHERE name=?", [name])
        f = cur.fetchone()
        if not f:
            conn.close()
            return
        cur.execute("SELECT fi.default_grams, h.name, h.sell_price FROM formula_items fi JOIN herbs h ON fi.herb_id=h.id WHERE fi.formula_id=?", [f["id"]])
        items = cur.fetchall()
        conn.close()

        dlg = QDialog(self)
        dlg.setWindowTitle(f"方剂详情 — {f['name']}")
        dlg.setMinimumSize(450, 300)
        dlg.setStyleSheet("QDialog { background: #FFFEF9; }")
        layout = QVBoxLayout(dlg)
        info = QLabel(f"名称：{f['name']}\n说明：{f['description'] or '-'}　|　分类：{f['category'] or '-'}")
        info.setStyleSheet("color: #5D4037; font-size: 12px; margin-bottom: 8px;")
        layout.addWidget(info)
        preview = PrescPreview()
        preview.set_items([(it["name"], it["default_grams"], it["sell_price"]) for it in items])
        layout.addWidget(preview)
        tbl = QTableWidget()
        tbl.setColumnCount(4)
        tbl.setHorizontalHeaderLabels(["药材","克数","单价","小计"])
        tbl.horizontalHeader().setStyleSheet("QHeaderView::section { background: #5C3322; color: #E8DFD2; padding: 6px; font-size: 11px; }")
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setRowCount(len(items))
        total = 0
        for i, it in enumerate(items):
            sub = it["default_grams"] * it["sell_price"]
            total += sub
            tbl.setItem(i, 0, QTableWidgetItem(it["name"]))
            tbl.setItem(i, 1, QTableWidgetItem(f"{it['default_grams']}g"))
            tbl.setItem(i, 2, QTableWidgetItem(f"¥{it['sell_price']:.2f}/g"))
            tbl.setItem(i, 3, QTableWidgetItem(f"¥{sub:.2f}"))
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(tbl)
        total_lbl = QLabel(f"单剂合计：¥{total:.2f}")
        total_lbl.setStyleSheet("font-size: 14px; color: #3E2723; font-weight: bold; padding: 8px 0;")
        total_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(total_lbl)
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("QPushButton { padding: 6px 20px; background: #7A4C32; color: #FFFEF9; border-radius: 3px; }")
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        dlg.exec()

    # ── Formula CRUD ──
    def _add_formula(self):
        dlg = FormulaEditDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            conn = get_conn()
            cur = conn.cursor()
            d = dlg.data
            cur.execute("INSERT INTO formulas(name,description,category) VALUES(?,?,?)",
                        [d["name"], d["description"], d["category"]])
            fid = cur.lastrowid
            for item in dlg.items:
                cur.execute("INSERT INTO formula_items(formula_id,herb_id,default_grams) VALUES(?,?,?)",
                            [fid, item["herb_id"], item["grams"]])
            conn.commit()
            conn.close()
            self.load_data()

    def _edit_formula(self):
        row = self.formula_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选中一个方剂")
            return
        name = self.formula_table.item(row, 1).text()
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM formulas WHERE name=?", [name])
        f = cur.fetchone()
        if not f:
            conn.close()
            return
        cur.execute("SELECT fi.*, h.name as herb_name FROM formula_items fi JOIN herbs h ON fi.herb_id=h.id WHERE fi.formula_id=?", [f["id"]])
        items = [{"herb_id": r["herb_id"], "herb_name": r["herb_name"], "grams": r["default_grams"]} for r in cur.fetchall()]
        conn.close()

        dlg = FormulaEditDialog(self, f, items)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            conn = get_conn()
            cur = conn.cursor()
            d = dlg.data
            cur.execute("UPDATE formulas SET name=?,description=?,category=? WHERE id=?",
                        [d["name"], d["description"], d["category"], f["id"]])
            cur.execute("DELETE FROM formula_items WHERE formula_id=?", [f["id"]])
            for item in dlg.items:
                cur.execute("INSERT INTO formula_items(formula_id,herb_id,default_grams) VALUES(?,?,?)",
                            [f["id"], item["herb_id"], item["grams"]])
            conn.commit()
            conn.close()
            self.load_data()

    def _delete_formula(self):
        row = self.formula_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选中一个方剂")
            return
        name = self.formula_table.item(row, 1).text()
        ret = QMessageBox.question(self, "确认删除", f"确定删除方剂「{name}」及其包含的药材？")
        if ret != QMessageBox.StandardButton.Yes:
            return
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM formulas WHERE name=?", [name])
        f = cur.fetchone()
        if f:
            cur.execute("DELETE FROM formula_items WHERE formula_id=?", [f["id"]])
            cur.execute("DELETE FROM formulas WHERE id=?", [f["id"]])
        conn.commit()
        conn.close()
        self.load_data()

    def _use_formula(self, fid):
        pass  # patched by main.py

    def _save_service_fee(self):
        val = self.service_fee_spin.value()
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('service_fee',?)", [str(val)])
        conn.commit()
        conn.close()

    def _go_presc(self):
        row = self.formula_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选中一个方剂")
            return
        name = self.formula_table.item(row, 1).text()
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM formulas WHERE name=?", [name])
        f = cur.fetchone()
        conn.close()
        if f and callable(self._use_formula):
            self._use_formula(f["id"])

    # ── Prescription detail ──
    def _show_presc_detail(self):
        row = self.presc_table.currentRow()
        if row < 0: return
        presc_no = self.presc_table.item(row, 1).text()
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT p.*, pt.name as patient_name FROM prescriptions p LEFT JOIN patients pt ON p.patient_id=pt.id WHERE p.prescription_no=?", [presc_no])
        p = cur.fetchone()
        if not p: conn.close(); return
        cur.execute("SELECT * FROM prescription_items WHERE prescription_id=?", [p["id"]])
        items = cur.fetchall()
        conn.close()

        dlg = QDialog(self)
        dlg.setWindowTitle(f"处方详情 — {presc_no}")
        dlg.setMinimumSize(520, 400)
        dlg.setStyleSheet("QDialog { background: #FFFEF9; }")
        layout = QVBoxLayout(dlg)

        info = QLabel(f"编号：{p['prescription_no']} | 患者：{p['patient_name']} | 时间：{p['created_at']}\n诊断：{p['diagnosis'] or '-'} | 门诊处理：{p['treatment'] or '-'}")
        info.setStyleSheet("color: #5D4037; font-size: 12px; margin-bottom: 8px;")
        layout.addWidget(info)

        preview = PrescPreview()
        preview.set_items([(it["herb_name"], it["actual_grams"], it["unit_price"]) for it in items])
        layout.addWidget(preview)

        tbl = QTableWidget()
        tbl.setColumnCount(4)
        tbl.setHorizontalHeaderLabels(["药材","克数","单价","小计"])
        tbl.horizontalHeader().setStyleSheet("QHeaderView::section { background: #5C3322; color: #E8DFD2; padding: 6px; font-size: 11px; }")
        tbl.verticalHeader().setVisible(False)
        tbl.setRowCount(len(items))
        total = 0
        for i, it in enumerate(items):
            sub = it["actual_grams"] * it["unit_price"]
            total += sub
            tbl.setItem(i, 0, QTableWidgetItem(it["herb_name"]))
            tbl.setItem(i, 1, QTableWidgetItem(f"{it['actual_grams']}g"))
            tbl.setItem(i, 2, QTableWidgetItem(f"¥{it['unit_price']:.2f}/g"))
            tbl.setItem(i, 3, QTableWidgetItem(f"¥{sub:.2f}"))
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tbl.setStyleSheet("QTableWidget { font-size: 11px; }")
        layout.addWidget(tbl)
        total_lbl = QLabel(f"合计：¥{total:.2f}")
        total_lbl.setStyleSheet("font-size: 14px; color: #3E2723; font-weight: bold; padding: 8px 0;")
        total_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(total_lbl)

        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("QPushButton { padding: 6px 20px; background: #7A4C32; color: #FFFEF9; border-radius: 3px; }")
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        dlg.exec()

    # ── Prescription delete ──
    def _delete_prescription(self):
        row = self.presc_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选中一个处方")
            return
        presc_no = self.presc_table.item(row, 1).text()
        patient = self.presc_table.item(row, 2).text()
        ret = QMessageBox.question(self, "确认删除",
            f"确定删除处方「{presc_no}」（患者：{patient}）？\n删除后库存不会恢复。")
        if ret != QMessageBox.StandardButton.Yes:
            return
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM prescriptions WHERE prescription_no=?", [presc_no])
        p = cur.fetchone()
        if p:
            cur.execute("DELETE FROM prescription_items WHERE prescription_id=?", [p["id"]])
            cur.execute("DELETE FROM prescriptions WHERE id=?", [p["id"]])
        conn.commit()
        conn.close()
        self.load_data()


class FormulaEditDialog(QDialog):
    def __init__(self, parent, data=None, items=None):
        super().__init__(parent)
        is_edit = data is not None
        self.setWindowTitle("编辑方剂" if is_edit else "新增方剂")
        self.setMinimumSize(500, 420)
        self.setStyleSheet("QDialog { background: #FFFEF9; }")
        self.data = {}
        self.items = items[:] if items else []

        layout = QVBoxLayout(self)
        form = QFormLayout()
        input_style = "padding: 6px 10px; border: 1px solid #C9B99A; border-radius: 3px; background: #FFFEF9; font-size: 12px;"
        self.w_name = QLineEdit(data["name"] if is_edit else "")
        self.w_name.setStyleSheet(input_style)
        self.w_desc = QLineEdit(data["description"] if is_edit else "")
        self.w_desc.setStyleSheet(input_style)
        self.w_cat = QLineEdit(data["category"] if is_edit else "")
        self.w_cat.setStyleSheet(input_style)
        form.addRow("方剂名称", self.w_name)
        form.addRow("说明", self.w_desc)
        form.addRow("分类", self.w_cat)
        layout.addLayout(form)

        # Item editor
        layout.addWidget(QLabel("<b>包含药材</b>"))
        self.item_table = QTableWidget()
        self.item_table.setColumnCount(3)
        self.item_table.setHorizontalHeaderLabels(["药材","克数(g)","操作"])
        self.item_table.horizontalHeader().setStyleSheet("QHeaderView::section { background: #5C3322; color: #E8DFD2; padding: 5px; font-size: 11px; }")
        self.item_table.verticalHeader().setVisible(False)
        self.item_table.setStyleSheet("QTableWidget { font-size: 11px; }")
        self.item_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._refresh_item_table()
        layout.addWidget(self.item_table)

        add_row = QHBoxLayout()
        self.herb_combo = QComboBox()
        self.herb_combo.setEditable(True)
        self.herb_combo.setStyleSheet(input_style)
        self.herb_combo.setMinimumWidth(160)
        self._load_herbs()
        self._herb_names = [self.herb_combo.itemText(i) for i in range(self.herb_combo.count())]
        completer = QCompleter(self._herb_names)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.herb_combo.setCompleter(completer)
        add_row.addWidget(self.herb_combo)
        self.gram_spin = QDoubleSpinBox()
        self.gram_spin.setDecimals(1)
        self.gram_spin.setMaximum(99999)
        self.gram_spin.setValue(9)
        self.gram_spin.setStyleSheet(input_style + "max-width: 70px;")
        add_row.addWidget(self.gram_spin)
        add_row.addWidget(QLabel("g"))
        add_item_btn = QPushButton("＋ 添加药材")
        add_item_btn.setStyleSheet("QPushButton { padding: 5px 12px; background: #7A4C32; color: #FFFEF9; border-radius: 3px; font-size: 11px; }")
        add_item_btn.clicked.connect(self._add_item)
        add_row.addWidget(add_item_btn)
        add_row.addStretch()
        layout.addLayout(add_row)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _load_herbs(self):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, name, supplier FROM herbs ORDER BY name COLLATE NOCASE ASC")
        self._herb_list = cur.fetchall()
        conn.close()
        for h in self._herb_list:
            self.herb_combo.addItem(f"{h['name']}（{h['supplier']}）", h["id"])

    def _add_item(self):
        hid = self.herb_combo.currentData()
        raw = self.herb_combo.currentText().strip()
        hname = raw.split("（")[0].strip() if "（" in raw else raw
        grams = self.gram_spin.value()
        if not hname:
            return
        if grams <= 0:
            return
        if hid is None:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT id FROM herbs WHERE name=? LIMIT 1", [hname])
            row = cur.fetchone()
            conn.close()
            if row:
                hid = row["id"]
            else:
                QMessageBox.warning(self, "提示", f"未找到药材「{hname}」")
                return
        self.items.append({"herb_id": hid, "herb_name": hname, "grams": grams})
        self._refresh_item_table()

    def _refresh_item_table(self):
        self.item_table.setRowCount(len(self.items))
        for i, item in enumerate(self.items):
            self.item_table.setItem(i, 0, QTableWidgetItem(item["herb_name"]))
            self.item_table.setItem(i, 1, QTableWidgetItem(f"{item['grams']}g"))
            del_w = QWidget()
            dl = QHBoxLayout(del_w)
            dl.setContentsMargins(0, 0, 0, 0)
            del_btn = QPushButton("删除")
            del_btn.setStyleSheet("QPushButton { padding: 2px 8px; border: 1px solid #D4645C; border-radius: 3px; color: #D4645C; font-size: 10px; }")
            del_btn.clicked.connect(lambda checked, idx=i: self._remove_item(idx))
            dl.addWidget(del_btn)
            self.item_table.setCellWidget(i, 2, del_w)

    def _remove_item(self, idx):
        if 0 <= idx < len(self.items):
            self.items.pop(idx)
            self._refresh_item_table()

    def _save(self):
        name = self.w_name.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "请输入方剂名称")
            return
        if not self.items:
            QMessageBox.warning(self, "提示", "请至少添加一味药材")
            return
        self.data = {
            "name": name,
            "description": self.w_desc.text().strip(),
            "category": self.w_cat.text().strip(),
        }
        self.accept()
