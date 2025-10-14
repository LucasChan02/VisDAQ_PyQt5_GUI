import sys
from PyQt6.QtCore import QDir, Qt
from PyQt6.QtGui import QFont, QPalette
from PyQt6.QtWidgets import (QApplication, QCheckBox, QColorDialog, QDialog,
    QErrorMessage, QFileDialog, QFontDialog, QFrame, QGridLayout,
    QInputDialog, QLabel, QLineEdit, QMessageBox, QPushButton)
from os.path import expanduser


class conditions(QDialog):
    def __init__(self, ui,parent=None):
        super(conditions, self).__init__(parent)
        self.ui = ui
        self.ui.browse_directory.clicked.connect(self.browse_clicked)
        self.my_dir = ""

    def browse_clicked(self):
        # options = QFileDialog.DontResolveSymlinks | QFileDialog.ShowDirsOnly
        self.my_dir = QFileDialog.getExistingDirectory(
            self,
            "Open a folder",
            expanduser("~"),
            QFileDialog.ShowDirsOnly)
        print(self.my_dir)

