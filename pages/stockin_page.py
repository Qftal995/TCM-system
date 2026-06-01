"""Page 3: 药材入库 — 搜索选药商 → 填入库单 → 提交验收"""
from datetime import date, timedelta, datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFrame, QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox,
)
from PyQt6.QtCore import Qt

from database import get_conn
from widgets.searchbox import SearchBox

PAGE_SIZE = 20


class StockinPage(QWidget):
    def __init__(self):
        super().__init__()
        self._supplier_rows = []  # rows from herb search
        self._selected_herb = None  # the exact herb row selected

        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        top = QHBoxLayout()
        top.setContentsMargins(18, 14, 18, 10)
        title = QLabel("药材入库")
        title.setStyleSheet("font-family: KaiTi, SimSun; font-size: 16px; color: #3E2723; letter-spacing: 2px;")
        top.addWidget(title)
        sub = QLabel("搜索药材 → 选择药商 → 提交入库 → 验收更新库存")
        sub.setStyleSheet("font-size: 11px; color: #8D6E63;")
        top.addWidget(sub)
        top.addStretch()
        main.addLayout(top)

        content = QVBoxLayout()
        content.setContentsMargins(18, 0, 18, 18)
        content.setSpacing(10)
        card_style = "QFrame { background: #FFFEF9; border: 1px solid #D7CCC8; border-radius: 5px; }"
        input_style = "padding: 7px 10px; border: 1px solid #C9B99A; border-radius: 3px; background: #FFFEF9; font-size: 12px;"

        # ── Search card ──
        scard = QFrame()
        scard.setStyleSheet(card_style)
        slayout = QHBoxLayout(scard)
        slayout.setContentsMargins(16, 12, 16, 12)
        slayout.addWidget(QLabel("搜索药材："))
        self.herb_search = SearchBox("输入药材名称搜索…", 220)
        self.herb_search.search_triggered.connect(self._on_herb_search)
        self.herb_search.set_search_fn(self._herb_search_fn)
        slayout.addWidget(self.herb_search)
        slayout.addStretch()
        content.addWidget(scard)

        # ── Supplier list card ──
        scard2 = QFrame()
        scard2.setStyleSheet(card_style)
        s2layout = QVBoxLayout(scard2)
        s2layout.setContentsMargins(16, 12, 16, 12)
        s2layout.addWidget(QLabel("选择厂家（点击行选中）"))
        self.supplier_table = QTableWidget()
        self.supplier_table.setColumnCount(7)
        self.supplier_table.setHorizontalHeaderLabels(["序号","品名","编号","厂家","数量(kg)","价格","售价(/g)"])
        self.supplier_table.horizontalHeader().setStyleSheet("QHeaderView::section { background: #5C3322; color: #E8DFD2; padding: 6px; font-size: 11px; border: none; }")
        self.supplier_table.verticalHeader().setVisible(False)
        self.supplier_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.supplier_table.setMaximumHeight(200)
        self.supplier_table.setStyleSheet("QTableWidget { background: #FFFEF9; border: 1px solid #D7CCC8; font-size: 11px; } QTableWidget::item { padding: 4px 6px; }")
        self.supplier_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.supplier_table.itemClicked.connect(self._on_supplier_selected)
        s2layout.addWidget(self.supplier_table)

        self.selected_lbl = QLabel("未选择厂家")
        self.selected_lbl.setStyleSheet("color: #8D6E63; font-size: 12px; padding: 4px 0;")
        s2layout.addWidget(self.selected_lbl)
        content.addWidget(scard2)

        # ── Stock-in form card ──
        fcard = QFrame()
        fcard.setStyleSheet(card_style)
        flayout = QVBoxLayout(fcard)
        flayout.setContentsMargins(16, 12, 16, 12)
        flayout.addWidget(QLabel("入库信息"))

        grid = QGridLayout()
        grid.setSpacing(8)
        self.si_qty = QDoubleSpinBox()
        self.si_qty.setDecimals(1)
        self.si_qty.setMaximum(99999)
        self.si_qty.setValue(10)
        self.si_qty.setStyleSheet(input_style)
        self.si_price = QDoubleSpinBox()
        self.si_price.setDecimals(2)
        self.si_price.setMaximum(999999)
        self.si_price.setValue(0)
        self.si_price.setStyleSheet(input_style)
        self.si_date = QLineEdit(date.today().isoformat())
        self.si_date.setStyleSheet(input_style)
        self.si_shelf = QSpinBox()
        self.si_shelf.setMaximum(9999)
        self.si_shelf.setValue(365)
        self.si_shelf.setStyleSheet(input_style)
        self.si_expiry = QLineEdit()
        self.si_expiry.setStyleSheet(input_style)
        self.si_expiry.setReadOnly(True)
        self.si_approver = QLineEdit("肖锋")
        self.si_approver.setStyleSheet(input_style)

        self.si_shelf.valueChanged.connect(self._calc_expiry)
        self.si_date.textChanged.connect(self._calc_expiry)

        grid.addWidget(QLabel("入库数量(kg)"), 0, 0); grid.addWidget(self.si_qty, 0, 1)
        grid.addWidget(QLabel("进货单价"), 0, 2); grid.addWidget(self.si_price, 0, 3)
        grid.addWidget(QLabel("进货日期"), 1, 0); grid.addWidget(self.si_date, 1, 1)
        grid.addWidget(QLabel("保存时长(天)"), 1, 2); grid.addWidget(self.si_shelf, 1, 3)
        grid.addWidget(QLabel("过期时间"), 2, 0); grid.addWidget(self.si_expiry, 2, 1)
        grid.addWidget(QLabel("验收员"), 2, 2); grid.addWidget(self.si_approver, 2, 3)
        flayout.addLayout(grid)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        submit_btn = QPushButton("提交入库")
        submit_btn.setStyleSheet("QPushButton { padding: 8px 20px; background: #7A4C32; color: #FFFEF9; border: none; border-radius: 3px; font-size: 13px; letter-spacing: 1px; } QPushButton:hover { background: #5C3322; }")
        submit_btn.clicked.connect(self._submit)
        btn_row.addWidget(submit_btn)
        flayout.addLayout(btn_row)
        content.addWidget(fcard)

        # ── Pending approvals card ──
        acard = QFrame()
        acard.setStyleSheet(card_style)
        alayout = QVBoxLayout(acard)
        alayout.setContentsMargins(16, 12, 16, 12)
        hdr = QHBoxLayout()
        hdr.addWidget(QLabel("待验收记录"))
        hdr.addStretch()
        refresh_btn = QPushButton("刷新")
        refresh_btn.setStyleSheet("QPushButton { padding: 4px 12px; border: 1px solid #BCAAA4; border-radius: 3px; background: transparent; color: #5D4037; font-size: 11px; } QPushButton:hover { background: #F5F0E8; }")
        refresh_btn.clicked.connect(self._load_pending)
        hdr.addWidget(refresh_btn)
        alayout.addLayout(hdr)

        self.pending_table = QTableWidget()
        self.pending_table.setColumnCount(8)
        self.pending_table.setHorizontalHeaderLabels(["序号","品名","厂家","数量(kg)","价格","入库日期","验收员","操作"])
        self.pending_table.horizontalHeader().setStyleSheet("QHeaderView::section { background: #5C3322; color: #E8DFD2; padding: 6px; font-size: 11px; border: none; }")
        self.pending_table.verticalHeader().setVisible(False)
        self.pending_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.pending_table.setMaximumHeight(220)
        self.pending_table.setStyleSheet("QTableWidget { background: #FFFEF9; border: 1px solid #D7CCC8; font-size: 11px; } QTableWidget::item { padding: 4px 6px; }")
        self.pending_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        alayout.addWidget(self.pending_table)
        content.addWidget(acard)

        main.addLayout(content, 1)
        self._calc_expiry()
        self._load_pending()

    def _herb_search_fn(self, text):
        conn = get_conn()
        cur = conn.cursor()
        kw = f"%{text}%"
        cur.execute("SELECT DISTINCT name FROM herbs WHERE name LIKE ? OR alias LIKE ? OR name2 LIKE ? LIMIT 8", [kw, kw, kw])
        results = [row["name"] for row in cur.fetchall()]
        conn.close()
        return results

    def _on_herb_search(self, kw):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM herbs WHERE name=? ORDER BY supplier", [kw])
        self._supplier_rows = cur.fetchall()
        conn.close()
        self._selected_herb = None
        self.selected_lbl.setText("未选择药商")
        self._render_supplier_table()

    def _render_supplier_table(self):
        rows = self._supplier_rows
        self.supplier_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.supplier_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.supplier_table.setItem(i, 1, QTableWidgetItem(r["name"]))
            self.supplier_table.setItem(i, 2, QTableWidgetItem(r["alias"] or ""))
            self.supplier_table.setItem(i, 3, QTableWidgetItem(r["supplier"]))
            self.supplier_table.setItem(i, 4, QTableWidgetItem(f"{r['stock_qty']:.2f}"))
            self.supplier_table.setItem(i, 5, QTableWidgetItem(f"¥{r['purchase_price']:.2f}"))
            self.supplier_table.setItem(i, 6, QTableWidgetItem(f"¥{r['sell_price']:.2f}"))

    def _on_supplier_selected(self, item):
        row = item.row()
        if 0 <= row < len(self._supplier_rows):
            r = self._supplier_rows[row]
            self._selected_herb = r
            self.selected_lbl.setText(
                f"已选择：{r['name']}（{r['supplier']}） | "
                f"当前库存 {r['stock_qty']:.2f}kg | 价格 ¥{r['purchase_price']:.2f} | "
                f"售价 ¥{r['sell_price']:.2f}/g"
            )
            self.si_price.setValue(r["purchase_price"])
            self.si_shelf.setValue(r["shelf_life_days"])
            self._calc_expiry()

    def _calc_expiry(self):
        try:
            d = date.fromisoformat(self.si_date.text().strip())
            days = self.si_shelf.value()
            exp = d + timedelta(days=days)
            self.si_expiry.setText(exp.isoformat())
        except Exception:
            self.si_expiry.setText("")

    def _submit(self):
        if not self._selected_herb:
            QMessageBox.warning(self, "提示", "请先搜索并选择药材药商")
            return
        qty = self.si_qty.value()
        if qty <= 0:
            QMessageBox.warning(self, "提示", "请输入有效入库数量")
            return
        price = self.si_price.value()
        if price <= 0:
            QMessageBox.warning(self, "提示", "请输入有效进货单价")
            return

        conn = get_conn()
        cur = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        cur.execute(
            "INSERT INTO stock_in_records(herb_id,herb_name,supplier,qty,purchase_price,purchase_date,shelf_life_days,expiry_date,approver,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            [
                self._selected_herb["id"],
                self._selected_herb["name"],
                self._selected_herb["supplier"],
                qty, price,
                self.si_date.text().strip(),
                self.si_shelf.value(),
                self.si_expiry.text().strip(),
                self.si_approver.text().strip() or "待验收",
                "pending", now
            ]
        )
        conn.commit()
        conn.close()
        QMessageBox.information(self, "提示", "入库单已提交，等待验收")
        self._load_pending()

    def _load_pending(self):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM stock_in_records WHERE status='pending' ORDER BY created_at DESC")
        rows = cur.fetchall()
        conn.close()

        self.pending_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.pending_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.pending_table.setItem(i, 1, QTableWidgetItem(r["herb_name"]))
            self.pending_table.setItem(i, 2, QTableWidgetItem(r["supplier"]))
            self.pending_table.setItem(i, 3, QTableWidgetItem(f"{r['qty']:.2f}"))
            self.pending_table.setItem(i, 4, QTableWidgetItem(f"¥{r['purchase_price']:.2f}"))
            self.pending_table.setItem(i, 5, QTableWidgetItem(r["purchase_date"]))
            self.pending_table.setItem(i, 6, QTableWidgetItem(r["approver"]))
            # Action buttons
            act_w = QWidget()
            act = QHBoxLayout(act_w)
            act.setContentsMargins(0, 0, 0, 0)
            rid = r["id"]
            approve_btn = QPushButton("验收通过")
            approve_btn.setStyleSheet("QPushButton { padding: 2px 8px; border: 1px solid #5C8A4C; border-radius: 3px; background: transparent; color: #5C8A4C; font-size: 10px; } QPushButton:hover { background: #EDF5E8; }")
            approve_btn.clicked.connect(lambda checked, x=rid: self._approve(x))
            act.addWidget(approve_btn)
            reject_btn = QPushButton("驳回")
            reject_btn.setStyleSheet("QPushButton { padding: 2px 8px; border: 1px solid #D4645C; border-radius: 3px; background: transparent; color: #D4645C; font-size: 10px; } QPushButton:hover { background: #FDF0EF; }")
            reject_btn.clicked.connect(lambda checked, x=rid: self._reject(x))
            act.addWidget(reject_btn)
            self.pending_table.setCellWidget(i, 7, act_w)

    def _approve(self, rid):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM stock_in_records WHERE id=?", [rid])
        rec = cur.fetchone()
        if not rec:
            conn.close()
            return
        # Update herb inventory
        cur.execute(
            "UPDATE herbs SET stock_qty=stock_qty+?, purchase_price=?, purchase_date=?, shelf_life_days=?, expiry_date=?, updated_at=date('now') WHERE id=?",
            [rec["qty"], rec["purchase_price"], rec["purchase_date"],
             rec["shelf_life_days"], rec["expiry_date"], rec["herb_id"]]
        )
        cur.execute("UPDATE stock_in_records SET status='approved' WHERE id=?", [rid])
        conn.commit()
        conn.close()
        self._load_pending()
        QMessageBox.information(self, "验收通过", f"{rec['herb_name']}（{rec['supplier']}）已入库 {rec['qty']:.2f}kg，库存已更新")

    def _reject(self, rid):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("UPDATE stock_in_records SET status='rejected' WHERE id=?", [rid])
        conn.commit()
        conn.close()
        self._load_pending()
        QMessageBox.information(self, "驳回", "入库单已驳回")
