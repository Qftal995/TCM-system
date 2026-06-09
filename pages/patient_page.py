"""Page 2: 患者信息管理"""
from datetime import date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QComboBox,
    QSpinBox, QDialogButtonBox, QFileDialog, QFrame,
)
from PyQt6.QtCore import Qt

from database import get_conn
from widgets.searchbox import SearchBox
from widgets.paginator import Paginator
from widgets.presc_preview import PrescPreview

PAGE_SIZE = 28


class PatientPage(QWidget):
    def __init__(self):
        super().__init__()
        self.page = 1
        self.search_keyword = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Top bar ──
        top = QHBoxLayout()
        top.setContentsMargins(18, 14, 18, 10)
        title = QLabel("患者信息管理")
        title.setStyleSheet("font-family: KaiTi, SimSun; font-size: 16px; color: #3E2723; letter-spacing: 2px;")
        top.addWidget(title)

        self.search = SearchBox("搜姓名、电话、地址…")
        self.search.search_triggered.connect(self._on_search)
        self.search.set_search_fn(self._search_fn)
        top.addWidget(self.search)

        self.count_lbl = QLabel()
        self.count_lbl.setStyleSheet("font-size: 11px; color: #8D6E63;")
        top.addStretch()
        top.addWidget(self.count_lbl)
        layout.addLayout(top)

        # ── Toolbar ──
        tb = QHBoxLayout()
        tb.setContentsMargins(18, 0, 18, 8)
        tb.setSpacing(6)
        btn_base = (
            "QPushButton { padding: 6px 14px; border-radius: 3px; font-size: 12px; letter-spacing: 1px; }"
        )
        add_btn = QPushButton("＋ 新增患者")
        add_btn.setStyleSheet(btn_base + "QPushButton { background: #7A4C32; color: #FFFEF9; border: none; } QPushButton:hover { background: #5C3322; }")
        add_btn.clicked.connect(self._add)
        tb.addWidget(add_btn)

        import_btn = QPushButton("↥ 导入Excel")
        import_btn.setStyleSheet(btn_base + "QPushButton { background: transparent; color: #5D4037; border: 1px solid #BCAAA4; } QPushButton:hover { background: #F5F0E8; }")
        import_btn.clicked.connect(self._import_excel)
        tb.addWidget(import_btn)
        tmpl_btn = QPushButton("模板")
        tmpl_btn.setStyleSheet(btn_base + "QPushButton { background: transparent; color: #5D4037; border: 1px solid #BCAAA4; } QPushButton:hover { background: #F5F0E8; }")
        tmpl_btn.clicked.connect(self._download_template)
        tb.addWidget(tmpl_btn)
        export_btn = QPushButton("↧ 导出Excel")
        export_btn.setStyleSheet(btn_base + "QPushButton { background: transparent; color: #5D4037; border: 1px solid #BCAAA4; } QPushButton:hover { background: #F5F0E8; }")
        export_btn.clicked.connect(self._export_excel)
        tb.addWidget(export_btn)
        tb.addStretch()
        layout.addLayout(tb)

        # ── Table ──
        self.table = QTableWidget()
        self.table.setColumnCount(14)
        self.table.setHorizontalHeaderLabels([
            "序号","月序号","姓名","就诊日期","病案号","性别","职业","年龄","电话","常住地址","症状","诊断","门诊处理","操作"
        ])
        self.table.horizontalHeader().setStyleSheet(
            "QHeaderView::section { background: #5C3322; color: #E8DFD2; padding: 7px; font-size: 11px; border: none; }"
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget { background: #FFFEF9; border: 1px solid #D7CCC8; font-size: 12px; gridline-color: rgba(188,170,164,0.2); }
            QTableWidget::item { padding: 4px 8px; color: #3E2723; }
            QTableWidget::item:alternate { background: rgba(232,223,210,0.25); }
            QTableWidget::item:selected { background: rgba(200,164,92,0.15); color: #3E2723; }
        """)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 110)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 60)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(2, 85)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 100)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 90)
        hh.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 40)
        hh.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 50)
        hh.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(7, 50)
        hh.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(8, 110)
        hh.setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(9, 130)
        hh.setSectionResizeMode(10, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(11, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(12, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(13, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(13, 185)
        layout.addWidget(self.table, 1)

        # ── Paginator ──
        self.paginator = Paginator(PAGE_SIZE)
        self.paginator.page_changed.connect(lambda p: self.load_data())
        layout.addWidget(self.paginator)

        self.load_data()

    def load_data(self):
        conn = get_conn()
        cur = conn.cursor()
        base = ("FROM patients p LEFT JOIN ("
                "SELECT patient_id, created_at as visit_date, diagnosis, treatment, "
                "ROW_NUMBER() OVER (PARTITION BY patient_id ORDER BY created_at DESC) as rn "
                "FROM prescriptions"
                ") rx ON p.id=rx.patient_id AND rx.rn=1")
        params = []
        if self.search_keyword:
            kw = f"%{self.search_keyword}%"
            base += " WHERE p.name LIKE ? OR p.phone LIKE ? OR p.address LIKE ? OR p.monthly_no LIKE ? OR p.medical_record_no LIKE ?"
            params = [kw, kw, kw, kw, kw]
        cur.execute(f"SELECT COUNT(*) {base}", params)
        total = cur.fetchone()[0]
        self.paginator.set_data(total)
        offset = (self.paginator.current_page - 1) * PAGE_SIZE
        cur.execute(f"SELECT p.*, COALESCE(p.visit_date, rx.visit_date) as visit_date, COALESCE(p.diagnosis, rx.diagnosis) as diagnosis, COALESCE(p.treatment, rx.treatment) as treatment {base} ORDER BY substr(p.visit_date, 1, 7) DESC, CAST(p.monthly_no AS INTEGER) DESC LIMIT ? OFFSET ?", params + [PAGE_SIZE, offset])
        rows = cur.fetchall()
        conn.close()

        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            items_data = [
                str(offset + i + 1),                     # 序号
                str(row["monthly_no"] or ""),             # 月序号
                str(row["name"]),                         # 姓名
                str(row["visit_date"] or ""),             # 就诊日期
                str(row["medical_record_no"] or ""),      # 病案号
                str(row["gender"] or ""),                 # 性别
                str(row["occupation"] or ""),             # 职业
                str(row["age"] or ""),                    # 年龄
                str(row["phone"] or ""),                  # 电话
                str(row["address"] or ""),                # 常住地址
                str(row["condition"] or ""),              # 症状
                str(row["diagnosis"] or ""),              # 诊断
                str(row["treatment"] or ""),              # 门诊处理
            ]
            for j, val in enumerate(items_data):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, j, item)
            # Actions widget
            act_w = QWidget()
            act = QHBoxLayout(act_w)
            act.setContentsMargins(0, 0, 0, 0)
            act.setSpacing(4)
            pid = row["id"]
            hist_btn = QPushButton("历史开方")
            hist_btn.setStyleSheet("QPushButton { padding: 2px 8px; border: 1px solid #BCAAA4; border-radius: 3px; background: transparent; color: #5D4037; font-size: 11px; } QPushButton:hover { background: #F5F0E8; }")
            hist_btn.clicked.connect(lambda checked, p=pid: self._show_history(p))
            act.addWidget(hist_btn)
            edit_btn = QPushButton("编辑")
            edit_btn.setStyleSheet(hist_btn.styleSheet())
            edit_btn.clicked.connect(lambda checked, p=pid: self._edit(p))
            act.addWidget(edit_btn)
            del_btn = QPushButton("删除")
            del_btn.setStyleSheet("QPushButton { padding: 2px 8px; border: 1px solid #D4645C; border-radius: 3px; background: transparent; color: #D4645C; font-size: 11px; } QPushButton:hover { background: #FDF0EF; }")
            del_btn.clicked.connect(lambda checked, p=pid: self._delete(p))
            act.addWidget(del_btn)
            self.table.setCellWidget(i, 13, act_w)

        self.count_lbl.setText(f"共 {total} 条")

    def _on_search(self, kw):
        self.search_keyword = kw
        self.paginator.current_page = 1
        self.load_data()

    def _search_fn(self, text):
        conn = get_conn()
        kw = f"%{text}%"
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT name FROM patients WHERE name LIKE ? OR phone LIKE ? OR monthly_no LIKE ? OR medical_record_no LIKE ? LIMIT 8", [kw, kw, kw, kw])
        results = [row["name"] for row in cur.fetchall()]
        conn.close()
        return results

    def _add(self):
        dlg = PatientDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.data
            conn = get_conn()
            cur = conn.cursor()
            visit_date = d.get("visit_date","") or date.today().isoformat()
            visit_month = visit_date[:7]
            cur.execute("SELECT COALESCE(MAX(CAST(monthly_no AS INTEGER)), 0) + 1 FROM patients WHERE substr(visit_date,1,7)=?", [visit_month])
            monthly_no = str(cur.fetchone()[0]).zfill(2)
            cur.execute("INSERT INTO patients(name,phone,age,gender,occupation,address,condition,monthly_no,medical_record_no,visit_date,diagnosis,treatment,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,date('now'))",
                         [d["name"],d["phone"],d["age"],d["gender"],d["occupation"],d["address"],d["condition"],monthly_no,d["medical_record_no"],visit_date,d.get("diagnosis",""),d.get("treatment","")])
            conn.commit(); conn.close()
            self.load_data()

    def _edit(self, pid):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM patients WHERE id=?", [pid])
        row = cur.fetchone()
        conn.close()
        if not row: return
        dlg = PatientDialog(self, dict(row))
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.data
            conn = get_conn()
            cur = conn.cursor()
            monthly_no = (row["monthly_no"] or "").zfill(2)
            cur.execute("UPDATE patients SET name=?,phone=?,age=?,gender=?,occupation=?,address=?,condition=?,monthly_no=?,medical_record_no=?,diagnosis=?,treatment=? WHERE id=?",
                         [d["name"],d["phone"],d["age"],d["gender"],d["occupation"],d["address"],d["condition"],monthly_no,d["medical_record_no"],d.get("diagnosis",""),d.get("treatment",""),pid])
            conn.commit(); conn.close()
            self.load_data()

    def _delete(self, pid):
        ret = QMessageBox.question(self, "确认删除", "确定删除该患者？")
        if ret != QMessageBox.StandardButton.Yes: return
        conn = get_conn()
        conn.execute("DELETE FROM patients WHERE id=?", [pid])
        conn.commit(); conn.close()
        self.load_data()

    def _show_history(self, pid):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM patients WHERE id=?", [pid])
        pat = cur.fetchone()
        if not pat: conn.close(); return
        cur.execute("SELECT * FROM prescriptions WHERE patient_id=? ORDER BY created_at DESC", [pid])
        prescs = cur.fetchall()
        conn.close()

        dlg = QDialog(self)
        dlg.setWindowTitle(f"{pat['name']} — 历史开方")
        dlg.setMinimumSize(600, 350)
        dlg.setStyleSheet("QDialog { background: #FFFEF9; }")
        layout = QVBoxLayout(dlg)
        info = QLabel(f"患者：{pat['name']} | 症状：{pat['condition'] or '-'} | 职业：{pat['occupation'] or '-'} | 历史开方：{len(prescs)} 次")
        info.setStyleSheet("color: #5D4037; font-size: 13px; margin-bottom: 10px;")
        layout.addWidget(info)
        if not prescs:
            layout.addWidget(QLabel("暂无历史处方"))
        else:
            tbl = QTableWidget()
            tbl.setColumnCount(6)
            tbl.setHorizontalHeaderLabels(["处方编号","方剂","诊断","门诊处理","总价","时间"])
            tbl.horizontalHeader().setStyleSheet("QHeaderView::section { background: #5C3322; color: #E8DFD2; padding: 6px; }")
            tbl.verticalHeader().setVisible(False)
            tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            tbl.setRowCount(len(prescs))
            for i, p in enumerate(prescs):
                presc_no_item = QTableWidgetItem(p["prescription_no"])
                presc_no_item.setData(Qt.ItemDataRole.UserRole, p["prescription_no"])
                tbl.setItem(i, 0, presc_no_item)
                tbl.setItem(i, 1, QTableWidgetItem(p["formula_name"] or ""))
                tbl.setItem(i, 2, QTableWidgetItem(p["diagnosis"] or ""))
                tbl.setItem(i, 3, QTableWidgetItem(p["treatment"] or ""))
                tbl.setItem(i, 4, QTableWidgetItem(f"¥{p['total_price']:.2f}"))
                tbl.setItem(i, 5, QTableWidgetItem(p["created_at"] or ""))
            tbl.cellDoubleClicked.connect(lambda r, c: self._show_presc_detail_from_history(tbl.item(r, 0)))
            tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            layout.addWidget(tbl)
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("QPushButton { padding: 6px 20px; background: #7A4C32; color: #FFFEF9; border-radius: 3px; }")
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        dlg.exec()

    def _show_presc_detail_from_history(self, item):
        if item is None:
            return
        presc_no = item.data(Qt.ItemDataRole.UserRole)
        if not presc_no:
            return
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
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
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

    # ── Excel ──
    def _import_excel(self):
        from utils.excel_io import import_patients
        path, _ = QFileDialog.getOpenFileName(self, "导入患者Excel", "", "Excel (*.xlsx)")
        if not path:
            return
        try:
            success, errs = import_patients(path)
            msg = f"成功导入 {success} 条"
            if errs:
                msg += f"\n{len(errs)} 条错误:\n" + "\n".join(errs[:5])
            QMessageBox.information(self, "导入完成", msg)
            self.load_data()
        except Exception as e:
            QMessageBox.warning(self, "导入失败", str(e))

    def _download_template(self):
        from utils.excel_io import generate_patient_template
        path, _ = QFileDialog.getSaveFileName(self, "下载患者导入模板", "患者导入模板.xlsx", "Excel (*.xlsx)")
        if not path:
            return
        try:
            generate_patient_template(path)
            QMessageBox.information(self, "成功", f"模板已保存到：\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "失败", str(e))

    def _export_excel(self):
        from utils.excel_io import export_patients
        from datetime import date
        path, _ = QFileDialog.getSaveFileName(self, "导出患者Excel", f"患者数据_{date.today().isoformat()}.xlsx", "Excel (*.xlsx)")
        if not path:
            return
        try:
            export_patients(path)
            QMessageBox.information(self, "导出成功", f"数据已导出到：\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "导出失败", str(e))


class PatientDialog(QDialog):
    def __init__(self, parent, data=None):
        super().__init__(parent)
        self.setWindowTitle("编辑患者" if data else "新增患者")
        self.setMinimumWidth(450)
        self.setStyleSheet("QDialog { background: #FFFEF9; }")
        self.data = {}

        layout = QFormLayout(self)
        fields = [
            ("visit_date","就诊日期"), ("medical_record_no","病案号"),
            ("name","姓名"), ("phone","电话"), ("age","年龄"),
            ("gender","性别"), ("occupation","职业"),
            ("address","常住地址"), ("condition","症状"),
            ("diagnosis","诊断"), ("treatment","门诊处理"),
        ]
        self.widgets = {}
        for key, label in fields:
            if key == "age":
                w = QSpinBox()
                w.setMaximum(150)
                if data: w.setValue(data.get(key, 0))
            elif key == "gender":
                w = QComboBox()
                w.addItems(["","男","女"])
                if data:
                    w.setCurrentText(data.get(key, ""))
            else:
                w = QLineEdit(data.get(key, "") if data else "")
            w.setStyleSheet("padding: 6px 10px; border: 1px solid #C9B99A; border-radius: 3px; background: #FFFEF9;")
            self.widgets[key] = w
            layout.addRow(QLabel(label), w)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def _save(self):
        self.data = {k: (w.text().strip() if hasattr(w,'text') else w.value() if hasattr(w,'value') else w.currentText()) for k, w in self.widgets.items()}
        if not self.data["name"]:
            QMessageBox.warning(self, "提示", "请输入姓名")
            return
        self.accept()
