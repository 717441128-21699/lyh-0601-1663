from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from services.auth_service import AuthService

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('登录')
        self.setFixedSize(400, 350)
        self.setModal(True)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        title_label = QLabel('二手车检测调度系统')
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet('color: #2c3e50;')
        layout.addWidget(title_label)
        
        subtitle_label = QLabel('车辆检测与交易调度管理')
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet('color: #7f8c8d; font-size: 12px;')
        layout.addWidget(subtitle_label)
        
        layout.addSpacing(20)
        
        username_label = QLabel('用户名')
        username_label.setStyleSheet('color: #34495e; font-weight: bold;')
        layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText('请输入用户名')
        self.username_input.setStyleSheet('''
            QLineEdit {
                padding: 10px;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        ''')
        layout.addWidget(self.username_input)
        
        password_label = QLabel('密码')
        password_label.setStyleSheet('color: #34495e; font-weight: bold;')
        layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText('请输入密码')
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet('''
            QLineEdit {
                padding: 10px;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        ''')
        layout.addWidget(self.password_input)
        
        layout.addSpacing(20)
        
        login_btn = QPushButton('登 录')
        login_btn.setStyleSheet('''
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 12px;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #2573a7;
            }
        ''')
        login_btn.clicked.connect(self.handle_login)
        layout.addWidget(login_btn)
        
        hint_label = QLabel('测试账号：admin / 123456')
        hint_label.setAlignment(Qt.AlignCenter)
        hint_label.setStyleSheet('color: #95a5a6; font-size: 11px;')
        layout.addWidget(hint_label)
    
    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username:
            QMessageBox.warning(self, '提示', '请输入用户名')
            return
        
        if not password:
            QMessageBox.warning(self, '提示', '请输入密码')
            return
        
        user = AuthService.login(username, password)
        
        if user:
            self.accept()
        else:
            QMessageBox.warning(self, '登录失败', '用户名或密码错误')
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.handle_login()
        else:
            super().keyPressEvent(event)
