from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QStackedWidget, QLabel, QStatusBar, QToolBar, QMessageBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont, QAction
from services.auth_service import AuthService

from ui.vehicle_management import VehicleManagementWidget
from ui.scheduling_widget import SchedulingWidget
from ui.inspection_widget import InspectionWidget
from ui.trading_widget import TradingWidget
from ui.statistics_widget import StatisticsWidget
from ui.approval_widget import ApprovalWidget
from ui.parking_map_widget import ParkingMapWidget
from ui.login_dialog import LoginDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('二手车交易市场车辆检测与交易调度系统')
        self.setMinimumSize(1200, 800)
        
        self.current_user = None
        self.setup_ui()
    
    def setup_ui(self):
        self.show_login_dialog()
    
    def show_login_dialog(self):
        dialog = LoginDialog(self)
        if dialog.exec():
            self.current_user = AuthService.get_current_user()
            self.init_main_ui()
        else:
            self.close()
    
    def init_main_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        sidebar = self.create_sidebar()
        sidebar.setFixedWidth(220)
        main_layout.addWidget(sidebar)
        
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)
        
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage(f'欢迎，{self.current_user["real_name"]} | 角色：{self.get_role_name(self.current_user["role"])}')
        
        self.setup_content_pages()
        self.setup_toolbar()
    
    def create_sidebar(self):
        sidebar = QListWidget()
        sidebar.setStyleSheet('''
            QListWidget {
                background-color: #2c3e50;
                color: white;
                border: none;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 15px 20px;
                border-bottom: 1px solid #34495e;
            }
            QListWidget::item:hover {
                background-color: #34495e;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        ''')
        
        menu_items = self.get_menu_items()
        
        for icon_text, page_name in menu_items:
            item = QListWidgetItem(icon_text)
            item.setData(Qt.UserRole, page_name)
            sidebar.addItem(item)
        
        sidebar.currentRowChanged.connect(self.on_sidebar_changed)
        sidebar.setCurrentRow(0)
        
        return sidebar
    
    def get_menu_items(self):
        role = self.current_user['role']
        all_menus = [
            ('🚗 车辆管理', 'vehicle'),
            ('📋 检测排程', 'scheduling'),
            ('🔧 检测终端', 'inspection'),
            ('💰 交易管理', 'trading'),
            ('📊 统计分析', 'statistics'),
            ('🅿️ 车库平面图', 'parking_map'),
            ('✅ 审批中心', 'approval'),
        ]
        
        if role == 'admin':
            return all_menus
        elif role == 'chief_inspector':
            return [m for m in all_menus if m[1] in ['vehicle', 'scheduling', 'inspection', 'statistics', 'parking_map', 'approval']]
        elif role == 'inspector':
            return [m for m in all_menus if m[1] in ['vehicle', 'scheduling', 'inspection', 'parking_map']]
        elif role == 'sales_manager':
            return [m for m in all_menus if m[1] in ['vehicle', 'trading', 'statistics', 'parking_map', 'approval']]
        elif role == 'sales_person':
            return [m for m in all_menus if m[1] in ['vehicle', 'trading', 'parking_map']]
        elif role == 'marketing':
            return [m for m in all_menus if m[1] in ['vehicle', 'statistics', 'parking_map']]
        
        return all_menus
    
    def setup_content_pages(self):
        self.vehicle_page = VehicleManagementWidget()
        self.content_stack.addWidget(self.vehicle_page)
        
        self.scheduling_page = SchedulingWidget()
        self.content_stack.addWidget(self.scheduling_page)
        
        self.inspection_page = InspectionWidget()
        self.content_stack.addWidget(self.inspection_page)
        
        self.trading_page = TradingWidget()
        self.content_stack.addWidget(self.trading_page)
        
        self.statistics_page = StatisticsWidget()
        self.content_stack.addWidget(self.statistics_page)
        
        self.parking_map_page = ParkingMapWidget()
        self.content_stack.addWidget(self.parking_map_page)
        
        self.approval_page = ApprovalWidget()
        self.content_stack.addWidget(self.approval_page)
    
    def setup_toolbar(self):
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setMovable(False)
        toolbar.setStyleSheet('''
            QToolBar {
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
                padding: 5px;
            }
        ''')
        self.addToolBar(toolbar)
        
        refresh_action = QAction('🔄 刷新', self)
        refresh_action.triggered.connect(self.refresh_current_page)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        logout_action = QAction('🚪 退出登录', self)
        logout_action.triggered.connect(self.logout)
        toolbar.addAction(logout_action)
    
    def on_sidebar_changed(self, index):
        menu_items = self.get_menu_items()
        if index < len(menu_items):
            page_name = menu_items[index][1]
            page_index = self.get_page_index(page_name)
            if page_index >= 0:
                self.content_stack.setCurrentIndex(page_index)
                self.refresh_current_page()
    
    def get_page_index(self, page_name):
        page_map = {
            'vehicle': 0,
            'scheduling': 1,
            'inspection': 2,
            'trading': 3,
            'statistics': 4,
            'parking_map': 5,
            'approval': 6,
        }
        return page_map.get(page_name, -1)
    
    def refresh_current_page(self):
        current_widget = self.content_stack.currentWidget()
        if hasattr(current_widget, 'refresh'):
            current_widget.refresh()
    
    def get_role_name(self, role):
        role_names = {
            'admin': '系统管理员',
            'chief_inspector': '检测主管',
            'inspector': '检测师',
            'sales_manager': '销售经理',
            'sales_person': '销售员',
            'marketing': '营销人员',
        }
        return role_names.get(role, role)
    
    def logout(self):
        AuthService.logout()
        self.current_user = None
        self.hide()
        self.show_login_dialog()
