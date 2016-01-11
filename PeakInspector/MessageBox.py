from PyQt4 import QtGui


class MessageBox(QtGui.QMessageBox):

    def __init__(self, parent=None):
        QtGui.QMessageBox.__init__(self, parent)
        self.setWindowTitle('Message box')