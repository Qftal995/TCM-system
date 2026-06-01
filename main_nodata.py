"""中药诊疗管理系统 — 无数据版入口"""
import sys
from PyQt6.QtWidgets import QApplication
from database import init_db
from main import MainWindow

if __name__ == "__main__":
    init_db(seed=False)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
