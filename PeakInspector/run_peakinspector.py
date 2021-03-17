# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import QApplication
from MainWindow import MainWindow


def run_peakinspector():
    app = QApplication(sys.argv)
    gui = MainWindow()
    gui.showMaximized()
    sys.exit(app.exec_())

if __name__ == '__main__':
    run_peakinspector()


# TODO secondary tab in GUI with output options
# TODO multiple output formats and unified format of code for output production
# TODO cant open data with small amount of points - probably because of the SG filter
# TODO fix layout
# TODO mpl style change
