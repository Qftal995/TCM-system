"""搜索联想输入框"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QListWidget
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QEvent


class SearchBox(QWidget):
    search_triggered = pyqtSignal(str)

    def __init__(self, placeholder="搜索...", max_width=360):
        super().__init__()
        self.setMaximumWidth(max_width)
        self._search_fn = None
        self._dirty_geometry = True

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)

        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        self.input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px; border: 1px solid #C9B99A;
                border-right: none; border-radius: 3px 0 0 3px;
                background: #FFFEF9; color: #3E2723; font-size: 12px;
            }
            QLineEdit:focus { border-color: #7A4C32; }
        """)
        self.input.textChanged.connect(self._on_text_changed)
        self.input.returnPressed.connect(lambda: self._do_search())
        row.addWidget(self.input)

        self.btn = QPushButton("搜索")
        self.btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px; background: #7A4C32; color: #FFFEF9;
                border: none; border-radius: 0 3px 3px 0; font-size: 12px; letter-spacing: 1px;
            }
            QPushButton:hover { background: #5C3322; }
        """)
        self.btn.clicked.connect(lambda: self._do_search())
        row.addWidget(self.btn)
        layout.addLayout(row)

        # Embedded child widget, not a Popup — avoids focus interference
        self.dropdown = QListWidget(self)
        self.dropdown.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.dropdown.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.dropdown.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.dropdown.installEventFilter(self)
        self.dropdown.hide()
        self.dropdown.setStyleSheet("""
            QListWidget {
                border: 1px solid #C9B99A; border-top: none;
                background: #FFFEF9; font-size: 12px; outline: none;
            }
            QListWidget::item {
                padding: 8px 12px; color: #5D4037; border-bottom: 1px solid #F0EBE3;
            }
            QListWidget::item:hover { background: #F5F0E8; color: #3E2723; }
            QListWidget::item:selected { background: #F5F0E8; color: #3E2723; }
        """)
        self.dropdown.itemClicked.connect(self._on_item_clicked)

        self._suggest_timer = QTimer()
        self._suggest_timer.setSingleShot(True)
        self._suggest_timer.setInterval(200)
        self._suggest_timer.timeout.connect(self._show_suggestions)

        self._reset_timer = QTimer()
        self._reset_timer.setSingleShot(True)
        self._reset_timer.setInterval(400)
        self._reset_timer.timeout.connect(self._check_reset)

    def set_search_fn(self, fn):
        self._search_fn = fn

    def eventFilter(self, obj, event):
        if obj == self.dropdown and event.type() == QEvent.Type.KeyPress:
            self.input.setFocus()
            return False
        return super().eventFilter(obj, event)

    def _do_search(self):
        self._suggest_timer.stop()
        self._reset_timer.stop()
        self.dropdown.hide()
        self.search_triggered.emit(self.input.text().strip())
        self.input.setFocus()

    def _on_text_changed(self, text):
        now = text.strip()
        self.dropdown.hide()
        if now:
            self._suggest_timer.start()
            self._reset_timer.stop()
        else:
            self._suggest_timer.stop()
            self._reset_timer.start()

    def _show_suggestions(self):
        text = self.input.text().strip()
        if not text or not self._search_fn:
            self.dropdown.hide()
            return
        results = self._search_fn(text)
        if not results:
            self.dropdown.hide()
            return
        top = self.window()
        if top and self.dropdown.parent() != top:
            self.dropdown.setParent(top)
            self.dropdown.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.dropdown.installEventFilter(self)
        self.dropdown.clear()
        self.dropdown.addItems(results[:8])
        h = min(200, max(20, self.dropdown.sizeHint().height()))
        pos = self.input.mapTo(top or self, self.input.rect().bottomLeft())
        self.dropdown.setGeometry(pos.x(), pos.y(), self.input.width(), h)
        self.dropdown.raise_()
        self.dropdown.show()
        self.input.setFocus()

    def _check_reset(self):
        if not self.input.text().strip():
            self.dropdown.hide()
            self.search_triggered.emit("")
            self.input.setFocus()

    def _on_item_clicked(self, item):
        self.input.setText(item.text())
        self._do_search()

    def text(self):
        return self.input.text().strip()

    def setText(self, txt):
        self._suggest_timer.stop()
        self._reset_timer.stop()
        self.dropdown.hide()
        self.input.blockSignals(True)
        self.input.setText(txt)
        self.input.blockSignals(False)

    def hide_dropdown(self):
        self.dropdown.hide()
