
from PyQt5.QtWidgets import QMessageBox
class MessageBox(QMessageBox):

    def __init__(self, parent=None):
        QMessageBox.__init__(self, parent)
        self.setWindowTitle('Message box')
