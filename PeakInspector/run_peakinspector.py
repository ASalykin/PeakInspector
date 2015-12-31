# -*- coding: utf-8 -*-
import sys
from PyQt4 import QtGui
from MainWindow import MainWindow
from OnClick import OnClick


def run_peakinspector():
    app = QtGui.QApplication(sys.argv)
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
