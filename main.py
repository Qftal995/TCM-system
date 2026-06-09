"""中药诊疗管理系统 — 主入口"""
import sys
import os

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QStackedWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon

from database import init_db, get_conn
from widgets.sidebar import Sidebar
from pages.presc_page import PrescPage
from pages.patient_page import PatientPage
from pages.stockin_page import StockinPage
from pages.stockinlog_page import StockinlogPage
from pages.herb_page import HerbPage
from pages.formula_page import FormulaPage
from pages.alert_page import AlertPage
from pages.backup_page import BackupPage

GLOBAL_QSS = """
* {
    font-family: "Microsoft YaHei", "SimSun", "KaiTi";
}

QMainWindow {
    background: #F5F0E8;
}

QWidget#contentArea {
    background: #F5F0E8;
}

QScrollBar:vertical {
    background: #F5F0E8;
    width: 8px;
    border: none;
}
QScrollBar::handle:vertical {
    background: #BCAAA4;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #8D6E63;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background: #F5F0E8;
    height: 8px;
    border: none;
}
QScrollBar::handle:horizontal {
    background: #BCAAA4;
    border-radius: 4px;
    min-width: 30px;
}

QToolTip {
    background: #5C3322;
    color: #E8DFD2;
    border: 1px solid #3E2723;
    padding: 4px 8px;
    font-size: 11px;
}

QMessageBox {
    background: #FFFEF9;
}
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("中药诊疗管理系统")
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.ico")
        if hasattr(sys, '_MEIPASS'):
            icon_path = os.path.join(sys._MEIPASS, "logo.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.resize(1200, 780)
        self.setMinimumSize(960, 600)
        self.setStyleSheet(GLOBAL_QSS)

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.page_changed.connect(self._on_nav)
        root.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.stack.setObjectName("contentArea")
        root.addWidget(self.stack, 1)

        self.presc_page = PrescPage()
        self.patient_page = PatientPage()
        self.stockin_page = StockinPage()
        self.stockinlog_page = StockinlogPage()
        self.herb_page = HerbPage()
        self.formula_page = FormulaPage()
        self.alert_page = AlertPage()
        self.backup_page = BackupPage()

        self.stack.addWidget(self.presc_page)      # 0
        self.stack.addWidget(self.patient_page)    # 1
        self.stack.addWidget(self.stockin_page)    # 2
        self.stack.addWidget(self.stockinlog_page) # 3
        self.stack.addWidget(self.herb_page)       # 4
        self.stack.addWidget(self.formula_page)    # 5
        self.stack.addWidget(self.alert_page)      # 6
        self.stack.addWidget(self.backup_page)     # 7

        self._wire_formula_to_presc()

        self._alert_timer = QTimer(self)
        self._alert_timer.timeout.connect(self._update_alert_badge)
        self._alert_timer.start(30000)
        QTimer.singleShot(500, self._update_alert_badge)

    def _wire_formula_to_presc(self):
        """Replace _use_formula so '去开方' buttons switch to presc page with the formula loaded."""

        def go_presc(fid):
            conn = get_conn()
            cur = conn.cursor()
            cur.execute(
                "SELECT fi.herb_id, h.name, fi.default_grams, h.sell_price "
                "FROM formula_items fi JOIN herbs h ON fi.herb_id=h.id "
                "WHERE fi.formula_id=?", [fid]
            )
            items = cur.fetchall()
            cur.execute("SELECT name FROM formulas WHERE id=?", [fid])
            fname = cur.fetchone()
            conn.close()

            if items:
                self.presc_page.presc_items = [
                    [r["herb_id"], r["name"], r["default_grams"], r["sell_price"]]
                    for r in items
                ]
                self.presc_page._refresh()
                if fname:
                    self.presc_page.formula_search.setText(fname["name"])

            self.sidebar.switch_to(0)
            self.stack.setCurrentIndex(0)

        self.formula_page._use_formula = go_presc

    def _on_nav(self, index):
        self.stack.setCurrentIndex(index)
        page = self.stack.widget(index)
        if hasattr(page, 'load_data'):
            page.load_data()

    def _update_alert_badge(self):
        from datetime import date
        try:
            conn = get_conn()
            cur = conn.cursor()
            today = date.today().isoformat()
            cur.execute(
                "SELECT COUNT(*) as c FROM herbs WHERE stock_qty < 1 AND stock_qty > 0"
            )
            low = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) as c FROM herbs WHERE expiry_date < ?", [today])
            expired = cur.fetchone()["c"]
            conn.close()
            self.sidebar.set_badge(low + expired)
        except Exception:
            pass


def main():
    init_db()
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("tcm.management.system")
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
