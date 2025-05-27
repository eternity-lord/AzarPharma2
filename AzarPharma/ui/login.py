# ui/login.py

from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QSizePolicy, QMessageBox
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt

from ui.dashboard import MainDashboard
class LoginPage(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("سیستم آذرفارما")
        self.setGeometry(200, 100, 400, 450)
        self.setMinimumSize(300, 300) 

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(35)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.addStretch(1)

        title_label = QLabel("ورود به سیستم") 
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(True) 
        layout.addWidget(title_label)

        self.username_label = QLabel("نام کاربری:") 
        layout.addWidget(self.username_label)
        self.username_input = QLineEdit()
        self.username_input.setText("")
        self.username_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.username_input)

        self.password_label = QLabel("رمز عبور:")
        layout.addWidget(self.password_label)
        self.password_input = QLineEdit() 
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setText("")
        self.password_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.password_input)

        self.login_button = QPushButton("ورود")
        
        self.login_button.clicked.connect(self.check_login)
        self.login_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.login_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(1)

    def check_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        if username == "Azar" and password == "1394":
            self.main_dashboard = MainDashboard()
            self.main_dashboard.showMaximized()
            self.close()
        else:
            QMessageBox.warning(self, "خطا", "نام کاربری یا رمز عبور اشتباه است!")