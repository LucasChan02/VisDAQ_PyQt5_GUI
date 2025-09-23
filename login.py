from PyQt6 import QtWidgets
import pickle
import hashlib

class Login(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(Login, self).__init__(parent)
        self.textName = QtWidgets.QLineEdit(self)
        self.textPass = QtWidgets.QLineEdit(self)
        self.textPass.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.username = QtWidgets.QLabel(self)
        self.password = QtWidgets.QLabel(self)
        self.username.setText("Username")
        self.password.setText("Password")
        self.buttonLogin = QtWidgets.QPushButton('Login', self)
        self.buttonLogin.clicked.connect(self.handleLogin)

        self.avalaible = pickle.load(open("p.p","rb"))
        username_layout = QtWidgets.QHBoxLayout()
        password_layout = QtWidgets.QHBoxLayout()
        layout = QtWidgets.QVBoxLayout(self)

        username_layout.addWidget(self.username)
        username_layout.addWidget(self.textName)

        password_layout.addWidget(self.password)
        password_layout.addWidget(self.textPass)

        layout.addLayout(username_layout)
        layout.addLayout(password_layout)
        layout.addWidget(self.buttonLogin)

    def handleLogin(self):
        hashed_password = hashlib.sha512(self.textPass.text().encode()).hexdigest()
        if (self.textName.text() == self.avalaible[0][0] and
            hashed_password == self.avalaible[0][1]):
            self.accept()
        else:
            QtWidgets.QMessageBox.warning(
                self, 'Error', 'Bad user or password')
