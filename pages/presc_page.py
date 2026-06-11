"""Page 1: 患者登记与开方"""
from datetime import date, datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFrame, QListWidget,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from database import get_conn
from widgets.searchbox import SearchBox
from widgets.presc_preview import PrescPreview


class PrescPage(QWidget):
    def __init__(self):
        super().__init__()
        self.presc_items = []  # [(herb_id, name, grams, unit_price)]
        self._selected_formula_id = 0
        self._formula_cache = {}  # display_name -> formula_id
        self._building = False
        self._service_fee = 0
        self._load_service_fee()

        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # Top bar
        top = QHBoxLayout()
        top.setContentsMargins(18, 14, 18, 10)
        title = QLabel("患者登记与开方")
        title.setStyleSheet("font-family: KaiTi, SimSun; font-size: 16px; color: #3E2723; letter-spacing: 2px;")
        top.addWidget(title)
        sub = QLabel("新建处方 · 选药计价 · 自动扣库")
        sub.setStyleSheet("font-size: 11px; color: #8D6E63;")
        top.addWidget(sub)
        top.addStretch()
        main.addLayout(top)

        content = QVBoxLayout()
        content.setContentsMargins(18, 0, 18, 18)
        content.setSpacing(10)

        # ── Patient info card ──
        card_style = "QFrame { background: #FFFEF9; border: 1px solid #D7CCC8; border-radius: 5px; }"
        self._make_card_title = lambda t: QLabel(f"<b>{t}</b>") or None

        pat_card = QFrame()
        pat_card.setStyleSheet(card_style)
        pat_layout = QVBoxLayout(pat_card)
        pat_layout.setContentsMargins(16, 12, 16, 12)
        pat_layout.addWidget(QLabel("患者信息"))
        grid = QGridLayout()
        grid.setSpacing(8)
        self.p_name = QLineEdit()
        self.p_name.setPlaceholderText("患者姓名 *（输入时自动匹配）")

        # Patient name autocomplete — embedded child, not a Popup
        self._pat_dropdown = QListWidget(self)
        self._pat_dropdown.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._pat_dropdown.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._pat_dropdown.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._pat_dropdown.hide()
        self._pat_dropdown.setStyleSheet("""
            QListWidget {
                border: 1px solid #C9B99A; border-top: none;
                background: #FFFEF9; font-size: 12px; outline: none;
            }
            QListWidget::item {
                padding: 7px 10px; color: #5D4037; border-bottom: 1px solid #F0EBE3;
            }
            QListWidget::item:hover { background: #F5F0E8; color: #3E2723; }
        """)
        self._pat_dropdown.itemClicked.connect(self._on_patient_select)
        self._pat_timer = QTimer()
        self._pat_timer.setSingleShot(True)
        self._pat_timer.setInterval(200)
        self._pat_timer.timeout.connect(self._do_patient_search)
        self.p_name.textChanged.connect(lambda t: self._pat_timer.start())
        self.p_medical_no = QLineEdit()
        self.p_medical_no.setPlaceholderText("病案号")
        self.p_phone = QLineEdit()
        self.p_phone.setPlaceholderText("手机号")
        self.p_age = QLineEdit()
        self.p_age.setPlaceholderText("年龄")
        self.p_gender = QComboBox()
        self.p_gender.addItems(["","男","女"])
        self.p_occupation = QLineEdit()
        self.p_occupation.setPlaceholderText("职业")
        self.p_address = QLineEdit()
        self.p_address.setPlaceholderText("常住地址")
        self.p_condition = QLineEdit()
        self.p_condition.setPlaceholderText("症状 *")
        self.p_diagnosis = QLineEdit()
        self.p_diagnosis.setPlaceholderText("诊断")
        self.p_treatment = QLineEdit()
        self.p_treatment.setPlaceholderText("门诊处理")

        input_style = "padding: 7px 10px; border: 1px solid #C9B99A; border-radius: 3px; background: #FFFEF9; font-size: 12px; color: #3E2723;"
        for w in [self.p_name, self.p_medical_no, self.p_phone, self.p_age, self.p_occupation, self.p_address, self.p_condition, self.p_diagnosis, self.p_treatment]:
            w.setStyleSheet(input_style)
        self.p_gender.setStyleSheet(
            "QComboBox { padding: 7px 10px; border: 1px solid #C9B99A; border-radius: 3px; background: #FFFEF9; font-size: 12px; color: #3E2723; }"
            "QComboBox:hover { border-color: #7A4C32; }"
            "QComboBox QAbstractItemView { background: #FFFEF9; border: 1px solid #C9B99A; color: #3E2723; font-size: 12px; selection-background-color: #F5F0E8; selection-color: #3E2723; padding: 4px; outline: none; }"
            "QComboBox::drop-down { border: none; width: 20px; }"
            "QComboBox::down-arrow { image: none; border: none; }"
        )

        grid.addWidget(QLabel("姓名 *"),0,0); grid.addWidget(self.p_name,0,1,1,3)
        grid.addWidget(QLabel("病案号"),0,4); grid.addWidget(self.p_medical_no,0,5)
        grid.addWidget(QLabel("年龄"),1,0); grid.addWidget(self.p_age,1,1)
        grid.addWidget(QLabel("性别"),1,2); grid.addWidget(self.p_gender,1,3)
        grid.addWidget(QLabel("职业"),1,4); grid.addWidget(self.p_occupation,1,5)
        grid.addWidget(QLabel("电话"),2,0); grid.addWidget(self.p_phone,2,1,1,3)
        grid.addWidget(QLabel("常住地址"),2,4); grid.addWidget(self.p_address,2,5)
        grid.addWidget(QLabel("症状 *"),3,0); grid.addWidget(self.p_condition,3,1,1,2)
        grid.addWidget(QLabel("诊断"),3,3); grid.addWidget(self.p_diagnosis,3,4,1,2)
        grid.addWidget(QLabel("门诊处理"),4,0); grid.addWidget(self.p_treatment,4,1,1,5)
        pat_layout.addLayout(grid)
        content.addWidget(pat_card)

        # ── Prescription builder card ──
        presc_card = QFrame()
        presc_card.setStyleSheet(card_style)
        presc_layout = QVBoxLayout(presc_card)
        presc_layout.setContentsMargins(16, 12, 16, 12)
        presc_layout.addWidget(QLabel("开方明细"))

        # Preview
        self.preview = PrescPreview()
        self.preview.herb_clicked.connect(self._on_preview_herb_clicked)
        presc_layout.addWidget(self.preview)

        # Controls
        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)
        ctrl.addWidget(QLabel("快速选方剂："))
        self.formula_search = SearchBox("搜方剂名称…", 200)
        self.formula_search.set_search_fn(self._formula_search_fn)
        ctrl.addWidget(self.formula_search)
        apply_btn = QPushButton("套用")
        apply_btn.setStyleSheet("QPushButton { padding: 6px 12px; border: 1px solid #BCAAA4; border-radius: 3px; background: transparent; color: #5D4037; font-size: 11px; } QPushButton:hover { background: #F5F0E8; }")
        apply_btn.clicked.connect(self._apply_formula)
        ctrl.addWidget(apply_btn)
        ctrl.addWidget(QLabel("|"))
        ctrl.addWidget(QLabel("手动添加："))
        self.herb_search = SearchBox("搜药材…", 260)
        self.herb_search.search_triggered.connect(self._on_herb_select)
        self.herb_search.set_search_fn(self._herb_search_fn)
        ctrl.addWidget(self.herb_search)
        self.gram_input = QDoubleSpinBox()
        self.gram_input.setDecimals(1)
        self.gram_input.setMaximum(99999)
        self.gram_input.setValue(9)
        self.gram_input.setStyleSheet(input_style + "max-width: 70px;")
        ctrl.addWidget(self.gram_input)
        add_btn = QPushButton("+")
        add_btn.setStyleSheet("QPushButton { padding: 6px 12px; background: #7A4C32; color: #FFFEF9; border-radius: 3px; font-size: 14px; } QPushButton:hover { background: #5C3322; }")
        add_btn.clicked.connect(self._add_herb_item)
        ctrl.addWidget(add_btn)
        ctrl.addStretch()
        presc_layout.addLayout(ctrl)

        # Detail table
        self.detail_table = QTableWidget()
        self.detail_table.setColumnCount(4)
        self.detail_table.setHorizontalHeaderLabels(["药材","克数(g)","库存余量","操作"])
        self.detail_table.horizontalHeader().setStyleSheet("QHeaderView::section { background: #5C3322; color: #E8DFD2; padding: 6px; font-size: 11px; border: none; }")
        self.detail_table.verticalHeader().setVisible(False)
        self.detail_table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)
        self.detail_table.cellChanged.connect(self._on_cell_changed)
        self.detail_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.detail_table.verticalHeader().setDefaultSectionSize(30)
        self.detail_table.setStyleSheet("QTableWidget { background: #FFFEF9; border: 1px solid #D7CCC8; font-size: 11px; } QTableWidget::item { padding: 3px 6px; }")
        presc_layout.addWidget(self.detail_table)

        # Total + actions
        bottom = QHBoxLayout()
        self.total_lbl = QLabel("处方合计：¥0.00")
        self.total_lbl.setStyleSheet("font-family: KaiTi, SimSun; font-size: 17px; color: #3E2723; letter-spacing: 1px;")
        bottom.addWidget(self.total_lbl)
        bottom.addStretch()
        bottom.addWidget(QLabel("服数："))
        self.doses = QSpinBox()
        self.doses.setMinimum(1)
        self.doses.setMaximum(999)
        self.doses.setValue(7)
        self.doses.setStyleSheet("QSpinBox { padding: 5px 8px; border: 1px solid #C9B99A; border-radius: 3px; background: #FFFEF9; font-size: 13px; color: #3E2723; max-width: 60px; }")
        self.doses.valueChanged.connect(lambda v: self._refresh())
        bottom.addWidget(self.doses)
        bottom.addWidget(QLabel("剂"))
        bottom.addSpacing(12)
        self.presc_no_lbl = QLabel()
        self.presc_no_lbl.setStyleSheet("font-size: 12px; color: #8D6E63;")
        bottom.addWidget(self.presc_no_lbl)
        bottom.addSpacing(12)
        reset_btn = QPushButton("重置")
        reset_btn.setStyleSheet("QPushButton { padding: 6px 14px; border: 1px solid #BCAAA4; border-radius: 3px; background: transparent; color: #5D4037; font-size: 11px; } QPushButton:hover { background: #F5F0E8; }")
        reset_btn.clicked.connect(self._safely_reset)
        bottom.addWidget(reset_btn)
        self.save_btn = QPushButton("保存开方")
        self.save_btn.setStyleSheet("QPushButton { padding: 8px 20px; background: #7A4C32; color: #FFFEF9; border: none; border-radius: 3px; font-size: 13px; letter-spacing: 1px; } QPushButton:hover { background: #5C3322; }")
        self.save_btn.clicked.connect(self._save)
        bottom.addWidget(self.save_btn)
        presc_layout.addLayout(bottom)

        content.addWidget(presc_card)
        main.addLayout(content, 1)

        self._load_formulas()
        self._gen_presc_no()
        self._refresh()

    def _do_patient_search(self):
        text = self.p_name.text().strip()
        if not text or len(text) < 1:
            self._pat_dropdown.hide()
            return
        conn = get_conn()
        cur = conn.cursor()
        kw = f"%{text}%"
        cur.execute("SELECT name, phone, age, gender, occupation, address, condition, monthly_no, medical_record_no FROM patients WHERE name LIKE ? OR phone LIKE ? OR condition LIKE ? ORDER BY visit_date DESC, id DESC LIMIT 8", [kw, kw, kw])
        rows = cur.fetchall()
        conn.close()
        if not rows:
            self._pat_dropdown.hide()
            return
        self._pat_dropdown.clear()
        for row in rows:
            phone_tail = row['phone'][-4:] if row['phone'] and len(row['phone']) >= 4 else row['phone'] or ''
            self._pat_dropdown.addItem(f"{row['name']}  ***{phone_tail}  {row['condition'] or row['address'] or ''}")
        # Position dropdown — reparent to window to avoid clipping
        top = self.window()
        if top and self._pat_dropdown.parent() != top:
            self._pat_dropdown.setParent(top)
            self._pat_dropdown.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        pos = self.p_name.mapTo(top or self, self.p_name.rect().bottomLeft())
        self._pat_dropdown.setGeometry(pos.x(), pos.y(), self.p_name.width() + 160, min(200, self._pat_dropdown.sizeHint().height()))
        self._pat_dropdown.raise_()
        self._pat_dropdown.show()
        self.p_name.setFocus()

    def _on_patient_select(self, item):
        display = item.text()
        name = display.split("  ")[0].strip()
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM patients WHERE name=? ORDER BY visit_date DESC, id DESC LIMIT 1", [name])
        pat = cur.fetchone()
        if pat:
            self.p_name.setText(pat["name"] or "")
            self.p_medical_no.setText(pat["medical_record_no"] or "")
            self.p_phone.setText(pat["phone"] or "")
            self.p_age.setText(str(pat["age"] or ""))
            idx = self.p_gender.findText(pat["gender"] or "")
            if idx >= 0:
                self.p_gender.setCurrentIndex(idx)
            self.p_occupation.setText(pat["occupation"] or "")
            self.p_address.setText(pat["address"] or "")
            self.p_condition.setText(pat["condition"] or "")
            self.p_diagnosis.setText(pat["diagnosis"] or "")
            self.p_treatment.setText(pat["treatment"] or "")
            # Load last prescription items
            cur.execute("""
                SELECT pi.herb_id, pi.herb_name, pi.actual_grams, pi.unit_price
                FROM prescriptions p
                JOIN prescription_items pi ON pi.prescription_id = p.id
                WHERE p.patient_id IN (SELECT id FROM patients WHERE name=? ORDER BY visit_date DESC, id DESC LIMIT 1)
                ORDER BY p.created_at DESC, pi.id
            """, [name])
            last_items = cur.fetchall()
            if last_items:
                self.presc_items = [[r["herb_id"], r["herb_name"], r["actual_grams"], r["unit_price"]] for r in last_items]
                self._refresh()
        conn.close()
        self._pat_dropdown.hide()

    def _load_formulas(self):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM formulas ORDER BY id")
        self._formula_cache = {row["name"]: row["id"] for row in cur.fetchall()}
        conn.close()

    def _formula_search_fn(self, text):
        conn = get_conn()
        cur = conn.cursor()
        kw = f"%{text}%"
        cur.execute("SELECT id, name FROM formulas WHERE name LIKE ? ORDER BY id LIMIT 8", [kw])
        results = cur.fetchall()
        conn.close()
        display_names = []
        for row in results:
            display_names.append(row["name"])
            self._formula_cache[row["name"]] = row["id"]
        return display_names

    def _herb_search_fn(self, text):
        conn = get_conn()
        cur = conn.cursor()
        kw = f"%{text}%"
        cur.execute("SELECT name, supplier FROM herbs WHERE name LIKE ? OR alias LIKE ? OR name2 LIKE ? ORDER BY name, supplier LIMIT 8", [kw, kw, kw])
        results = [f"{row['name']} — {row['supplier']}" if row['supplier'] else row['name'] for row in cur.fetchall()]
        conn.close()
        return results

    def _on_herb_select(self, display_text):
        pass  # We use the name from search for adding

    def _add_herb_item(self):
        txt = self.herb_search.text()
        if not txt:
            QMessageBox.warning(self, "提示", "请先搜索药材")
            return
        # Parse "药名 — 药商" or "药名"
        if " — " in txt:
            name, supplier = txt.split(" — ", 1)
        else:
            name, supplier = txt.strip(), ""
        grams = self.gram_input.value()
        if grams <= 0:
            QMessageBox.warning(self, "提示", "请输入有效克数")
            return

        conn = get_conn()
        cur = conn.cursor()
        if supplier:
            cur.execute("SELECT * FROM herbs WHERE name=? AND supplier=? LIMIT 1", [name.strip(), supplier.strip()])
        else:
            cur.execute("SELECT * FROM herbs WHERE name=? LIMIT 1", [name.strip()])
        herb = cur.fetchone()
        conn.close()
        if not herb:
            QMessageBox.warning(self, "提示", "未找到该药材")
            return
        if herb["stock_qty"] <= 0:
            QMessageBox.warning(self, "提示", "该药材已无库存")
            return
        if herb["stock_qty"] * 1000 < grams:
            QMessageBox.warning(self, "提示", f"库存不足（当前{herb['stock_qty']:.2f}kg，需要{grams}g）")
            return

        # Check if already in list
        for item in self.presc_items:
            if item[0] == herb["id"]:
                item[2] += grams
                self._refresh()
                return
        self.presc_items.append([herb["id"], herb["name"], grams, herb["sell_price"]])
        self._refresh()

    def _apply_formula(self):
        name = self.formula_search.text()
        if not name:
            QMessageBox.warning(self, "提示", "请先搜索并选择方剂")
            return
        fid = self._formula_cache.get(name, 0)
        if not fid:
            QMessageBox.warning(self, "提示", "未找到该方剂，请从下拉列表中选择")
            return
        if self.presc_items:
            ret = QMessageBox.question(self, "确认套用", f"当前已添加 {len(self.presc_items)} 味药材，套用方剂将清空列表，是否继续？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if ret != QMessageBox.StandardButton.Yes:
                return
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT fi.herb_id, h.name, fi.default_grams, h.sell_price FROM formula_items fi JOIN herbs h ON fi.herb_id=h.id WHERE fi.formula_id=?", [fid])
        items = cur.fetchall()
        conn.close()
        if not items: return
        self.presc_items = [[r["herb_id"], r["name"], r["default_grams"], r["sell_price"]] for r in items]
        self._refresh()
        QMessageBox.information(self, "提示", f"已套用方剂：{name}")

    def _refresh(self):
        self._building = True
        total = 0
        self.detail_table.clearSpans()
        self.detail_table.setRowCount(0)
        self.detail_table.setRowCount(len(self.presc_items))

        conn = get_conn()
        cur = conn.cursor()
        for i, item in enumerate(self.presc_items):
            hid, name, grams, price = item
            subtotal = grams * price
            total += subtotal
            cur.execute("SELECT stock_qty FROM herbs WHERE id=?", [hid])
            row = cur.fetchone()
            stock = row["stock_qty"] if row else 0

            name_item = QTableWidgetItem(name)
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.detail_table.setItem(i, 0, name_item)
            gram_w = QWidget()
            gram_w.setStyleSheet("background: transparent;")
            gram_layout = QHBoxLayout(gram_w)
            gram_layout.setContentsMargins(0, 0, 0, 0)
            gram_layout.setSpacing(1)
            gram_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            gram_spin = QDoubleSpinBox()
            gram_spin.setDecimals(1)
            gram_spin.setMaximum(99999)
            gram_spin.setValue(grams)
            gram_spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
            gram_spin.setStyleSheet("QDoubleSpinBox { border: none; background: transparent; color: #3E2723; font-size: 11px; padding: 0px; }")
            gram_spin.setAlignment(Qt.AlignmentFlag.AlignRight)
            gram_spin.valueChanged.connect(lambda v, idx=i: self._on_gram_changed(idx, v))
            gram_layout.addWidget(gram_spin)
            g_lbl = QLabel("g")
            g_lbl.setStyleSheet("color: #3E2723; font-size: 11px; background: transparent; padding: 0px;")
            gram_layout.addWidget(g_lbl)
            self.detail_table.setCellWidget(i, 1, gram_w)
            stock_item = QTableWidgetItem(f"{stock:.2f}kg")
            stock_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if stock < 1:
                stock_item.setForeground(Qt.GlobalColor.red)
            self.detail_table.setItem(i, 2, stock_item)

            del_w = QWidget()
            del_layout = QHBoxLayout(del_w)
            del_layout.setContentsMargins(0, 0, 0, 0)
            del_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            del_btn = QPushButton("删除")
            del_btn.setStyleSheet("QPushButton { padding: 2px 8px; border: 1px solid #D4645C; border-radius: 3px; background: transparent; color: #D4645C; font-size: 10px; }")
            del_btn.clicked.connect(lambda checked, idx=i: self._remove_item(idx))
            del_layout.addWidget(del_btn)
            self.detail_table.setCellWidget(i, 3, del_w)
        conn.close()

        if len(self.presc_items) == 0:
            self.detail_table.setRowCount(1)
            empty_item = QTableWidgetItem("请添加药材")
            empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.detail_table.setItem(0, 0, empty_item)
            self.detail_table.setSpan(0, 0, 1, 4)
            self.total_lbl.setText("处方合计：¥0.00")
        else:
            doses = self.doses.value()
            total = total * doses + self._service_fee
            self.total_lbl.setText(f"处方合计：¥{total:.2f}（{len(self.presc_items)} 味药 × {doses} 剂）")
        preview_data = [(it[1], it[2], it[3]) for it in self.presc_items]
        self.preview.set_items(preview_data)
        self._building = False

    def _on_gram_changed(self, idx, val):
        if self._building or idx >= len(self.presc_items):
            return
        if val > 0 and abs(self.presc_items[idx][2] - val) > 0.01:
            self.presc_items[idx][2] = val
            self._refresh()

    def _on_cell_changed(self, row, col):
        if self._building or row >= len(self.presc_items):
            return
        item = self.presc_items[row]
        txt = self.detail_table.item(row, col)
        if txt is None:
            return
        val = txt.text().strip()

        if col == 0:  # herb name changed
            # Search for the new herb name
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT * FROM herbs WHERE name=? LIMIT 1", [val])
            herb = cur.fetchone()
            conn.close()
            if herb:
                item[0] = herb["id"]
                item[1] = herb["name"]
                item[3] = herb["sell_price"]
            else:
                QMessageBox.warning(self, "提示", f"未找到药材「{val}」")
        elif col == 1:  # grams changed
            try:
                g = float(val.replace("g", "").strip())
                if g <= 0:
                    raise ValueError
                item[2] = g
            except ValueError:
                QMessageBox.warning(self, "提示", "请输入有效克数")

        self._refresh()

    def _remove_item(self, idx):
        if 0 <= idx < len(self.presc_items):
            self.presc_items.pop(idx)
            self._refresh()

    def _on_preview_herb_clicked(self, idx):
        if idx < 0 or idx >= len(self.presc_items):
            return
        name = self.presc_items[idx][1]
        msg = QMessageBox(self)
        msg.setWindowTitle("操作")
        msg.setText(f"药材「{name}」")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.button(QMessageBox.StandardButton.Yes).setText("删除")
        msg.button(QMessageBox.StandardButton.No).setText("返回")
        if msg.exec() == QMessageBox.StandardButton.Yes:
            self._remove_item(idx)

    def _safely_reset(self):
        self._pat_timer.stop()
        self._pat_dropdown.hide()
        self.presc_items = []
        self.p_name.clear()
        self.p_medical_no.clear()
        self.p_phone.clear()
        self.p_age.clear()
        self.p_gender.setCurrentIndex(0)
        self.p_occupation.clear()
        self.p_address.clear()
        self.p_condition.clear()
        self.p_diagnosis.clear()
        self.p_treatment.clear()
        self.formula_search.setText("")
        self.herb_search.setText("")
        self.doses.setValue(7)
        self._load_service_fee()
        self._gen_presc_no()
        self._refresh()

    def _gen_presc_no(self):
        ds = date.today().strftime("%Y%m%d")
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as c FROM prescriptions WHERE prescription_no LIKE ?", [f"CF-{ds}-%"])
        count = cur.fetchone()["c"] + 1
        conn.close()
        self.presc_no_lbl.setText(f"编号：CF-{ds}-{count:03d}")

    def _load_service_fee(self):
        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT value FROM settings WHERE key='service_fee'")
            row = cur.fetchone()
            conn.close()
            if row:
                self._service_fee = float(row["value"])
        except Exception:
            self._service_fee = 50

    def _save(self):
        # Stop all timers to prevent interference during save
        self._pat_timer.stop()
        self._pat_dropdown.hide()

        name = self.p_name.text().strip()
        condition = self.p_condition.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "请输入患者姓名")
            return
        if not condition:
            QMessageBox.warning(self, "提示", "请输入症状")
            return
        if not self.presc_items:
            QMessageBox.warning(self, "提示", "请添加至少一味药材")
            return

        herb_subtotal = sum(it[2] * it[3] for it in self.presc_items)
        doses = self.doses.value()
        total = herb_subtotal * doses + self._service_fee
        presc_no = self.presc_no_lbl.text().replace("编号：", "")
        diagnosis = self.p_diagnosis.text().strip()
        treatment = self.p_treatment.text().strip()
        ret = QMessageBox.question(self, "确认开方",
            f"处方编号：{presc_no}\n"
            f"患者：{name}\n"
            f"药材：{len(self.presc_items)} 味\n"
            f"¥{herb_subtotal:.2f} × {doses} 剂 + ¥{self._service_fee:.0f} = ¥{total:.2f}\n\n"
            f"确认保存并扣减库存？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if ret != QMessageBox.StandardButton.Yes:
            return

        conn = None
        try:
            conn = get_conn()
            cur = conn.cursor()

            # 一次性检查所有药材库存，收集不足项
            shortage = []
            for item in self.presc_items:
                hid, hname, grams, price = item
                cur.execute("SELECT stock_qty FROM herbs WHERE id=?", [hid])
                row = cur.fetchone()
                need_kg = grams * doses / 1000
                stock_kg = row['stock_qty'] if row else 0
                if stock_kg < need_kg:
                    need_g = grams * doses
                    shortage.append(f"「{hname}」库存 {stock_kg*1000:.1f}g，需要 {need_g:.1f}g（{grams}g×{doses}剂）")
            if shortage:
                QMessageBox.warning(self, "库存不足", "以下药材库存不足，请更换：\n\n" + "\n".join(shortage))
                return

            phone = self.p_phone.text().strip()
            age = int(self.p_age.text() or 0)
            gender = self.p_gender.currentText()
            occupation = self.p_occupation.text().strip()
            address = self.p_address.text().strip()
            medical_no = self.p_medical_no.text().strip()
            today_str = date.today().isoformat()
            visit_month = today_str[:7]
            cur.execute("SELECT COALESCE(MAX(CAST(monthly_no AS INTEGER)), 0) + 1 FROM patients WHERE substr(visit_date,1,7)=?", [visit_month])
            monthly_no = str(cur.fetchone()[0]).zfill(2)
            cur.execute("INSERT INTO patients(name,phone,age,gender,occupation,address,condition,monthly_no,medical_record_no,diagnosis,treatment,visit_date,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,date('now'))",
                        [name, phone, age, gender, occupation, address, condition, monthly_no, medical_no, diagnosis, treatment, today_str])
            pid = cur.lastrowid

            for item in self.presc_items:
                cur.execute("UPDATE herbs SET stock_qty = MAX(0, stock_qty - ?) WHERE id=?", [item[2] * doses / 1000, item[0]])

            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            cur.execute("INSERT INTO prescriptions(prescription_no,patient_id,formula_name,diagnosis,treatment,total_price,created_at,doses) VALUES(?,?,?,?,?,?,?,?)",
                        [presc_no, pid, self.formula_search.text(), diagnosis, treatment, round(total, 2), now, doses])
            presc_id = cur.lastrowid
            for item in self.presc_items:
                cur.execute("INSERT INTO prescription_items(prescription_id,herb_id,herb_name,actual_grams,unit_price) VALUES(?,?,?,?,?)",
                            [presc_id, item[0], item[1], item[2], item[3]])

            conn.commit()
            QMessageBox.information(self, "开方成功", f"{presc_no}\n合计 ¥{total:.2f}\n已自动扣减库存")
            if conn:
                conn.close()
            self._safely_reset()
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"开方过程中出现错误：\n{str(e)}")
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
                conn.close()
