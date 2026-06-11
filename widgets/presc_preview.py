"""方子预览网格 — 4列药材名+克数，点击弹出删除"""
from PyQt6.QtWidgets import QWidget, QGridLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class _ClickableFrame(QFrame):
    clicked = pyqtSignal()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)


class PrescPreview(QWidget):
    herb_clicked = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QWidget#prescPreview {
                background: qlineargradient(x1:0 y1:0, x2:1 y2:1, stop:0 #FFFEF9, stop:1 #F8F3E8);
                border: 1px solid #E8DFD2; border-radius: 5px;
            }
        """)
        self.setObjectName("prescPreview")

        self._outer = QGridLayout(self)
        self._outer.setContentsMargins(14, 10, 14, 8)

        badge = QLabel("方 子")
        badge.setStyleSheet("""
            background: #5C3322; color: #E0C88E; font-family: KaiTi, SimSun;
            font-size: 10px; letter-spacing: 3px; padding: 2px 10px; border-radius: 3px;
        """)
        self._outer.addWidget(badge, 0, 0, 1, 4, Qt.AlignmentFlag.AlignLeft)

        self._grid = QGridLayout()
        self._grid.setSpacing(6)
        self._outer.addLayout(self._grid, 1, 0, 1, 4)

        self.set_items([])

    def set_items(self, items):
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not items:
            empty = QLabel("尚未添加药材")
            empty.setStyleSheet("color: #8D6E63; font-size: 13px; letter-spacing: 2px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._grid.addWidget(empty, 0, 0, 1, 4)
            return

        cols = 4
        for i, item in enumerate(items):
            name, grams = item[0], item[1]

            card = _ClickableFrame()
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            card.setStyleSheet("""
                _ClickableFrame {
                    background: rgba(255,255,255,0.7);
                    border: 1px solid rgba(188,170,164,0.25);
                    border-radius: 3px;
                }
                _ClickableFrame:hover {
                    background: rgba(200,164,92,0.08);
                    border-color: rgba(200,164,92,0.3);
                }
            """)
            card.clicked.connect(lambda idx=i: self.herb_clicked.emit(idx))
            card_layout = QGridLayout(card)
            card_layout.setContentsMargins(6, 6, 6, 6)
            card_layout.setSpacing(2)

            name_lbl = QLabel(name)
            name_lbl.setFont(QFont("KaiTi", 13))
            name_lbl.setStyleSheet("color: #3E2723; letter-spacing: 2px; border: none; background: transparent;")
            name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(name_lbl, 0, 0)

            gram_lbl = QLabel(f"{grams}g")
            gram_lbl.setFont(QFont("KaiTi", 10))
            gram_lbl.setStyleSheet("color: #7A4C32; border: none; background: transparent;")
            gram_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(gram_lbl, 1, 0)

            row, col = divmod(i, cols)
            self._grid.addWidget(card, row, col)
