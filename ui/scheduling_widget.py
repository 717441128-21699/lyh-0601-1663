from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QLabel, QDateEdit, QMessageBox, QHeaderView, QGroupBox, QComboBox,
    QDialog, QTextEdit, QFormLayout, QLineEdit
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QBrush
from services.scheduling_service import SchedulingService
from services.auth_service import AuthService
from datetime import date

class SchedulingWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.refresh()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel('检测排程管理')
        title.setStyleSheet('font-size: 20px; font-weight: bold; color: #2c3e50;')
        layout.addWidget(title)
        
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat('yyyy-MM-dd')
        self.date_edit.setCalendarPopup(True)
        self.date_edit.dateChanged.connect(self.refresh)
        toolbar.addWidget(QLabel('排程日期:'))
        toolbar.addWidget(self.date_edit)
        
        generate_btn = QPushButton('⚡ 生成排程')
        generate_btn.setStyleSheet('''
            QPushButton {
                background-color: #e67e22;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        ''')
        generate_btn.clicked.connect(self.generate_schedule)
        toolbar.addWidget(generate_btn)
        
        approve_all_btn = QPushButton('✅ 批量审批')
        approve_all_btn.setStyleSheet('''
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        ''')
        approve_all_btn.clicked.connect(self.approve_all)
        toolbar.addWidget(approve_all_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        pending_group = QGroupBox('待审批排程')
        pending_layout = QVBoxLayout(pending_group)
        
        self.pending_table = QTableWidget()
        self.pending_table.setColumnCount(9)
        self.pending_table.setHorizontalHeaderLabels([
            'ID', 'VIN码', '品牌', '型号', '检测项目', '检测师', '工位', 
            '时间', '优先级'
        ])
        self.pending_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.pending_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.pending_table.setEditTriggers(QTableWidget.NoEditTriggers)
        pending_layout.addWidget(self.pending_table)
        
        pending_btn_layout = QHBoxLayout()
        
        approve_btn = QPushButton('通过审批')
        approve_btn.setStyleSheet('background-color: #27ae60; color: white; padding: 6px 12px; border-radius: 4px; border: none;')
        approve_btn.clicked.connect(lambda: self.handle_approval('approve'))
        pending_btn_layout.addWidget(approve_btn)
        
        reject_btn = QPushButton('驳回')
        reject_btn.setStyleSheet('background-color: #e74c3c; color: white; padding: 6px 12px; border-radius: 4px; border: none;')
        reject_btn.clicked.connect(lambda: self.handle_approval('reject'))
        pending_btn_layout.addWidget(reject_btn)
        
        pending_btn_layout.addStretch()
        pending_layout.addLayout(pending_btn_layout)
        
        layout.addWidget(pending_group, 1)
        
        approved_group = QGroupBox('已安排排程')
        approved_layout = QVBoxLayout(approved_group)
        
        self.approved_table = QTableWidget()
        self.approved_table.setColumnCount(9)
        self.approved_table.setHorizontalHeaderLabels([
            'ID', 'VIN码', '品牌', '型号', '检测项目', '检测师', '工位',
            '时间', '状态'
        ])
        self.approved_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.approved_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.approved_table.setEditTriggers(QTableWidget.NoEditTriggers)
        approved_layout.addWidget(self.approved_table)
        
        layout.addWidget(approved_group, 1)
    
    def refresh(self):
        self.refresh_pending()
        self.refresh_approved()
    
    def refresh_pending(self):
        schedules = SchedulingService.get_pending_approval_schedules()
        
        self.pending_table.setRowCount(len(schedules))
        
        for row, sched in enumerate(schedules):
            self.pending_table.setItem(row, 0, QTableWidgetItem(str(sched['id'])))
            self.pending_table.setItem(row, 1, QTableWidgetItem(sched['vin']))
            self.pending_table.setItem(row, 2, QTableWidgetItem(sched['brand']))
            self.pending_table.setItem(row, 3, QTableWidgetItem(sched.get('model', '')))
            self.pending_table.setItem(row, 4, QTableWidgetItem(sched.get('inspection_type', '')))
            self.pending_table.setItem(row, 5, QTableWidgetItem(sched.get('inspector_name', '-')))
            self.pending_table.setItem(row, 6, QTableWidgetItem(sched.get('workstation_name', '-')))
            
            time_str = f"{sched.get('start_time', '-')} - {sched.get('end_time', '-')}"
            self.pending_table.setItem(row, 7, QTableWidgetItem(time_str))
            
            priority = sched.get('priority', 0)
            priority_text = '高' if priority >= 3 else ('中' if priority >= 2 else '低')
            priority_item = QTableWidgetItem(priority_text)
            if priority >= 3:
                priority_item.setForeground(QBrush(QColor('#e74c3c')))
            self.pending_table.setItem(row, 8, priority_item)
    
    def refresh_approved(self):
        schedule_date = self.date_edit.date().toString('yyyy-MM-dd')
        schedules = SchedulingService.get_schedules_by_date(schedule_date)
        approved_schedules = [s for s in schedules if s['status'] == 'approved']
        
        self.approved_table.setRowCount(len(approved_schedules))
        
        for row, sched in enumerate(approved_schedules):
            self.approved_table.setItem(row, 0, QTableWidgetItem(str(sched['id'])))
            self.approved_table.setItem(row, 1, QTableWidgetItem(sched['vin']))
            self.approved_table.setItem(row, 2, QTableWidgetItem(sched['brand']))
            self.approved_table.setItem(row, 3, QTableWidgetItem(sched.get('model', '')))
            self.approved_table.setItem(row, 4, QTableWidgetItem(sched.get('inspection_type', '')))
            self.approved_table.setItem(row, 5, QTableWidgetItem(sched.get('inspector_name', '-')))
            self.approved_table.setItem(row, 6, QTableWidgetItem(sched.get('workstation_name', '-')))
            
            time_str = f"{sched.get('start_time', '-')} - {sched.get('end_time', '-')}"
            self.approved_table.setItem(row, 7, QTableWidgetItem(time_str))
            
            status_item = QTableWidgetItem(self.get_status_text(sched['status']))
            status_item.setForeground(QBrush(self.get_status_color(sched['status'])))
            self.approved_table.setItem(row, 8, status_item)
    
    def get_status_text(self, status):
        status_map = {
            'pending_approval': '待审批',
            'approved': '已批准',
            'rejected': '已驳回',
            'in_progress': '进行中',
            'completed': '已完成',
            'adjustment_pending': '调整待批',
            'cancelled': '已取消',
        }
        return status_map.get(status, status)
    
    def get_status_color(self, status):
        color_map = {
            'pending_approval': QColor('#f39c12'),
            'approved': QColor('#27ae60'),
            'rejected': QColor('#e74c3c'),
            'in_progress': QColor('#3498db'),
            'completed': QColor('#27ae60'),
            'adjustment_pending': QColor('#e67e22'),
            'cancelled': QColor('#7f8c8d'),
        }
        return color_map.get(status, QColor('#333'))
    
    def generate_schedule(self):
        schedule_date = self.date_edit.date().toPython()
        
        reply = QMessageBox.question(
            self, '确认生成',
            f'确定要生成 {schedule_date} 的检测排程吗？',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                schedules = SchedulingService.generate_daily_schedule(schedule_date)
                QMessageBox.information(self, '成功', f'成功生成 {len(schedules)} 条排程记录')
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, '错误', f'生成排程失败: {str(e)}')
    
    def handle_approval(self, action):
        current_row = self.pending_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, '提示', '请先选择一条待审批排程')
            return
        
        schedule_id = int(self.pending_table.item(current_row, 0).text())
        user = AuthService.get_current_user()
        
        if action == 'approve':
            try:
                SchedulingService.approve_schedule(schedule_id, user['id'])
                QMessageBox.information(self, '成功', '排程已通过审批')
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, '错误', f'审批失败: {str(e)}')
        else:
            reason, ok = self.get_reject_reason()
            if ok:
                try:
                    SchedulingService.reject_schedule(schedule_id, user['id'], reason)
                    QMessageBox.information(self, '成功', '排程已驳回')
                    self.refresh()
                except Exception as e:
                    QMessageBox.critical(self, '错误', f'驳回失败: {str(e)}')
    
    def approve_all(self):
        pending = SchedulingService.get_pending_approval_schedules()
        if not pending:
            QMessageBox.information(self, '提示', '没有待审批的排程')
            return
        
        reply = QMessageBox.question(
            self, '确认批量审批',
            f'确定要审批通过所有 {len(pending)} 条待审批排程吗？',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            user = AuthService.get_current_user()
            success_count = 0
            for sched in pending:
                try:
                    SchedulingService.approve_schedule(sched['id'], user['id'])
                    success_count += 1
                except:
                    pass
            
            QMessageBox.information(self, '完成', f'成功审批 {success_count} 条排程')
            self.refresh()
    
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
