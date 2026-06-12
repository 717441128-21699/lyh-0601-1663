from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QLabel, QMessageBox, QHeaderView, QGroupBox, QDialog, QTextEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush
from services.approval_service import ApprovalService
from services.auth_service import AuthService

class ApprovalWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.refresh()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel('审批中心')
        title.setStyleSheet('font-size: 20px; font-weight: bold; color: #2c3e50;')
        layout.addWidget(title)
        
        info_label = QLabel('待我审批的事项')
        info_label.setStyleSheet('font-size: 14px; color: #7f8c8d;')
        layout.addWidget(info_label)
        
        self.approval_table = QTableWidget()
        self.approval_table.setColumnCount(7)
        self.approval_table.setHorizontalHeaderLabels([
            'ID', '类型', '标题', '申请人', '申请时间', '状态', '原因'
        ])
        self.approval_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.approval_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.approval_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.approval_table, 1)
        
        btn_layout = QHBoxLayout()
        
        approve_btn = QPushButton('✅ 通过')
        approve_btn.setStyleSheet('''
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px 24px;
                border-radius: 4px;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #229954; }
        ''')
        approve_btn.clicked.connect(lambda: self.handle_approval('approve'))
        btn_layout.addWidget(approve_btn)
        
        reject_btn = QPushButton('❌ 驳回')
        reject_btn.setStyleSheet('''
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 10px 24px;
                border-radius: 4px;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #c0392b; }
        ''')
        reject_btn.clicked.connect(lambda: self.handle_approval('reject'))
        btn_layout.addWidget(reject_btn)
        
        detail_btn = QPushButton('📋 查看详情')
        detail_btn.setStyleSheet('''
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 24px;
                border-radius: 4px;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #2980b9; }
        ''')
        detail_btn.clicked.connect(self.show_detail)
        btn_layout.addWidget(detail_btn)
        
        refresh_btn = QPushButton('🔄 刷新')
        refresh_btn.clicked.connect(self.refresh)
        btn_layout.addWidget(refresh_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        history_group = QGroupBox('已处理的审批')
        history_layout = QVBoxLayout(history_group)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(7)
        self.history_table.setHorizontalHeaderLabels([
            'ID', '类型', '标题', '申请人', '处理时间', '状态', '审批意见'
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        history_layout.addWidget(self.history_table)
        
        layout.addWidget(history_group, 1)
    
    def refresh(self):
        user = AuthService.get_current_user()
        if not user:
            return
        
        approver_role = user['role']
        
        pending = ApprovalService.get_pending_approvals(approver_role)
        
        self.approval_table.setRowCount(len(pending))
        
        for row, request in enumerate(pending):
            self.approval_table.setItem(row, 0, QTableWidgetItem(str(request['id'])))
            self.approval_table.setItem(row, 1, QTableWidgetItem(self.get_type_text(request['request_type'])))
            self.approval_table.setItem(row, 2, QTableWidgetItem(request.get('title', '')))
            self.approval_table.setItem(row, 3, QTableWidgetItem(request.get('applicant_name', '-')))
            self.approval_table.setItem(row, 4, QTableWidgetItem(request.get('created_at', '')[:16]))
            
            status_item = QTableWidgetItem(self.get_status_text(request['status']))
            status_item.setForeground(QBrush(self.get_status_color(request['status'])))
            self.approval_table.setItem(row, 5, status_item)
            
            self.approval_table.setItem(row, 6, QTableWidgetItem(request.get('reason', '')[:30]))
        
        from db.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.*, u.real_name as applicant_name
            FROM approval_requests a
            LEFT JOIN users u ON a.applicant_id = u.id
            WHERE a.approver_role = ? AND a.status != 'pending'
            ORDER BY a.approved_at DESC
            LIMIT 20
        ''', (approver_role,))
        history = [dict(r) for r in cursor.fetchall()]
        conn.close()
        
        self.history_table.setRowCount(len(history))
        
        for row, request in enumerate(history):
            self.history_table.setItem(row, 0, QTableWidgetItem(str(request['id'])))
            self.history_table.setItem(row, 1, QTableWidgetItem(self.get_type_text(request['request_type'])))
            self.history_table.setItem(row, 2, QTableWidgetItem(request.get('title', '')))
            self.history_table.setItem(row, 3, QTableWidgetItem(request.get('applicant_name', '-')))
            self.history_table.setItem(row, 4, QTableWidgetItem(request.get('approved_at', '')[:16] if request.get('approved_at') else '-'))
            
            status_item = QTableWidgetItem(self.get_status_text(request['status']))
            status_item.setForeground(QBrush(self.get_status_color(request['status'])))
            self.history_table.setItem(row, 5, status_item)
            
            self.history_table.setItem(row, 6, QTableWidgetItem(request.get('approval_notes', '-')[:30]))
    
    def get_type_text(self, req_type):
        type_map = {
            'schedule_adjustment': '排程调整',
            'price_adjustment': '价格调整',
            'offer_approval': '出价审批',
            'vehicle_entry': '车辆入库',
        }
        return type_map.get(req_type, req_type)
    
    def get_status_text(self, status):
        status_map = {
            'pending': '待审批',
            'approved': '已通过',
            'rejected': '已驳回',
        }
        return status_map.get(status, status)
    
    def get_status_color(self, status):
        color_map = {
            'pending': QColor('#f39c12'),
            'approved': QColor('#27ae60'),
            'rejected': QColor('#e74c3c'),
        }
        return color_map.get(status, QColor('#333'))
    
    def handle_approval(self, action):
        current_row = self.approval_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, '提示', '请先选择一条待审批事项')
            return
        
        request_id = int(self.approval_table.item(current_row, 0).text())
        user = AuthService.get_current_user()
        
        if action == 'approve':
            reply = QMessageBox.question(
                self, '确认通过',
                '确定要通过此审批吗？',
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                try:
                    ApprovalService.approve_request(request_id, user['id'])
                    QMessageBox.information(self, '成功', '审批已通过')
                    self.refresh()
                except Exception as e:
                    QMessageBox.critical(self, '错误', f'审批失败: {str(e)}')
        else:
            reason, ok = self.get_reject_reason()
            if ok:
                try:
                    ApprovalService.reject_request(request_id, user['id'], reason)
                    QMessageBox.information(self, '成功', '已驳回')
                    self.refresh()
                except Exception as e:
                    QMessageBox.critical(self, '错误', f'驳回失败: {str(e)}')
    
    def get_reject_reason(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('驳回原因')
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel('请输入驳回原因:'))
        
        reason_edit = QTextEdit()
        reason_edit.setMaximumHeight(150)
        layout.addWidget(reason_edit)
        
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton('确定')
        ok_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton('取消')
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        if dialog.exec():
            return reason_edit.toPlainText(), True
        return '', False
    
    def show_detail(self):
        current_row = self.approval_table.currentRow()
        if current_row < 0:
            current_row = self.history_table.currentRow()
            table = self.history_table
        else:
            table = self.approval_table
        
        if current_row < 0:
            QMessageBox.warning(self, '提示', '请先选择一条记录')
            return
        
        request_id = int(table.item(current_row, 0).text())
        
        from db.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.*, u.real_name as applicant_name
            FROM approval_requests a
            LEFT JOIN users u ON a.applicant_id = u.id
            WHERE a.id = ?
        ''', (request_id,))
        request = cursor.fetchone()
        conn.close()
        
        if not request:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle('审批详情')
        dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout(dialog)
        
        detail_text = QTextEdit()
        detail_text.setReadOnly(True)
        detail_text.setText(f'''审批详情
{'='*50}
申请类型: {self.get_type_text(request['request_type'])}
标题: {request.get('title', '-')}
申请人: {request.get('applicant_name', '-')}
申请时间: {request.get('created_at', '-')}
状态: {self.get_status_text(request['status'])}

申请原因:
{request.get('reason', '-')}

{'审批意见:' if request.get('approval_notes') else ''}
{request.get('approval_notes', '')}
''')
        layout.addWidget(detail_text)
        
        close_btn = QPushButton('关闭')
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
