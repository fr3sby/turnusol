"""Arayüzü başlatır: python -m turnusol.gui"""
import os
import sys
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from .tema import uygula
from .ana_pencere import AnaPencere


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('Turnusol'); app.setOrganizationName('Turnusol')
    uygula(app)
    app.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), 'ikonlar', 'uygulama.png')))
    w = AnaPencere(); w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
