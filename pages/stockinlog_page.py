"""Page 4: 入库记录"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
)
from PyQt6.QtCore import Qt

from database import get_conn
from widgets.paginator import Paginator

PAGE_SIZE = 28


class StockinlogPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        top = QHBoxLayout()
        top.setContentsMargins(18, 14, 18, 10)
        title = QLabel("入库记录")
        title.setStyleSheet("font-family: KaiTi, SimSun; font-size: 16px; color: #3E2723; letter-spacing: 2px;")
        top.addWidget(title)
        top.addStretch()
        self.count_lbl = QLabel()
        self.count_lbl.setStyleSheet("font-size: 11px; color: #8D6E63;")
        top.addWidget(self.count_lbl)
        layout.addLayout(top)

        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "序号","入库编号","品名","厂家","数量(kg)","价格","合计",
            "进货日期","效期","验收员","状态"
        ])
        self.table.horizontalHeader().setStyleSheet(
            "QHeaderView::section { background: #5C3322; color: #E8DFD2; padding: 8px; font-size: 11px; border: none; }"
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget { background: #FFFEF9; border: 1px solid #D7CCC8; font-size: 12px; gridline-color: rgba(188,170,164,0.2); }
            QTableWidget::item { padding: 6px 8px; color: #3E2723; }
            QTableWidget::item:alternate { background: rgba(232,223,210,0.25); }
        """)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)

        self.paginator = Paginator(PAGE_SIZE)
        self.paginator.page_changed.connect(lambda p: self.load_data())
        layout.addWidget(self.paginator)

        self.load_data()

    def load_data(self):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as c FROM stock_in_records")
        total = cur.fetchone()["c"]
        self.paginator.set_data(total)
        offset = (self.paginator.current_page - 1) * PAGE_SIZE
        cur.execute(
            "SELECT * FROM stock_in_records ORDER BY created_at DESC LIMIT ? OFFSET ?",
            [PAGE_SIZE, offset]
        )
        rows = cur.fetchall()
        conn.close()

        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(offset + i + 1)))
            self.table.setItem(i, 1, QTableWidgetItem(f"SI-{r['id']:04d}"))
            self.table.setItem(i, 2, QTableWidgetItem(r["herb_name"]))
            self.table.setItem(i, 3, QTableWidgetItem(r["supplier"]))
            self.table.setItem(i, 4, QTableWidgetItem(f"{r['qty']:.2f}"))
            self.table.setItem(i, 5, QTableWidgetItem(f"¥{r['purchase_price']:.2f}"))
            self.table.setItem(i, 6, QTableWidgetItem(f"¥{r['qty'] * r['purchase_price']:.2f}"))
            self.table.setItem(i, 7, QTableWidgetItem(r["purchase_date"]))
            self.table.setItem(i, 8, QTableWidgetItem(r["expiry_date"]))
            self.table.setItem(i, 9, QTableWidgetItem(r["approver"] or ""))
            status_map = {"pending": "待验收", "approved": "已验收", "rejected": "已驳回"}
            status_item = QTableWidgetItem(status_map.get(r["status"], r["status"]))
            if r["status"] == "approved":
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            elif r["status"] == "rejected":
                status_item.setForeground(Qt.GlobalColor.red)
            else:
                status_item.setForeground(Qt.GlobalColor.darkYellow)
            self.table.setItem(i, 10, status_item)

        self.count_lbl.setText(f"共 {total} 条")
