"""左侧导航栏"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPalette, QColor


NAV_ITEMS = [
    ("患者登记与开方", "presc"),
    ("患者信息管理", "patients"),
    ("药材入库", "stockin"),
    ("入库记录", "stockinlog"),
    ("中药药材管理", "herbs"),
    ("方子管理", "formulas"),
    ("预警面板", "alerts"),
    ("数据备份恢复", "backup"),
]


class Sidebar(QWidget):
    page_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setObjectName("sidebar")
        self.setFixedWidth(220)
        self.setAutoFillBackground(True)

        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor("#5C3322"))
        self.setPalette(pal)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        hdr = QVBoxLayout()
        hdr.setContentsMargins(18, 24, 18, 14)
        icon = QLabel("\U0001F33F")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 28px; background: transparent;")
        hdr.addWidget(icon)
        title = QLabel("中药诊疗管理系统")
        title.setObjectName("navTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "color: #E0C88E; font-family: KaiTi, SimSun; font-size: 15px; "
            "letter-spacing: 3px; background: transparent;"
        )
        hdr.addWidget(title)
        sep = QHBoxLayout()
        sep.setContentsMargins(0, 8, 0, 0)
        line = QLabel()
        line.setFixedSize(50, 2)
        line.setStyleSheet("background: #C8A45C; border-radius: 1px;")
        sep.addStretch()
        sep.addWidget(line)
        sep.addStretch()
        hdr.addLayout(sep)
        layout.addLayout(hdr)

        # Nav buttons
        self.buttons = []
        self._badge = None
        for i, (text, page) in enumerate(NAV_ITEMS):
            btn = QPushButton(f"  ◦  {text}")
            btn.setObjectName("navBtn")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if i == 0:
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, idx=i: self._on_click(idx))
            btn.setStyleSheet(self._btn_style())
            self.buttons.append(btn)

            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.addWidget(btn)
            row.addStretch()
            if text == "预警面板":
                self._badge = QLabel("0")
                self._badge.setObjectName("navBadge")
                self._badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self._badge.setStyleSheet(
                    "background: #D4645C; color: #fff; font-size: 9px; "
                    "padding: 2px 7px; border-radius: 8px; min-width: 18px;"
                )
                row.addWidget(self._badge)
                row.addSpacing(12)
            layout.addLayout(row)

        layout.addStretch()
        ver = QLabel("v1.0 · 单机版")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver.setStyleSheet(
            "color: rgba(232,223,210,0.5); font-size: 10px; "
            "letter-spacing: 1px; background: transparent;"
        )
        layout.addWidget(ver)
        layout.addSpacing(12)

    def _btn_style(self):
        return (
            "QPushButton {"
            "  text-align: left; padding: 10px 20px;"
            "  border: none; border-left: 3px solid transparent;"
            "  color: #E8DFD2; font-size: 13px;"
            "  letter-spacing: 1px; background: transparent;"
            "}"
            "QPushButton:hover {"
            "  color: #FFFEF9;"
            "  background: rgba(255,255,255,0.06);"
            "}"
            "QPushButton:checked {"
            "  color: #FFFEF9;"
            "  background: rgba(200,164,92,0.15);"
            "  border-left: 3px solid #C8A45C;"
            "}"
        )

    def _on_click(self, index):
        for i, btn in enumerate(self.buttons):
            btn.setChecked(i == index)
        self.page_changed.emit(index)

    def set_badge(self, count):
        if self._badge:
            self._badge.setText(str(count))

    def switch_to(self, index):
        if 0 <= index < len(self.buttons):
            self.buttons[index].setChecked(True)
            for i, btn in enumerate(self.buttons):
                if i != index:
                    btn.setChecked(False)
