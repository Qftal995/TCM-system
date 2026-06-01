"""分页组件"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import pyqtSignal


class Paginator(QWidget):
    page_changed = pyqtSignal(int)

    def __init__(self, page_size=10):
        super().__init__()
        self.page_size = page_size
        self.current_page = 1
        self.total_pages = 1
        self.total_count = 0

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        self.count_label = QLabel()
        self.count_label.setStyleSheet("font-size: 12px; color: #5D4037;")
        layout.addWidget(self.count_label)
        layout.addStretch()

        btn_style = """
            QPushButton {
                padding: 6px 10px; border: 1px solid #C9B99A; border-radius: 3px;
                background: #FFFEF9; color: #5D4037; font-size: 11px; min-width: 30px;
            }
            QPushButton:hover { border-color: #7A4C32; color: #3E2723; }
            QPushButton:checked { background: #7A4C32; color: #FFFEF9; border-color: #7A4C32; }
            QPushButton:disabled { color: #BCAAA4; border-color: #D7CCC8; }
        """

        self.prev_btn = QPushButton("上一页")
        self.prev_btn.setStyleSheet(btn_style)
        self.prev_btn.clicked.connect(lambda: self._go(self.current_page - 1))
        layout.addWidget(self.prev_btn)

        self.page_buttons = []
        self._btn_container = QHBoxLayout()
        self._btn_container.setSpacing(3)
        layout.addLayout(self._btn_container)

        self.next_btn = QPushButton("下一页")
        self.next_btn.setStyleSheet(btn_style)
        self.next_btn.clicked.connect(lambda: self._go(self.current_page + 1))
        layout.addWidget(self.next_btn)

    def set_data(self, total_count):
        self.total_count = total_count
        self.total_pages = max(1, (total_count + self.page_size - 1) // self.page_size)
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
        self.count_label.setText(f"共 {total_count} 条")
        self._render_buttons()

    def _render_buttons(self):
        for btn in self.page_buttons:
            self._btn_container.removeWidget(btn)
            btn.deleteLater()
        self.page_buttons.clear()

        pages = self.total_pages
        cp = self.current_page
        visible = []
        if pages <= 7:
            visible = list(range(1, pages + 1))
        else:
            visible = [1]
            if cp > 3:
                visible.append(-1)
            for p in range(max(2, cp - 1), min(pages, cp + 2)):
                visible.append(p)
            if cp < pages - 2:
                visible.append(-1)
            if pages not in visible:
                visible.append(pages)

        for p in visible:
            if p == -1:
                lbl = QLabel("…")
                lbl.setStyleSheet("font-size: 12px; color: #BCAAA4; padding: 6px 4px;")
                self._btn_container.addWidget(lbl)
                self.page_buttons.append(lbl)
            else:
                btn = QPushButton(str(p))
                btn.setStyleSheet(self.prev_btn.styleSheet())
                btn.setCheckable(True)
                btn.setChecked(p == cp)
                btn.clicked.connect(lambda checked, pg=p: self._go(pg))
                self._btn_container.addWidget(btn)
                self.page_buttons.append(btn)

        self.prev_btn.setEnabled(cp > 1)
        self.next_btn.setEnabled(cp < pages)

    def _go(self, page):
        if page < 1 or page > self.total_pages:
            return
        self.current_page = page
        self._render_buttons()
        self.page_changed.emit(page)
